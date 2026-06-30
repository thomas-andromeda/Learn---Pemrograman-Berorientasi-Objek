# database.py
"""
Modul pengelolaan database SQLite untuk aplikasi Court Rent.
Berisi: koneksi, eksekusi query, setup tabel, dan seed data awal.
"""

import sqlite3
import hashlib
import datetime
import pandas as pd
from konfigurasi import (
    DB_PATH, HARGA_FUTSAL, HARGA_BADMINTON, HARGA_TENIS
)


# Koneksi database
def get_db_connection() -> sqlite3.Connection | None:
    """Buka dan kembalikan koneksi baru ke database SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10,
                               detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(f"[database.py] ERROR koneksi database: {e}")
        return None


# Helper query
def execute_query(query: str, params: tuple | None = None):
    """Eksekusi query INSERT / UPDATE / DELETE. Kembalikan lastrowid jika INSERT."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        conn.rollback()
        print(f"[database.py] ERROR query: {e} | Query: {query[:80]}")
        return None
    finally:
        conn.close()


def fetch_query(query: str, params: tuple | None = None, fetch_all: bool = True):
    """Eksekusi SELECT query. Kembalikan list rows atau single row."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchall() if fetch_all else cursor.fetchone()
    except sqlite3.Error as e:
        print(f"[database.py] ERROR fetch: {e} | Query: {query[:80]}")
        return None
    finally:
        conn.close()


def get_dataframe(query: str, params: tuple | None = None) -> pd.DataFrame:
    """Eksekusi SELECT query dan kembalikan hasil sebagai Pandas DataFrame."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"[database.py] ERROR dataframe: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


# Setup tabel
def setup_database() -> bool:
    """Buat semua tabel jika belum ada: users, lapangan, booking."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL CHECK(role IN ('admin','kasir','pelanggan')),
                nama_lengkap  TEXT    DEFAULT ''
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lapangan (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                nama           TEXT    NOT NULL,
                jenis          TEXT    NOT NULL CHECK(jenis IN ('Futsal','Badminton','Tenis')),
                harga_per_jam  REAL    NOT NULL CHECK(harga_per_jam > 0),
                is_indoor      INTEGER NOT NULL DEFAULT 1,
                atribut_khusus TEXT    DEFAULT ''
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS booking (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_tim     TEXT    NOT NULL,
                id_lapangan  INTEGER NOT NULL REFERENCES lapangan(id),
                tanggal      DATE    NOT NULL,
                jam_mulai    TEXT    NOT NULL,
                durasi_menit INTEGER NOT NULL CHECK(durasi_menit >= 30),
                id_user      INTEGER NOT NULL REFERENCES users(id),
                total_biaya  REAL    NOT NULL,
                status       TEXT    NOT NULL DEFAULT 'Aktif'
                             CHECK(status IN ('Aktif','Selesai','Dibatalkan'))
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT    PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT    NOT NULL,
                expires_at TEXT    NOT NULL
            );
        """)

        conn.commit()
        print("[database.py] Tabel berhasil dibuat/diverifikasi.")
        return True

    except sqlite3.Error as e:
        conn.rollback()
        print(f"[database.py] ERROR setup tabel: {e}")
        return False
    finally:
        conn.close()


