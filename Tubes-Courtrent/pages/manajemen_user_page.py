# pages/manajemen_user_page.py
"""Halaman Manajemen Pengguna: Tambah dan Lihat Pengguna. Khusus Admin."""

import streamlit as st
import pandas as pd

from auth import require_role, register
from database import get_all_users_db
from konfigurasi import ROLE_ADMIN


def render():
    if not require_role(ROLE_ADMIN):
        return

    st.markdown("## Manajemen Pengguna")
    st.markdown("Kelola staf admin, kasir, dan akun pelanggan.")
    st.divider()

    tab_tambah, tab_daftar = st.tabs(["Tambah Pengguna Baru", "Daftar Pengguna"])

    # Tab: Tambah Pengguna Baru
    with tab_tambah:
        st.markdown("#### Buat Akun Baru")
        with st.form("form_tambah_user", clear_on_submit=True):
            cols_nama = st.columns(2)
            nama_lengkap = cols_nama[0].text_input("Nama Lengkap*", placeholder="Nama Lengkap")
            username = cols_nama[1].text_input("Username*", placeholder="Min. 4 karakter")

            cols_role = st.columns(3)
            role = cols_role[0].selectbox("Role Akun*", ["pelanggan", "kasir", "admin"],
                                          format_func=lambda x: x.upper())
            password = cols_role[1].text_input("Password*", type="password", placeholder="Min. 6 karakter")
            konfirmasi = cols_role[2].text_input("Konfirmasi Password*", type="password", placeholder="Ulangi password")

            submit = st.form_submit_button("Daftar Pengguna", use_container_width=True)

        if submit:
            sukses, pesan = register(
                username     = username,
                password     = password,
                konfirmasi   = konfirmasi,
                role         = role,
                nama_lengkap = nama_lengkap,
            )
            if sukses:
                st.success(f"{pesan} Akun baru berhasil dibuat!")
                st.rerun()
            else:
                st.error(pesan)

    # Tab: Daftar Pengguna
    with tab_daftar:
        users = get_all_users_db()
        if not users:
            st.info("Belum ada pengguna terdaftar.")
        else:
            df_users = pd.DataFrame(users)
            
            # Format tampilan
            df_users.columns = ["ID", "Username", "Role", "Nama Lengkap"]
            df_users["Role"] = df_users["Role"].str.upper()
            
            st.dataframe(df_users, use_container_width=True, hide_index=True)
