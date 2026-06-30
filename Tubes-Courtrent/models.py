# models.py
"""
Modul class utama aplikasi Court Rent.
Mengimplementasikan konsep OOP: Inheritance, Polymorphism, Encapsulation.
"""

import datetime
import hashlib


# Superclass: Lapangan
class Lapangan:
    """Superclass untuk semua jenis lapangan sport center."""

    def __init__(self, id_lapangan: int, nama: str,
                 harga_per_jam: float, is_indoor: bool, jenis: str):
        self._id_lapangan   = id_lapangan
        self._nama          = nama
        self._harga_per_jam = float(harga_per_jam)
        self._is_indoor     = bool(is_indoor)
        self._jenis         = jenis

    @property
    def id_lapangan(self) -> int:
        return self._id_lapangan

    @property
    def nama(self) -> str:
        return self._nama

    @nama.setter
    def nama(self, value: str):
        if not value or not isinstance(value, str):
            raise ValueError("Nama lapangan tidak boleh kosong.")
        self._nama = value

    @property
    def harga_per_jam(self) -> float:
        return self._harga_per_jam

    @harga_per_jam.setter
    def harga_per_jam(self, value: float):
        if value <= 0:
            raise ValueError("Harga harus lebih dari 0.")
        self._harga_per_jam = float(value)

    @property
    def is_indoor(self) -> bool:
        return self._is_indoor

    @property
    def jenis(self) -> str:
        return self._jenis

    def hitung_biaya(self, durasi_menit: int) -> float:
        """Hitung biaya sewa berdasarkan durasi (menit). Polymorphism dasar."""
        durasi_jam = durasi_menit / 60
        return round(self._harga_per_jam * durasi_jam, 0)

    def get_tipe_lokasi(self) -> str:
        return "Indoor" if self._is_indoor else "Outdoor"

    def get_atribut_khusus(self) -> str:
        return "-"

    def to_dict(self) -> dict:
        return {
            "id_lapangan"   : self._id_lapangan,
            "nama"          : self._nama,
            "harga_per_jam" : self._harga_per_jam,
            "is_indoor"     : self._is_indoor,
            "jenis"         : self._jenis,
            "atribut_khusus": self.get_atribut_khusus(),
        }

    def __repr__(self) -> str:
        return (f"Lapangan(ID:{self._id_lapangan}, Nama:'{self._nama}', "
                f"Jenis:'{self._jenis}', Harga:{self._harga_per_jam})")


# Subclass 1: LapanganFutsal
class LapanganFutsal(Lapangan):
    """Subclass lapangan Futsal. Atribut tambahan: jenis_rumput."""

    def __init__(self, id_lapangan: int, nama: str,
                 harga_per_jam: float, is_indoor: bool, jenis_rumput: str):
        super().__init__(id_lapangan, nama, harga_per_jam, is_indoor, "Futsal")
        self._jenis_rumput = jenis_rumput

    @property
    def jenis_rumput(self) -> str:
        return self._jenis_rumput


    def get_atribut_khusus(self) -> str:
        return f"Rumput: {self._jenis_rumput}"

    def __repr__(self) -> str:
        return (f"LapanganFutsal(ID:{self._id_lapangan}, Nama:'{self._nama}', "
                f"Rumput:'{self._jenis_rumput}')")


# Subclass 2: LapanganBadminton
class LapanganBadminton(Lapangan):
    """Subclass lapangan Badminton. Atribut tambahan: jenis_karpet."""

    def __init__(self, id_lapangan: int, nama: str,
                 harga_per_jam: float, is_indoor: bool, jenis_karpet: str):
        super().__init__(id_lapangan, nama, harga_per_jam, is_indoor, "Badminton")
        self._jenis_karpet = jenis_karpet

    @property
    def jenis_karpet(self) -> str:
        return self._jenis_karpet


    def get_atribut_khusus(self) -> str:
        return f"Karpet: {self._jenis_karpet}"

    def __repr__(self) -> str:
        return (f"LapanganBadminton(ID:{self._id_lapangan}, Nama:'{self._nama}', "
                f"Karpet:'{self._jenis_karpet}')")


