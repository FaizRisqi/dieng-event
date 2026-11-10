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

1. Salin `.env.example` jadi `.env`, isi `SECRET_KEY` (acak) dan `DATABASE_URL`
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

## Contoh isi `.env`

```
SECRET_KEY=ganti-dengan-string-acak-yang-panjang
DATABASE_URL=mysql+pymysql://root:password@localhost/dieng_event
```

## Perintah berguna

| Perintah | Fungsi |
|---|---|
| `python run.py` | Jalankan server development |
| `flask --app run db migrate -m "pesan"` | Buat file migrasi baru |
| `flask --app run db upgrade` | Terapkan migrasi ke database |
| `python create_admin.py` | Buat akun admin |
| `python log_harian.py` | Perbarui HISTORY.md dari git log |

## Teknologi

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login
- **Database**: MySQL (via PyMySQL)
- **Frontend**: Jinja2, Tailwind CSS (CDN), FullCalendar 6.1.15 (CDN)
