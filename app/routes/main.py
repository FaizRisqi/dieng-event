from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.decorators import role_required
from app import db

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    from datetime import datetime, timedelta
    from app.models import Event, EventRegistration, Tugas, Pengumpulan, Sesi, CommunityMember, Pengumuman

    sekarang = datetime.now()
    minggu_depan = sekarang + timedelta(days=7)

    # Event mendatang yang diikuti user
    if current_user.role == "admin":
        upcoming_events = Event.query.filter(Event.selesai >= sekarang).order_by(Event.mulai).limit(5).all()
    else:
        reg_ids = [r.event_id for r in current_user.registrations if r.status != "batal"]
        upcoming_events = Event.query.filter(
            Event.id.in_(reg_ids), Event.selesai >= sekarang
        ).order_by(Event.mulai).limit(5).all()

    # Tugas mendatang (belum dikumpulkan, tenggat < 7 hari)
    community_ids = [m.community_id for m in current_user.memberships]
    sudah_kumpul = {p.tugas_id for p in Pengumpulan.query.filter_by(user_id=current_user.id).all()}
    tugas_mendatang = Tugas.query.filter(
        Tugas.tenggat >= sekarang,
        Tugas.tenggat <= minggu_depan,
        Tugas.id.notin_(sudah_kumpul),
        db.or_(Tugas.community_id.in_(community_ids), Tugas.community_id.is_(None))
    ).order_by(Tugas.tenggat).all() if not (current_user.role in ("admin", "mentor")) else []

    # Sesi mendatang
    sesi_mendatang = Sesi.query.filter(Sesi.tanggal >= sekarang.date()).order_by(Sesi.tanggal, Sesi.jam_mulai).limit(3).all()

    # Pengumuman terbaru
    if current_user.role in ("admin", "mentor"):
        pengumuman_terbaru = Pengumuman.query.order_by(Pengumuman.pin.desc(), Pengumuman.created_at.desc()).limit(3).all()
    else:
        pengumuman_terbaru = Pengumuman.query.filter(
            db.or_(Pengumuman.community_id.is_(None), Pengumuman.community_id.in_(community_ids))
        ).order_by(Pengumuman.pin.desc(), Pengumuman.created_at.desc()).limit(3).all()

    return render_template("dashboard.html",
                           upcoming_events=upcoming_events,
                           tugas_mendatang=tugas_mendatang,
                           sesi_mendatang=sesi_mendatang,
                           pengumuman_terbaru=pengumuman_terbaru,
                           sekarang=sekarang)


@bp.route("/admin")
@role_required("admin")
def admin_page():
    return "Halaman khusus admin"
