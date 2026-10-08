from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    no_wa = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="anggota")  # admin / anggota
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Community(db.Model):
    __tablename__ = "communities"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    members = db.relationship("CommunityMember", backref="community", cascade="all, delete-orphan")
    events = db.relationship("Event", backref="community")


class CommunityMember(db.Model):
    __tablename__ = "community_members"

    community_id = db.Column(db.Integer, db.ForeignKey("communities.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    role = db.Column(db.String(20), default="anggota")  # pengurus / anggota
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="memberships")


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey("communities.id"), nullable=True)
    judul = db.Column(db.String(150), nullable=False)
    deskripsi = db.Column(db.Text)
    lokasi = db.Column(db.String(100))
    mulai = db.Column(db.DateTime, nullable=False)
    selesai = db.Column(db.DateTime, nullable=False)
    kuota = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    registrations = db.relationship("EventRegistration", backref="event", cascade="all, delete-orphan")
    notes = db.relationship("CalendarNote", backref="event")


class EventRegistration(db.Model):
    __tablename__ = "event_registrations"

    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    status = db.Column(db.String(20), default="terdaftar")  # terdaftar / hadir / batal

    user = db.relationship("User", backref="registrations")


class CalendarNote(db.Model):
    __tablename__ = "calendar_notes"

    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=True)
    community_id = db.Column(db.Integer, db.ForeignKey("communities.id"), nullable=True)
    isi = db.Column(db.Text, nullable=False)
    foto = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)