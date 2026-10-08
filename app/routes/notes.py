import os
import uuid
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, abort, current_app,
)
from flask_login import current_user, login_required
from app import db
from app.models import CalendarNote, Event, CommunityMember, User
from app.routes.events import komunitas_dikelola

bp = Blueprint("notes", __name__, url_prefix="/catatan")

ALLOWED = {"png", "jpg", "jpeg", "webp"}


def event_dikelola():
    if current_user.role == "admin":
        return Event.query.order_by(Event.mulai.desc()).all()
    ids = [c.id for c in komunitas_dikelola()]
    if not ids:
        return []
    return (
        Event.query.filter(Event.community_id.in_(ids))
        .order_by(Event.mulai.desc())
        .all()
    )


def bisa_ubah(note):
    if not current_user.is_authenticated:
        return False
    if current_user.role == "admin" or note.created_by == current_user.id:
        return True
    if note.community_id:
        m = db.session.get(CommunityMember, (note.community_id, current_user.id))
        return bool(m and m.role == "pengurus")
    return False


def simpan_foto(file):
    ext = file.filename.rsplit(".", 1)[-1].lower()
    nama = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(current_app.static_folder, "uploads", "notes")
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, nama))
    return nama


def hapus_foto(nama):
    if not nama:
        return
    path = os.path.join(current_app.static_folder, "uploads", "notes", nama)
    if os.path.exists(path):
        os.remove(path)


def _handle_form(note=None):
    kom = komunitas_dikelola()
    evs = event_dikelola()

    if request.method == "POST":
        isi = request.form["isi"].strip()
        try:
            tanggal = datetime.strptime(request.form["tanggal"], "%Y-%m-%d").date()
        except ValueError:
            tanggal = None

        eid = request.form.get("event_id") or None
        cid = request.form.get("community_id") or None
        eid = int(eid) if eid else None
        cid = int(cid) if cid else None

        foto = request.files.get("foto")
        ada_foto = bool(foto and foto.filename)
        foto_ok = (not ada_foto) or foto.filename.rsplit(".", 1)[-1].lower() in ALLOWED

        if not isi or not tanggal:
            flash("Tanggal dan isi catatan wajib diisi.", "error")
        elif not foto_ok:
            flash("Format foto harus PNG, JPG, atau WEBP.", "error")
        elif eid is not None and eid not in {e.id for e in evs}:
            abort(403)
        elif eid is None and cid is not None and cid not in {c.id for c in kom}:
            abort(403)
        elif eid is None and cid is None and current_user.role != "admin":
            flash("Pilih komunitas atau event.", "error")
        else:
            if eid is not None:
                cid = db.session.get(Event, eid).community_id

            if note is None:
                note = CalendarNote(created_by=current_user.id)
                db.session.add(note)

            note.tanggal = tanggal
            note.isi = isi
            note.event_id = eid
            note.community_id = cid

            if ada_foto:
                hapus_foto(note.foto)
                note.foto = simpan_foto(foto)
            elif request.form.get("hapus_foto"):
                hapus_foto(note.foto)
                note.foto = None

            db.session.commit()
            flash("Catatan disimpan.", "success")
            return redirect(url_for("notes.detail", note_id=note.id))

    return render_template("note_form.html", note=note, komunitas=kom, events=evs)


@bp.route("/")
def index():
    daftar = CalendarNote.query.order_by(CalendarNote.tanggal.desc(), CalendarNote.id.desc()).all()
    bisa_tulis = current_user.is_authenticated and (
        current_user.role == "admin" or bool(komunitas_dikelola())
    )
    return render_template("notes.html", daftar=daftar, bisa_tulis=bisa_tulis)


@bp.route("/api")
def api():
    data = [
        {
            "id": f"note-{n.id}",
            "title": "Catatan: " + (n.isi[:25] + "..." if len(n.isi) > 25 else n.isi),
            "start": n.tanggal.isoformat(),
            "allDay": True,
            "color": "#d97706",
            "url": url_for("notes.detail", note_id=n.id),
        }
        for n in CalendarNote.query.all()
    ]
    return jsonify(data)


@bp.route("/<int:note_id>")
def detail(note_id):
    note = db.get_or_404(CalendarNote, note_id)
    penulis = db.session.get(User, note.created_by) if note.created_by else None
    komunitas = None
    if note.community_id:
        from app.models import Community
        komunitas = db.session.get(Community, note.community_id)
    return render_template(
        "note_detail.html",
        note=note, penulis=penulis, komunitas=komunitas, bisa=bisa_ubah(note),
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if current_user.role != "admin" and not komunitas_dikelola():
        abort(403)
    return _handle_form()


@bp.route("/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def edit(note_id):
    note = db.get_or_404(CalendarNote, note_id)
    if not bisa_ubah(note):
        abort(403)
    return _handle_form(note)


@bp.route("/<int:note_id>/delete", methods=["POST"])
@login_required
def delete(note_id):
    note = db.get_or_404(CalendarNote, note_id)
    if not bisa_ubah(note):
        abort(403)
    hapus_foto(note.foto)
    db.session.delete(note)
    db.session.commit()
    flash("Catatan dihapus.", "success")
    return redirect(url_for("notes.index"))