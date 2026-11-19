"""
Tes deteksi bentrok lokasi event (TUGAS 4 - bentrok).
"""
from datetime import datetime
import pytest
from app.models import Event, Lokasi
from tests.conftest import make_admin


def _dt(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


@pytest.fixture()
def admin(db):
    return make_admin(db)


@pytest.fixture()
def lokasi(db):
    l = Lokasi(nama="Aula Utama", alamat="Jl. Dieng No.1")
    db.session.add(l)
    db.session.commit()
    return l


@pytest.fixture()
def event_a(db, lokasi, admin):
    e = Event(
        judul="Event A",
        lokasi_id=lokasi.id,
        mulai=_dt("2026-12-01 09:00"),
        selesai=_dt("2026-12-01 11:00"),
        created_by=admin.id,
    )
    db.session.add(e)
    db.session.commit()
    return e


def test_overlap_ditolak(app, db, event_a, lokasi):
    """Jadwal yang tumpang tindih harus terdeteksi sebagai bentrok."""
    from app.routes.events import cari_bentrok
    with app.app_context():
        # reload
        from app.models import Event as E
        result = cari_bentrok(lokasi.id, None, _dt("2026-12-01 10:00"), _dt("2026-12-01 12:00"))
        assert len(result) == 1
        assert result[0].judul == "Event A"


def test_berbatasan_diterima(app, db, event_a, lokasi):
    """Jadwal yang berbatasan persis (selesai == mulai berikutnya) TIDAK bentrok."""
    from app.routes.events import cari_bentrok
    with app.app_context():
        # mulai == selesai event_a → seharusnya kosong (tidak bentrok)
        result = cari_bentrok(lokasi.id, None, _dt("2026-12-01 11:00"), _dt("2026-12-01 13:00"))
        assert result == []


def test_edit_tidak_bentrok_dengan_dirinya(app, db, event_a, lokasi):
    """Edit event dengan waktu yang sama tidak dianggap bentrok dengan dirinya sendiri."""
    from app.routes.events import cari_bentrok
    with app.app_context():
        result = cari_bentrok(
            lokasi.id, None,
            _dt("2026-12-01 09:00"), _dt("2026-12-01 11:00"),
            abaikan_id=event_a.id,
        )
        assert result == []


def test_overlap_lokasi_teks(app, db, admin):
    """Bentrok menggunakan lokasi teks (bukan lokasi_id) juga terdeteksi."""
    from app.models import Event as E
    from app.routes.events import cari_bentrok
    with app.app_context():
        e = E(
            judul="Teks Event",
            lokasi="Ruang Rapat",
            mulai=_dt("2026-12-10 10:00"),
            selesai=_dt("2026-12-10 12:00"),
            created_by=admin.id,
        )
        db.session.add(e)
        db.session.commit()

        result = cari_bentrok(None, "Ruang Rapat", _dt("2026-12-10 11:00"), _dt("2026-12-10 13:00"))
        assert len(result) == 1
