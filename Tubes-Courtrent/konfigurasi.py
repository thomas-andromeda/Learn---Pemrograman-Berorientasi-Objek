# konfigurasi.py
import os

# Path Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME  = 'court_rent.db'
DB_PATH  = os.path.join(BASE_DIR, DB_NAME)

# Path Assets
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
LOGO_PATH  = os.path.join(ASSETS_DIR, 'logo.png')

# Jam Operasional
JAM_BUKA   = 7    # 07:00
JAM_TUTUP  = 22   # 22:00

# Durasi Booking
DURASI_MIN_MENIT  = 30
DURASI_MAX_MENIT  = 360

# Jenis Lapangan dan Atributnya
JENIS_LAPANGAN = ["Futsal", "Badminton", "Tenis"]
JENIS_RUMPUT   = ["Sintetis", "Interlock"]
JENIS_KARPET   = ["Vinyl", "Kayu"]
JENIS_SURFACE  = ["Clay", "Hard Court"]

# Harga Default (Rp/jam)
HARGA_FUTSAL    = 100_000
HARGA_BADMINTON =  75_000
HARGA_TENIS     = 150_000

# Status Booking
STATUS_BOOKING = ["Aktif", "Selesai", "Dibatalkan"]

# Role Pengguna
ROLE_ADMIN     = "admin"
ROLE_KASIR     = "kasir"
ROLE_PELANGGAN = "pelanggan"
ROLES          = [ROLE_ADMIN, ROLE_KASIR, ROLE_PELANGGAN]

# Warna Tema
COLOR_PRIMARY   = "#166534"   # Hijau tua (utama)
COLOR_SECONDARY = "#E9EDF4"   # Abu-abu terang
COLOR_BG        = "#F8F8FF"   # Ghost white
COLOR_TEXT      = "#1A2E25"
COLOR_SUCCESS   = "#166534"
COLOR_WARNING   = "#B45309"
COLOR_ERROR     = "#B91C1C"
COLOR_INFO      = "#1D4ED8"


def tampilkan_peringatan_kosong(pesan: str):
    import streamlit as st
    st.markdown(f"""
    <div style="
        background-color: #F0FDF4;
        border-left: 5px solid {COLOR_PRIMARY};
        color: {COLOR_PRIMARY};
        padding: 0.75rem 1rem;
        border-radius: 6px;
        font-weight: 500;
        margin: 1rem 0;
    ">
        {pesan}
    </div>
    """, unsafe_allow_html=True)
