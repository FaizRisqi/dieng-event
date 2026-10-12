import os
import uuid
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, abort, current_app, send_from_directory,
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Sesi, SesiFile, Community, CommunityMember
from app.decorators import role_required

bp = Blueprint("sesi", __name__, url_prefix="/sesi")

ALLOWED = {"pdf", "ppt", "pptx", "doc", "docx", "xls", "xlsx", "zip"}
MAKS_ULANG_HARI = 60


def staff():
    return current_user.is_authenticated and current_user.role in ("admin", "mentor")


def bisa_akses(s):
    if staff():
        return True
    if not current_user.is_authenticated:
        return False
    if s.community_id is None:
        return True
    return db.session.get(CommunityMember, (s.community_id, current_user.id)) is not None


def link_ok(link):
    return link == "" or link.startswith(("http://", "https://"))


def folder():
    path = os.path.join(current_app.instance_path, "uploads", "sesi")
    os.makedirs(path, exist_ok=True)
    return path


def ext_file(nama):
    return nama.rsplit(".", 1)[-1].lower() if "." in nama else ""


def hapus_dari_disk(nama_simpan):
    path = os.path.join(folder(), nama_simpan)
    if os.path.exists(path):
        os.remove(path)


def _form(sesi=None):
    komunitas = Community.query.order_by(Community.nama).all()

    if request.method == "POST":
        judul = request.form["judul"].strip()
        deskripsi = request.form.get("deskripsi", "").strip()
        link_zoom = request.form.get("link_zoom", "").strip()
        link_rekaman = request.form.get("link_rekaman", "").strip()
        ringkasan = request.form.get("ringkasan", "").strip()
        cid = request.form.get("community_id") or None
        cid = int(cid) if cid else None

        try:
            tanggal = datetime.strptime(request.form["tanggal"], "%Y-%m-%d").date()
            mulai = datetime.strptime(request.form["jam_mulai"], "%H:%M").time()
            selesai = datetime.strptime(request.form["jam_selesai"], "%H:%M").time()
        except ValueError:
            tanggal = mulai = selesai = None

        error = None
        if not judul or tanggal is None:
            error = "Judul, tanggal, dan jam wajib diisi."
        elif selesai <= mulai:
            error = "Jam selesai harus setelah jam mulai."
        elif not (link_ok(link_zoom) and link_ok(link_rekaman)):
            error = "Link harus diawali http:// atau https://"
        elif cid is not None and db.session.get(Community, cid) is None:
            error = "Komunitas tidak valid."

        tanggal_list = [tanggal]
        if not error and sesi is None and request.form.get("ulangi"):
            try:
                sampai = datetime.strptime(request.form["sampai"], "%Y-%m-%d").date()
            except ValueError:
                sampai = None
            if sampai is None or sampai < tanggal:
                error = "Tanggal 'ulangi sampai' tidak valid."
            elif (sampai - tanggal).days > MAKS_ULANG_HARI:
                error = f"Pengulangan maksimal {MAKS_ULANG_HARI} hari."
            else:
                tanggal_list = [
                    tanggal + timedelta(days=i)
                    for i in range((sampai - tanggal).days + 1)
                    if i == 0 or (tanggal + timedelta(days=i)).weekday() < 5
                ]

        if error:
            flash(error, "error")
        else:
            if sesi is not None:
                targets = [sesi]
            else:
                targets = [Sesi(mentor_id=current_user.id) for _ in tanggal_list]
                db.session.add_all(targets)

            for s, tgl in zip(targets, tanggal_list):
                s.judul = judul
                s.deskripsi = deskripsi
                s.tanggal = tgl
                s.jam_mulai = mulai
                s.jam_selesai = selesai
                s.link_zoom = link_zoom
                s.link_rekaman = link_rekaman
                s.ringkasan = ringkasan
                s.community_id = cid

            db.session.commit()
            if len(targets) > 1:
                flash(f"{len(targets)} sesi dibuat.", "success")
            else:
                flash("Sesi disimpan.", "success")
            return redirect(url_for("sesi.detail", sesi_id=targets[0].id))

    return render_template("sesi_form.html", sesi=sesi, komunitas=komunitas)


@bp.route("/")
def index():
    daftar = Sesi.query.order_by(Sesi.tanggal.desc(), Sesi.jam_mulai.desc()).all()
    return render_template("sesi.html", daftar=daftar, staff=staff())


@bp.route("/api")
def api():
    data = [
        {
            "id": f"sesi-{s.id}",
            "title": "Zoom: " + s.judul,
            "start": datetime.combine(s.tanggal, s.jam_mulai).isoformat(),
            "end": datetime.combine(s.tanggal, s.jam_selesai).isoformat(),
            "color": "#16a34a",
            "url": url_for("sesi.detail", sesi_id=s.id),
        }
        for s in Sesi.query.all()
    ]
    return jsonify(data)


@bp.route("/<int:sesi_id>")
def detail(sesi_id):
    s = db.get_or_404(Sesi, sesi_id)
    return render_template("sesi_detail.html", s=s, akses=bisa_akses(s), staff=staff())


@bp.route("/new", methods=["GET", "POST"])
@role_required("admin", "mentor")
def new():
    return _form()


@bp.route("/<int:sesi_id>/edit", methods=["GET", "POST"])
@role_required("admin", "mentor")
def edit(sesi_id):
    s = db.get_or_404(Sesi, sesi_id)
    return _form(s)


@bp.route("/<int:sesi_id>/delete", methods=["POST"])
@role_required("admin", "mentor")
def delete(sesi_id):
    s = db.get_or_404(Sesi, sesi_id)
    for f in s.files:
        hapus_dari_disk(f.nama_simpan)
    db.session.delete(s)
    db.session.commit()
    flash("Sesi dihapus.", "success")
    return redirect(url_for("sesi.index"))


@bp.route("/<int:sesi_id>/file", methods=["POST"])
@role_required("admin", "mentor")
def upload(sesi_id):
    s = db.get_or_404(Sesi, sesi_id)
    f = request.files.get("file")

    if not f or not f.filename:
        flash("Pilih file dulu.", "error")
    elif ext_file(f.filename) not in ALLOWED:
        flash("Format harus PDF, PPT/PPTX, DOC/DOCX, XLS/XLSX, atau ZIP.", "error")
    else:
        nama = f"{uuid.uuid4().hex}.{ext_file(f.filename)}"
        f.save(os.path.join(folder(), nama))
        db.session.add(
            SesiFile(
                sesi_id=s.id,
                nama_asli=secure_filename(f.filename) or nama,
                nama_simpan=nama,
                uploaded_by=current_user.id,
            )
        )
        db.session.commit()
        flash("Materi diunggah.", "success")

    return redirect(url_for("sesi.detail", sesi_id=s.id))


@bp.route("/file/<int:file_id>")
def download(file_id):
    f = db.get_or_404(SesiFile, file_id)
    if not bisa_akses(f.sesi):
        abort(403)
    return send_from_directory(
        folder(), f.nama_simpan,
        as_attachment=not f.nama_simpan.endswith(".pdf"),
        download_name=f.nama_asli,
    )


@bp.route("/file/<int:file_id>/hapus", methods=["POST"])
@role_required("admin", "mentor")
def hapus_file(file_id):
    f = db.get_or_404(SesiFile, file_id)
    sesi_id = f.sesi_id
    hapus_dari_disk(f.nama_simpan)
    db.session.delete(f)
    db.session.commit()
    flash("Materi dihapus.", "success")
    return redirect(url_for("sesi.detail", sesi_id=sesi_id))