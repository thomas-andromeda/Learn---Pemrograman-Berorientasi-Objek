# pages/ketersediaan_page.py
"""Halaman Cek Ketersediaan Slot: semua role."""

import datetime
import streamlit as st

from database import get_all_lapangan
from manajemen import get_slot_status
from konfigurasi import COLOR_PRIMARY, tampilkan_peringatan_kosong


WARNA_JENIS = {"Futsal": COLOR_PRIMARY, "Badminton": COLOR_PRIMARY, "Tenis": COLOR_PRIMARY}


def render():
    st.markdown("## Cek Ketersediaan Slot")
    st.markdown("Cek jadwal kosong lapangan pada tanggal tertentu.")
    st.divider()

    all_lapangan = get_all_lapangan()
    if not all_lapangan:
        tampilkan_peringatan_kosong("Belum ada lapangan yang terdaftar.")
        return

    col1, col2, col3 = st.columns(3)
    today = datetime.date.today()

    with col1:
        tgl_cek = st.date_input("Pilih Tanggal", value=today,
                                  min_value=today, key="ket_tanggal")
    with col2:
        jenis_filter = st.selectbox("Jenis Lapangan",
                                     ["Semua", "Futsal", "Badminton", "Tenis"],
                                     key="ket_jenis")
    with col3:
        lap_options = {"(Semua Lapangan)": None}
        for l in all_lapangan:
            if jenis_filter == "Semua" or l["jenis"] == jenis_filter:
                lap_options[f"{l['nama']} ({l['jenis']})"] = l["id"]
        lap_pilihan   = st.selectbox("Pilih Lapangan", list(lap_options.keys()),
                                      key="ket_lapangan")
        lap_id_filter = lap_options[lap_pilihan]

    st.divider()
    st.markdown(f"### Slot pada **{tgl_cek.strftime('%A, %d %B %Y')}**")

    lapangan_tampil = all_lapangan
    if jenis_filter != "Semua":
        lapangan_tampil = [l for l in all_lapangan if l["jenis"] == jenis_filter]
    if lap_id_filter is not None:
        lapangan_tampil = [l for l in lapangan_tampil if l["id"] == lap_id_filter]

    if not lapangan_tampil:
        tampilkan_peringatan_kosong("Tidak ada lapangan yang sesuai filter.")
        return

    for lap in lapangan_tampil:
        lokasi      = "Indoor" if lap["is_indoor"] else "Outdoor"
        warna_jenis = WARNA_JENIS.get(lap["jenis"], COLOR_PRIMARY)
        slots       = get_slot_status(lap["id"], tgl_cek)

        n_bebas  = sum(1 for s in slots if s["tersedia"])
        n_terisi = len(slots) - n_bebas

        st.markdown(f"""
        <div style="background:#F9FAFB; border:1px solid #E5E7EB;
                    border-top: 4px solid {warna_jenis};
                    border-radius:12px; padding:1rem 1.3rem; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:1.05rem; font-weight:700; color:{warna_jenis};">
                    {lap['nama']}
                </span>
                <span style="font-size:0.82rem; color:#6B7280;">
                    {lap['jenis']} &middot; {lokasi} &middot; Rp {lap['harga_per_jam']:,.0f}/jam
                </span>
            </div>
            <div style="margin: 0.5rem 0 0.3rem 0; font-size:0.85rem; color:#374151;">
                <span style="color:#166534; font-weight:600;">{n_bebas} slot tersedia</span>
                &nbsp;|&nbsp;
                <span style="color:#B91C1C; font-weight:600;">{n_terisi} slot terisi</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(8)
        for i, slot in enumerate(slots):
            if slot["tersedia"]:
                bg    = "#D1FAE5"
                teks  = "Kosong"
                color = "#065F46"
            else:
                bg    = "#FEE2E2"
                teks  = "Terisi"
                color = "#991B1B"

            cols[i % 8].markdown(
                f"<div style='background:{bg}; border-radius:6px; "
                f"padding:0.3rem 0.4rem; text-align:center; "
                f"font-size:0.7rem; font-weight:600; color:{color}; "
                f"margin-bottom:0.35rem;'>"
                f"{teks}<br>{slot['jam']}</div>",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.82rem; color:#6B7280; margin-top:0.5rem;">
        Hijau = Slot Tersedia &nbsp;&nbsp; Merah = Slot Terisi
    </div>
    """, unsafe_allow_html=True)
