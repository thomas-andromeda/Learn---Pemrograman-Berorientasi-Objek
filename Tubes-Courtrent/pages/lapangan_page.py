# pages/lapangan_page.py
"""Halaman Daftar Lapangan: tampilkan semua lapangan beserta statusnya."""

import datetime
import streamlit as st

from database import get_all_lapangan, get_booking_by_tanggal_lapangan
from konfigurasi import COLOR_PRIMARY, tampilkan_peringatan_kosong


WARNA_JENIS = {"Futsal": COLOR_PRIMARY, "Badminton": COLOR_PRIMARY, "Tenis": COLOR_PRIMARY}


def render():
    st.markdown("## Daftar Lapangan")
    st.markdown("Lihat semua lapangan yang tersedia di Court Rent Sport Center.")
    st.divider()

    all_lapangan = get_all_lapangan()
    if not all_lapangan:
        tampilkan_peringatan_kosong("Belum ada lapangan yang terdaftar.")
        return

    today = datetime.date.today()
    col_filter, _ = st.columns([2, 4])
    with col_filter:
        tgl_cek = st.date_input("Cek status pada tanggal:", value=today,
                                 min_value=today, key="lap_tgl_cek")

    st.divider()

    jenis_filter = st.radio("Filter Jenis:",
                             ["Semua", "Futsal", "Badminton", "Tenis"],
                             horizontal=True, key="lap_jenis_filter")

    lapangan_tampil = all_lapangan
    if jenis_filter != "Semua":
        lapangan_tampil = [l for l in all_lapangan if l["jenis"] == jenis_filter]

    if not lapangan_tampil:
        tampilkan_peringatan_kosong(f"Tidak ada lapangan jenis {jenis_filter}.")
        return

    cols = st.columns(3)
    for idx, lap in enumerate(lapangan_tampil):
        bookings    = get_booking_by_tanggal_lapangan(lap["id"], tgl_cek)
        ada_booking = len(bookings) > 0

        warna_jenis  = WARNA_JENIS.get(lap["jenis"], COLOR_PRIMARY)
        lokasi       = "Indoor" if lap["is_indoor"] else "Outdoor"
        attr         = lap.get("atribut_khusus", "-")

        status_text  = f"{len(bookings)} Booking Aktif" if ada_booking else "Tersedia"
        status_color = "#B91C1C" if ada_booking else "#166534"
        bg_color     = "#FFFBEB" if ada_booking else "#F0FDF4"

        with cols[idx % 3]:
            st.markdown(f"""
            <div style="
                background: {bg_color};
                border: 1px solid {warna_jenis}33;
                border-top: 4px solid {warna_jenis};
                border-radius: 12px;
                padding: 1.2rem;
                margin-bottom: 1rem;
                box-shadow: 0 2px 6px rgba(0,0,0,0.06);
            ">
                <div style="font-size: 1.1rem; font-weight: 700;
                            color: {warna_jenis}; margin: 0.4rem 0;">
                    {lap['nama']}
                </div>
                <div style="font-size: 0.82rem; color: #6B7280; margin-bottom: 0.6rem;">
                    {lap['jenis']} &nbsp;&middot;&nbsp; {lokasi}<br>
                    {attr}
                </div>
                <div style="font-size: 1rem; font-weight: 600; color: #1F2937;">
                    Rp {lap['harga_per_jam']:,.0f}
                    <span style="font-weight:400; color:#6B7280; font-size:0.8rem;">/jam</span>
                </div>
                <div style="margin-top: 0.6rem; font-size: 0.85rem;
                            font-weight: 600; color: {status_color};">
                    {status_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if ada_booking:
                with st.expander(f"Lihat jadwal ({len(bookings)} booking)"):
                    for b in bookings:
                        jam, menit = map(int, b["jam_mulai"].split(":"))
                        selesai    = jam * 60 + menit + b["durasi_menit"]
                        jam_sel    = f"{selesai // 60:02d}:{selesai % 60:02d}"
                        st.markdown(
                            f"- **{b['nama_tim']}** &nbsp; "
                            f"{b['jam_mulai']} - {jam_sel} "
                            f"({b['durasi_menit']} mnt)"
                        )
