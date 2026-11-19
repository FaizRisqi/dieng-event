"""
Tes rekap: persentase hadir dan rata-rata nilai (TUGAS 4 - rekap).
"""
import csv
import io
import pytest
from datetime import datetime, date, time
from app.models import Community, CommunityMember, Sesi, SesiAbsensi, Tugas, Pengumpulan
from tests.conftest import make_user, make_admin, make_mentor, login


@pytest.fixture()
def admin(db):
    return make_admin(db)


@pytest.fixture()
def mentor(db):
    return make_mentor(db)


@pytest.fixture()
def setup_rekap(db, admin, mentor):
    """Siapkan: 1 komunitas, 2 anggota, 2 sesi, 2 tugas dengan data absensi dan nilai."""
    # Komunitas
    c = Community(nama="Komunitas Rekap", created_by=admin.id)
    db.session.add(c)
    db.session.flush()

    # Anggota
    u1 = make_user(db, nama="Adi", email="adi@test.com", role="anggota")
    u2 = make_user(db, nama="Bela", email="bela@test.com", role="anggota")
    for u in [u1, u2]:
        db.session.add(CommunityMember(community_id=c.id, user_id=u.id, role="anggota"))

    # Sesi
    s1 = Sesi(judul="Sesi 1", tanggal=date(2026, 11, 1), jam_mulai=time(9, 0), jam_selesai=time(10, 0), community_id=c.id, mentor_id=mentor.id)
    s2 = Sesi(judul="Sesi 2", tanggal=date(2026, 11, 8), jam_mulai=time(9, 0), jam_selesai=time(10, 0), community_id=c.id, mentor_id=mentor.id)
    db.session.add_all([s1, s2])
    db.session.flush()

    # Absensi: u1 hadir 2x, u2 hadir 1x
    db.session.add_all([
        SesiAbsensi(sesi_id=s1.id, user_id=u1.id, hadir=True),
        SesiAbsensi(sesi_id=s2.id, user_id=u1.id, hadir=True),
        SesiAbsensi(sesi_id=s1.id, user_id=u2.id, hadir=True),
        SesiAbsensi(sesi_id=s2.id, user_id=u2.id, hadir=False),
    ])

    # Tugas
    t1 = Tugas(judul="Tugas 1", tenggat=datetime(2026, 11, 15, 23, 59), community_id=c.id, created_by=mentor.id)
    t2 = Tugas(judul="Tugas 2", tenggat=datetime(2026, 11, 22, 23, 59), community_id=c.id, created_by=mentor.id)
    db.session.add_all([t1, t2])
    db.session.flush()

    # Nilai: u1 → 80 & 90, u2 → 70 & tidak kumpul t2
    db.session.add_all([
        Pengumpulan(tugas_id=t1.id, user_id=u1.id, teks="a", dikumpulkan_at=datetime(2026, 11, 14), terlambat=False, nilai=80),
        Pengumpulan(tugas_id=t2.id, user_id=u1.id, teks="b", dikumpulkan_at=datetime(2026, 11, 20), terlambat=False, nilai=90),
        Pengumpulan(tugas_id=t1.id, user_id=u2.id, teks="c", dikumpulkan_at=datetime(2026, 11, 14), terlambat=False, nilai=70),
    ])
    db.session.commit()

    return c, u1, u2, s1, s2, t1, t2


def test_persentase_hadir(db, setup_rekap):
    """Persentase hadir: u1 = 100%, u2 = 50%."""
    c, u1, u2, s1, s2, t1, t2 = setup_rekap
    sesi_list = [s1, s2]

    absensi_raw = SesiAbsensi.query.filter(SesiAbsensi.sesi_id.in_([s.id for s in sesi_list])).all()
    absensi = {}
    for a in absensi_raw:
        absensi.setdefault(a.user_id, {})[a.sesi_id] = a

    for user, expected_pct in [(u1, 100.0), (u2, 50.0)]:
        u_ab = absensi.get(user.id, {})
        hadir = sum(1 for s in sesi_list if u_ab.get(s.id) and u_ab[s.id].hadir)
        pct = round(hadir / len(sesi_list) * 100, 1)
        assert pct == expected_pct, f"{user.nama}: expected {expected_pct}%, got {pct}%"


def test_rata_rata_nilai(db, setup_rekap):
    """Rata-rata nilai: u1 = 85.0, u2 = 70.0."""
    c, u1, u2, s1, s2, t1, t2 = setup_rekap
    tugas_list = [t1, t2]

    peng_raw = Pengumpulan.query.filter(Pengumpulan.tugas_id.in_([t.id for t in tugas_list])).all()
    pengumpulan = {}
    for p in peng_raw:
        pengumpulan.setdefault(p.user_id, {})[p.tugas_id] = p

    for user, expected_avg in [(u1, 85.0), (u2, 70.0)]:
        u_pg = pengumpulan.get(user.id, {})
        nilai_list = [p.nilai for p in u_pg.values() if p.nilai is not None]
        avg = round(sum(nilai_list) / len(nilai_list), 1) if nilai_list else None
        assert avg == expected_avg, f"{user.nama}: expected {expected_avg}, got {avg}"


def test_export_csv_berhasil(client, db, setup_rekap):
    """Endpoint export CSV harus mengembalikan file CSV yang valid."""
    c, u1, u2, s1, s2, t1, t2 = setup_rekap
    # Ambil admin yang sudah dibuat oleh setup_rekap (email admin@test.com)
    from app.models import User
    admin_user = User.query.filter_by(role="admin").first()
    assert admin_user is not None
    login(client, admin_user.email)
    r = client.get(f"/rekap/komunitas/{c.id}/export")
    assert r.status_code == 200
    assert "text/csv" in r.content_type

    # Parse CSV
    content = r.data.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) >= 3  # header + 2 anggota

    # Cek kolom header ada "Persentase Hadir" dan "Rata-rata Nilai"
    header = rows[0]
    assert any("Persentase" in h for h in header)
    assert any("Rata-rata" in h for h in header)
