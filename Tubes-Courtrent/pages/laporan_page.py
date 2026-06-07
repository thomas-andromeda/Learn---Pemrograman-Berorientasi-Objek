# pages/laporan_page.py
"""Halaman Laporan Pendapatan: khusus Admin dan Kasir."""

import datetime
import streamlit as st
import pandas as pd

from auth import get_current_user, require_role
from database import (
    get_pendapatan_harian, get_pendapatan_per_lapangan,
    get_all_booking_db
)
from manajemen import get_total_pendapatan_db
from konfigurasi import ROLE_ADMIN, ROLE_KASIR, COLOR_PRIMARY, tampilkan_peringatan_kosong


def render():
    if not require_role(ROLE_ADMIN, ROLE_KASIR):
        return

    st.markdown("## Laporan Pendapatan")
    st.divider()

    today = datetime.date.today()
    col1, col2, col3 = st.columns(3)
    with col1:
        periode = st.selectbox("Periode Laporan",
                                ["7 Hari Terakhir", "30 Hari Terakhir",
                                 "Bulan Ini", "Custom"],
                                key="lap_periode")
    if periode == "7 Hari Terakhir":
        tgl_mulai   = today - datetime.timedelta(days=6)
        tgl_selesai = today
    elif periode == "30 Hari Terakhir":
        tgl_mulai   = today - datetime.timedelta(days=29)
        tgl_selesai = today
    elif periode == "Bulan Ini":
        tgl_mulai   = today.replace(day=1)
        tgl_selesai = today
    else:
        with col2:
            tgl_mulai = st.date_input("Dari",
                                       value=today - datetime.timedelta(days=30),
                                       key="lap_dari")
        with col3:
            tgl_selesai = st.date_input("Sampai", value=today, key="lap_sampai")

    total_pend = get_total_pendapatan_db(tgl_mulai, tgl_selesai)
    df_harian  = get_pendapatan_harian(n_hari=(tgl_selesai - tgl_mulai).days + 1)
    df_booking = get_all_booking_db()

    if not df_booking.empty:
        df_booking["tanggal_dt"] = pd.to_datetime(df_booking["tanggal"])
        df_range = df_booking[
            (df_booking["tanggal_dt"].dt.date >= tgl_mulai) &
            (df_booking["tanggal_dt"].dt.date <= tgl_selesai) &
            (df_booking["status"] != "Dibatalkan")
        ]
        total_booking = len(df_range)
        rata_rata     = total_pend / total_booking if total_booking else 0
    else:
        total_booking = 0
        rata_rata     = 0
        df_range      = pd.DataFrame()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Pendapatan", f"Rp {total_pend:,.0f}")
    with c2:
        st.metric("Total Booking", str(total_booking))
    with c3:
        st.metric("Rata-rata per Booking", f"Rp {rata_rata:,.0f}")

    st.divider()

    st.markdown("### Tren Pendapatan Harian")
    if not df_harian.empty:
        df_harian["tanggal"] = pd.to_datetime(df_harian["tanggal"])
        df_harian = df_harian[
            (df_harian["tanggal"].dt.date >= tgl_mulai) &
            (df_harian["tanggal"].dt.date <= tgl_selesai)
        ].set_index("tanggal")

        if not df_harian.empty:
            tab1, tab2 = st.tabs(["Bar Chart", "Line Chart"])
            with tab1:
                st.bar_chart(df_harian["pendapatan"],
                             use_container_width=True, color=COLOR_PRIMARY)
            with tab2:
                st.line_chart(df_harian["pendapatan"],
                              use_container_width=True, color=COLOR_PRIMARY)
        else:
            tampilkan_peringatan_kosong("Tidak ada data dalam rentang tanggal ini.")
    else:
        tampilkan_peringatan_kosong("Belum ada data pendapatan.")

    st.divider()

    st.markdown("### Pendapatan per Lapangan")
    df_per_lap = get_pendapatan_per_lapangan()
    if not df_per_lap.empty:
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.dataframe(
                df_per_lap.rename(columns={
                    "lapangan": "Lapangan", "jenis": "Jenis",
                    "total_pendapatan": "Total Pendapatan (Rp)",
                    "jumlah_booking": "Jml Booking"
                }),
                use_container_width=True, hide_index=True
            )
        with col_b:
            df_chart = df_per_lap.set_index("lapangan")[["total_pendapatan"]]
            st.bar_chart(df_chart, use_container_width=True, color=COLOR_PRIMARY)
    else:
        tampilkan_peringatan_kosong("Belum ada data pendapatan per lapangan.")

    st.divider()

    st.markdown("### Detail Booking dalam Periode")
    if not df_booking.empty and total_booking > 0:
        detail = df_range[["id", "nama_tim", "lapangan", "jenis",
                             "tanggal", "jam_mulai", "durasi_menit",
                             "total_biaya", "status"]].copy()
        detail["total_biaya"] = detail["total_biaya"].apply(
            lambda x: f"Rp {x:,.0f}"
        )
        detail = detail.rename(columns={
            "id": "No.", "nama_tim": "Nama Tim", "lapangan": "Lapangan",
            "jenis": "Jenis", "tanggal": "Tanggal", "jam_mulai": "Jam",
            "durasi_menit": "Durasi (mnt)", "total_biaya": "Biaya", "status": "Status"
        })
        st.dataframe(detail, use_container_width=True, hide_index=True)
    else:
        tampilkan_peringatan_kosong("Tidak ada booking dalam periode ini.")
