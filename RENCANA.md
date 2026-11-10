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

## Belum / Sisa Pekerjaan 🔲

- [ ] Pengingat WhatsApp (via n8n atau Fonnte)
- [ ] Ringkasan Zoom dengan AI (opsional, butuh API key)
- [ ] Lokasi event jadi tabel/dropdown agar bisa deteksi bentrok lebih akurat
- [ ] Pagination di halaman list (sesi, tugas, event)
- [ ] Proteksi CSRF dengan Flask-WTF (wajib sebelum produksi)
- [ ] Deploy ke server / VPS