# Subclass 3: LapanganTenis
class LapanganTenis(Lapangan):
    """Subclass lapangan Tenis. Atribut tambahan: jenis_lapangan (surface)."""

    def __init__(self, id_lapangan: int, nama: str,
                 harga_per_jam: float, is_indoor: bool, jenis_lapangan_surface: str):
        super().__init__(id_lapangan, nama, harga_per_jam, is_indoor, "Tenis")
        self._jenis_lapangan = jenis_lapangan_surface

    @property
    def jenis_lapangan(self) -> str:
        return self._jenis_lapangan


    def get_atribut_khusus(self) -> str:
        return f"Surface: {self._jenis_lapangan}"

    def __repr__(self) -> str:
        return (f"LapanganTenis(ID:{self._id_lapangan}, Nama:'{self._nama}', "
                f"Surface:'{self._jenis_lapangan}')")


# Class User
class User:
    """Merepresentasikan pengguna aplikasi (Admin / Kasir / Pelanggan)."""

    def __init__(self, id_user: int, username: str, password_hash: str,
                 role: str, nama_lengkap: str = ""):
        self._id_user       = id_user
        self._username      = username
        self._password_hash = password_hash
        self._role          = role
        self._nama_lengkap  = nama_lengkap

    @property
    def id_user(self) -> int:
        return self._id_user

    @property
    def username(self) -> str:
        return self._username

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def role(self) -> str:
        return self._role

    @property
    def nama_lengkap(self) -> str:
        return self._nama_lengkap

    def cek_password(self, password: str) -> bool:
        """Validasi password dengan membandingkan hash SHA-256."""
        return self._password_hash == hashlib.sha256(password.encode()).hexdigest()

    def is_admin(self) -> bool:
        return self._role == "admin"

    def is_kasir(self) -> bool:
        return self._role == "kasir"

    def is_pelanggan(self) -> bool:
        return self._role == "pelanggan"

    def __repr__(self) -> str:
        return f"User(ID:{self._id_user}, Username:'{self._username}', Role:'{self._role}')"


