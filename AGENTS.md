# AGENTS.md - Dieng Cyber Event

Sistem penjadwalan event dan pengelolaan komunitas berbasis web untuk Dieng Cyber, Wonosobo (proyek skripsi).

## Stack
- Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF
- MySQL (driver pymysql), konfigurasi lewat `.env`
- Jinja2 + Tailwind (CDN) + FullCalendar 6.1.15 (CDN)
- Semua teks antarmuka berbahasa Indonesia

## Struktur
- `app/__init__.py`: `create_app()`, objek `db`, `migrate`, `login_manager`, `csrf`, registrasi blueprint
- `app/models.py`: semua model
- `app/decorators.py`: `role_required(*roles)`
- `app/routes/`: `main`, `auth`, `events`, `communities`, `notes`, `sesi`, `tugas`, `admin`, `rekap`, `profil`, `pengumuman`
- `app/templates/`: semua template extend `base.html`
- `config.py`, `run.py`, `create_admin.py`, `log_harian.py`, `migrations/`

## Perintah
- Jalankan: `python run.py`
- Migrasi: `flask --app run db migrate -m "pesan"` lalu `flask --app run db upgrade`
- Buat admin: `python create_admin.py`
- Perbarui riwayat: `python log_harian.py`

## Model
User (role: admin / mentor / anggota), Community, CommunityMember (role: pengurus / anggota), Lokasi, Event, EventRegistration (status: terdaftar / hadir / batal), CalendarNote, Sesi, SesiFile, SesiAbsensi, Tugas, Pengumpulan, Pengumuman.

## Hak akses
- admin: semua, termasuk menunjuk mentor di `/admin/users`
- mentor: kelola sesi Zoom, materi, tugas, penilaian
- pengurus komunitas: kelola event dan catatan komunitasnya
- anggota: daftar event, gabung komunitas, kumpul tugas
- Sesi dan tugas yang terkait komunitas hanya bisa diakses anggotanya (plus admin/mentor)

## Konvensi
- Cek izin di route (helper `bisa_*` / `bisa_akses`), jangan hanya menyembunyikan tombol di template
- Link dari pengguna harus divalidasi diawali `http://` atau `https://`
- Upload sesi dan tugas disimpan di `instance/uploads/` dan diunduh lewat route yang mengecek akses. Foto catatan di `app/static/uploads/notes/`
- Setelah mengubah `models.py`: buat migrasi baru, jangan edit file migrasi lama
- Jangan taruh Jinja (`{% %}`) di dalam `<script>`; kirim data lewat atribut `data-*`
- Pesan commit: `feat:`, `fix:`, `docs:`, `refactor:`. Setelah commit jalankan `log_harian.py`, tambahkan `HISTORY.md` ke commit
- Jangan pernah commit `.env`, token, atau API key

## Status
Selesai: setup, auth + role, event + kalender + deteksi bentrok, pendaftaran + absensi event, komunitas, calendar notes, sesi Zoom + materi, tugas + penilaian, absensi sesi + rekap peserta, dashboard informatif, profil pengguna, filter & pencarian, halaman error 403/404/413, pengumuman (umum dan per komunitas), master lokasi event & deteksi bentrok akurat, pagination & event list view, proteksi CSRF (Flask-WTF).

Belum:
- Pengingat WhatsApp (rencana via workflow n8n)
- Ringkasan Zoom dengan AI (butuh API key, opsional)
- Deploy ke server / VPS

## Cara kerja dengan pemilik proyek
- Jawab dalam bahasa Indonesia yang santai dan ringkas
- Ubah kode dengan diff sekecil mungkin
- Debug satu masalah per langkah
- Pemilik biasanya mengirim screenshot error
