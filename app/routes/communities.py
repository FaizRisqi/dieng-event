from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from app import db
from app.models import Community, CommunityMember, Event, CalendarNote
from app.decorators import role_required

bp = Blueprint("communities", __name__, url_prefix="/komunitas")


def membership(community_id):
    if not current_user.is_authenticated:
        return None
    return db.session.get(CommunityMember, (community_id, current_user.id))


def bisa_kelola_komunitas(c):
    if not current_user.is_authenticated:
        return False
    if current_user.role == "admin":
        return True
    m = membership(c.id)
    return bool(m and m.role == "pengurus")


@bp.route("/")
def index():
    daftar = Community.query.order_by(Community.nama).all()
    diikuti = set()
    if current_user.is_authenticated:
        diikuti = {m.community_id for m in current_user.memberships}
    return render_template("communities.html", daftar=daftar, diikuti=diikuti)


@bp.route("/<int:community_id>")
def detail(community_id):
    c = db.get_or_404(Community, community_id)
    events = Event.query.filter_by(community_id=c.id).order_by(Event.mulai.desc()).all()
    return render_template(
        "community_detail.html",
        c=c, m=membership(c.id), events=events, kelola=bisa_kelola_komunitas(c),
    )


@bp.route("/new", methods=["GET", "POST"])
@role_required("admin")
def new():
    if request.method == "POST":
        nama = request.form["nama"].strip()
        if not nama:
            flash("Nama komunitas wajib diisi.", "error")
        else:
            c = Community(
                nama=nama,
                deskripsi=request.form.get("deskripsi", "").strip(),
                created_by=current_user.id,
            )
            db.session.add(c)
            db.session.flush()
            db.session.add(CommunityMember(community_id=c.id, user_id=current_user.id, role="pengurus"))
            db.session.commit()
            flash("Komunitas dibuat.", "success")
            return redirect(url_for("communities.detail", community_id=c.id))
    return render_template("community_form.html", c=None)


@bp.route("/<int:community_id>/edit", methods=["GET", "POST"])
@login_required
def edit(community_id):
    c = db.get_or_404(Community, community_id)
    if not bisa_kelola_komunitas(c):
        abort(403)
    if request.method == "POST":
        nama = request.form["nama"].strip()
        if not nama:
            flash("Nama komunitas wajib diisi.", "error")
        else:
            c.nama = nama
            c.deskripsi = request.form.get("deskripsi", "").strip()
            db.session.commit()
            flash("Komunitas diperbarui.", "success")
            return redirect(url_for("communities.detail", community_id=c.id))
    return render_template("community_form.html", c=c)


@bp.route("/<int:community_id>/delete", methods=["POST"])
@role_required("admin")
def delete(community_id):
    c = db.get_or_404(Community, community_id)
    Event.query.filter_by(community_id=c.id).update({"community_id": None})
    CalendarNote.query.filter_by(community_id=c.id).update({"community_id": None})
    db.session.delete(c)
    db.session.commit()
    flash("Komunitas dihapus. Event miliknya jadi event umum.", "success")
    return redirect(url_for("communities.index"))


@bp.route("/<int:community_id>/gabung", methods=["POST"])
@login_required
def gabung(community_id):
    c = db.get_or_404(Community, community_id)
    if membership(c.id):
        flash("Kamu sudah jadi anggota.", "error")
    else:
        db.session.add(CommunityMember(community_id=c.id, user_id=current_user.id))
        db.session.commit()
        flash("Berhasil bergabung.", "success")
    return redirect(url_for("communities.detail", community_id=c.id))


@bp.route("/<int:community_id>/keluar", methods=["POST"])
@login_required
def keluar(community_id):
    m = membership(community_id)
    if not m:
        flash("Kamu bukan anggota komunitas ini.", "error")
    else:
        db.session.delete(m)
        db.session.commit()
        flash("Kamu sudah keluar dari komunitas.", "success")
    return redirect(url_for("communities.detail", community_id=community_id))


@bp.route("/<int:community_id>/anggota/<int:user_id>/peran", methods=["POST"])
@login_required
def peran(community_id, user_id):
    c = db.get_or_404(Community, community_id)
    if not bisa_kelola_komunitas(c):
        abort(403)
    m = db.get_or_404(CommunityMember, (c.id, user_id))
    m.role = "anggota" if m.role == "pengurus" else "pengurus"
    db.session.commit()
    return redirect(url_for("communities.detail", community_id=c.id))


@bp.route("/<int:community_id>/anggota/<int:user_id>/hapus", methods=["POST"])
@login_required
def hapus_anggota(community_id, user_id):
    c = db.get_or_404(Community, community_id)
    if not bisa_kelola_komunitas(c):
        abort(403)
    m = db.get_or_404(CommunityMember, (c.id, user_id))
    db.session.delete(m)
    db.session.commit()
    flash("Anggota dikeluarkan.", "success")
    return redirect(url_for("communities.detail", community_id=c.id))