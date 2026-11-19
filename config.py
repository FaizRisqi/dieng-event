import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    _secret = os.getenv("SECRET_KEY", "")
    if not _secret and os.getenv("FLASK_ENV") == "production":
        raise RuntimeError(
            "SECRET_KEY harus diisi di environment production. "
            "Tambahkan SECRET_KEY ke file .env atau variabel environment."
        )
    SECRET_KEY = _secret or "dev-key-only-for-local"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # maksimal upload 20 MB
    WTF_CSRF_TIME_LIMIT = 3600  # token CSRF valid 1 jam