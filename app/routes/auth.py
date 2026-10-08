from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        nama = request.form["nama"].strip()
        email = request.form["email"].strip().lower()
        no_wa = request.form.get("no_wa", "").strip()
        password = request.form["password"]

        if len(password) < 6:
            flash("Password minimal 6 karakter.", "error")
        elif User.query.filter_by(email=email).first():
            flash("Email sudah terdaftar.", "error")
        else:
            user = User(nama=nama, email=email, no_wa=no_wa)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Registrasi berhasil, silakan login.", "success")
            return redirect(url_for("auth.login"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Email atau password salah.", "error")

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))