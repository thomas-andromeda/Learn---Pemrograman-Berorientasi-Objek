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


def _generate_excel(total_pend, total_booking, rata_rata, df_range, df_per_lap):
    import io
    output = io.BytesIO()
    
    # 1. Buat DataFrame Ringkasan Utama
    df_ringkasan = pd.DataFrame([{
        "Total Pendapatan (Rp)": total_pend,
        "Total Booking": total_booking,
        "Rata-rata Pendapatan per Booking (Rp)": rata_rata
    }])
    
    # 1.5. Buat DataFrame Rincian Kontribusi per Lapangan (periode terpilih)
    if not df_range.empty:
        df_kontribusi = df_range.groupby(["lapangan", "jenis"]).agg(
            Jumlah_Booking=('id', 'count'),
            Total_Pendapatan=('total_biaya', 'sum')
        ).reset_index()
        # Hitung persentase kontribusi terhadap total_pend
        df_kontribusi["Persentase_Kontribusi"] = (df_kontribusi["Total_Pendapatan"] / total_pend) * 100 if total_pend else 0
        df_kontribusi["Persentase_Kontribusi"] = df_kontribusi["Persentase_Kontribusi"].round(2).apply(lambda x: f"{x}%")
        df_kontribusi.columns = ["Nama Lapangan", "Jenis Lapangan", "Jumlah Booking", "Pendapatan (Rp)", "Kontribusi (%)"]
        df_kontribusi = df_kontribusi.sort_values(by="Pendapatan (Rp)", ascending=False)
    else:
        df_kontribusi = pd.DataFrame(columns=["Nama Lapangan", "Jenis Lapangan", "Jumlah Booking", "Pendapatan (Rp)", "Kontribusi (%)"])
    
    # 2. Buat DataFrame Detail Booking
    if not df_range.empty:
        df_detail = df_range[["id", "nama_tim", "lapangan", "jenis", "tanggal", "jam_mulai", "durasi_menit", "total_biaya", "status"]].copy()
        df_detail.columns = ["No. Booking", "Nama Tim", "Lapangan", "Jenis", "Tanggal", "Jam Mulai", "Durasi (Menit)", "Total Biaya (Rp)", "Status"]
    else:
        df_detail = pd.DataFrame(columns=["No. Booking", "Nama Tim", "Lapangan", "Jenis", "Tanggal", "Jam Mulai", "Durasi (Menit)", "Total Biaya (Rp)", "Status"])
        
    # 3. Buat DataFrame Pendapatan per Lapangan (All-time)
    if not df_per_lap.empty:
        df_lapangan = df_per_lap.rename(columns={
            "lapangan": "Lapangan",
            "jenis": "Jenis",
            "total_pendapatan": "Total Pendapatan (Rp)",
            "jumlah_booking": "Jumlah Booking"
        })
    else:
        df_lapangan = pd.DataFrame(columns=["Lapangan", "Jenis", "Total Pendapatan (Rp)", "Jumlah Booking"])

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Tulis label dan tabel Ringkasan Utama
        pd.DataFrame([["=== RINGKASAN UTAMA PERIODE ==="]]).to_excel(writer, sheet_name='Ringkasan', index=False, header=False, startrow=0)
        df_ringkasan.to_excel(writer, sheet_name='Ringkasan', index=False, startrow=1)
        
        # Tulis label dan tabel Rincian Kontribusi Lapangan
        pd.DataFrame([["=== RINCIAN KONTRIBUSI PER LAPANGAN (PERIODE TERPILIH) ==="]]).to_excel(writer, sheet_name='Ringkasan', index=False, header=False, startrow=4)
        df_kontribusi.to_excel(writer, sheet_name='Ringkasan', index=False, startrow=5)
        
        # Tulis Sheet Detail Booking & Statistik All-time
        df_detail.to_excel(writer, sheet_name='Detail Booking', index=False)
        df_lapangan.to_excel(writer, sheet_name='Statistik Lapangan (All-time)', index=False)
        
    return output.getvalue()


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
    df_per_lap = get_pendapatan_per_lapangan()

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

    try:
        excel_data = _generate_excel(total_pend, total_booking, rata_rata, df_range, df_per_lap)
        st.download_button(
            label="Unduh Laporan (Excel)",
            data=excel_data,
            file_name=f"laporan_court_rent_{tgl_mulai}_to_{tgl_selesai}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Gagal menyiapkan file unduhan Excel: {e}")

    st.divider()

    st.markdown("### Tren Pendapatan Harian")
    if not df_harian.empty:
        df_harian["tanggal"] = pd.to_datetime(df_harian["tanggal"])
        df_harian = df_harian[
            (df_harian["tanggal"].dt.date >= tgl_mulai) &
            (df_harian["tanggal"].dt.date <= tgl_selesai)
        ].copy()
 
        if not df_harian.empty:
            import altair as alt
            df_harian["tanggal"] = df_harian["tanggal"].dt.strftime("%d %b %Y")
            
            tab1, tab2 = st.tabs(["Bar Chart", "Line Chart"])
            with tab1:
                chart = alt.Chart(df_harian).mark_bar(
                    color=COLOR_PRIMARY,
                    size=40
                ).encode(
                    x=alt.X('tanggal:O', axis=alt.Axis(labelAngle=0), title=None),
                    y=alt.Y('pendapatan:Q', title='Pendapatan (Rp)')
                ).properties(
                    height=300
                )
                st.altair_chart(chart, use_container_width=True)
            with tab2:
                chart_line = alt.Chart(df_harian).mark_line(
                    color=COLOR_PRIMARY,
                    point=True
                ).encode(
                    x=alt.X('tanggal:O', axis=alt.Axis(labelAngle=0), title=None),
                    y=alt.Y('pendapatan:Q', title='Pendapatan (Rp)')
                ).properties(
                    height=300
                )
                st.altair_chart(chart_line, use_container_width=True)
        else:
            tampilkan_peringatan_kosong("Tidak ada data dalam rentang tanggal ini.")
    else:
        tampilkan_peringatan_kosong("Belum ada data pendapatan.")

    st.divider()

    st.markdown("### Pendapatan per Lapangan")
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
            import altair as alt
            chart_lap = alt.Chart(df_per_lap).mark_bar(
                color=COLOR_PRIMARY,
                size=40
            ).encode(
                x=alt.X('lapangan:O', axis=alt.Axis(labelAngle=0), title=None),
                y=alt.Y('total_pendapatan:Q', title='Pendapatan (Rp)')
            ).properties(
                height=300
            )
            st.altair_chart(chart_lap, use_container_width=True)
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
