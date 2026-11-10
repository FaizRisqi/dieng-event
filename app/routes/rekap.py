from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from app import db
from app.models import Community, CommunityMember, Sesi, SesiAbsensi, Tugas, Pengumpulan, User
from app.decorators import role_required

bp = Blueprint("rekap", __name__, url_prefix="/rekap")


def bisa_lihat_rekap(community_id):
    if not current_user.is_authenticated:
        return False
    if current_user.role in ("admin", "mentor"):
        return True
    m = db.session.get(CommunityMember, (community_id, current_user.id))
    return bool(m and m.role == "pengurus")


@bp.route("/")
@login_required
def index():
    if current_user.role in ("admin", "mentor"):
        komunitas = Community.query.order_by(Community.nama).all()
    else:
        komunitas = [
            m.community for m in current_user.memberships if m.role == "pengurus"
        ]
    return render_template("rekap_index.html", komunitas=komunitas)


@bp.route("/komunitas/<int:community_id>")
@login_required
def komunitas(community_id):
    c = db.get_or_404(Community, community_id)
    if not bisa_lihat_rekap(community_id):
        abort(403)

    # Semua anggota (role anggota)
    anggota_list = sorted(
        [m.user for m in c.members if m.user.role == "anggota"],
        key=lambda u: u.nama,
    )

    # Semua sesi komunitas ini, urut tanggal
    sesi_list = Sesi.query.filter_by(community_id=c.id).order_by(Sesi.tanggal).all()

    # Semua tugas komunitas ini
    tugas_list = Tugas.query.filter_by(community_id=c.id).order_by(Tugas.tenggat).all()

    # Absensi: {user_id: {sesi_id: SesiAbsensi}}
    absensi_raw = SesiAbsensi.query.filter(
        SesiAbsensi.sesi_id.in_([s.id for s in sesi_list])
    ).all()
    absensi = {}
    for a in absensi_raw:
        absensi.setdefault(a.user_id, {})[a.sesi_id] = a

    # Pengumpulan: {user_id: {tugas_id: Pengumpulan}}
    pengumpulan_raw = Pengumpulan.query.filter(
        Pengumpulan.tugas_id.in_([t.id for t in tugas_list])
    ).all()
    pengumpulan = {}
    for p in pengumpulan_raw:
        pengumpulan.setdefault(p.user_id, {})[p.tugas_id] = p

    return render_template(
        "rekap_komunitas.html",
        c=c,
        anggota_list=anggota_list,
        sesi_list=sesi_list,
        tugas_list=tugas_list,
        absensi=absensi,
        pengumpulan=pengumpulan,
    )
