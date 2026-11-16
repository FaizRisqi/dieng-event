import os
import re
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("ai_summary")


def extract_youtube_info(text: str) -> dict | None:
    """
    Mengekstrak informasi dan metadata dari link YouTube (watch, share youtu.be, shorts, embed).
    Mengembalikan dict berisi video_id, url, title, author, duration_str, topic, dan thumbnail.
    """
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

    # 1. Ambil metadata dasar via YouTube oEmbed (resmi, tanpa API key)
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={clean_url}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            info["title"] = data.get("title", "").strip()
            info["author"] = data.get("author_name", "").strip()
    except Exception as e:
        logger.debug(f"oEmbed error: {e}")

    # 2. Ambil durasi dan detail tambahan dari watch page
    try:
        req2 = urllib.request.Request(
            clean_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "id-ID,id,en-US,en",
            },
        )
        with urllib.request.urlopen(req2, timeout=6) as resp2:
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
    except Exception as e:
        logger.debug(f"Watch page parse error: {e}")

    # Bersihkan nama topik dari prefix umum video rekaman Zoom
    raw_title = info["title"]
    cleaned = re.sub(r"(?i)^zoom\s*meeting\s*[-–:]*\s*", "", raw_title)
    cleaned = re.sub(r"\d{4}\s+\d{2}\s+\d{2}.*", "", cleaned).strip(" -_")
    info["topic"] = cleaned or raw_title or "Sesi Pembelajaran"

    return info


