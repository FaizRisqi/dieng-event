from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from app import db
from app.models import Pengumuman, Community, CommunityMember

bp = Blueprint("pengumuman", __name__, url_prefix="/pengumuman")


def staff():
    return current_user.is_authenticated and current_user.role in ("admin", "mentor")


def komunitas_dikelola():
    if not current_user.is_authenticated:
        return []
    if current_user.role in ("admin", "mentor"):
        return Community.query.order_by(Community.nama).all()
    return (
        Community.query.join(CommunityMember)
        .filter(CommunityMember.user_id == current_user.id, CommunityMember.role == "pengurus")
        .order_by(Community.nama)
        .all()
    )


def bisa_baca(p):
    if p.community_id is None:
        return True
    if staff():
        return True
    if not current_user.is_authenticated:
        return False
    return db.session.get(CommunityMember, (p.community_id, current_user.id)) is not None


def bisa_kelola(p):
    if not current_user.is_authenticated:
        return False
    if current_user.role == "admin" or p.created_by == current_user.id:
        return True
    if p.community_id:
        m = db.session.get(CommunityMember, (p.community_id, current_user.id))
        return bool(m and m.role == "pengurus")
    return False


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    cid = request.args.get("community_id", type=int)

    query = Pengumuman.query
    if q:
        query = query.filter(
            db.or_(Pengumuman.judul.ilike(f"%{q}%"), Pengumuman.isi.ilike(f"%{q}%"))
        )
    if cid:
        query = query.filter_by(community_id=cid)

    # Urutkan: pin terlebih dahulu (desc), lalu created_at (desc)
    semua = query.order_by(Pengumuman.pin.desc(), Pengumuman.created_at.desc()).all()
    daftar = [p for p in semua if bisa_baca(p)]

    bisa_buat = bool(staff() or komunitas_dikelola())
    komunitas = Community.query.order_by(Community.nama).all()

    return render_template(
        "pengumuman.html",
        daftar=daftar,
        bisa_buat=bisa_buat,
        komunitas=komunitas,
        q=q,
        cid=cid,
        bisa_kelola=bisa_kelola,
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    pilihan = komunitas_dikelola()
    if not staff() and not pilihan:
        abort(403)

    if request.method == "POST":
        judul = request.form.get("judul", "").strip()
        isi = request.form.get("isi", "").strip()
        pin = bool(request.form.get("pin"))
        cid = request.form.get("community_id") or None
        cid = int(cid) if cid else None

        if not judul or not isi:
            flash("Judul dan isi pengumuman wajib diisi.", "error")
        elif cid is None and not staff():
            flash("Pengumuman umum hanya bisa dibuat oleh admin/mentor.", "error")
        elif cid is not None and cid not in {c.id for c in pilihan}:
            abort(403)
        else:
            p = Pengumuman(
                judul=judul,
                isi=isi,
                pin=pin,
                community_id=cid,
                created_by=current_user.id,
            )
            db.session.add(p)
            db.session.commit()
            flash("Pengumuman berhasil dipublikasikan.", "success")
            return redirect(url_for("pengumuman.index"))

    return render_template("pengumuman_form.html", p=None, komunitas=pilihan, staff=staff())


@bp.route("/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def edit(pid):
    p = db.get_or_404(Pengumuman, pid)
    if not bisa_kelola(p):
        abort(403)

    pilihan = komunitas_dikelola()

    if request.method == "POST":
        judul = request.form.get("judul", "").strip()
        isi = request.form.get("isi", "").strip()
        pin = bool(request.form.get("pin"))
        cid = request.form.get("community_id") or None
        cid = int(cid) if cid else None

        if not judul or not isi:
            flash("Judul dan isi pengumuman wajib diisi.", "error")
        elif cid is None and not staff():
            flash("Pengumuman umum hanya bisa dibuat oleh admin/mentor.", "error")
        elif cid is not None and cid not in {c.id for c in pilihan}:
            abort(403)
        else:
            p.judul = judul
            p.isi = isi
            p.pin = pin
            p.community_id = cid
            db.session.commit()
            flash("Pengumuman berhasil diperbarui.", "success")
            return redirect(url_for("pengumuman.index"))

    return render_template("pengumuman_form.html", p=p, komunitas=pilihan, staff=staff())


@bp.route("/<int:pid>/delete", methods=["POST"])
@login_required
def delete(pid):
    p = db.get_or_404(Pengumuman, pid)
    if not bisa_kelola(p):
        abort(403)
    db.session.delete(p)
    db.session.commit()
    flash("Pengumuman dihapus.", "success")
    return redirect(url_for("pengumuman.index"))


@bp.route("/<int:pid>/pin", methods=["POST"])
@login_required
def toggle_pin(pid):
    p = db.get_or_404(Pengumuman, pid)
    if not bisa_kelola(p):
        abort(403)
    p.pin = not p.pin
    db.session.commit()
    status = "disematkan di atas" if p.pin else "batal disematkan"
    flash(f"Pengumuman {status}.", "success")
    return redirect(url_for("pengumuman.index"))
