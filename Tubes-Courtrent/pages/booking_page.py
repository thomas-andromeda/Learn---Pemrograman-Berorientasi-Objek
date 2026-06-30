# pages/booking_page.py
"""Halaman Form Booking Baru."""

import datetime
import streamlit as st

from auth import get_current_user
from manajemen import proses_booking, get_lapangan_objects, get_slot_status
from database import get_all_lapangan
from konfigurasi import JAM_BUKA, JAM_TUTUP, COLOR_PRIMARY, tampilkan_peringatan_kosong


def _format_durasi(menit: int) -> str:
    jam  = menit // 60
    sisa = menit % 60
    if jam and sisa:
        return f"{jam} jam {sisa} menit"
    elif jam:
        return f"{jam} jam"
    return f"{sisa} menit"


def render():
    user  = get_current_user()
    today = datetime.date.today()

    st.markdown("## Booking Lapangan Baru")
    st.markdown("Isi formulir di bawah untuk membuat booking baru.")
    st.divider()

    # State sukses booking untuk mencegah double-submit/spam button
    if "bk_success" not in st.session_state:
        st.session_state.bk_success = False

    if st.session_state.bk_success:
        st.success("Booking berhasil dibuat!")
        st.balloons()
        if "bk_nota" in st.session_state:
            with st.expander("Lihat Nota Booking", expanded=True):
                st.code(st.session_state.bk_nota, language=None)
        if st.button("Buat Booking Baru Lagi", use_container_width=True, type="primary"):
            st.session_state.bk_success = False
            st.session_state.pop("bk_nota", None)
            st.rerun()
        return

    all_lapangan = get_all_lapangan()
    if not all_lapangan:
        tampilkan_peringatan_kosong("Belum ada lapangan yang tersedia.")
        return

    # 1. Pilih Lapangan
    st.markdown("### 1. Pilih Lapangan")
    lap_options = {f"{l['nama']} ({l['jenis']}) - Rp {l['harga_per_jam']:,.0f}/jam": l
                   for l in all_lapangan}
    lap_label   = st.selectbox("Lapangan*", list(lap_options.keys()),
                                key="bk_lapangan")
    lap_data    = lap_options[lap_label]

    attr   = lap_data.get("atribut_khusus", "-")
    lokasi = "Indoor" if lap_data["is_indoor"] else "Outdoor"
    st.markdown(f"""
    <div style="background:#F0F4F2; border-left:4px solid {COLOR_PRIMARY};
                border-radius:6px; padding:0.7rem 1rem; font-size:0.9rem;
                margin-bottom:1rem;">
        <b>{lap_data['nama']}</b> &nbsp;&middot;&nbsp; {lap_data['jenis']}
        &nbsp;&middot;&nbsp; {lokasi} &nbsp;&middot;&nbsp; {attr}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 2. Pilih Jadwal
    st.markdown("### 2. Pilih Jadwal")
    col1, col2 = st.columns(2)

    with col1:
        tanggal = st.date_input("Tanggal Booking*", value=today,
                                 min_value=today, key="bk_tanggal")

    slots       = get_slot_status(lap_data["id"], tanggal)
    slots_bebas = [s["jam"] for s in slots if s["tersedia"]]

    if not slots_bebas:
        st.error(f"Semua slot pada {tanggal.strftime('%d %B %Y')} sudah terisi.")
        return

    with col2:
        jam_mulai = st.selectbox("Jam Mulai*", slots_bebas, key="bk_jam_mulai")

    durasi_options = {_format_durasi(m): m for m in range(30, 361, 30)}
    durasi_label   = st.selectbox("Durasi*", list(durasi_options.keys()),
                                   index=1, key="bk_durasi")
    durasi_menit   = durasi_options[durasi_label]

    is_invalid_time = False
    total_m = 0
    if jam_mulai:
        jam, menit  = map(int, jam_mulai.split(":"))
        total_m     = jam * 60 + menit + durasi_menit
        jam_selesai = f"{total_m // 60:02d}:{total_m % 60:02d}"

        lap_obj   = next((l for l in get_lapangan_objects()
                          if l.id_lapangan == lap_data["id"]), None)
        biaya_est = lap_obj.hitung_biaya(durasi_menit) if lap_obj else 0

        is_invalid_time = total_m > JAM_TUTUP * 60

        if is_invalid_time:
            st.error(f"⚠️ Waktu selesai ({jam_selesai} WIB) melebihi jam tutup Sport Center ({JAM_TUTUP:02d}:00 WIB). Silakan kurangi durasi atau pilih jam mulai lebih awal.")
        else:
            st.markdown(f"""
            <div style="background:#F0FDF4; border:1px solid #86EFAC;
                        border-radius:8px; padding:0.9rem 1.2rem;
                        margin: 0.5rem 0 1rem 0;">
                Jam selesai: <b>{jam_selesai} WIB</b> &nbsp;|&nbsp;
                Estimasi biaya: <b>Rp {biaya_est:,.0f}</b>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # 3. Informasi Pemesan
    st.markdown("### 3. Informasi Pemesan")
    nama_tim = st.text_input("Nama Tim / Pemesan*",
                              placeholder="Contoh: Tim Garuda, Keluarga Budi",
                              key="bk_nama_tim")

    st.divider()

    with st.expander("Lihat semua slot hari ini"):
        cols_slot = st.columns(6)
        for i, slot in enumerate(slots):
            warna = "#D1FAE5" if slot["tersedia"] else "#FEE2E2"
            teks  = "Kosong" if slot["tersedia"] else "Terisi"
            cols_slot[i % 6].markdown(
                f"<div style='background:{warna}; border-radius:6px; "
                f"padding:0.3rem; text-align:center; font-size:0.75rem; "
                f"margin-bottom:0.3rem;'>{teks}<br>{slot['jam']}</div>",
                unsafe_allow_html=True
            )

    # Menonaktifkan tombol jika waktu selesai tidak valid
    btn_disabled = is_invalid_time or not jam_mulai

    if st.button("Konfirmasi dan Buat Booking", use_container_width=True, type="primary", disabled=btn_disabled):
        if not nama_tim.strip():
            st.error("Nama tim / pemesan tidak boleh kosong.")
        else:
            with st.spinner("Memproses booking..."):
                sukses, pesan, booking_obj = proses_booking(
                    nama_tim     = nama_tim.strip(),
                    id_lapangan  = lap_data["id"],
                    tanggal      = tanggal,
                    jam_mulai    = jam_mulai,
                    durasi_menit = durasi_menit,
                    id_user      = user.id_user,
                )

            if sukses and booking_obj:
                st.session_state.bk_success = True
                st.session_state.bk_nota = booking_obj.generate_nota()
                st.rerun()
            else:
                st.error(pesan)
