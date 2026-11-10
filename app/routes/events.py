from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import current_user, login_required
from app import db
from app.models import Event, EventRegistration, Community, CommunityMember, Lokasi

bp = Blueprint("events", __name__, url_prefix="/events")

FMT = "%Y-%m-%dT%H:%M"


def komunitas_dikelola():
    if not current_user.is_authenticated:
        return []
    if current_user.role == "admin":
        return Community.query.order_by(Community.nama).all()
    return (
        Community.query.join(CommunityMember)
        .filter(CommunityMember.user_id == current_user.id, CommunityMember.role == "pengurus")
        .order_by(Community.nama)
        .all()
    )


def bisa_kelola(event):
    if not current_user.is_authenticated:
        return False
    if current_user.role == "admin":
        return True
    if event.community_id is None:
        return False
    m = db.session.get(CommunityMember, (event.community_id, current_user.id))
    return bool(m and m.role == "pengurus")


def cari_bentrok(lokasi_id, lokasi_teks, mulai, selesai, abaikan_id=None):
    if lokasi_id:
        q = Event.query.filter(
            Event.lokasi_id == lokasi_id,
            Event.mulai < selesai,
            Event.selesai > mulai,
        )
    elif lokasi_teks:
        q = Event.query.filter(
            Event.lokasi == lokasi_teks,
            Event.mulai < selesai,
            Event.selesai > mulai,
        )
    else:
        return []
    if abaikan_id:
        q = q.filter(Event.id != abaikan_id)
    return q.all()


def hitung_aktif(event_id):
    return EventRegistration.query.filter(
        EventRegistration.event_id == event_id,
        EventRegistration.status != "batal",
    ).count()


def _handle_form(event=None):
    pilihan = komunitas_dikelola()
    daftar_lokasi = Lokasi.query.order_by(Lokasi.nama).all()

    if request.method == "POST":
        judul = request.form["judul"].strip()
        lid = request.form.get("lokasi_id") or None
        lid = int(lid) if lid else None
        lokasi_manual = request.form.get("lokasi_manual", "").strip()

        lokasi_obj = db.session.get(Lokasi, lid) if lid else None
        lokasi_nama = lokasi_obj.nama if lokasi_obj else lokasi_manual

        deskripsi = request.form.get("deskripsi", "").strip()
        kuota = request.form.get("kuota")
        cid = request.form.get("community_id") or None
        cid = int(cid) if cid else None
        mulai = datetime.strptime(request.form["mulai"], FMT)
        selesai = datetime.strptime(request.form["selesai"], FMT)

        if not lokasi_nama:
            flash("Pilih lokasi tersimpan atau isi lokasi manual.", "error")
        elif selesai <= mulai:
            flash("Waktu selesai harus setelah waktu mulai.", "error")
        elif cid is None and current_user.role != "admin":
            flash("Pilih komunitas untuk event ini.", "error")
        elif cid is not None and cid not in {c.id for c in pilihan}:
            abort(403)
        else:
            bentrok = cari_bentrok(lid, lokasi_nama, mulai, selesai, event.id if event else None)
            if bentrok:
                b = bentrok[0]
                flash(
                    f"Jadwal bentrok dengan '{b.judul}' "
                    f"({b.mulai:%d/%m/%Y %H:%M} - {b.selesai:%H:%M}) di {lokasi_nama}.",
                    "error",
                )
            else:
                if event is None:
                    event = Event(created_by=current_user.id)
                    db.session.add(event)
                event.judul = judul
                event.lokasi_id = lid
                event.lokasi = lokasi_nama
                event.deskripsi = deskripsi
                event.kuota = int(kuota) if kuota else (lokasi_obj.kapasitas if lokasi_obj and not kuota else None)
                event.community_id = cid
                event.mulai = mulai
                event.selesai = selesai
                db.session.commit()
                flash("Event berhasil disimpan.", "success")
                return redirect(url_for("events.detail", event_id=event.id))

    return render_template("event_form.html", event=event, komunitas=pilihan, daftar_lokasi=daftar_lokasi)


@bp.route("/")
def calendar():
    return render_template("calendar.html", bisa_buat=bool(komunitas_dikelola()))


