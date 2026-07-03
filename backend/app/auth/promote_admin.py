"""
promote_admin.py
=================
Script satu-kali untuk menjadikan sebuah user sebagai admin. Tidak diekspos
lewat HTTP (tidak ada self-service promote-to-admin).

Jalankan dari folder backend/:
    python -m app.auth.promote_admin <username>
"""
import sys

from . import db


def main():
    if len(sys.argv) != 2:
        print("Pemakaian: python -m app.auth.promote_admin <username>")
        sys.exit(1)

    username = sys.argv[1]
    db.init_db()
    if db.set_admin(username, is_admin=True):
        print(f"'{username}' sekarang admin.")
    else:
        print(f"User '{username}' tidak ditemukan.")
        sys.exit(1)


if __name__ == "__main__":
    main()
