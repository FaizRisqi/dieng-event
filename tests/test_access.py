"""
Tes kontrol akses (TUGAS 4 - access).
- Anggota biasa mendapat 403 di /sesi/new dan /tugas/new
- Sesi/tugas komunitas tidak bisa diakses non-anggota
- Admin tidak bisa mengubah role sesama admin
"""
import pytest
from app.models import Community, CommunityMember, Sesi, Tugas
from tests.conftest import make_user, make_admin, make_mentor, login
from datetime import datetime, date, time


@pytest.fixture()
def admin(db):
    return make_admin(db)


@pytest.fixture()
def mentor(db):
    return make_mentor(db)


@pytest.fixture()
def anggota(db):
    return make_user(db, nama="Budi", email="budi@test.com", role="anggota")


@pytest.fixture()
def komunitas(db, admin):
    c = Community(nama="Komunitas A", created_by=admin.id)
    db.session.add(c)
    db.session.commit()
    return c


def test_anggota_tidak_bisa_buka_sesi_new(client, db, anggota):
    login(client, anggota.email)
    r = client.get("/sesi/new", follow_redirects=False)
    assert r.status_code in (302, 403)


def test_anggota_tidak_bisa_buka_tugas_new(client, db, anggota):
    login(client, anggota.email)
    r = client.get("/tugas/new", follow_redirects=False)
    assert r.status_code in (302, 403)


def test_sesi_komunitas_tidak_bisa_diakses_non_anggota(client, db, mentor, komunitas):
    """Anggota yang bukan member komunitas tidak boleh lihat sesi komunitas itu."""
    # Buat sesi milik komunitas
    s = Sesi(
        judul="Sesi Rahasia",
        tanggal=date(2026, 12, 1),
        jam_mulai=time(9, 0),
        jam_selesai=time(10, 0),
        community_id=komunitas.id,
        mentor_id=mentor.id,
    )
    db.session.add(s)
    db.session.commit()

    # Login sebagai anggota yang BUKAN member komunitas ini
    outsider = make_user(db, nama="Outsider", email="outsider@test.com", role="anggota")
    login(client, outsider.email)
    r = client.get(f"/sesi/{s.id}", follow_redirects=False)
    assert r.status_code in (302, 403)


def test_tugas_komunitas_tidak_bisa_diakses_non_anggota(client, db, mentor, komunitas):
    """Anggota yang bukan member komunitas tidak boleh lihat tugas komunitas itu."""
    t = Tugas(
        judul="Tugas Rahasia",
        tenggat=datetime(2026, 12, 31, 23, 59),
        community_id=komunitas.id,
        created_by=mentor.id,
    )
    db.session.add(t)
    db.session.commit()

    outsider = make_user(db, nama="Outsider2", email="outsider2@test.com", role="anggota")
    login(client, outsider.email)
    r = client.get(f"/tugas/{t.id}", follow_redirects=False)
    assert r.status_code in (302, 403)


def test_admin_tidak_bisa_ubah_role_sesama_admin(client, db, admin):
    """Admin tidak bisa mengubah role admin lain."""
    admin2 = make_user(db, nama="Admin2", email="admin2@test.com", role="admin")
    login(client, admin.email)
    r = client.post(
        f"/admin/users/{admin2.id}/role",
        data={"role": "anggota"},
        follow_redirects=False,
    )
    # Harus 403 atau redirect balik (dengan flash error)
    assert r.status_code in (302, 403)
    # Jika redirect, cek role tidak berubah
    if r.status_code == 302:
        from app.models import User
        u = db.session.get(User, admin2.id)
        assert u.role == "admin", "Role admin lain tidak boleh diubah oleh sesama admin"
