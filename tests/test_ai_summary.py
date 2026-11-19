"""
Tes ai_summary mode lokal: tanpa transkrip tidak menghasilkan poin pembahasan karangan
(TUGAS 4 - ai_summary kejujuran).
"""
import pytest


def test_tanpa_transkrip_tanpa_link_tidak_ada_poin(app):
    """Input hanya judul (tanpa transkrip/catatan) → tidak ada poin pembahasan buatan."""
    from app.services.ai_summary import generate_ai_summary
    with app.app_context():
        ok, ringkasan, mode, reason = generate_ai_summary(
            judul="Workshop Python Lanjut",
            deskripsi="",
            transkrip="",
            link_rekaman="",
        )
    assert mode == "lokal"
    # Tidak boleh ada poin pembahasan
    assert "1. Intisari" not in ringkasan
    assert "Pembahasan materi" not in ringkasan
    # Harus ada pesan bahwa belum bisa diringkas
    assert "Belum ada" in ringkasan or "belum bisa diringkas" in ringkasan or "tidak ada teks" in ringkasan.lower()
    # Harus ada closing line
    assert "Periksa sebelum dibagikan" in ringkasan


def test_dengan_link_youtube_saja_tidak_ada_poin(app, monkeypatch):
    """Input hanya link YouTube (tanpa transkrip) → kartu metadata saja, bukan poin pembahasan."""
    from app.services.ai_summary import generate_ai_summary

    # Patch extract_youtube_info agar tidak hit network
    def fake_yt(text):
        if not text:
            return None
        if "youtu" in text:
            return {"video_id": "abc123", "url": "https://youtu.be/abc123", "title": "Video Test", "author": "Kanal X", "thumbnail": "", "duration_str": "10 menit", "topic": "Video Test"}
        return None

    monkeypatch.setattr("app.services.ai_summary.extract_youtube_info", fake_yt)

    with app.app_context():
        ok, ringkasan, mode, reason = generate_ai_summary(
            judul="Zoom Pagi",
            deskripsi="",
            transkrip="https://youtu.be/abc123",
            link_rekaman="",
        )

    assert mode == "lokal"
    # Tidak boleh ada poin pembahasan karangan
    assert "Intisari Pembahasan" not in ringkasan
    assert "bidang teknologi" not in ringkasan
    assert "studi kasus" not in ringkasan
    # Harus menyebut bahwa isi tidak bisa diringkas tanpa transkrip
    assert "belum bisa diringkas" in ringkasan or "tidak ada teks" in ringkasan.lower()


def test_dengan_transkrip_nyata_ada_poin(app):
    """Input dengan transkrip nyata → poin pembahasan berasal dari teks tersebut."""
    from app.services.ai_summary import generate_ai_summary
    transkrip = (
        "Hari ini kita membahas konsep dasar OOP. "
        "Kita belajar tentang class dan object di Python. "
        "Tugas: kerjakan latihan membuat class hewan."
    )
    with app.app_context():
        ok, ringkasan, mode, reason = generate_ai_summary(
            judul="Zoom Pagi",
            deskripsi="",
            transkrip=transkrip,
            link_rekaman="",
        )

    assert mode == "lokal"
    # Harus ada poin dari teks
    assert "OOP" in ringkasan or "class" in ringkasan.lower() or "Python" in ringkasan
    # Harus ada closing line
    assert "Periksa sebelum dibagikan" in ringkasan


def test_closing_line_selalu_ada(app):
    """Closing line harus selalu ada di setiap output."""
    from app.services.ai_summary import generate_ai_summary
    for transkrip in ["", "ini catatan singkat yang nyata untuk diuji", "https://youtu.be/abc"]:
        with app.app_context():
            ok, ringkasan, mode, reason = generate_ai_summary(
                judul="Test",
                deskripsi="",
                transkrip=transkrip,
                link_rekaman="",
            )
        assert "Periksa sebelum dibagikan" in ringkasan, f"Closing line hilang untuk input: {transkrip!r}"
