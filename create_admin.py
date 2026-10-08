from getpass import getpass
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    nama = input("Nama: ")
    email = input("Email: ").strip().lower()
    password = getpass("Password: ")

    user = User(nama=nama, email=email, role="admin")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print("Admin dibuat.")