# Dieng Cyber Event

Sistem penjadwalan event dan pengelolaan komunitas berbasis web untuk Dieng Cyber, Wonosobo.

## Setup

```bash
git clone https://github.com/FaizRisqi/dieng-event.git
cd dieng-event
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

1. Salin `.env.example` jadi `.env`, isi variabel yang diperlukan (lihat bagian [Variabel Lingkungan](#variabel-lingkungan))
2. Buat database MySQL:
   ```sql
   CREATE DATABASE dieng_event CHARACTER SET utf8mb4;
   ```
3. Jalankan migrasi:
   ```bash
   flask --app run db upgrade
   ```
4. Buat akun admin pertama:
   ```bash
   python create_admin.py
   ```
5. Jalankan server:
   ```bash
   python run.py
   ```
   Lalu buka http://127.0.0.1:5000

## Variabel Lingkungan

Semua variabel diatur di file `.env` (salin dari `.env.example`):

| Variabel | Wajib | Keterangan |
|---|---|---|
| `SECRET_KEY` | ✅ (di produksi) | String acak panjang untuk keamanan sesi & CSRF. Aplikasi gagal start jika kosong saat `FLASK_ENV=production`. |
| `DATABASE_URL` | ✅ | URL koneksi database, misal `mysql+pymysql://root:@localhost/dieng_event` |
| `FLASK_ENV` | - | Set ke `production` di server live untuk mengaktifkan pengecekan keamanan. |
| `FLASK_DEBUG` | - | Set ke `1` untuk mode debug lokal. **Jangan aktifkan di produksi.** |
| `WA_PROVIDER` | - | Provider WhatsApp: `fonnte`, `n8n`, atau `simulasi`. Jika kosong, otomatis dipilih dari token yang tersedia. |
| `FONNTE_TOKEN` | - | Token API Fonnte untuk pengiriman WhatsApp. Jika diisi, mode otomatis menjadi `fonnte`. |
| `N8N_WEBHOOK_URL` | - | URL webhook n8n untuk pengiriman WhatsApp. Jika diisi (dan FONNTE_TOKEN kosong), mode menjadi `n8n`. |
| `GEMINI_API_KEY` | - | API key Google Gemini untuk ringkasan AI. Jika kosong, digunakan mode lokal berbasis aturan. |
| `GEMINI_MODEL` | - | Model Gemini yang dipakai. Default: `gemini-1.5-flash`. |

### Mode WhatsApp

| Mode | Kondisi | Perilaku |
|---|---|---|
| `fonnte` | `FONNTE_TOKEN` terisi | Pesan dikirim ke WhatsApp via API Fonnte |
| `n8n` | `N8N_WEBHOOK_URL` terisi (dan `FONNTE_TOKEN` kosong) | Pesan dikirim via webhook n8n |
| `simulasi` | Tidak ada token / `WA_PROVIDER=simulasi` | Pesan **hanya dicatat di log**, tidak dikirim ke WhatsApp. Flash berkatagori *warning* akan muncul di UI. |

### Mode Ringkasan AI

| Mode | Kondisi | Perilaku |
|---|---|---|
| `gemini` | `GEMINI_API_KEY` terisi | Ringkasan dibuat oleh Google Gemini. Mendukung input teks transkrip manual atau ekstraksi otomatis transkrip dari link video YouTube & Google Docs. |
| `lokal` | `GEMINI_API_KEY` kosong atau Gemini gagal | Ringkasan berbasis aturan ekstraktif dari teks transkrip manual atau transkrip otomatis yang ditarik dari link video YouTube / dokumen Google Drive. Jika link video tidak memiliki subtitle publik, output berupa kartu informasi metadata rekaman. |

## Menjalankan Tes

```bash
# Install dependencies pengembangan (hanya perlu sekali)
pip install -r requirements-dev.txt

# Jalankan semua tes (menggunakan SQLite in-memory, tanpa MySQL)
python -m pytest tests/ -v
```

Hasil terakhir: **36 passed, 0 failed** (Python 3.13, pytest 9.2.0).

## Perintah Berguna

| Perintah | Fungsi |
|---|---|
| `python run.py` | Jalankan server development |
| `flask --app run db migrate -m "pesan"` | Buat file migrasi baru |
| `flask --app run db upgrade` | Terapkan migrasi ke database |
| `python create_admin.py` | Buat akun admin |
| `python log_harian.py` | Perbarui HISTORY.md dari git log |
| `python -m pytest tests/ -v` | Jalankan rangkaian tes otomatis |

## Teknologi

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF
- **Database**: MySQL (via PyMySQL) — tes menggunakan SQLite in-memory
- **Frontend**: Jinja2, Tailwind CSS (CDN), FullCalendar 6.1.15 (CDN)
- **AI**: Google Gemini API (opsional) + smart local summarizer
- **WhatsApp**: Fonnte API / n8n webhook / mode simulasi
