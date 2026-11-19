"""
Tes aturan pengumpulan tugas (TUGAS 4 - tugas).
- Pengumpulan setelah tenggat ditandai terlambat
- Ditolak jika terima_terlambat=False
- Tidak bisa kirim ulang setelah dinilai
- Nilai di luar 0-100 ditolak
"""
import pytest
from datetime import datetime, timedelta
from app.models import Tugas, Pengumpulan
from tests.conftest import make_user, make_admin, make_mentor, login


PAST = datetime(2020, 1, 1, 0, 0)
FUTURE = datetime(2099, 12, 31, 23, 59)


@pytest.fixture()
def mentor(db):
    return make_mentor(db)


@pytest.fixture()
def anggota(db):
    return make_user(db, nama="Candra", email="candra@test.com", role="anggota")


@pytest.fixture()
def tugas_aktif(db, mentor):
    t = Tugas(judul="Tugas Aktif", tenggat=FUTURE, terima_terlambat=True, created_by=mentor.id)
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture()
def tugas_lewat(db, mentor):
    t = Tugas(judul="Tugas Lewat", tenggat=PAST, terima_terlambat=True, created_by=mentor.id)
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture()
def tugas_tidak_terima_terlambat(db, mentor):
    t = Tugas(judul="Tugas Ketat", tenggat=PAST, terima_terlambat=False, created_by=mentor.id)
    db.session.add(t)
    db.session.commit()
    return t


def test_pengumpulan_setelah_tenggat_ditandai_terlambat(client, db, anggota, tugas_lewat):
    """Pengumpulan setelah tenggat harus menyimpan terlambat=True."""
    login(client, anggota.email)
    r = client.post(f"/tugas/{tugas_lewat.id}/kumpul", data={"teks": "Jawaban saya"}, follow_redirects=True)
    p = Pengumpulan.query.filter_by(tugas_id=tugas_lewat.id, user_id=anggota.id).first()
    assert p is not None
    assert p.terlambat is True


def test_pengumpulan_terlambat_ditolak_jika_tidak_diterima(client, db, anggota, tugas_tidak_terima_terlambat):
    """Jika terima_terlambat=False, pengumpulan setelah tenggat harus ditolak (tidak masuk DB)."""
    login(client, anggota.email)
    r = client.post(
        f"/tugas/{tugas_tidak_terima_terlambat.id}/kumpul",
        data={"teks": "Jawaban saya"},
        follow_redirects=True,
    )
    p = Pengumpulan.query.filter_by(tugas_id=tugas_tidak_terima_terlambat.id, user_id=anggota.id).first()
    assert p is None, "Tidak boleh ada pengumpulan jika terlambat dan terima_terlambat=False"


def test_tidak_bisa_kirim_ulang_setelah_dinilai(client, db, anggota, mentor, tugas_aktif):
    """Setelah pengumpulan sudah dinilai, pengiriman ulang harus ditolak."""
    # Buat pengumpulan yang sudah dinilai
    p = Pengumpulan(
        tugas_id=tugas_aktif.id,
        user_id=anggota.id,
        teks="Jawaban awal",
        dikumpulkan_at=datetime.now(),
        terlambat=False,
        nilai=85,
        dinilai_by=mentor.id,
        dinilai_at=datetime.now(),
    )
    db.session.add(p)
    db.session.commit()

    login(client, anggota.email)
    r = client.post(f"/tugas/{tugas_aktif.id}/kumpul", data={"teks": "Revisi saya"}, follow_redirects=True)

    # Pastikan teks tidak berubah (request ditolak)
    db.session.refresh(p)
    assert p.teks == "Jawaban awal", "Teks tidak boleh berubah setelah tugas dinilai"


def test_nilai_di_luar_0_100_ditolak(client, db, mentor, tugas_aktif, anggota):
    """Nilai di luar 0-100 harus ditolak."""
    # Buat pengumpulan terlebih dahulu
    p = Pengumpulan(
        tugas_id=tugas_aktif.id,
        user_id=anggota.id,
        teks="Jawaban",
        dikumpulkan_at=datetime.now(),
        terlambat=False,
    )
    db.session.add(p)
    db.session.commit()

    login(client, mentor.email)
    r = client.post(f"/tugas/pengumpulan/{p.id}/nilai", data={"nilai": "150"}, follow_redirects=True)
    db.session.refresh(p)
    assert p.nilai is None, "Nilai 150 (di luar 0-100) tidak boleh tersimpan"


def test_nilai_valid_tersimpan(client, db, mentor, tugas_aktif, anggota):
    """Nilai dalam rentang 0-100 harus tersimpan dengan benar."""
    p = Pengumpulan(
        tugas_id=tugas_aktif.id,
        user_id=anggota.id,
        teks="Jawaban",
        dikumpulkan_at=datetime.now(),
        terlambat=False,
    )
    db.session.add(p)
    db.session.commit()

    login(client, mentor.email)
    client.post(f"/tugas/pengumpulan/{p.id}/nilai", data={"nilai": "90"}, follow_redirects=True)
    db.session.refresh(p)
    assert p.nilai == 90
