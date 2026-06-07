# pages/dashboard_page.py
"""Halaman Dashboard: ringkasan statistik hari ini."""

import datetime
import streamlit as st
import pandas as pd

from auth import get_current_user
from database import (
    get_summary_hari_ini, get_all_lapangan, get_all_booking_db,
    get_pendapatan_harian
)
from konfigurasi import COLOR_PRIMARY, ROLE_ADMIN, ROLE_KASIR, tampilkan_peringatan_kosong


def _card(label: str, value: str, color: str = None) -> str:
    c = color or COLOR_PRIMARY
    return f"""
    <div style="
        background:#F8F8FF; border-radius:12px; padding:1.2rem 1.5rem;
        box-shadow:0 2px 8px rgba(0,0,0,0.07);
        border-left: 5px solid {c}; margin-bottom:0.5rem;">
        <div style="font-size:1.6rem; font-weight:700; color:{c};">{value}</div>
        <div style="color:#6B7280; font-size:0.85rem; margin-top:0.25rem;">{label}</div>
    </div>
    """


def render():
    user  = get_current_user()
    today = datetime.date.today()

    st.markdown("## Dashboard")
    st.markdown(f"**{today.strftime('%A, %d %B %Y')}** &nbsp;|&nbsp; "
                f"Halo, **{user.nama_lengkap or user.username}**")
    st.divider()

    summary      = get_summary_hari_ini()
    all_lapangan = get_all_lapangan()
    total_lap    = len(all_lapangan)

    booking_df = get_all_booking_db()
    aktif_hari_ini = 0
    if not booking_df.empty:
        aktif_hari_ini = len(booking_df[
            (booking_df["tanggal"] == today.strftime("%Y-%m-%d")) &
            (booking_df["status"] == "Aktif")
        ])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(_card("Booking Hari Ini",
                          str(summary["total_booking"]), COLOR_PRIMARY),
                    unsafe_allow_html=True)
    with col2:
        st.markdown(_card("Slot Aktif Hari Ini",
                          str(aktif_hari_ini), "#047857"),
                    unsafe_allow_html=True)
    with col3:
        st.markdown(_card("Total Lapangan",
                          str(total_lap), "#047857"),
                    unsafe_allow_html=True)
    with col4:
        if user.role in (ROLE_ADMIN, ROLE_KASIR):
            pendapatan = summary["total_pendapatan"]
            st.markdown(_card("Pendapatan Hari Ini",
                              f"Rp {pendapatan:,.0f}", "#047857"),
                        unsafe_allow_html=True)
        else:
            st.markdown(_card("Status Akun",
                              user.role.capitalize(), "#047857"),
                        unsafe_allow_html=True)

    st.divider()

    if user.role in (ROLE_ADMIN, ROLE_KASIR):
        st.markdown("### Pendapatan 14 Hari Terakhir")
        df_pend = get_pendapatan_harian(n_hari=14)
        if not df_pend.empty:
            df_pend["tanggal"] = pd.to_datetime(df_pend["tanggal"])
            df_pend = df_pend.set_index("tanggal")
            st.bar_chart(df_pend["pendapatan"], use_container_width=True, color=COLOR_PRIMARY)
        else:
            tampilkan_peringatan_kosong("Belum ada data pendapatan dalam 14 hari terakhir.")
        st.divider()

    st.markdown("### Booking Terbaru")
    if not booking_df.empty:
        tampil = booking_df.head(8).copy()
        tampil = tampil.rename(columns={
            "id": "No.", "nama_tim": "Nama Tim", "lapangan": "Lapangan",
            "jenis": "Jenis", "tanggal": "Tanggal",
            "jam_mulai": "Jam Mulai", "durasi_menit": "Durasi (mnt)",
            "total_biaya": "Total Biaya", "status": "Status"
        })
        if "Total Biaya" in tampil.columns:
            tampil["Total Biaya"] = tampil["Total Biaya"].apply(
                lambda x: f"Rp {x:,.0f}"
            )
        cols_show = ["No.", "Nama Tim", "Lapangan", "Jenis",
                     "Tanggal", "Jam Mulai", "Durasi (mnt)", "Total Biaya", "Status"]
        cols_show = [c for c in cols_show if c in tampil.columns]
        st.dataframe(tampil[cols_show], use_container_width=True, hide_index=True)
    else:
        tampilkan_peringatan_kosong("Belum ada data booking.")

    st.markdown("### Status Lapangan Hari Ini")
    if not booking_df.empty:
        terisi_ids = set(booking_df[
            (booking_df["tanggal"] == today.strftime("%Y-%m-%d")) &
            (booking_df["status"].isin(["Aktif"]))
        ]["id_lapangan"].tolist())
    else:
        terisi_ids = set()

    cols = st.columns(3)
    for idx, lap in enumerate(all_lapangan):
        ada_booking = lap["id"] in terisi_ids
        status_text  = f"Ada Booking" if ada_booking else "Tersedia"
        warna_bg     = "#FEF2F2" if ada_booking else "#F0FDF4"
        warna_border = "#EF4444" if ada_booking else "#22C55E"
        with cols[idx % 3]:
            st.markdown(f"""
            <div style="background:{warna_bg}; border:1px solid {warna_border};
                        border-radius:10px; padding:0.8rem 1rem; margin-bottom:0.5rem;">
                <b>{lap['nama']}</b><br>
                <span style="color:#6B7280; font-size:0.8rem;">
                    {lap['jenis']} &middot; {'Indoor' if lap['is_indoor'] else 'Outdoor'}
                </span><br>
                <span style="font-size:0.85rem; font-weight:600;
                             color:{'#B91C1C' if ada_booking else '#166534'};">
                    {status_text}
                </span>
            </div>
            """, unsafe_allow_html=True)