# Class Booking
class Booking:
    """Merepresentasikan satu sesi booking lapangan (Asosiasi dengan Lapangan)."""

    def __init__(self, id_booking: int | None, nama_tim: str,
                 objek_lapangan: Lapangan, tanggal: datetime.date | str,
                 jam_mulai: str, durasi_menit: int, id_user: int,
                 status: str = "Aktif", total_biaya: float | None = None):
        self._id_booking      = id_booking
        self._nama_tim        = nama_tim
        self._objek_lapangan  = objek_lapangan
        self._jam_mulai       = jam_mulai
        self._durasi_menit    = int(durasi_menit)
        self._id_user         = id_user
        self._status          = status

        if isinstance(tanggal, datetime.date):
            self._tanggal = tanggal
        elif isinstance(tanggal, str):
            try:
                self._tanggal = datetime.datetime.strptime(tanggal, "%Y-%m-%d").date()
            except ValueError:
                self._tanggal = datetime.date.today()
        else:
            self._tanggal = datetime.date.today()

        if total_biaya is not None:
            self._total_biaya = float(total_biaya)
        else:
            self._total_biaya = self._objek_lapangan.hitung_biaya(self._durasi_menit)

    @property
    def id_booking(self) -> int | None:
        return self._id_booking

    @id_booking.setter
    def id_booking(self, value: int):
        self._id_booking = value

    @property
    def nama_tim(self) -> str:
        return self._nama_tim

    @property
    def objek_lapangan(self) -> Lapangan:
        return self._objek_lapangan

    @property
    def tanggal(self) -> datetime.date:
        return self._tanggal

    @property
    def jam_mulai(self) -> str:
        return self._jam_mulai

    @property
    def durasi_menit(self) -> int:
        return self._durasi_menit

    @property
    def id_user(self) -> int:
        return self._id_user

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        self._status = value

    @property
    def total_biaya(self) -> float:
        return self._total_biaya

    def get_jam_selesai(self) -> str:
        """Hitung jam selesai dari jam mulai dan durasi."""
        jam, menit    = map(int, self._jam_mulai.split(":"))
        total_menit   = jam * 60 + menit + self._durasi_menit
        jam_selesai   = (total_menit // 60) % 24
        menit_selesai = total_menit % 60
        return f"{jam_selesai:02d}:{menit_selesai:02d}"

    def validasi_jadwal(self, jam_buka: int = 7, jam_tutup: int = 22) -> tuple[bool, str]:
        """Validasi jadwal: dalam jam operasional dan durasi minimal 30 menit."""
        jam, menit    = map(int, self._jam_mulai.split(":"))
        mulai_menit   = jam * 60 + menit
        selesai_menit = mulai_menit + self._durasi_menit

        if mulai_menit < jam_buka * 60:
            return False, f"Jam mulai terlalu awal. Sport Center buka pukul {jam_buka:02d}:00."
        if selesai_menit > jam_tutup * 60:
            return False, f"Jadwal melebihi jam tutup pukul {jam_tutup:02d}:00."
        if self._durasi_menit < 30:
            return False, "Durasi minimum booking adalah 30 menit."
        return True, "Jadwal valid."

    def generate_nota(self) -> str:
        """Generate teks nota booking yang terformat."""
        garis_tebal  = "=" * 42
        garis_tipis  = "-" * 42
        jam_selesai  = self.get_jam_selesai()
        durasi_jam   = self._durasi_menit // 60
        durasi_sisa  = self._durasi_menit % 60
        durasi_str   = (
            f"{durasi_jam} jam {durasi_sisa} menit" if durasi_sisa
            else f"{durasi_jam} jam"
        )
        id_str = f"#{self._id_booking:05d}" if self._id_booking else "#-----"

        nota = (
            f"\n{garis_tebal}\n"
            f"      COURT RENT SPORT CENTER\n"
            f"         NOTA BOOKING LAPANGAN\n"
            f"{garis_tebal}\n"
            f"  No. Booking  : {id_str}\n"
            f"  Nama Tim     : {self._nama_tim}\n"
            f"{garis_tipis}\n"
            f"  DETAIL LAPANGAN\n"
            f"{garis_tipis}\n"
            f"  Lapangan     : {self._objek_lapangan.nama}\n"
            f"  Jenis        : {self._objek_lapangan.jenis}\n"
            f"  Lokasi       : {self._objek_lapangan.get_tipe_lokasi()}\n"
            f"  {self._objek_lapangan.get_atribut_khusus()}\n"
            f"{garis_tipis}\n"
            f"  JADWAL\n"
            f"{garis_tipis}\n"
            f"  Tanggal      : {self._tanggal.strftime('%d %B %Y')}\n"
            f"  Jam Mulai    : {self._jam_mulai} WIB\n"
            f"  Jam Selesai  : {jam_selesai} WIB\n"
            f"  Durasi       : {durasi_str}\n"
            f"{garis_tipis}\n"
            f"  Harga/Jam    : Rp {self._objek_lapangan.harga_per_jam:>10,.0f}\n"
            f"  TOTAL BIAYA  : Rp {self._total_biaya:>10,.0f}\n"
            f"{garis_tebal}\n"
            f"  Status       : {self._status}\n"
            f"{garis_tebal}\n"
            f"   Terima kasih telah menggunakan\n"
            f"         layanan Court Rent!\n"
            f"{garis_tebal}\n"
        )
        return nota

    def __repr__(self) -> str:
        return (f"Booking(ID:{self._id_booking}, Tim:'{self._nama_tim}', "
                f"Lapangan:'{self._objek_lapangan.nama}', Tanggal:{self._tanggal})")


# Class SportCenter
class SportCenter:
    """Class manajemen utama Sport Center. Menyimpan lapangan dan booking."""

    def __init__(self, nama: str = "Court Rent Sport Center"):
        self._nama             = nama
        self._daftar_lapangan : list[Lapangan] = []
        self._daftar_booking  : list[Booking]  = []

    @property
    def nama(self) -> str:
        return self._nama

    @property
    def daftar_lapangan(self) -> list[Lapangan]:
        return self._daftar_lapangan

    @property
    def daftar_booking(self) -> list[Booking]:
        return self._daftar_booking

    def tambah_lapangan(self, lapangan: Lapangan) -> bool:
        """Tambah objek lapangan ke daftar."""
        if isinstance(lapangan, Lapangan):
            self._daftar_lapangan.append(lapangan)
            return True
        return False

    def get_lapangan_by_id(self, id_lapangan: int) -> Lapangan | None:
        """Cari lapangan berdasarkan ID."""
        for lap in self._daftar_lapangan:
            if lap.id_lapangan == id_lapangan:
                return lap
        return None

    def tambah_booking(self, booking: Booking,
                       jam_buka: int = 7, jam_tutup: int = 22) -> tuple[bool, str]:
        """Tambah booking baru setelah validasi jadwal dan ketersediaan slot."""
        valid, pesan = booking.validasi_jadwal(jam_buka, jam_tutup)
        if not valid:
            return False, pesan

        tersedia, pesan_cek = self.cek_ketersediaan_slot(
            id_lapangan  = booking.objek_lapangan.id_lapangan,
            tanggal      = booking.tanggal,
            jam_mulai    = booking.jam_mulai,
            durasi_menit = booking.durasi_menit,
        )
        if not tersedia:
            return False, pesan_cek

        self._daftar_booking.append(booking)
        return True, "Booking berhasil ditambahkan."

    def tambah_booking_langsung(self, booking: Booking) -> bool:
        """Tambah booking ke daftar secara langsung tanpa validasi (loading DB)."""
        if isinstance(booking, Booking):
            self._daftar_booking.append(booking)
            return True
        return False

    def cek_ketersediaan_slot(self, id_lapangan: int, tanggal: datetime.date,
                               jam_mulai: str, durasi_menit: int,
                               exclude_id: int | None = None) -> tuple[bool, str]:
        """Cek apakah slot waktu tidak bentrok dengan booking yang sudah ada."""
        jam, menit   = map(int, jam_mulai.split(":"))
        mulai_baru   = jam * 60 + menit
        selesai_baru = mulai_baru + durasi_menit

        for b in self._daftar_booking:
            if b.status == "Dibatalkan":
                continue
            if exclude_id is not None and b.id_booking == exclude_id:
                continue
            if b.objek_lapangan.id_lapangan != id_lapangan:
                continue
            if b.tanggal != tanggal:
                continue

            jam_b, menit_b = map(int, b.jam_mulai.split(":"))
            mulai_b        = jam_b * 60 + menit_b
            selesai_b      = mulai_b + b.durasi_menit

            if not (selesai_baru <= mulai_b or mulai_baru >= selesai_b):
                return (False,
                        f"Slot bentrok dengan booking #{b.id_booking} "
                        f"({b.jam_mulai}-{b.get_jam_selesai()}).")

        return True, "Slot tersedia."

    def get_total_pendapatan(self, tanggal_mulai: datetime.date | None = None,
                              tanggal_selesai: datetime.date | None = None) -> float:
        """Hitung total pendapatan dari booking aktif dan selesai."""
        total = 0.0
        for b in self._daftar_booking:
            if b.status == "Dibatalkan":
                continue
            if tanggal_mulai   and b.tanggal < tanggal_mulai:
                continue
            if tanggal_selesai and b.tanggal > tanggal_selesai:
                continue
            total += b.total_biaya
        return total

    def __repr__(self) -> str:
        return (f"SportCenter('{self._nama}', "
                f"Lapangan:{len(self._daftar_lapangan)}, "
                f"Booking:{len(self._daftar_booking)})")
