# manajemen.py
"""
Modul business logic SportCenter.
Menjembatani class OOP (models.py) dengan database (database.py).
"""

import datetime
import pandas as pd

from models import (
    Lapangan, LapanganFutsal, LapanganBadminton, LapanganTenis,
    Booking, SportCenter
)
import database as db
from konfigurasi import JAM_BUKA, JAM_TUTUP


# Factory: buat objek Lapangan dari dict database
def buat_objek_lapangan(data: dict) -> Lapangan:
    """Konversi dict dari database menjadi objek Lapangan sesuai jenisnya."""
    id_l   = data["id"]
    nama   = data["nama"]
    harga  = data["harga_per_jam"]
    indoor = bool(data["is_indoor"])
    attr   = data.get("atribut_khusus", "")
    jenis  = data["jenis"]

    if jenis == "Futsal":
        return LapanganFutsal(id_l, nama, harga, indoor, attr or "Sintetis")
    elif jenis == "Badminton":
        return LapanganBadminton(id_l, nama, harga, indoor, attr or "Vinyl")
    elif jenis == "Tenis":
        return LapanganTenis(id_l, nama, harga, indoor, attr or "Hard Court")
    else:
        return Lapangan(id_l, nama, harga, indoor, jenis)


# Load sport center dari database
def load_sport_center() -> SportCenter:
    """Muat seluruh data lapangan dari database ke objek SportCenter."""
    sc = SportCenter()
    for data in db.get_all_lapangan():
        sc.tambah_lapangan(buat_objek_lapangan(data))
    return sc


def get_lapangan_objects() -> list[Lapangan]:
    """Kembalikan list objek Lapangan dari database."""
    return [buat_objek_lapangan(d) for d in db.get_all_lapangan()]


def get_lapangan_by_id(id_lapangan: int) -> Lapangan | None:
    """Cari satu objek Lapangan berdasarkan ID."""
    for lap in get_lapangan_objects():
        if lap.id_lapangan == id_lapangan:
            return lap
    return None


# Cek ketersediaan
def cek_ketersediaan_slot(id_lapangan: int, tanggal: datetime.date,
                           jam_mulai: str, durasi_menit: int,
                           exclude_id: int | None = None) -> tuple[bool, str]:
    """
    Cek ketersediaan slot dengan mengambil booking dari database
    dan menggunakan logika validasi dari class SportCenter.
    """
    existing = db.get_booking_by_tanggal_lapangan(id_lapangan, tanggal)

    lap_data = db.fetch_query("SELECT * FROM lapangan WHERE id=?",
                               (id_lapangan,), fetch_all=False)
    if not lap_data:
        return False, "Lapangan tidak ditemukan."

    lap_obj = buat_objek_lapangan(dict(lap_data))

    sc = SportCenter()
    for b in existing:
        if exclude_id and b["id"] == exclude_id:
            continue
        dummy_booking = Booking(
            id_booking     = b["id"],
            nama_tim       = b["nama_tim"],
            objek_lapangan = lap_obj,
            tanggal        = tanggal,
            jam_mulai      = b["jam_mulai"],
            durasi_menit   = b["durasi_menit"],
            id_user        = 0,
            status         = b["status"],
        )
        sc.daftar_booking.append(dummy_booking)

    return sc.cek_ketersediaan_slot(id_lapangan, tanggal, jam_mulai, durasi_menit)


# Proses booking
def proses_booking(nama_tim: str, id_lapangan: int, tanggal: datetime.date,
                   jam_mulai: str, durasi_menit: int,
                   id_user: int) -> tuple[bool, str, Booking | None]:
    """
    Proses booking lengkap:
    1. Buat objek Lapangan dan Booking
    2. Validasi jadwal (jam operasional)
    3. Cek ketersediaan slot
    4. Simpan ke database
    5. Kembalikan objek Booking dengan ID baru
    """
    lap_obj = get_lapangan_by_id(id_lapangan)
    if not lap_obj:
        return False, "Lapangan tidak ditemukan.", None

    booking = Booking(
        id_booking     = None,
        nama_tim       = nama_tim,
        objek_lapangan = lap_obj,
        tanggal        = tanggal,
        jam_mulai      = jam_mulai,
        durasi_menit   = durasi_menit,
        id_user        = id_user,
    )

    valid, pesan = booking.validasi_jadwal(JAM_BUKA, JAM_TUTUP)
    if not valid:
        return False, pesan, None

    tersedia, pesan_cek = cek_ketersediaan_slot(id_lapangan, tanggal,
                                                  jam_mulai, durasi_menit)
    if not tersedia:
        return False, pesan_cek, None

    new_id = db.tambah_booking_db(
        nama_tim     = booking.nama_tim,
        id_lapangan  = id_lapangan,
        tanggal      = booking.tanggal,
        jam_mulai    = booking.jam_mulai,
        durasi_menit = booking.durasi_menit,
        id_user      = id_user,
        total_biaya  = booking.total_biaya,
    )
    if not new_id:
        return False, "Gagal menyimpan booking ke database.", None

    booking.id_booking = new_id
    return True, "Booking berhasil!", booking


# Slot kosong per tanggal
def get_slot_status(id_lapangan: int, tanggal: datetime.date) -> list[dict]:
    """Kembalikan list slot 30 menit dari jam buka hingga tutup dengan status tersedia/terisi."""
    bookings = db.get_booking_by_tanggal_lapangan(id_lapangan, tanggal)

    terisi_menit = set()
    for b in bookings:
        jam, menit = map(int, b["jam_mulai"].split(":"))
        mulai      = jam * 60 + menit
        selesai    = mulai + b["durasi_menit"]
        for m in range(mulai, selesai, 30):
            terisi_menit.add(m)

    slots = []
    mulai = JAM_BUKA * 60
    tutup = JAM_TUTUP * 60
    while mulai < tutup:
        jam_str  = f"{mulai // 60:02d}:{mulai % 60:02d}"
        tersedia = mulai not in terisi_menit
        slots.append({"jam": jam_str, "tersedia": tersedia})
        mulai += 30

    return slots


# Laporan pendapatan
def get_total_pendapatan_db(tanggal_mulai: datetime.date | None = None,
                             tanggal_selesai: datetime.date | None = None) -> float:
    """Hitung total pendapatan dari database dalam rentang tanggal."""
    query  = "SELECT COALESCE(SUM(total_biaya), 0) FROM booking WHERE status != 'Dibatalkan'"
    params = []
    if tanggal_mulai:
        query += " AND tanggal >= ?"
        params.append(tanggal_mulai.strftime("%Y-%m-%d"))
    if tanggal_selesai:
        query += " AND tanggal <= ?"
        params.append(tanggal_selesai.strftime("%Y-%m-%d"))

    row = db.fetch_query(query, tuple(params) if params else None, fetch_all=False)
    return float(row[0]) if row else 0.0
