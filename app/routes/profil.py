from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app import db

bp = Blueprint("profil", __name__, url_prefix="/profil")


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        aksi = request.form.get("aksi")

        if aksi == "profil":
            nama = request.form.get("nama", "").strip()
            no_wa = request.form.get("no_wa", "").strip()
            if not nama:
                flash("Nama tidak boleh kosong.", "error")
            else:
                current_user.nama = nama
                current_user.no_wa = no_wa
                db.session.commit()
                flash("Profil diperbarui.", "success")

        elif aksi == "password":
            lama = request.form.get("password_lama", "")
            baru = request.form.get("password_baru", "")
            konfirmasi = request.form.get("konfirmasi", "")
            if not current_user.check_password(lama):
                flash("Password lama salah.", "error")
            elif len(baru) < 6:
                flash("Password baru minimal 6 karakter.", "error")
            elif baru != konfirmasi:
                flash("Konfirmasi password tidak cocok.", "error")
            else:
                current_user.set_password(baru)
                db.session.commit()
                flash("Password berhasil diubah.", "success")

        return redirect(url_for("profil.index"))

    return render_template("profil.html")
