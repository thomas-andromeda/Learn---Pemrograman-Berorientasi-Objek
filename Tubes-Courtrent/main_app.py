# main_app.py
"""
Court Rent - Manajemen Lapangan Sport Center
Entry point aplikasi Streamlit.
"""

import os
import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(
    page_title = "Court Rent - Sport Center",
    page_icon  = "assets/logo.png",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

from database import init_db
from auth     import init_session, is_logged_in, get_current_user, clear_session
from konfigurasi import (
    COLOR_PRIMARY, ROLE_ADMIN, ROLE_KASIR, ROLE_PELANGGAN, LOGO_PATH
)

import pages.login_page              as login_page
import pages.dashboard_page          as dashboard_page
import pages.lapangan_page           as lapangan_page
import pages.booking_page            as booking_page
import pages.riwayat_page            as riwayat_page
import pages.laporan_page            as laporan_page
import pages.manajemen_lapangan_page as manajemen_lapangan_page
import pages.ketersediaan_page       as ketersediaan_page
import pages.manajemen_user_page     as manajemen_user_page


# Inisialisasi database dan sesi
if "db_ready" not in st.session_state:
    st.session_state.db_ready = init_db()

init_session()


# CSS Global
st.markdown(f"""
<style>
[data-testid="stSidebar"] {{
    background-color: #E9EDF4;
    border-right: 1px solid #D1D5DB;
}}
[data-testid="stApp"] {{
    background-color: #F8F8FF;
}}
.stButton > button[kind="primary"] {{
    background-color: {COLOR_PRIMARY};
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
}}
.stButton > button[kind="primary"]:hover {{
    background-color: #0F4723;
    box-shadow: 0 4px 12px rgba(22,101,52,0.3);
    transform: translateY(-1px);
}}
[data-testid="stMetric"] {{
    background: white;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}}
[data-testid="stExpander"] {{
    border: 1px solid #E5E7EB;
    border-radius: 8px;
}}
[data-testid="stDataFrame"] {{
    border-radius: 8px;
    overflow: hidden;
}}
.user-badge {{
    background: white;
    border: 1px solid #D1D5DB;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    margin: 0.5rem 0;
    font-size: 0.82rem;
}}
</style>
""", unsafe_allow_html=True)


# Sidebar logo - tampil paling atas sebelum dan sesudah login
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown(f"<h2 style='color:{COLOR_PRIMARY}; text-align:center;'>Court Rent</h2>",
                    unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#6B7280; font-size:0.78rem; margin-top:-0.5rem;'>Sport Center Management</p>",
                unsafe_allow_html=True)

# Halaman login jika belum masuk
if not is_logged_in():
    login_page.render()
    st.stop()


# Sidebar navigasi
user = get_current_user()

MENU_SEMUA = [
    ("Dashboard",       "house",         "Dashboard"),
    ("Daftar Lapangan", "building",      "Lapangan"),
    ("Cek Ketersediaan","calendar-check","Ketersediaan"),
    ("Booking Baru",    "plus-circle",   "Booking"),
    ("Riwayat Booking", "clock-history", "Riwayat"),
]
MENU_STAFF = [
    ("Laporan Pendapatan", "bar-chart-line", "Laporan"),
]
MENU_ADMIN = [
    ("Kelola Lapangan", "gear", "Manajemen"),
    ("Kelola Pengguna", "people", "ManajemenUser"),
]

menu_labels = [m[0] for m in MENU_SEMUA]
menu_icons  = [m[1] for m in MENU_SEMUA]
menu_keys   = [m[2] for m in MENU_SEMUA]

if user.role in (ROLE_ADMIN, ROLE_KASIR):
    for m in MENU_STAFF:
        menu_labels.append(m[0])
        menu_icons.append(m[1])
        menu_keys.append(m[2])

if user.role == ROLE_ADMIN:
    for m in MENU_ADMIN:
        menu_labels.append(m[0])
        menu_icons.append(m[1])
        menu_keys.append(m[2])

with st.sidebar:
    # Badge user
    role_label = {"admin": "Administrator", "kasir": "Kasir", "pelanggan": "Pelanggan"}.get(user.role, user.role)
    st.markdown(f"""
    <div class="user-badge">
        <b>{user.nama_lengkap or user.username}</b><br>
        <span style="color:#6B7280;">@{user.username} &middot; {role_label}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Menu navigasi
    active_index = (menu_keys.index(st.session_state.active_page)
                    if st.session_state.active_page in menu_keys else 0)

    selected = option_menu(
        menu_title    = "",
        options       = menu_labels,
        icons         = menu_icons,
        default_index = active_index,
        styles = {
            "container"       : {"padding": "0", "background-color": "#E9EDF4"},
            "icon"            : {"color": COLOR_PRIMARY, "font-size": "16px"},
            "nav-link"        : {
                "font-size"    : "0.9rem",
                "text-align"   : "left",
                "color"        : "#374151",
                "--hover-color": "#D1E7DD",
                "border-radius": "8px",
                "margin"       : "2px 0",
            },
            "nav-link-selected": {
                "background-color": COLOR_PRIMARY,
                "color"           : "white",
                "font-weight"     : "600",
            },
        }
    )

    st.markdown("---")

    if st.button("Keluar", use_container_width=True):
        clear_session()
        st.rerun()

    st.markdown(
        "<div style='text-align:center; font-size:0.7rem; color:#9CA3AF; margin-top:1rem;'>"
        "Court Rent</div>",
        unsafe_allow_html=True
    )


# Routing halaman
if selected in menu_labels:
    idx = menu_labels.index(selected)
    new_page = menu_keys[idx]
    if st.session_state.active_page != new_page:
        st.session_state.active_page = new_page
        st.rerun()

page = st.session_state.active_page

if   page == "Dashboard"   : dashboard_page.render()
elif page == "Lapangan"    : lapangan_page.render()
elif page == "Ketersediaan": ketersediaan_page.render()
elif page == "Booking"     : booking_page.render()
elif page == "Riwayat"     : riwayat_page.render()
elif page == "Laporan"     : laporan_page.render()
elif page == "Manajemen"   : manajemen_lapangan_page.render()
elif page == "ManajemenUser": manajemen_user_page.render()
else                       : dashboard_page.render()
