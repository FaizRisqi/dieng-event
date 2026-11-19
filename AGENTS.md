# AGENTS.md - Dieng Cyber Event

Sistem penjadwalan event dan pengelolaan komunitas berbasis web untuk Dieng Cyber, Wonosobo (proyek skripsi).

## Stack
- Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF
- MySQL (driver pymysql), konfigurasi lewat `.env`
- Jinja2 + Tailwind (CDN) + FullCalendar 6.1.15 (CDN)
- Semua teks antarmuka berbahasa Indonesia

## Struktur
- `app/__init__.py`: `create_app(config_override=None)`, objek `db`, `migrate`, `login_manager`, `csrf`, registrasi blueprint
- `app/models.py`: semua model
- `app/decorators.py`: `role_required(*roles)`
- `app/routes/`: `main`, `auth`, `events`, `communities`, `notes`, `sesi`, `tugas`, `admin`, `rekap`, `profil`, `pengumuman`
- `app/templates/`: semua template extend `base.html`
- `app/services/`: `ai_summary.py`, `whatsapp.py`
- `config.py`, `run.py`, `create_admin.py`, `log_harian.py`, `migrations/`
- `tests/`: rangkaian tes otomatis dengan pytest (SQLite in-memory)

## Perintah
- Jalankan: `python run.py`
- Migrasi: `flask --app run db migrate -m "pesan"` lalu `flask --app run db upgrade`
- Buat admin: `python create_admin.py`
- Perbarui riwayat: `python log_harian.py`
- **Jalankan tes:** `python -m pytest tests/ -v`

## Model
User (role: admin / mentor / anggota), Community, CommunityMember (role: pengurus / anggota), Lokasi, Event, EventRegistration (status: terdaftar / hadir / batal), CalendarNote, Sesi, SesiFile, SesiAbsensi, Tugas, Pengumpulan, Pengumuman.

## Hak akses
- admin: semua, termasuk menunjuk mentor di `/admin/users`
- mentor: kelola sesi Zoom, materi, tugas, penilaian
- pengurus komunitas: kelola event dan catatan komunitasnya
- anggota: daftar event, gabung komunitas, kumpul tugas
- Sesi dan tugas yang terkait komunitas hanya bisa diakses anggotanya (plus admin/mentor)

## Konvensi
- Cek izin di route dengan `abort(403)` (helper `bisa_*` / `bisa_akses`) — jangan hanya menyembunyikan tombol di template
- Link dari pengguna harus divalidasi diawali `http://` atau `https://`
- Upload sesi dan tugas disimpan di `instance/uploads/` dan diunduh lewat route yang mengecek akses. Foto catatan di `app/static/uploads/notes/` (lihat RENCANA.md untuk rencana migrasi ke route berizin)
- Setelah mengubah `models.py`: buat migrasi baru, jangan edit file migrasi lama
- Jangan taruh Jinja (`{% %}`) di dalam `<script>`; kirim data lewat atribut `data-*`
- Pesan commit: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`. Setelah commit jalankan `log_harian.py`, tambahkan `HISTORY.md` ke commit (`git commit --amend --no-edit`)
- Jangan pernah commit `.env`, token, atau API key

## Alur Kerja AI Summary
- `generate_ai_summary(judul, deskripsi, transkrip, link_rekaman)` → `(ok, text, mode, reason)`
- `mode`: `"gemini"` atau `"lokal"`; `reason`: alasan gagal jika Gemini error
- Mode lokal TIDAK menghasilkan poin pembahasan jika tidak ada teks transkrip/catatan
- Input dipotong 4.000 karakter; peringatan flash muncul jika terpotong

## Alur Kerja WhatsApp
- `get_wa_mode()` → `"fonnte"` / `"n8n"` / `"simulasi"`
- `send_wa_message(target, message)` → `(ok: bool, msg: str)`
- Mode simulasi: flash peringatan (amber), pesan hanya dicatat di log
- Mode nyata: flash ringkasan "N berhasil, M gagal, K dilewati"

## Status
**Hasil pytest terakhir: 34 passed, 0 failed** (19 Nov 2026, Python 3.13, pytest 9.2)

Fitur selesai: setup, auth + role, event + kalender + deteksi bentrok, pendaftaran + absensi event, komunitas, calendar notes, sesi Zoom + materi, tugas + penilaian, absensi sesi + rekap peserta, dashboard informatif, profil pengguna, filter & pencarian, halaman error 403/404/413/500, pengumuman (umum dan per komunitas), master lokasi event & deteksi bentrok akurat, pagination & event list view, proteksi CSRF (Flask-WTF), ekspor rekap ke CSV, pengingat WhatsApp (Fonnte/n8n/simulasi + transparansi status), ringkasan Zoom AI (Gemini / smart local summarizer + kejujuran mode lokal), dark mode / light mode toggle, tes otomatis pytest, audit keamanan ringan.

## Batasan yang Diketahui (Penting untuk Pengembangan)
1. Ringkasan AI hanya dari teks transkrip/catatan yang ditempel — tidak memproses audio/video
2. Pengingat WhatsApp manual satu klik, bukan terjadwal otomatis
3. Belum ada UAT di Dieng Cyber
4. Belum ada uji beban
5. Foto catatan di `static/uploads/notes/` masih dapat diakses publik
6. Tidak ada fitur sertifikat (dihapus dari scope)

## Cara Kerja dengan Pemilik Proyek
- Jawab dalam bahasa Indonesia yang santai dan ringkas
- Ubah kode dengan diff sekecil mungkin
- Debug satu masalah per langkah
- Pemilik biasanya mengirim screenshot error
