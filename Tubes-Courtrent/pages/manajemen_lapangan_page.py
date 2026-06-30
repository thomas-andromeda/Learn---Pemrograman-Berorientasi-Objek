# pages/manajemen_lapangan_page.py
"""Halaman Manajemen Lapangan: Tambah, Edit, Hapus lapangan. Khusus Admin."""

import streamlit as st

from auth import require_role
from database import (
    get_all_lapangan, tambah_lapangan_db,
    update_lapangan_db, hapus_lapangan_db
)
from konfigurasi import (
    ROLE_ADMIN, JENIS_LAPANGAN, JENIS_RUMPUT, JENIS_KARPET, JENIS_SURFACE,
    COLOR_PRIMARY, tampilkan_peringatan_kosong
)


ATRIBUT_MAP = {
    "Futsal"   : ("Jenis Rumput",   JENIS_RUMPUT),
    "Badminton": ("Jenis Karpet",   JENIS_KARPET),
    "Tenis"    : ("Jenis Lapangan", JENIS_SURFACE),
}


def render():
    if not require_role(ROLE_ADMIN):
        return

    st.markdown("## Manajemen Lapangan")
    st.markdown("Tambah, edit, atau hapus lapangan sport center.")
    st.divider()

    all_lapangan = get_all_lapangan()

    tab_tambah, tab_kelola = st.tabs(["Tambah Lapangan", "Edit dan Hapus"])

    # Tab: Tambah Lapangan
    with tab_tambah:
        with st.form("form_tambah_lapangan", clear_on_submit=True):
            st.markdown("#### Data Lapangan Baru")
            col1, col2 = st.columns(2)
            nama      = col1.text_input("Nama Lapangan*", placeholder="Contoh: Futsal C")
            jenis     = col2.selectbox("Jenis Lapangan*", JENIS_LAPANGAN)
            harga     = col1.number_input("Harga per Jam (Rp)*",
                                           min_value=10_000, step=5_000, value=100_000)
            is_indoor = col2.selectbox("Tipe Lokasi*",
                                        ["Indoor", "Outdoor"]) == "Indoor"

            label_attr, pilihan_attr = ATRIBUT_MAP[jenis]
            atribut = st.selectbox(f"{label_attr}*", pilihan_attr)

            submit = st.form_submit_button("Tambah Lapangan", use_container_width=True)

        if submit:
            if not nama.strip():
                st.error("Nama lapangan tidak boleh kosong.")
            else:
                new_id = tambah_lapangan_db(nama.strip(), jenis, harga,
                                             is_indoor, atribut)
                if new_id:
                    st.success(f"Lapangan **{nama}** berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.error("Gagal menambahkan lapangan.")

    # Tab: Edit dan Hapus Lapangan
    with tab_kelola:
        if not all_lapangan:
            tampilkan_peringatan_kosong("Belum ada lapangan yang terdaftar.")
        else:
            for lap in all_lapangan:
                lokasi = "Indoor" if lap["is_indoor"] else "Outdoor"

                with st.expander(
                    f"[{lap['id']}] {lap['nama']} "
                    f"- {lap['jenis']} - {lokasi} - "
                    f"Rp {lap['harga_per_jam']:,.0f}/jam"
                ):
                    with st.form(f"form_edit_{lap['id']}"):
                        c1, c2 = st.columns(2)
                        e_nama    = c1.text_input("Nama", value=lap["nama"])
                        e_harga   = c2.number_input("Harga/Jam (Rp)",
                                                     min_value=10_000,
                                                     step=5_000,
                                                     value=int(lap["harga_per_jam"]))
                        e_lokasi  = c1.selectbox(
                            "Lokasi",
                            ["Indoor", "Outdoor"],
                            index=0 if lap["is_indoor"] else 1,
                            key=f"lok_{lap['id']}"
                        )
                        label_attr, pilihan_attr = ATRIBUT_MAP[lap["jenis"]]
                        curr_idx  = (pilihan_attr.index(lap["atribut_khusus"])
                                     if lap["atribut_khusus"] in pilihan_attr else 0)
                        e_attr    = c2.selectbox(label_attr, pilihan_attr,
                                                  index=curr_idx,
                                                  key=f"attr_{lap['id']}")

                        simpan = st.form_submit_button("Simpan Perubahan", use_container_width=True)

                    # Tombol hapus diletakkan di luar form edit agar tidak terpicu bersamaan
                    # dan ditambahkan konfirmasi interaktif
                    confirm_key = f"confirm_hapus_{lap['id']}"
                    if confirm_key not in st.session_state:
                        st.session_state[confirm_key] = False

                    if not st.session_state[confirm_key]:
                        if st.button("🗑️ Hapus Lapangan", key=f"btn_hapus_{lap['id']}", use_container_width=True):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        st.warning(f"Apakah Anda yakin ingin menghapus lapangan **{lap['nama']}**?")
                        col_yes, col_no = st.columns(2)
                        if col_yes.button("Ya, Hapus Sekarang", key=f"btn_hapus_yes_{lap['id']}", use_container_width=True, type="primary"):
                            st.session_state[confirm_key] = False
                            ok = hapus_lapangan_db(lap["id"])
                            if ok:
                                st.success(f"Lapangan **{lap['nama']}** berhasil dihapus.")
                                st.rerun()
                            else:
                                st.error("Tidak bisa menghapus lapangan yang masih memiliki booking aktif.")
                        if col_no.button("Batal", key=f"btn_hapus_no_{lap['id']}", use_container_width=True):
                            st.session_state[confirm_key] = False
                            st.rerun()

                    if simpan:
                        ok = update_lapangan_db(
                            id_lapangan    = lap["id"],
                            nama           = e_nama.strip(),
                            harga_per_jam  = e_harga,
                            is_indoor      = (e_lokasi == "Indoor"),
                            atribut_khusus = e_attr,
                        )
                        if ok:
                            st.success(f"Lapangan **{e_nama}** berhasil diperbarui.")
                            st.rerun()
                        else:
                            st.error("Gagal memperbarui.")
