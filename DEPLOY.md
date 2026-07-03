# Deploy SIAGA ke Production

Panduan langkah-demi-langkah untuk deploy backend ke Railway/Render dan
frontend ke Vercel, sampai bisa diakses lewat URL publik.

Urutan penting: **backend dulu, baru frontend**, lalu balik lagi ke backend
untuk mengunci CORS ke domain frontend yang sebenarnya (chicken-and-egg:
backend butuh tahu URL frontend, frontend butuh tahu URL backend).

## 0. Generate SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Simpan hasilnya — ini dipakai backend untuk menandatangani JWT. Jangan pernah
commit nilai ini ke git.

## 1. Deploy backend (Railway atau Render)

Repo sudah punya `backend/Dockerfile` dan `backend/railway.json`, jadi kedua
platform bisa langsung mendeteksi & build tanpa konfigurasi tambahan.

**Railway (CLI):**
```bash
cd backend
railway login
railway init
railway up
```

**Render (dashboard):** New → Web Service → connect repo ini → set **Root
Directory** ke `backend` → Render otomatis mendeteksi `Dockerfile`.

Di kedua platform, set environment variables berikut di dashboard project:

| Env var       | Nilai                                   |
|---------------|------------------------------------------|
| `SECRET_KEY`  | hasil dari langkah 0                     |
| `ENVIRONMENT` | `production`                             |
| `CORS_ALLOWED_ORIGINS` | kosongkan dulu, isi di langkah 4 |

Setelah deploy selesai, catat URL backend-nya, misal:
`https://siaga-backend.up.railway.app`

## 2. Smoke-test backend

```bash
curl https://<url-backend>/api/health
# {"status": "ok"}
```

## 3. Deploy frontend (Vercel)

`frontend/vercel.json` sudah disiapkan (build command, output dir, SPA
rewrite).

```bash
cd frontend
vercel
```

Di Vercel project settings → Environment Variables, set:

| Env var         | Nilai                              |
|-----------------|--------------------------------------|
| `VITE_API_URL`  | URL backend dari langkah 1           |

Redeploy setelah env var diset (`vercel --prod`), karena Vite meng-*compile*
`VITE_API_URL` ke dalam bundle statis saat build — mengubah env var setelah
build tidak berpengaruh sampai build ulang.

Catat URL frontend-nya, misal: `https://siaga.vercel.app`

## 4. Kunci CORS di backend

Balik ke dashboard Railway/Render, update env var:

```
CORS_ALLOWED_ORIGINS=https://siaga.vercel.app
```

Redeploy backend supaya perubahan env var diterapkan.

## 5. Smoke-test end-to-end

Buka `https://siaga.vercel.app` di browser, pastikan dashboard memuat data
asli (chart historis, forecast, dll) — ini membuktikan CORS antara frontend
dan backend production sudah benar.

## (Opsional) Buat admin untuk testing endpoint /api/admin

Endpoint admin butuh user dengan `is_admin=1`. Karena tidak ada endpoint
self-promote (sengaja), jalankan dari mesin yang punya akses ke database
production (atau lakukan ini secara lokal sebelum deploy jika DB dibawa
sebagai volume):

```bash
cd backend
python -m app.auth.promote_admin <username>
```
