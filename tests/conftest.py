"""
Konfigurasi pytest: app + database SQLite in-memory, CSRF dimatikan.
Setiap test-function mendapat fresh database (function-scoped).
"""
import pytest
from sqlalchemy.pool import StaticPool
from app import create_app, db as _db

TEST_CONFIG = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite://",
    "SQLALCHEMY_ENGINE_OPTIONS": {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}},
    "WTF_CSRF_ENABLED": False,
    "SECRET_KEY": "test-secret-key",
    "SERVER_NAME": None,
    "UPLOAD_FOLDER": "/tmp/dieng_test_uploads",
}


@pytest.fixture()
def app():
    application = create_app(TEST_CONFIG)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


# ------------------------------------------------------------------
# Helper factories (reusable across test modules)
# ------------------------------------------------------------------

def make_user(db, nama="Anggota", email="anggota@test.com", role="anggota", no_wa="08123456789"):
    from app.models import User
    u = User(nama=nama, email=email, role=role, no_wa=no_wa)
    u.set_password("password123")
    db.session.add(u)
    db.session.commit()
    return u


def make_admin(db, nama="Admin", email="admin@test.com"):
    return make_user(db, nama=nama, email=email, role="admin", no_wa="08199999999")


def make_mentor(db, nama="Mentor", email="mentor@test.com"):
    return make_user(db, nama=nama, email=email, role="mentor", no_wa="08188888888")


def login(client, email, password="password123"):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def logout(client):
    return client.get("/logout", follow_redirects=True)
