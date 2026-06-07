# auth.py
"""
Modul autentikasi: login, register, dan manajemen sesi Streamlit.
"""

import hashlib
import streamlit as st
from database import get_user_by_username, tambah_user_db
from models import User


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITAS
# ══════════════════════════════════════════════════════════════════════════════
def hash_password(password: str) -> str:
    """Hash password menggunakan SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def login(username: str, password: str) -> tuple[bool, str, User | None]:
    """
    Proses login user.
    Returns: (sukses, pesan, objek_user)
    """
    if not username or not password:
        return False, "Username dan password tidak boleh kosong.", None

    data = get_user_by_username(username.strip())
    if not data:
        return False, "Username tidak ditemukan.", None

    user = User(
        id_user       = data["id"],
        username      = data["username"],
        password_hash = data["password_hash"],
        role          = data["role"],
        nama_lengkap  = data["nama_lengkap"],
    )

    if not user.cek_password(password):
        return False, "Password salah.", None

    return True, f"Selamat datang, {user.nama_lengkap or user.username}!", user


# ══════════════════════════════════════════════════════════════════════════════
#  REGISTER
# ══════════════════════════════════════════════════════════════════════════════
def register(username: str, password: str, konfirmasi: str,
             role: str, nama_lengkap: str) -> tuple[bool, str]:
    """
    Daftarkan user baru.
    Returns: (sukses, pesan)
    """
    username = username.strip()
    if not username or not password:
        return False, "Username dan password tidak boleh kosong."
    if len(username) < 4:
        return False, "Username minimal 4 karakter."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."
    if password != konfirmasi:
        return False, "Konfirmasi password tidak cocok."
    if role not in ("admin", "kasir", "pelanggan"):
        return False, "Role tidak valid."

    # Cek apakah username sudah ada
    existing = get_user_by_username(username)
    if existing:
        return False, f"Username '{username}' sudah digunakan."

    new_id = tambah_user_db(username, password, role, nama_lengkap)
    if new_id:
        return True, f"Akun '{username}' berhasil dibuat."
    return False, "Gagal membuat akun. Silakan coba lagi."


# ══════════════════════════════════════════════════════════════════════════════
#  SESI STREAMLIT
# ══════════════════════════════════════════════════════════════════════════════
def init_session():
    """Inisialisasi variabel sesi jika belum ada."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in   = False
    if "user" not in st.session_state:
        st.session_state.user        = None
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Dashboard"

    # Jika session_state menunjukkan belum login, coba cari token di URL
    if not st.session_state.logged_in:
        token = st.query_params.get("token")
        if token:
            from database import get_user_from_token
            user_data = get_user_from_token(token)
            if user_data:
                user_obj = User(
                    id_user       = user_data["id"],
                    username      = user_data["username"],
                    password_hash = user_data["password_hash"],
                    role          = user_data["role"],
                    nama_lengkap  = user_data["nama_lengkap"],
                )
                st.session_state.logged_in = True
                st.session_state.user      = user_obj
            else:
                # Token tidak valid atau kedaluwarsa, hapus dari query param
                st.query_params.pop("token", None)


def set_session(user: User):
    """Simpan data user ke session setelah login berhasil."""
    st.session_state.logged_in   = True
    st.session_state.user        = user
    st.session_state.active_page = "Dashboard"

    # Buat token baru di DB dan simpan di query parameter
    from database import create_session_token
    try:
        token = create_session_token(user.id_user)
        st.query_params["token"] = token
    except Exception as e:
        print(f"[auth.py] Gagal membuat token sesi: {e}")


def clear_session():
    """Hapus sesi (logout)."""
    token = st.query_params.get("token")
    if token:
        from database import delete_session_token
        try:
            delete_session_token(token)
        except Exception as e:
            print(f"[auth.py] Gagal menghapus token sesi dari DB: {e}")
        st.query_params.pop("token", None)
    st.session_state.logged_in   = False
    st.session_state.user        = None
    st.session_state.active_page = "Dashboard"


def get_current_user() -> User | None:
    """Kembalikan objek User dari sesi aktif."""
    return st.session_state.get("user", None)


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def require_role(*roles: str) -> bool:
    """
    Periksa apakah user yang login memiliki role yang diizinkan.
    Tampilkan pesan error jika tidak.
    """
    user = get_current_user()
    if not user or user.role not in roles:
        st.error("⛔ Anda tidak memiliki akses ke halaman ini.")
        return False
    return True