@bp.route("/daftar")
def daftar():
    q = request.args.get("q", "").strip()
    cid = request.args.get("community_id", type=int)
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)

    query = Event.query
    if q:
        query = query.filter(
            db.or_(Event.judul.ilike(f"%{q}%"), Event.lokasi.ilike(f"%{q}%"))
        )
    if cid:
        query = query.filter_by(community_id=cid)

    sekarang = datetime.now()
    if status == "mendatang":
        query = query.filter(Event.selesai >= sekarang).order_by(Event.mulai.asc())
    elif status == "selesai":
        query = query.filter(Event.selesai < sekarang).order_by(Event.mulai.desc())
    else:
        query = query.order_by(Event.mulai.desc())

    pagination = query.paginate(page=page, per_page=10, error_out=False)
    events = pagination.items
    komunitas = Community.query.order_by(Community.nama).all()
    extra_args = {}
    if q:
        extra_args["q"] = q
    if cid:
        extra_args["community_id"] = cid
    if status:
        extra_args["status"] = status

    return render_template(
        "events_list.html",
        events=events,
        pagination=pagination,
        extra_args=extra_args,
        komunitas=komunitas,
        q=q,
        cid=cid,
        status=status,
        bisa_buat=bool(komunitas_dikelola()),
        sekarang=sekarang,
    )


@bp.route("/api")
def api():
    data = [
        {
            "id": e.id,
            "title": f"{e.judul} ({e.nama_lokasi})" if e.nama_lokasi != "-" else e.judul,
            "start": e.mulai.isoformat(),
            "end": e.selesai.isoformat(),
            "url": url_for("events.detail", event_id=e.id),
        }
        for e in Event.query.all()
    ]
    return jsonify(data)


@bp.route("/<int:event_id>")
def detail(event_id):
    event = db.get_or_404(Event, event_id)
    aktif = [r for r in event.registrations if r.status != "batal"]
    reg = None
    if current_user.is_authenticated:
        reg = db.session.get(EventRegistration, (event.id, current_user.id))
    penuh = event.kuota is not None and len(aktif) >= event.kuota
    selesai = event.selesai < datetime.now()
    return render_template(
        "event_detail.html",
        event=event, aktif=aktif, reg=reg, penuh=penuh, selesai=selesai,
        bisa=bisa_kelola(event),
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if not komunitas_dikelola():
        abort(403)
    return _handle_form()


@bp.route("/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit(event_id):
    event = db.get_or_404(Event, event_id)
    if not bisa_kelola(event):
        abort(403)
    return _handle_form(event)


@bp.route("/<int:event_id>/delete", methods=["POST"])
@login_required
def delete(event_id):
    event = db.get_or_404(Event, event_id)
    if not bisa_kelola(event):
        abort(403)
    db.session.delete(event)
    db.session.commit()
    flash("Event dihapus.", "success")
    return redirect(url_for("events.calendar"))


@bp.route("/<int:event_id>/daftar", methods=["POST"])
@login_required
def daftar(event_id):
    event = db.get_or_404(Event, event_id)
    reg = db.session.get(EventRegistration, (event.id, current_user.id))

    if event.selesai < datetime.now():
        flash("Event sudah selesai.", "error")
    elif reg and reg.status != "batal":
        flash("Kamu sudah terdaftar.", "error")
    elif event.kuota is not None and hitung_aktif(event.id) >= event.kuota:
        flash("Kuota event sudah penuh.", "error")
    else:
        if reg:
            reg.status = "terdaftar"
        else:
            db.session.add(EventRegistration(event_id=event.id, user_id=current_user.id))
        db.session.commit()
        flash("Berhasil mendaftar.", "success")

    return redirect(url_for("events.detail", event_id=event.id))


@bp.route("/<int:event_id>/batal", methods=["POST"])
@login_required
def batal(event_id):
    reg = db.session.get(EventRegistration, (event_id, current_user.id))

    if not reg or reg.status == "batal":
        flash("Kamu belum terdaftar di event ini.", "error")
    elif reg.status == "hadir":
        flash("Kehadiran sudah tercatat, pendaftaran tidak bisa dibatalkan.", "error")
    else:
        reg.status = "batal"
        db.session.commit()
        flash("Pendaftaran dibatalkan.", "success")

    return redirect(url_for("events.detail", event_id=event_id))


@bp.route("/<int:event_id>/absen/<int:user_id>", methods=["POST"])
@login_required
def absen(event_id, user_id):
    event = db.get_or_404(Event, event_id)
    if not bisa_kelola(event):
        abort(403)
    reg = db.get_or_404(EventRegistration, (event_id, user_id))
    if reg.status == "batal":
        flash("Peserta ini sudah membatalkan pendaftaran.", "error")
    else:
        reg.status = "terdaftar" if reg.status == "hadir" else "hadir"
        db.session.commit()
    return redirect(url_for("events.detail", event_id=event_id))