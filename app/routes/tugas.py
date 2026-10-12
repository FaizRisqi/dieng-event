import os
import uuid
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, abort, current_app, send_from_directory,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.models import Tugas, Pengumpulan, Sesi, Community, CommunityMember, User
from app.decorators import role_required

bp = Blueprint("tugas", __name__, url_prefix="/tugas")

ALLOWED = {"pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "zip", "png", "jpg", "jpeg", "txt"}
FMT = "%Y-%m-%dT%H:%M"


def staff():
    return current_user.is_authenticated and current_user.role in ("admin", "mentor")


def bisa_akses(t):
    if staff():
        return True
    if not current_user.is_authenticated:
        return False
    if t.community_id is None:
        return True
    return db.session.get(CommunityMember, (t.community_id, current_user.id)) is not None


def peserta_target(t):
    if t.community_id:
        anggota = CommunityMember.query.filter_by(community_id=t.community_id).all()
        return sorted(
            [m.user for m in anggota if m.user.role == "anggota"],
            key=lambda u: u.nama,
        )
    return User.query.filter_by(role="anggota").order_by(User.nama).all()


def folder():
    path = os.path.join(current_app.instance_path, "uploads", "tugas")
    os.makedirs(path, exist_ok=True)
    return path


def ext_file(nama):
    return nama.rsplit(".", 1)[-1].lower() if "." in nama else ""


def hapus_dari_disk(nama_simpan):
    if not nama_simpan:
        return
    path = os.path.join(folder(), nama_simpan)
    if os.path.exists(path):
        os.remove(path)


def _form(tugas=None):
    daftar_sesi = Sesi.query.order_by(Sesi.tanggal.desc()).limit(60).all()
    komunitas = Community.query.order_by(Community.nama).all()

    if request.method == "POST":
        judul = request.form["judul"].strip()
        deskripsi = request.form.get("deskripsi", "").strip()
        terima = bool(request.form.get("terima_terlambat"))
        sid = request.form.get("sesi_id") or None
        sid = int(sid) if sid else None
        cid = request.form.get("community_id") or None
        cid = int(cid) if cid else None

        try:
            tenggat = datetime.strptime(request.form["tenggat"], FMT)
        except ValueError:
            tenggat = None

        sesi = db.session.get(Sesi, sid) if sid else None

        error = None
        if not judul or tenggat is None:
            error = "Judul dan tenggat wajib diisi."
        elif sid and sesi is None:
            error = "Sesi tidak valid."
        elif cid and db.session.get(Community, cid) is None:
            error = "Komunitas tidak valid."

        if error:
            flash(error, "error")
        else:
            if cid is None and sesi:
                cid = sesi.community_id

            baru = tugas is None
            if baru:
                tugas = Tugas(created_by=current_user.id)
                db.session.add(tugas)

            tugas.judul = judul
            tugas.deskripsi = deskripsi
            tugas.tenggat = tenggat
            tugas.terima_terlambat = terima
            tugas.sesi_id = sid
            tugas.community_id = cid

            if not baru:
                for p in tugas.pengumpulan:
                    p.terlambat = p.dikumpulkan_at > tenggat

            db.session.commit()
            flash("Tugas disimpan.", "success")
            return redirect(url_for("tugas.detail", tugas_id=tugas.id))

    return render_template("tugas_form.html", tugas=tugas, daftar_sesi=daftar_sesi, komunitas=komunitas)


@bp.route("/")
@login_required
def index():
    semua = Tugas.query.order_by(Tugas.tenggat.desc()).all()
    daftar = [t for t in semua if bisa_akses(t)]
    mine, jumlah = {}, {}
    if staff():
        jumlah = {t.id: len(t.pengumpulan) for t in daftar}
    else:
        mine = {
            p.tugas_id: p
            for p in Pengumpulan.query.filter_by(user_id=current_user.id).all()
        }
    return render_template(
        "tugas.html", daftar=daftar, staff=staff(),
        mine=mine, jumlah=jumlah, sekarang=datetime.now(),
    )


@bp.route("/api")
def api():
    if not current_user.is_authenticated:
        return jsonify([])
    data = [
        {
            "id": f"tugas-{t.id}",
            "title": "Tenggat: " + t.judul,
            "start": t.tenggat.isoformat(),
            "color": "#dc2626",
            "url": url_for("tugas.detail", tugas_id=t.id),
        }
        for t in Tugas.query.all()
        if bisa_akses(t)
    ]
    return jsonify(data)


@bp.route("/<int:tugas_id>")
@login_required
def detail(tugas_id):
    t = db.get_or_404(Tugas, tugas_id)
    if not bisa_akses(t):
        abort(403)

    lewat = datetime.now() > t.tenggat

    if staff():
        target = peserta_target(t)
        sudah_ids = {p.user_id for p in t.pengumpulan}
        belum = [u for u in target if u.id not in sudah_ids]
        daftar = sorted(t.pengumpulan, key=lambda p: p.dikumpulkan_at)
        return render_template(
            "tugas_detail.html", t=t, staff=True, lewat=lewat,
            daftar=daftar, belum=belum, total=len(target),
        )

    mine = Pengumpulan.query.filter_by(tugas_id=t.id, user_id=current_user.id).first()
    return render_template("tugas_detail.html", t=t, staff=False, lewat=lewat, mine=mine)


@bp.route("/new", methods=["GET", "POST"])
@role_required("admin", "mentor")
def new():
    return _form()


@bp.route("/<int:tugas_id>/edit", methods=["GET", "POST"])
@role_required("admin", "mentor")
def edit(tugas_id):
    t = db.get_or_404(Tugas, tugas_id)
    return _form(t)


@bp.route("/<int:tugas_id>/delete", methods=["POST"])
@role_required("admin", "mentor")
def delete(tugas_id):
    t = db.get_or_404(Tugas, tugas_id)
    for p in t.pengumpulan:
        hapus_dari_disk(p.nama_simpan)
    db.session.delete(t)
    db.session.commit()
    flash("Tugas dihapus.", "success")
    return redirect(url_for("tugas.index"))


@bp.route("/<int:tugas_id>/kumpul", methods=["POST"])
@login_required
def kumpul(tugas_id):
    t = db.get_or_404(Tugas, tugas_id)
    if not bisa_akses(t):
        abort(403)
    if staff():
        flash("Mentor/admin tidak mengumpulkan tugas.", "error")
        return redirect(url_for("tugas.detail", tugas_id=t.id))

    sekarang = datetime.now()
    terlambat = sekarang > t.tenggat
    p = Pengumpulan.query.filter_by(tugas_id=t.id, user_id=current_user.id).first()

    teks = request.form.get("teks", "").strip()
    link = request.form.get("link", "").strip()
    f = request.files.get("file")
    ada_file = bool(f and f.filename)

    error = None
    if terlambat and not t.terima_terlambat:
        error = "Tenggat sudah lewat dan tugas ini tidak menerima pengumpulan terlambat."
    elif p and p.nilai is not None:
        error = "Tugas sudah dinilai, tidak bisa dikirim ulang."
    elif not (teks or link or ada_file or (p and p.nama_simpan)):
        error = "Isi teks, link, atau unggah file."
    elif link and not link.startswith(("http://", "https://")):
        error = "Link harus diawali http:// atau https://"
    elif ada_file and ext_file(f.filename) not in ALLOWED:
        error = "Format file tidak didukung."

    if error:
        flash(error, "error")
        return redirect(url_for("tugas.detail", tugas_id=t.id))

    if p is None:
        p = Pengumpulan(tugas_id=t.id, user_id=current_user.id)
        db.session.add(p)

    p.teks = teks
    p.link = link
    if ada_file:
        hapus_dari_disk(p.nama_simpan)
        nama = f"{uuid.uuid4().hex}.{ext_file(f.filename)}"
        f.save(os.path.join(folder(), nama))
        p.nama_asli = secure_filename(f.filename) or nama
        p.nama_simpan = nama
    p.dikumpulkan_at = sekarang
    p.terlambat = terlambat

    db.session.commit()
    flash("Tugas berhasil dikumpulkan." + (" (terlambat)" if terlambat else ""), "success")
    return redirect(url_for("tugas.detail", tugas_id=t.id))


@bp.route("/pengumpulan/<int:pid>/nilai", methods=["POST"])
@role_required("admin", "mentor")
def nilai(pid):
    p = db.get_or_404(Pengumpulan, pid)
    raw = request.form.get("nilai", "").strip()
    feedback = request.form.get("feedback", "").strip()

    if raw == "":
        p.nilai = None
    else:
        try:
            n = int(raw)
        except ValueError:
            n = -1
        if not 0 <= n <= 100:
            flash("Nilai harus angka 0-100.", "error")
            return redirect(url_for("tugas.detail", tugas_id=p.tugas_id))
        p.nilai = n

    p.feedback = feedback
    p.dinilai_by = current_user.id
    p.dinilai_at = datetime.now()
    db.session.commit()
    flash("Penilaian disimpan.", "success")
    return redirect(url_for("tugas.detail", tugas_id=p.tugas_id))


@bp.route("/pengumpulan/<int:pid>/file")
@login_required
def unduh(pid):
    p = db.get_or_404(Pengumpulan, pid)
    if not p.nama_simpan:
        abort(404)
    if not (staff() or p.user_id == current_user.id):
        abort(403)
    return send_from_directory(
        folder(), p.nama_simpan,
        as_attachment=not p.nama_simpan.endswith((".pdf", ".png", ".jpg", ".jpeg")),
        download_name=p.nama_asli,
    )