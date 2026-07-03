"""Fixture bersama: pastikan test auth tidak pernah menyentuh users.db asli."""
import pytest

from app.auth import db as auth_db


@pytest.fixture(autouse=True)
def isolated_users_db(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_db, "DB_PATH", tmp_path / "test_users.db")
    auth_db.init_db()
    yield
