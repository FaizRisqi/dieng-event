import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, abort, Response
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


@bp.route("/komunitas/<int:community_id>/export")
@login_required
def export_csv(community_id):
    c = db.get_or_404(Community, community_id)
    if not bisa_lihat_rekap(community_id):
        abort(403)

    anggota_list = sorted(
        [m.user for m in c.members if m.user.role == "anggota"],
        key=lambda u: u.nama,
    )
    sesi_list = Sesi.query.filter_by(community_id=c.id).order_by(Sesi.tanggal).all()
    tugas_list = Tugas.query.filter_by(community_id=c.id).order_by(Tugas.tenggat).all()

    absensi_raw = SesiAbsensi.query.filter(
        SesiAbsensi.sesi_id.in_([s.id for s in sesi_list])
    ).all() if sesi_list else []
    absensi = {}
    for a in absensi_raw:
        absensi.setdefault(a.user_id, {})[a.sesi_id] = a

    pengumpulan_raw = Pengumpulan.query.filter(
        Pengumpulan.tugas_id.in_([t.id for t in tugas_list])
    ).all() if tugas_list else []
    pengumpulan = {}
    for p in pengumpulan_raw:
        pengumpulan.setdefault(p.user_id, {})[p.tugas_id] = p

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    header = ["Nama", "Email", "No WA"]
    for s in sesi_list:
        header.append(f"Sesi: {s.judul} ({s.tanggal.strftime('%d/%m/%Y')})")
    header.append("Total Hadir")
    header.append("Persentase Hadir (%)")

    for t in tugas_list:
        header.append(f"Tugas: {t.judul}")
    header.append("Total Kumpul")
    header.append("Rata-rata Nilai")

    writer.writerow(header)

    # Rows
    for u in anggota_list:
        u_ab = absensi.get(u.id, {})
        u_pg = pengumpulan.get(u.id, {})

        hadir_count = sum(1 for s in sesi_list if u_ab.get(s.id) and u_ab[s.id].hadir)
        persen_hadir = round((hadir_count / len(sesi_list) * 100), 1) if sesi_list else 0

        kumpul_count = len(u_pg)
        nilai_list = [p.nilai for p in u_pg.values() if p.nilai is not None]
        rata_nilai = round(sum(nilai_list) / len(nilai_list), 1) if nilai_list else "-"

        row = [u.nama, u.email, u.no_wa or "-"]
        for s in sesi_list:
            ab = u_ab.get(s.id)
            row.append("Hadir" if ab and ab.hadir else "-")
        row.append(hadir_count)
        row.append(f"{persen_hadir}%")

        for t in tugas_list:
            pg = u_pg.get(t.id)
            if pg:
                ket = str(pg.nilai) if pg.nilai is not None else "Belum dinilai"
                if pg.terlambat:
                    ket += " (terlambat)"
                row.append(ket)
            else:
                row.append("-")
        row.append(kumpul_count)
        row.append(rata_nilai)

        writer.writerow(row)

    output.seek(0)
    nama_file = f"rekap_{c.nama.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue().encode("utf-8-sig"),  # UTF-8 with BOM for Excel compatibility
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nama_file}"},
    )