# Seed data awal
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def seed_data() -> bool:
    """Isi data awal jika tabel masih kosong (3 user + 6 lapangan dummy)."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            users = [
                ("admin",     _hash("admin123"),     "admin",     "Administrator"),
                ("kasir",     _hash("kasir123"),     "kasir",     "Kasir Utama"),
                ("pelanggan", _hash("pelanggan123"), "pelanggan", "Pelanggan Umum"),
            ]
            cursor.executemany(
                "INSERT INTO users (username, password_hash, role, nama_lengkap) VALUES (?,?,?,?)",
                users
            )
            print("[database.py] Seed: 3 user default ditambahkan.")

        cursor.execute("SELECT COUNT(*) FROM lapangan")
        if cursor.fetchone()[0] == 0:
            lapangan_data = [
                ("Futsal A",      "Futsal",    90000.0,    1, "Sintetis"),
                ("Futsal B",      "Futsal",    80000.0,    0, "Interlock"),
                ("Badminton 1",   "Badminton", 50000.0,    1, "Vinyl"),
                ("Badminton 2",   "Badminton", 60000.0,    1, "Kayu"),
                ("Tenis Utama",   "Tenis",     100000.0,   0, "Hard Court"),
                ("Tenis Premium", "Tenis",     120000.0,   0, "Clay"),
            ]
            cursor.executemany(
                "INSERT INTO lapangan (nama, jenis, harga_per_jam, is_indoor, atribut_khusus) "
                "VALUES (?,?,?,?,?)",
                lapangan_data
            )
            print("[database.py] Seed: 6 lapangan dummy ditambahkan.")

        conn.commit()
        return True

    except sqlite3.Error as e:
        conn.rollback()
        print(f"[database.py] ERROR seed data: {e}")
        return False
    finally:
        conn.close()


def migrate_prices_in_db() -> bool:
    """Perbarui harga lapangan yang sudah ada di database ke harga baru yang lebih murah."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE lapangan SET harga_per_jam = 90000.0 WHERE nama = 'Futsal A' AND jenis = 'Futsal'")
        cursor.execute("UPDATE lapangan SET harga_per_jam = 80000.0 WHERE nama = 'Futsal B' AND jenis = 'Futsal'")
        cursor.execute("UPDATE lapangan SET harga_per_jam = 50000.0 WHERE nama = 'Badminton 1' AND jenis = 'Badminton'")
        cursor.execute("UPDATE lapangan SET harga_per_jam = 60000.0 WHERE nama = 'Badminton 2' AND jenis = 'Badminton'")
        cursor.execute("UPDATE lapangan SET harga_per_jam = 100000.0 WHERE nama = 'Tenis Utama' AND jenis = 'Tenis'")
        cursor.execute("UPDATE lapangan SET harga_per_jam = 120000.0 WHERE nama = 'Tenis Premium' AND jenis = 'Tenis'")
        conn.commit()
        print("[database.py] Migrasi harga sewa lapangan berhasil.")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"[database.py] ERROR migrasi harga sewa: {e}")
        return False
    finally:
        conn.close()


