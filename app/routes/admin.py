from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app import db
from app.models import User
from app.decorators import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/users")
@role_required("admin")
def users():
    daftar = User.query.order_by(User.nama).all()
    return render_template("users.html", daftar=daftar)


@bp.route("/users/<int:user_id>/role", methods=["POST"])
@role_required("admin")
def ubah_role(user_id):
    u = db.get_or_404(User, user_id)
    role = request.form.get("role")
    if role not in ("anggota", "mentor"):
        abort(400)
    if u.role == "admin":
        flash("Role admin tidak bisa diubah dari sini.", "error")
    else:
        u.role = role
        db.session.commit()
        flash(f"Role {u.nama} diubah jadi {role}.", "success")
    return redirect(url_for("admin.users"))