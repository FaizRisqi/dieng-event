import os
import re
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("ai_summary")


def _smart_local_summary(judul: str, deskripsi: str, transkrip: str) -> str:
    """
    Fallback summarizer cerdas berbasis ekstraksi teks lokal berbahasa Indonesia.
    Berfungsi tanpa memerlukan API key eksternal.
    """
    teks_sumber = (transkrip.strip() or deskripsi.strip() or judul).strip()
    
    # Pecah menjadi baris-baris kalimat
    baris_mentah = [b.strip() for b in re.split(r"[\n\r]+|\.\s+", teks_sumber) if len(b.strip()) > 10]
    
    poin_kunci = []
    tindak_lanjut = []
    
    kata_aksi = ["tugas", "kerjakan", "kumpul", "praktik", "install", "buka", "deadline", "link", "unduh", "buat", "selesaikan"]
    
    for b in baris_mentah:
        b_lower = b.lower()
        if any(ka in b_lower for ka in kata_aksi):
            tindak_lanjut.append(b)
        elif len(poin_kunci) < 5:
            poin_kunci.append(b)

    if not poin_kunci:
        poin_kunci = [f"Pembahasan materi utama mengenai topik '{judul}'."]
        if deskripsi:
            poin_kunci.append(deskripsi[:200])

    if not tindak_lanjut:
        tindak_lanjut = [
            "Mempelajari kembali modul materi dan rekaman sesi yang tersedia.",
            "Menyelesaikan tugas praktikum yang ditugaskan mentor sebelum tenggat waktu."
        ]

    ringkasan = (
        f"### 🎯 Ringkasan Sesi: {judul}\n\n"
        f"**1. Intisari Pembahasan:**\n"
        f"Sesi ini membahas materi terkait **{judul}** yang difokuskan pada penguasaan konsep, studi kasus, dan implementasi praktis di bidang teknologi.\n\n"
        f"**2. Poin-Poin Utama:**\n"
    )
    for p in poin_kunci[:4]:
        ringkasan += f"- {p.strip().rstrip('.')}.\n"

    ringkasan += f"\n**3. Tindak Lanjut & Action Items Peserta:**\n"
    for t in tindak_lanjut[:4]:
        ringkasan += f"- {t.strip().rstrip('.')}.\n"

    return ringkasan


def generate_ai_summary(judul: str, deskripsi: str = "", transkrip: str = "") -> tuple[bool, str]:
    """
    Menghasilkan ringkasan sesi Zoom menggunakan Google Gemini API (jika GEMINI_API_KEY diset),
    atau menggunakan smart local fallback jika API key belum dikonfigurasi.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    
    sumber = transkrip.strip() or deskripsi.strip() or judul
    
    # 1. Coba gunakan Google Gemini API jika key tersedia
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            
            prompt = (
                f"Kamu adalah asisten notulis AI profesional untuk komunitas teknologi 'Dieng Cyber Wonosobo'.\n"
                f"Buatlah ringkasan terstruktur dan rapi dari materi/sesi Zoom berikut ini:\n\n"
                f"Judul Sesi: {judul}\n"
                f"Deskripsi Sesi: {deskripsi}\n"
                f"Catatan/Transkrip Peserta:\n{sumber[:4000]}\n\n"
                f"Format output wajib menggunakan Bahasa Indonesia yang profesional dan jelas:\n"
                f"### 🎯 Ringkasan Sesi: {judul}\n"
                f"**1. Intisari Pembahasan:**\n(penjelasan 2-3 kalimat)\n\n"
                f"**2. Poin-Poin Penting:**\n(3-5 butir poin materi utama)\n\n"
                f"**3. Tindak Lanjut & Action Items:**\n(tugas, referensi, atau instruksi berikutnya untuk peserta)\n"
            )
            
            payload = json.dumps({
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return True, parts[0]["text"].strip()
        except Exception as e:
            logger.warning(f"Gemini API error, beralih ke local summarizer: {e}")

    # 2. Fallback cerdas lokal (selalu sukses)
    local_summary = _smart_local_summary(judul, deskripsi, transkrip)
    return True, local_summary
