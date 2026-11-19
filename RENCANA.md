# Rencana Pengerjaan

## Sudah Selesai ✅

- [x] Setup project, struktur folder, konfigurasi
- [x] Auth: register, login, logout
- [x] Role: admin, mentor, anggota
- [x] Event: CRUD, deteksi bentrok jadwal & lokasi
- [x] Kalender FullCalendar (event + sesi + tugas)
- [x] Pendaftaran event (daftar, batal, absensi)
- [x] Komunitas: CRUD, keanggotaan, role pengurus
- [x] Calendar notes (catatan per tanggal, foto, penanda)
- [x] Sesi Zoom: jadwal, link rekaman, materi upload, pengulangan
- [x] Role mentor: bisa kelola sesi dan tugas
- [x] Tugas: buat, tenggat, pengumpulan (teks/link/file), penilaian + feedback
- [x] Absensi sesi + rekap peserta (kehadiran dan nilai tugas per anggota)
- [x] Dashboard informatif (peringatan tenggat tugas < 7 hari, event & sesi mendatang, shortcut menu)
- [x] Profil pengguna (edit nama, no. WhatsApp, ganti password, riwayat event)
- [x] Pencarian & filter (pencarian kata kunci & filter komunitas di sesi, tugas, dan komunitas)
- [x] Halaman error khusus (403 Akses Ditolak, 404 Tidak Ditemukan, 413 File Terlalu Besar)
- [x] Pengumuman: umum dan per komunitas (pin/sematkan, filter komunitas, dashboard & detail komunitas)
- [x] Lokasi event jadi tabel/dropdown agar bisa deteksi bentrok lebih akurat (master data lokasi, kapasitas ruangan, deteksi bentrok ID & teks)
- [x] Pagination di halaman list (sesi, tugas, event daftar, pengumuman, catatan dengan navigasi halaman)
- [x] Proteksi CSRF dengan Flask-WTF (wajib sebelum produksi)
- [x] Ekspor rekap kehadiran & nilai tugas ke CSV untuk arsip/laporan
- [x] Pengingat WhatsApp (dukungan Fonnte & webhook n8n dengan tombol broadcast per event/sesi/tugas)
- [x] Halaman error 500 (Internal Server Error)
- [x] Setup database lokal (MySQL/MariaDB), migrasi, akun admin default, dan pengujian end-to-end fitur
- [x] Redesain UI/UX & tema warna resmi Dieng Cyber (hijau candi, charcoal, merah, kuning emas) + logo resmi di navbar & landing page
- [x] Ringkasan Notulen Sesi Zoom dengan AI (dukungan Google Gemini API & smart local extractive summarizer, serta auto-ekstraksi transkrip link YouTube & Google Docs)
- [x] Mode Gelap / Terang (Dark Mode & Light Mode) dengan tombol toggle interaktif, dukungan FullCalendar, dan persistensi tema di browser
- [x] Rangkaian tes otomatis dengan pytest (36 tes, 0 gagal)
- [x] Audit keamanan ringan: open redirect, SECRET_KEY prod, debug flag, isolasi sesi komunitas

## Status Project

**Status pengembangan per 19 November 2026:** Semua fitur utama selesai diimplementasikan dan berjalan di lingkungan lokal (Laragon + MySQL). Rangkaian tes otomatis: **36 passed, 0 failed** (dijalankan dengan SQLite in-memory).

> ⚠️ Belum dilakukan UAT formal di lingkungan Dieng Cyber, belum ada uji beban, dan belum ada deployment ke server/VPS publik.

## Batasan yang Diketahui

1. **Ringkasan AI:** Mendukung teks transkrip manual serta ekstraksi otomatis dari link video YouTube (berdasarkan subtitle/transkrip publik) dan dokumen Google Docs/Drive publik. Jika link video tidak memiliki subtitle atau dokumen Drive bersifat privat, output menampilkan kartu metadata rekaman dengan anjuran menempelkan catatan teks manual.
2. **Pengingat WhatsApp:** Manual satu klik per event/sesi/tugas. Tidak terjadwal otomatis. Tanpa token Fonnte/n8n, berjalan di mode simulasi (pesan hanya dicatat di log, tidak benar-benar terkirim).
3. **Belum UAT di Dieng Cyber:** Pengujian baru dilakukan di mesin pengembang (lokal).
4. **Belum uji beban:** Tidak diketahui performa saat banyak user concurrent.
5. **Foto catatan (notes):** Disimpan di `app/static/uploads/notes/` yang dapat diakses publik jika URL diketahui. Belum dipindahkan ke route berizin.

## Batasan dan Pekerjaan Lanjutan (dari Audit Keamanan)

Temuan di bawah ini **belum diperbaiki** dan perlu ditangani sebelum deployment produksi:

### Prioritas Tinggi
- **Validasi upload lebih ketat** (sesi, tugas, catatan): saat ini hanya mengecek ekstensi dan ukuran. Disarankan tambah pengecekan MIME type dan hash nama file unik sudah diterapkan — pertimbangkan antivirus scan untuk produksi.
- **Foto catatan publik:** File di `app/static/uploads/notes/` dapat diakses langsung via URL tanpa login. Pindahkan ke `instance/uploads/notes/` dan tambahkan route download yang mengecek autentikasi.
- **Validasi `next` di login:** Sudah ditambahkan `_safe_next()` yang memblokir URL eksternal. Pastikan Flask-Login menggunakan fungsi ini secara konsisten.

### Prioritas Menengah
- **Semua route POST mengecek peran:** Sudah menggunakan `@role_required` / `bisa_akses()`. Verifikasi manual di semua route hapus/nilai/absen disarankan sebelum go-live.
- **Download file pengumpulan:** Route `/tugas/pengumpulan/<id>/file` sudah mengecek `staff() or p.user_id == current_user.id`. Pertimbangkan logging akses unduhan untuk audit trail.

### Sudah Diperbaiki (commit `8695d1a`)
- ✅ **Open redirect di `next` parameter login**: ditambahkan `_safe_next()` yang menolak URL eksternal.
- ✅ **SECRET_KEY di production**: `config.py` sekarang raise `RuntimeError` jika `FLASK_ENV=production` dan `SECRET_KEY` tidak diisi.
- ✅ **`debug=True` di `run.py`**: sekarang membaca `FLASK_DEBUG` dari environment (default `False`).
