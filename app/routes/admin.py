from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app import db
from app.models import User, Lokasi
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


@bp.route("/lokasi", methods=["GET", "POST"])
@role_required("admin")
def lokasi():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        alamat = request.form.get("alamat", "").strip()
        kapasitas = request.form.get("kapasitas")
        keterangan = request.form.get("keterangan", "").strip()

        if not nama:
            flash("Nama lokasi wajib diisi.", "error")
        elif Lokasi.query.filter_by(nama=nama).first():
            flash("Nama lokasi sudah digunakan.", "error")
        else:
            lok = Lokasi(
                nama=nama,
                alamat=alamat,
                kapasitas=int(kapasitas) if kapasitas else None,
                keterangan=keterangan,
            )
            db.session.add(lok)
            db.session.commit()
            flash("Lokasi berhasil ditambahkan.", "success")
            return redirect(url_for("admin.lokasi"))

    daftar = Lokasi.query.order_by(Lokasi.nama).all()
    return render_template("admin_lokasi.html", daftar=daftar)


@bp.route("/lokasi/<int:lid>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_lokasi(lid):
    lok = db.get_or_404(Lokasi, lid)

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        alamat = request.form.get("alamat", "").strip()
        kapasitas = request.form.get("kapasitas")
        keterangan = request.form.get("keterangan", "").strip()

        duplikat = Lokasi.query.filter(Lokasi.nama == nama, Lokasi.id != lok.id).first()
        if not nama:
            flash("Nama lokasi wajib diisi.", "error")
        elif duplikat:
            flash("Nama lokasi sudah digunakan.", "error")
        else:
            lok.nama = nama
            lok.alamat = alamat
            lok.kapasitas = int(kapasitas) if kapasitas else None
            lok.keterangan = keterangan
            db.session.commit()
            flash("Lokasi berhasil diperbarui.", "success")
            return redirect(url_for("admin.lokasi"))

    return render_template("admin_lokasi_form.html", lok=lok)


@bp.route("/lokasi/<int:lid>/delete", methods=["POST"])
@role_required("admin")
def delete_lokasi(lid):
    lok = db.get_or_404(Lokasi, lid)
    db.session.delete(lok)
    db.session.commit()
    flash("Lokasi berhasil dihapus.", "success")
    return redirect(url_for("admin.lokasi"))