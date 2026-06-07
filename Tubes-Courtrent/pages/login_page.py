# pages/login_page.py
"""Halaman Login dan Register."""

import streamlit as st
from auth import login, register, set_session
from konfigurasi import COLOR_PRIMARY


def render():
    st.markdown(f"""
    <style>
    .login-header {{
        text-align: center;
        margin-bottom: 2rem;
    }}
    .login-header h1 {{
        font-size: 2.2rem;
        color: {COLOR_PRIMARY};
        font-weight: 800;
        margin-bottom: 0.25rem;
    }}
    .login-header p {{
        color: #6B7280;
        font-size: 1rem;
    }}
    .badge-info {{
        background: #F0F4F2;
        border-left: 4px solid {COLOR_PRIMARY};
        border-radius: 4px;
        padding: 0.75rem 1rem;
        font-size: 0.85rem;
        color: #374151;
        margin-bottom: 1rem;
    }}
    </style>
    """, unsafe_allow_html=True)

    import os
    from konfigurasi import LOGO_PATH

    col1, col2, col3 = st.columns([1.2, 1.0, 1.2])
    with col2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        else:
            st.markdown(f"""
            <div class="login-header">
                <h1>Court Rent</h1>
                <p>Manajemen Lapangan Sport Center</p>
            </div>
            """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["Masuk", "Daftar Akun Baru"])

    with tab_login:
        st.markdown("#### Silakan masuk untuk melanjutkan")
        with st.form("form_login", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Masukkan username")
            password = st.text_input("Password", type="password",
                                     placeholder="Masukkan password")
            masuk    = st.form_submit_button("Masuk", use_container_width=True)

        if masuk:
            sukses, pesan, user = login(username, password)
            if sukses:
                set_session(user)
                st.success(pesan)
                st.rerun()
            else:
                st.error(pesan)

        st.markdown("""
        <div class="badge-info">
        <b>Akun Default untuk Testing:</b><br>
        Admin &nbsp;&nbsp;&nbsp;&nbsp;: admin / admin123<br>
        Kasir &nbsp;&nbsp;&nbsp;&nbsp;: kasir / kasir123<br>
        Pelanggan : pelanggan / pelanggan123
        </div>
        """, unsafe_allow_html=True)

    with tab_register:
        st.markdown("#### Buat akun baru")
        with st.form("form_register", clear_on_submit=True):
            cols = st.columns(2)
            reg_nama     = cols[0].text_input("Nama Lengkap*", placeholder="Nama Anda")
            reg_username = cols[1].text_input("Username*", placeholder="Min. 4 karakter")
            reg_pass     = cols[0].text_input("Password*", type="password",
                                         placeholder="Min. 6 karakter")
            reg_konfirm  = cols[1].text_input("Konfirmasi Password*", type="password",
                                         placeholder="Ulangi password")
            daftar       = st.form_submit_button("Daftar Sekarang", use_container_width=True)

        if daftar:
            sukses, pesan = register(
                username     = reg_username,
                password     = reg_pass,
                konfirmasi   = reg_konfirm,
                role         = "pelanggan",
                nama_lengkap = reg_nama,
            )
            if sukses:
                st.success(f"{pesan} Silakan masuk.")
            else:
                st.error(pesan)