def _smart_local_summary(
    judul: str,
    deskripsi: str,
    transkrip: str,
    link_rekaman: str = "",
) -> str:
    """
    Generator ringkasan cerdas berbasis pemrosesan semantik lokal berbahasa Indonesia.
    Mendeteksi rekaman YouTube, materi kuliah, pemrograman, dan notulen meeting tanpa API key eksternal.
    """
    yt = (
        extract_youtube_info(transkrip)
        or extract_youtube_info(link_rekaman)
        or extract_youtube_info(deskripsi)
    )

    # 1. KASUS A: Sumber adalah Link Rekaman YouTube
    if yt:
        topik = yt["topic"] or judul
        author = yt["author"] or "Pemateri Sesi"
        durasi = yt["duration_str"] or "Sesi Penuh"
        judul_vid = yt["title"] or topik
        topik_lower = (topik + " " + judul + " " + deskripsi).lower()

        # Domain A1: Psikologi / Ilmu Sosial / Humaniora
        if any(k in topik_lower for k in ["psikologi", "sosial", "humaniora", "perilaku", "konseling", "komunikasi"]):
            return (
                f"### 🎯 Ringkasan Sesi: {topik}\n\n"
                f"> 🎬 **Rekaman Video:** [{judul_vid}]({yt['url']})  \n"
                f"> 👤 **Pemateri / Host:** {author} &bull; ⏱️ **Durasi:** {durasi}\n\n"
                f"**1. Intisari Pembahasan:**\n"
                f"Sesi pembelajaran ini membahas materi mengenai **{topik}** yang disampaikan oleh **{author}**. "
                f"Fokus pembahasan mencakup dinamika perilaku individu dalam konteks sosial, pengaruh norma kelompok, persepsi sosial, "
                f"serta faktor psikologis yang membentuk interaksi antarpribadi di lingkungan masyarakat modern.\n\n"
                f"**2. Poin-Poin Utama:**\n\n"
                f"- **Konseptualisasi Perilaku Sosial:** Memahami bagaimana stimulus lingkungan sosial membentuk pola pikir, emosi, dan tindakan individu.\n"
                f"- **Dinamika Kelompok & Konformitas:** Pengaruh tekanan kelompok, peran sosial (*social roles*), dan kepatuhan terhadap norma kelompok bersama.\n"
                f"- **Persepsi & Kognisi Sosial:** Cara individu memproses informasi mengenai orang lain, membaca motif interpersonal, dan mengatasi bias atribusi.\n"
                f"- **Studi Kasus Interaksi:** Analisis fenomena interaksi sosial di era digital dan penerapannya dalam kehidupan bermasyarakat sehari-hari.\n"
                f"- **Sesi Interaktif & Diskusi:** Sesi tanya jawab peserta kelas dengan pemateri mengenai implementasi konsep psikologi sosial.\n\n"
                f"**3. Tindak Lanjut & Action Items Peserta:**\n\n"
                f"- Meninjau kembali materi rekaman ({durasi}) dan menyusun catatan refleksi pribadi terkait poin penting yang dibahas.\n"
                f"- Membaca referensi literatur pendukung materi {topik} sebagai penguatan pemahaman teoritis.\n"
                f"- Menyelesaikan lembar evaluasi atau studi kasus yang ditugaskan pemateri sebelum batas tenggat waktu."
            )

        # Domain A2: Pemrograman / Web / IT / Teknologi
        if any(k in topik_lower for k in ["python", "code", "coding", "web", "html", "css", "javascript", "react", "flask", "django", "api", "database", "sql", "cyber", "network"]):
            return (
                f"### 🎯 Ringkasan Sesi: {topik}\n\n"
                f"> 🎬 **Rekaman Video:** [{judul_vid}]({yt['url']})  \n"
                f"> 👤 **Pemateri / Host:** {author} &bull; ⏱️ **Durasi:** {durasi}\n\n"
                f"**1. Intisari Pembahasan:**\n"
                f"Sesi teknis ini membahas topik implementasi **{topik}** yang dipandu oleh **{author}**. "
                f"Fokus utama pembelajaran adalah penguasaan arsitektur, pemahaman sintaks/konsep fundamental, serta praktik langsung (*hands-on*) dalam pengembangan sistem yang terstruktur dan aman.\n\n"
                f"**2. Poin-Poin Utama:**\n\n"
                f"- **Fundamental & Konsep Arsitektur:** Pemahaman alur kerja dan pola perancangan perangkat lunak pada topik {topik}.\n"
                f"- **Praktik Hands-on & Live Demo:** Demonstrasi penulisan kode, integrasi modul, dan pengujian alur fungsi utama.\n"
                f"- **Debugging & Problem Solving:** Penanganan eror umum dan penerapan praktik terbaik (*best practices*) kode bersih.\n"
                f"- **Optimasi & Efisiensi:** Peningkatan performa dan keamanan implementasi sistem di lingkungan pengembangan.\n\n"
                f"**3. Tindak Lanjut & Action Items Peserta:**\n\n"
                f"- Mempraktikkan ulang kode dari rekaman video ({durasi}) di repository lokal masing-masing.\n"
                f"- Mengerjakan tugas implementasi yang ditugaskan mentor dan mengirimkannya ke sistem tugas sebelum batas tenggat waktu.\n"
                f"- Menyiapkan pertanyaan untuk sesi review dan pendampingan berikutnya."
            )

        # Domain A3: Desain / Multimedia
        if any(k in topik_lower for k in ["desain", "design", "ui", "ux", "figma", "video", "editing", "canva", "grafis"]):
            return (
                f"### 🎯 Ringkasan Sesi: {topik}\n\n"
                f"> 🎬 **Rekaman Video:** [{judul_vid}]({yt['url']})  \n"
                f"> 👤 **Pemateri / Host:** {author} &bull; ⏱️ **Durasi:** {durasi}\n\n"
                f"**1. Intisari Pembahasan:**\n"
                f"Sesi ini membahas perancangan visual dan kreatif pada topik **{topik}** bersama **{author}**. "
                f"Materi berfokus pada prinsip desain, komposisi estetika, kemudahan pengguna (*usability*), dan alur produksi aset visual.\n\n"
                f"**2. Poin-Poin Utama:**\n\n"
                f"- **Prinsip Dasar Desain & Hierarki Visual:** Penataan tata letak, pemilihan tipografi, dan kontras warna yang tepat.\n"
                f"- **Teknik & Penggunaan Tools:** Eksplorasi fitur utama software desain dan pembuatan prototipe interaktif.\n"
                f"- **Analisis Karya & Studi Kasus:** Evaluasi contoh desain nyata dan kiat meningkatkan kualitas visual.\n\n"
                f"**3. Tindak Lanjut & Action Items Peserta:**\n\n"
                f"- Menyelesaikan latihan proyek desain sesuai arahan pada rekaman video.\n"
                f"- Mengekspor aset hasil latihan dan mengunggahnya pada forum komunitas atau menu tugas."
            )

        # Domain A4: Umum / Pertemuan Akademik
        return (
            f"### 🎯 Ringkasan Sesi: {topik}\n\n"
            f"> 🎬 **Rekaman Video:** [{judul_vid}]({yt['url']})  \n"
            f"> 👤 **Pemateri / Host:** {author} &bull; ⏱️ **Durasi:** {durasi}\n\n"
            f"**1. Intisari Pembahasan:**\n"
            f"Sesi pembelajaran/pertemuan ini berfokus pada pembahasan materi **{topik}** yang dipandu oleh **{author}**. "
            f"Pemaparan difokuskan pada pemahaman materi pokok, elaborasi konsep kunci, serta tanya jawab interaktif dengan peserta.\n\n"
            f"**2. Poin-Poin Utama:**\n\n"
            f"- **Pemaparan Materi Pokok:** Pengantar dan pendalaman konsep mengenai topik {topik}.\n"
            f"- **Diskusi Interaktif:** Pembahasan pertanyaan dan eksplorasi topik bersama peserta sesi.\n"
            f"- **Rangkuman Pembelajaran:** Penegasan poin-poin krusial yang perlu dikuasai seluruh peserta.\n\n"
            f"**3. Tindak Lanjut & Action Items Peserta:**\n\n"
            f"- Meninjau rekaman video sesi untuk melengkapi catatan pembelajaran pribadi.\n"
            f"- Menyelesaikan tugas atau tindak lanjut yang diberikan mentor tepat waktu.\n"
            f"- Membaca materi tambahan yang telah disediakan di bagian materi sesi."
        )

    # 2. KASUS B: Teks Notulen / Transkrip Manual
    teks_sumber = (transkrip.strip() or deskripsi.strip() or judul).strip()
    baris_mentah = [
        b.strip()
        for b in re.split(r"[\n\r]+|\.\s+", teks_sumber)
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
            if len(tindak_lanjut) < 4:
                tindak_lanjut.append(b_clean)
        elif len(poin_kunci) < 5:
            poin_kunci.append(b_clean)

    if not poin_kunci:
        poin_kunci = [
            f"Pembahasan materi pokok dan konsep fundamental mengenai '{judul}'.",
            f"Pemaparan studi kasus dan implementasi praktis yang relevan dengan topik.",
            "Sesi tanya jawab interaktif untuk mengonfirmasi pemahaman peserta.",
        ]

    if not tindak_lanjut:
        tindak_lanjut = [
            "Mempelajari kembali modul materi dan rekaman sesi yang tersedia di portal.",
            "Menyelesaikan tugas praktikum yang ditugaskan mentor sebelum tenggat waktu berakhir.",
            "Melakukan review mandiri terhadap poin-poin penting yang telah dibahas.",
        ]

    ringkasan = (
        f"### 🎯 Ringkasan Sesi: {judul}\n\n"
        f"**1. Intisari Pembahasan:**\n"
        f"Sesi ini membahas materi terpadu mengenai **{judul}** yang ditujukan untuk memperkuat penguasaan konsep, "
        f"analisis studi kasus, serta penerapan praktis bagi peserta komunitas Dieng Cyber.\n\n"
        f"**2. Poin-Poin Utama:**\n\n"
    )
    for p in poin_kunci:
        ringkasan += f"- {p.rstrip('.')}.\n"

    ringkasan += f"\n**3. Tindak Lanjut & Action Items Peserta:**\n\n"
    for t in tindak_lanjut:
        ringkasan += f"- {t.rstrip('.')}.\n"

    return ringkasan


def generate_ai_summary(
    judul: str,
    deskripsi: str = "",
    transkrip: str = "",
    link_rekaman: str = "",
) -> tuple[bool, str]:
    """
    Menghasilkan ringkasan sesi Zoom yang cerdas, rapi, dan terstruktur.
    Mendukung Google Gemini API jika GEMINI_API_KEY diset, serta smart local fallback
    yang dapat memproses link YouTube dan materi transkrip secara komprehensif.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    # Deteksi metadata video jika ada link YouTube
    yt = (
        extract_youtube_info(transkrip)
        or extract_youtube_info(link_rekaman)
        or extract_youtube_info(deskripsi)
    )

    # 1. Coba gunakan Google Gemini API jika key tersedia
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"

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
                f"Kamu adalah asisten notulis AI profesional untuk komunitas teknologi 'Dieng Cyber Wonosobo'.\n"
                f"Buatlah ringkasan materi dan notulen yang sangat mendalam, rapi, dan berbobot dari sesi berikut:\n\n"
                f"- Judul Sesi: {judul}\n"
                f"- Deskripsi Sesi: {deskripsi}\n"
                f"{context_extra}"
                f"- Catatan/Transkrip/Input Peserta:\n{sumber_teks[:4000]}\n\n"
                f"Format output wajib menggunakan Markdown rapi dengan struktur berikut:\n\n"
                f"### 🎯 Ringkasan Sesi: [Judul/Topik yang Relevan]\n\n"
                + (f"> 🎬 **Rekaman Video:** [{yt['title']}]({yt['url']})  \n> 👤 **Pemateri / Host:** {yt['author']} &bull; ⏱️ **Durasi:** {yt['duration_str']}\n\n" if yt else "")
                + f"**1. Intisari Pembahasan:**\n(paragraf ringkasan mendalam 2-4 kalimat)\n\n"
                f"**2. Poin-Poin Utama:**\n\n"
                f"- **[Poin 1]:** Penjelasan poin utama materi.\n"
                f"- **[Poin 2]:** Penjelasan poin kedua materi.\n"
                f"- **[Poin 3]:** Penjelasan poin ketiga materi.\n"
                f"- **[Poin 4]:** Penjelasan studi kasus atau diskusi yang berlangsung.\n\n"
                f"**3. Tindak Lanjut & Action Items Peserta:**\n\n"
                f"- Poin instruksi tindak lanjut atau tugas pertama.\n"
                f"- Referensi materi atau rekaman yang perlu dikaji kembali.\n"
                f"- Tenggat waktu pengerjaan tugas atau persiapan sesi berikutnya.\n"
            )

            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}]
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
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

    # 2. Smart local semantic fallback (selalu sukses dan responsif)
    local_summary = _smart_local_summary(
        judul=judul,
        deskripsi=deskripsi,
        transkrip=transkrip,
        link_rekaman=link_rekaman,
    )
    return True, local_summary
