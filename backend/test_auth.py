"""test_auth.py — Tes untuk register/login/me/admin (JWT auth).
Jalankan dengan: pytest
"""
from fastapi.testclient import TestClient

from app.auth import db as auth_db
from app.main import app

client = TestClient(app)


def _register(username="budi", password="secret123"):
    return client.post("/api/auth/register", json={"username": username, "password": password})


def _login(username="budi", password="secret123"):
    return client.post("/api/auth/login", data={"username": username, "password": password})


def test_register_success():
    r = _register()
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "budi"
    assert body["is_admin"] is False
    assert "password" not in body


def test_register_duplicate_username():
    _register()
    r = _register()
    assert r.status_code == 409


def test_login_success():
    _register()
    r = _login()
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password():
    _register()
    r = _login(password="wrongpass")
    assert r.status_code == 401


def test_login_nonexistent_user():
    r = _login(username="tidakada")
    assert r.status_code == 401


def test_me_requires_token():
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_with_valid_token():
    _register()
    token = _login().json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "budi"


def test_me_with_garbage_token():
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_admin_stats_forbidden_for_regular_user():
    _register()
    token = _login().json()["access_token"]
    r = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_admin_stats_ok_for_admin():
    _register()
    auth_db.set_admin("budi", is_admin=True)
    token = _login().json()["access_token"]
    r = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["total_registered_users"] >= 1