def migrate_existing_bookings_cost() -> bool:
    """Rekalkulasi total_biaya untuk semua booking yang ada di database berdasarkan harga flat baru."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        
        # Ambil semua booking beserta harga_per_jam lapangan saat ini
        cursor.execute("""
            SELECT b.id, b.durasi_menit, l.harga_per_jam
            FROM booking b
            JOIN lapangan l ON b.id_lapangan = l.id
        """)
        bookings = cursor.fetchall()
        
        for b in bookings:
            booking_id = b["id"]
            durasi = b["durasi_menit"]
            harga_per_jam = b["harga_per_jam"]
            
            # Hitung total biaya flat: (durasi_menit / 60) * harga_per_jam
            new_total = round((durasi / 60) * harga_per_jam, 0)
            
            # Update total_biaya di database
            cursor.execute("UPDATE booking SET total_biaya = ? WHERE id = ?", (new_total, booking_id))
            print(f"[database.py] Booking #{booking_id} diperbarui: Durasi {durasi}mnt, Harga/jam {harga_per_jam} -> Total {new_total}")
            
        conn.commit()
        print("[database.py] Rekalkulasi biaya seluruh booking selesai.")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"[database.py] ERROR rekalkulasi biaya booking: {e}")
        return False
    finally:
        conn.close()


def init_db() -> bool:
    """Inisialisasi database: setup tabel, seed data awal, migrasi harga lapangan, dan biaya booking."""
    ok_setup = setup_database()
    ok_seed  = seed_data()
    ok_mig   = migrate_prices_in_db()
    ok_mig_b = migrate_existing_bookings_cost()
    return ok_setup and ok_seed and ok_mig and ok_mig_b


# Operasi lapangan
def get_all_lapangan() -> list[dict]:
    """Ambil semua lapangan dari database."""
    rows = fetch_query(
        "SELECT id, nama, jenis, harga_per_jam, is_indoor, atribut_khusus "
        "FROM lapangan ORDER BY jenis, nama"
    )
    return [dict(r) for r in rows] if rows else []


def tambah_lapangan_db(nama: str, jenis: str, harga_per_jam: float,
                       is_indoor: bool, atribut_khusus: str) -> int | None:
    """Insert lapangan baru. Kembalikan ID baru atau None."""
    return execute_query(
        "INSERT INTO lapangan (nama, jenis, harga_per_jam, is_indoor, atribut_khusus) "
        "VALUES (?, ?, ?, ?, ?)",
        (nama, jenis, float(harga_per_jam), int(is_indoor), atribut_khusus)
    )


def update_lapangan_db(id_lapangan: int, nama: str, harga_per_jam: float,
                       is_indoor: bool, atribut_khusus: str) -> bool:
    """Update data lapangan berdasarkan ID."""
    result = execute_query(
        "UPDATE lapangan SET nama=?, harga_per_jam=?, is_indoor=?, atribut_khusus=? "
        "WHERE id=?",
        (nama, float(harga_per_jam), int(is_indoor), atribut_khusus, id_lapangan)
    )
    return result is not None


def hapus_lapangan_db(id_lapangan: int) -> bool:
    """Hapus lapangan jika tidak ada booking aktif."""
    row = fetch_query(
        "SELECT COUNT(*) FROM booking WHERE id_lapangan=? AND status='Aktif'",
        (id_lapangan,), fetch_all=False
    )
    if row and row[0] > 0:
        return False
    result = execute_query("DELETE FROM lapangan WHERE id=?", (id_lapangan,))
    return result is not None


# Operasi booking
def tambah_booking_db(nama_tim: str, id_lapangan: int, tanggal: datetime.date,
                      jam_mulai: str, durasi_menit: int, id_user: int,
                      total_biaya: float) -> int | None:
    """Insert booking baru. Kembalikan ID baru atau None."""
    return execute_query(
        "INSERT INTO booking (nama_tim, id_lapangan, tanggal, jam_mulai, "
        "durasi_menit, id_user, total_biaya, status) VALUES (?,?,?,?,?,?,?,'Aktif')",
        (nama_tim, id_lapangan, tanggal.strftime("%Y-%m-%d"),
         jam_mulai, durasi_menit, id_user, total_biaya)
    )


def get_all_booking_db() -> pd.DataFrame:
    """Ambil semua booking dengan info lapangan sebagai DataFrame."""
    return get_dataframe("""
        SELECT b.id, b.nama_tim, l.nama AS lapangan, l.jenis,
               b.tanggal, b.jam_mulai, b.durasi_menit,
               b.total_biaya, b.status, b.id_user, b.id_lapangan
        FROM booking b
        JOIN lapangan l ON b.id_lapangan = l.id
        ORDER BY b.tanggal DESC, b.jam_mulai DESC
    """)


def get_booking_by_user(id_user: int) -> pd.DataFrame:
    """Ambil booking milik user tertentu."""
    return get_dataframe("""
        SELECT b.id, b.nama_tim, l.nama AS lapangan, l.jenis,
               b.tanggal, b.jam_mulai, b.durasi_menit,
               b.total_biaya, b.status, b.id_lapangan
        FROM booking b
        JOIN lapangan l ON b.id_lapangan = l.id
        WHERE b.id_user = ?
        ORDER BY b.tanggal DESC, b.jam_mulai DESC
    """, (id_user,))


def get_booking_by_tanggal_lapangan(id_lapangan: int,
                                     tanggal: datetime.date) -> list[dict]:
    """Ambil semua booking aktif pada lapangan dan tanggal tertentu."""
    rows = fetch_query(
        "SELECT id, nama_tim, jam_mulai, durasi_menit, status "
        "FROM booking WHERE id_lapangan=? AND tanggal=? AND status != 'Dibatalkan' "
        "ORDER BY jam_mulai",
        (id_lapangan, tanggal.strftime("%Y-%m-%d"))
    )
    return [dict(r) for r in rows] if rows else []


def update_status_booking(id_booking: int, status: str) -> bool:
    """Update status booking: Aktif / Selesai / Dibatalkan."""
    result = execute_query(
        "UPDATE booking SET status=? WHERE id=?",
        (status, id_booking)
    )
    return result is not None


# Operasi user
def get_user_by_username(username: str) -> dict | None:
    """Cari user berdasarkan username."""
    row = fetch_query(
        "SELECT id, username, password_hash, role, nama_lengkap "
        "FROM users WHERE username=?",
        (username,), fetch_all=False
    )
    return dict(row) if row else None


def tambah_user_db(username: str, password: str,
                   role: str, nama_lengkap: str) -> int | None:
    """Daftarkan user baru. Kembalikan ID baru atau None."""
    pwd_hash = _hash(password)
    return execute_query(
        "INSERT INTO users (username, password_hash, role, nama_lengkap) VALUES (?,?,?,?)",
        (username, pwd_hash, role, nama_lengkap)
    )


def get_all_users_db() -> list[dict]:
    """Ambil semua user (tanpa password_hash)."""
    rows = fetch_query(
        "SELECT id, username, role, nama_lengkap FROM users ORDER BY role, username"
    )
    return [dict(r) for r in rows] if rows else []


# Laporan dan statistik
def get_pendapatan_harian(n_hari: int = 30) -> pd.DataFrame:
    """Pendapatan per hari dalam N hari terakhir."""
    cutoff_date = (datetime.date.today() - datetime.timedelta(days=n_hari)).strftime("%Y-%m-%d")
    return get_dataframe("""
        SELECT tanggal, SUM(total_biaya) AS pendapatan, COUNT(*) AS jumlah_booking
        FROM booking
        WHERE status != 'Dibatalkan'
          AND tanggal >= ?
        GROUP BY tanggal
        ORDER BY tanggal
    """, (cutoff_date,))


def get_pendapatan_per_lapangan() -> pd.DataFrame:
    """Total pendapatan per lapangan."""
    return get_dataframe("""
        SELECT l.nama AS lapangan, l.jenis,
               SUM(b.total_biaya) AS total_pendapatan,
               COUNT(b.id)        AS jumlah_booking
        FROM booking b
        JOIN lapangan l ON b.id_lapangan = l.id
        WHERE b.status != 'Dibatalkan'
        GROUP BY b.id_lapangan
        ORDER BY total_pendapatan DESC
    """)


def get_summary_hari_ini() -> dict:
    """Ringkasan statistik booking dan pendapatan hari ini."""
    today = datetime.date.today().strftime("%Y-%m-%d")
    row = fetch_query(
        "SELECT COUNT(*) as total_booking, COALESCE(SUM(total_biaya),0) as total_pendapatan "
        "FROM booking WHERE tanggal=? AND status != 'Dibatalkan'",
        (today,), fetch_all=False
    )
    return dict(row) if row else {"total_booking": 0, "total_pendapatan": 0}


# Manajemen sesi login (token)
import secrets

def create_session_token(user_id: int) -> str:
    """Buat token sesi baru dan simpan ke database. Berlaku 7 hari."""
    token   = secrets.token_urlsafe(32)
    now     = datetime.datetime.now()
    expires = now + datetime.timedelta(days=7)
    execute_query(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, now.isoformat(), expires.isoformat())
    )
    return token


def get_user_from_token(token: str) -> dict | None:
    """Ambil data user dari token sesi yang masih valid."""
    now = datetime.datetime.now().isoformat()
    row = fetch_query(
        "SELECT u.id, u.username, u.password_hash, u.role, u.nama_lengkap "
        "FROM users u JOIN sessions s ON u.id = s.user_id "
        "WHERE s.token = ? AND s.expires_at > ?",
        (token, now), fetch_all=False
    )
    return dict(row) if row else None


def delete_session_token(token: str):
    """Hapus token sesi saat logout."""
    execute_query("DELETE FROM sessions WHERE token = ?", (token,))


def cleanup_expired_sessions():
    """Hapus semua token yang sudah kadaluarsa."""
    now = datetime.datetime.now().isoformat()
    execute_query("DELETE FROM sessions WHERE expires_at <= ?", (now,))
