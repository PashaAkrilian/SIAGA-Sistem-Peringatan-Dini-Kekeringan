"""
config.py
=========
Konfigurasi aplikasi dari environment variable. Sengaja sederhana (bukan
pydantic-settings) karena cuma ada segelintir nilai.
"""
import os
import warnings

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-key-do-not-use-in-prod")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "")

if SECRET_KEY.startswith("dev-insecure") and ENVIRONMENT == "production":
    warnings.warn(
        "SECRET_KEY masih memakai nilai default yang tidak aman padahal "
        "ENVIRONMENT=production. Set environment variable SECRET_KEY.",
        RuntimeWarning,
    )
