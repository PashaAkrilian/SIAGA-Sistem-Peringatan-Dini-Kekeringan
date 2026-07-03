"""
db.py
=====
Penyimpanan user (SQLite biasa, stdlib sqlite3 — cocok untuk satu tabel kecil).
Terpisah dari backend/database/ (yang isinya latihan SQL mentah dan tidak
dipakai oleh aplikasi ini) dan dari backend/data/ (artefak model, read-only).

DB_PATH dibaca ulang tiap kali get_connection() dipanggil (bukan ditangkap
sebagai closure saat import), supaya test bisa memonkeypatch-nya.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "instance" / "users.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()


def get_user_by_username(username: str) -> sqlite3.Row | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT id, username, hashed_password, is_admin FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    return row


def create_user(username: str, hashed_password: str) -> sqlite3.Row:
    conn = get_connection()
    conn.execute(
        "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
        (username, hashed_password),
    )
    conn.commit()
    conn.close()
    return get_user_by_username(username)


def count_users() -> int:
    conn = get_connection()
    (n,) = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    conn.close()
    return n


def set_admin(username: str, is_admin: bool = True) -> bool:
    """Dipakai oleh promote_admin.py. Return True kalau ada baris yang diubah."""
    conn = get_connection()
    cur = conn.execute(
        "UPDATE users SET is_admin = ? WHERE username = ?",
        (1 if is_admin else 0, username),
    )
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed
