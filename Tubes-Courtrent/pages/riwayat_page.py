# pages/riwayat_page.py
"""Halaman Riwayat Booking: lihat dan kelola semua booking."""

import streamlit as st
import pandas as pd

from auth import get_current_user
from database import (
    get_all_booking_db, get_booking_by_user,
    update_status_booking
)
from manajemen import get_lapangan_by_id
from models import Booking
from konfigurasi import ROLE_ADMIN, ROLE_KASIR, tampilkan_peringatan_kosong


STATUS_STYLE = {
    "Aktif"      : ("#D1FAE5", "#065F46"),
    "Selesai"    : ("#DBEAFE", "#1E40AF"),
    "Dibatalkan" : ("#FEE2E2", "#991B1B"),
}


def _buat_booking_obj_dari_row(row) -> Booking | None:
    """Buat objek Booking dari baris DataFrame untuk generate_nota."""
    lap_obj = get_lapangan_by_id(int(row["id_lapangan"]))
    if not lap_obj:
        return None
    try:
        return Booking(
            id_booking     = int(row["id"]),
            nama_tim       = row["nama_tim"],
            objek_lapangan = lap_obj,
            tanggal        = row["tanggal"],
            jam_mulai      = row["jam_mulai"],
            durasi_menit   = int(row["durasi_menit"]),
            id_user        = 0,
            status         = row["status"],
            total_biaya    = float(row["total_biaya"]),
        )
    except Exception:
        return None


def render():
    user     = get_current_user()
    is_staff = user.role in (ROLE_ADMIN, ROLE_KASIR)

    st.markdown("## Riwayat Booking")
    st.divider()

    if is_staff:
        df = get_all_booking_db()
    else:
        df = get_booking_by_user(user.id_user)

    if df is None or df.empty:
        tampilkan_peringatan_kosong("Belum ada data booking.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.selectbox("Filter Status",
                                      ["Semua", "Aktif", "Selesai", "Dibatalkan"],
                                      key="rw_status")
    with col2:
        filter_jenis = st.selectbox("Filter Jenis",
                                     ["Semua", "Futsal", "Badminton", "Tenis"],
                                     key="rw_jenis")
    with col3:
        if is_staff:
            filter_tgl = st.date_input("Filter Tanggal (opsional)",
                                        value=None, key="rw_tgl")
        else:
            filter_tgl = None

    df_filter = df.copy()
    if filter_status != "Semua":
        df_filter = df_filter[df_filter["status"] == filter_status]
    if filter_jenis != "Semua":
        df_filter = df_filter[df_filter["jenis"] == filter_jenis]
    if filter_tgl:
        df_filter = df_filter[df_filter["tanggal"] == filter_tgl.strftime("%Y-%m-%d")]

    st.markdown(f"**{len(df_filter)}** booking ditemukan")
    st.divider()

    for _, row in df_filter.iterrows():
        bg, teks_c = STATUS_STYLE.get(row["status"], ("#F9FAFB", "#374151"))

        jam_end_mnt = (int(row["jam_mulai"].split(":")[0]) * 60
                       + int(row["jam_mulai"].split(":")[1])
                       + int(row["durasi_menit"]))
        jam_selesai = f"{jam_end_mnt // 60:02d}:{jam_end_mnt % 60:02d}"

        with st.container():
            st.markdown(f"""
            <div style="background:{bg}; border-radius:10px;
                        padding:1rem 1.2rem; margin-bottom:0.6rem;
                        border-left: 5px solid {teks_c};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700; font-size:1rem;">
                        #{row['id']:05d} &nbsp; {row['nama_tim']}
                    </span>
                    <span style="background:white; padding:0.2rem 0.7rem;
                                 border-radius:20px; font-size:0.8rem;
                                 font-weight:600; color:{teks_c};">
                        {row['status']}
                    </span>
                </div>
                <div style="margin-top:0.5rem; font-size:0.88rem; color:#374151;">
                    {row['lapangan']} ({row['jenis']}) &nbsp;|&nbsp;
                    {row['tanggal']} &nbsp;|&nbsp;
                    {row['jam_mulai']} - {jam_selesai}
                    ({row['durasi_menit']} mnt) &nbsp;|&nbsp;
                    Rp {float(row['total_biaya']):,.0f}
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                with st.expander("Lihat Nota"):
                    booking_obj = _buat_booking_obj_dari_row(row)
                    if booking_obj:
                        st.code(booking_obj.generate_nota(), language=None)
                    else:
                        st.error("Gagal memuat nota.")

            if is_staff and row["status"] == "Aktif":
                with c2:
                    if st.button("Selesai", key=f"selesai_{row['id']}",
                                  use_container_width=True):
                        update_status_booking(int(row["id"]), "Selesai")
                        st.success("Status diubah menjadi Selesai.")
                        st.rerun()

                confirm_batal_key = f"confirm_batal_{row['id']}"
                if confirm_batal_key not in st.session_state:
                    st.session_state[confirm_batal_key] = False

                if not st.session_state[confirm_batal_key]:
                    with c3:
                        if st.button("Batalkan", key=f"batal_{row['id']}",
                                      use_container_width=True):
                            st.session_state[confirm_batal_key] = True
                            st.rerun()
                else:
                    st.warning(f"Batalkan booking #{row['id']:05d}?")
                    col_yes, col_no = st.columns(2)
                    if col_yes.button("Ya, Batalkan", key=f"batal_yes_{row['id']}", use_container_width=True, type="primary"):
                        st.session_state[confirm_batal_key] = False
                        update_status_booking(int(row["id"]), "Dibatalkan")
                        st.warning("Booking dibatalkan.")
                        st.rerun()
                    if col_no.button("Batal", key=f"batal_no_{row['id']}", use_container_width=True):
                        st.session_state[confirm_batal_key] = False
                        st.rerun()

            elif not is_staff and row["status"] == "Aktif":
                confirm_batal_key = f"confirm_batal_user_{row['id']}"
                if confirm_batal_key not in st.session_state:
                    st.session_state[confirm_batal_key] = False

                if not st.session_state[confirm_batal_key]:
                    with c2:
                        if st.button("Batalkan", key=f"batal_user_{row['id']}",
                                      use_container_width=True):
                            st.session_state[confirm_batal_key] = True
                            st.rerun()
                else:
                    st.warning(f"Apakah Anda yakin ingin membatalkan booking #{row['id']:05d}?")
                    col_yes, col_no = st.columns(2)
                    if col_yes.button("Ya, Batalkan", key=f"batal_user_yes_{row['id']}", use_container_width=True, type="primary"):
                        st.session_state[confirm_batal_key] = False
                        update_status_booking(int(row["id"]), "Dibatalkan")
                        st.warning("Booking Anda dibatalkan.")
                        st.rerun()
                    if col_no.button("Batal", key=f"batal_user_no_{row['id']}", use_container_width=True):
                        st.session_state[confirm_batal_key] = False
                        st.rerun()
