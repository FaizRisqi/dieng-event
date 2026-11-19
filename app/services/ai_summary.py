import os
import re
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("ai_summary")


def extract_youtube_info(text: str) -> dict | None:
    if not text:
        return None
    m = re.search(
        r"(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|embed/|v/|shorts/)|youtu\.be/)([\w-]{11})",
        text,
    )
    if not m:
        return None
    video_id = m.group(1)
    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    info = {
        "video_id": video_id,
        "url": clean_url,
        "title": "",
        "author": "",
        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "duration_str": "",
        "topic": "",
    }
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={clean_url}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            info["title"] = data.get("title", "").strip()
            info["author"] = data.get("author_name", "").strip()
    except Exception:
        pass

    try:
        req2 = urllib.request.Request(
            clean_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            html = resp2.read().decode("utf-8", errors="ignore")
            m_player = re.search(
                r"ytInitialPlayerResponse\s*=\s*({.+?});(?:var\s|window\[|\n|</script>)",
                html,
            )
            if m_player:
                pdata = json.loads(m_player.group(1))
                v_det = pdata.get("videoDetails", {})
                if not info["title"]:
                    info["title"] = v_det.get("title", "").strip()
                if not info["author"]:
                    info["author"] = v_det.get("author", "").strip()
                sec = int(v_det.get("lengthSeconds", 0))
                if sec > 0:
                    menit = sec // 60
                    detik = sec % 60
                    info["duration_str"] = (
                        f"{menit} menit {detik} detik" if detik else f"{menit} menit"
                    )
    except Exception:
        pass

    raw_title = info["title"]
    cleaned = re.sub(r"(?i)^zoom\s*meeting\s*[-–:]*\s*", "", raw_title)
    cleaned = re.sub(r"\d{4}\s+\d{2}\s+\d{2}.*", "", cleaned).strip(" -_")
    info["topic"] = cleaned or raw_title or "Sesi Pembelajaran"
    return info


def _smart_local_summary(
    judul: str,
    deskripsi: str = "",
    transkrip: str = "",
    link_rekaman: str = "",
) -> str:
    yt = (
        extract_youtube_info(transkrip)
        or extract_youtube_info(link_rekaman)
        or extract_youtube_info(deskripsi)
    )

    # Bersihkan transkrip dari URL untuk mengecek apakah ada isi catatan nyata
    teks_tanpa_url = re.sub(r"https?://\S+", "", transkrip).strip()
    
    # KASUS 1: Tidak ada teks transkrip / catatan yang diberikan
    if not teks_tanpa_url:
        if yt:
            res = (
                f"### 🎯 Informasi Rekaman: {judul}\n\n"
                f"> 🎬 **Rekaman Video:** [{yt['title'] or 'Tonton Rekaman'}]({yt['url']})  \n"
                f"> 👤 **Pemateri / Kanal:** {yt['author'] or '-'} &bull; ⏱️ **Durasi:** {yt['duration_str'] or '-'}\n\n"
                f"**Catatan:**\n"
                f"Isi pembahasan belum bisa diringkas karena tidak ada teks transkrip atau catatan sesi yang dilampirkan. "
                f"Mode lokal tidak memproses audio/video dari link secara langsung. "
                f"Silakan tempel teks catatan atau notulen untuk membuat ringkasan isi pembahasan.\n\n"
                f"---\n*Dibuat otomatis (mode: lokal). Periksa sebelum dibagikan.*"
            )
            return res
        else:
            return (
                f"### 🎯 Ringkasan Sesi: {judul}\n\n"
                f"**Catatan:**\n"
                f"Belum ada teks transkrip atau catatan sesi yang diberikan untuk diringkas. "
                f"Silakan tempel teks catatan atau notulen sesi.\n\n"
                f"---\n*Dibuat otomatis (mode: lokal). Periksa sebelum dibagikan.*"
            )

    # KASUS 2: Ada teks transkrip nyata -> ambil HANYA poin dari teks tersebut
    baris_mentah = [
        b.strip()
        for b in re.split(r"[\n\r]+|\.\s+", teks_tanpa_url)
        if len(b.strip()) > 10 and not b.strip().startswith("http")
    ]

    poin_kunci = []
    tindak_lanjut = []
    kata_aksi = [
        "tugas", "kerjakan", "kumpul", "praktik", "install", "buka",
        "deadline", "link", "unduh", "buat", "selesaikan", "pelajari", "baca",
    ]

    for b in baris_mentah:
        b_clean = re.sub(r"^[0-9\.\-\*\#\s]+", "", b).strip()
        if not b_clean:
            continue
        b_lower = b_clean.lower()
        if any(ka in b_lower for ka in kata_aksi):
            if len(tindak_lanjut) < 4 and b_clean not in tindak_lanjut:
                tindak_lanjut.append(b_clean)
        else:
            if len(poin_kunci) < 5 and b_clean not in poin_kunci:
                poin_kunci.append(b_clean)

    # Jika tidak ada yang masuk tindak lanjut, masukkan semua ke poin kunci
    if not poin_kunci and not tindak_lanjut:
        poin_kunci = [b.rstrip(".") for b in baris_mentah[:4]]

    yt_header = ""
    if yt:
        yt_header = (
            f"> 🎬 **Rekaman Video:** [{yt['title'] or 'Tonton Rekaman'}]({yt['url']})  \n"
            f"> 👤 **Pemateri / Kanal:** {yt['author'] or '-'} &bull; ⏱️ **Durasi:** {yt['duration_str'] or '-'}\n\n"
        )

    ringkasan = f"### 🎯 Ringkasan Sesi: {judul}\n\n{yt_header}"
    if poin_kunci:
        ringkasan += "**1. Poin Pembahasan (dari catatan/transkrip):**\n\n"
        for p in poin_kunci:
            ringkasan += f"- {p.rstrip('.')}.\n"
        ringkasan += "\n"

    section_num = 2 if poin_kunci else 1
    if tindak_lanjut:
        ringkasan += f"**{section_num}. Tindak Lanjut & Action Items:**\n\n"
        for t in tindak_lanjut:
            ringkasan += f"- {t.rstrip('.')}.\n"
        ringkasan += "\n"

    if not poin_kunci and not tindak_lanjut:
        ringkasan += (
            "**Catatan:** Teks catatan/transkrip terlalu pendek untuk diekstrak poin pembahasannya.\n\n"
        )

    ringkasan += "---\n*Dibuat otomatis (mode: lokal). Periksa sebelum dibagikan.*"
    return ringkasan


def generate_ai_summary(
    judul: str,
    deskripsi: str = "",
    transkrip: str = "",
    link_rekaman: str = "",
) -> tuple[bool, str, str, str | None]:
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash"

    yt = (
        extract_youtube_info(transkrip)
        or extract_youtube_info(link_rekaman)
        or extract_youtube_info(deskripsi)
    )

    reason_failed = None

    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"
            context_extra = ""
            if yt:
                context_extra = (
                    f"- Link Video/Rekaman: {yt['url']}\n"
                    f"- Judul Rekaman YouTube: {yt['title']}\n"
                    f"- Channel/Pemateri: {yt['author']}\n"
                    f"- Durasi: {yt['duration_str']}\n"
                )

            sumber_teks = transkrip.strip() or deskripsi.strip() or judul
            prompt = (
                f"Kamu adalah asisten notulis untuk komunitas teknologi 'Dieng Cyber Wonosobo'.\n"
                f"Buatlah ringkasan terstruktur dari materi berikut berdasarkan teks yang diberikan.\n"
                f"Jangan mengarang informasi di luar teks yang diberikan.\n\n"
                f"- Judul Sesi: {judul}\n"
                f"- Deskripsi Sesi: {deskripsi}\n"
                f"{context_extra}"
                f"- Teks Catatan/Transkrip Peserta:\n{sumber_teks[:4000]}\n\n"
                f"Format output wajib Markdown rapi dengan baris penutup:\n"
                f"'---\\n*Dibuat otomatis (mode: gemini). Periksa sebelum dibagikan.*'\n"
            )

            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}]
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": gemini_key,
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        txt = parts[0]["text"].strip()
                        if "Dibuat otomatis (mode: gemini)" not in txt:
                            txt += "\n\n---\n*Dibuat otomatis (mode: gemini). Periksa sebelum dibagikan.*"
                        return True, txt, "gemini", None
        except urllib.error.HTTPError as e:
            reason_failed = f"HTTP {e.code}"
            logger.warning(f"Gemini API HTTP error: {e}")
        except Exception as e:
            reason_failed = str(e)
            logger.warning(f"Gemini API error: {e}")

    # Fallback ke mode lokal
    local_summary = _smart_local_summary(
        judul=judul,
        deskripsi=deskripsi,
        transkrip=transkrip,
        link_rekaman=link_rekaman,
    )
    return True, local_summary, "lokal", reason_failed
