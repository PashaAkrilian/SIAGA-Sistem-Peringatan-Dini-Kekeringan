# SIAGA — Sistem Peringatan Dini Kekeringan

**SDCI Early Warning System** — dashboard interaktif berbasis machine learning
untuk forecasting risiko kekeringan Indonesia (Godzilla El Niño 2026).

[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Model](https://img.shields.io/badge/Model-XGBoost-brightgreen?style=flat-square&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![Domain](https://img.shields.io/badge/Domain-Climate%20Intelligence-red?style=flat-square)](#)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)

Web app full-stack yang mengubah riset XGBoost (forecasting kekeringan
Godzilla El Niño 2026) menjadi produk yang bisa dipakai: dashboard interaktif
dengan simulator proyeksi *real-time*.

Dibangun dari notebook riset `godzila-el-nino.ipynb` menjadi aplikasi
**Python (FastAPI) + React** yang siap di-deploy.

---

## Daftar Isi

- [Arsitektur](#arsitektur)
- [Tech Stack](#tech-stack)
- [Menjalankan Secara Lokal](#menjalankan-secara-lokal)
- [Endpoint API](#endpoint-api)
- [Testing](#testing)
- [Deploy](#deploy)
- [Catatan Teknis](#catatan-teknis)
- [Lisensi](#lisensi)

---

## Arsitektur

```
┌──────────────────┐     REST/JSON      ┌────────────────────┐
│  React + Vite     │ ◄────────────────► │  FastAPI            │
│  (dashboard)      │                     │  (model serving)    │
│  recharts         │                     │                     │
└──────────────────┘                     └─────────┬──────────┘
                                                     │ load once
                                          ┌──────────┴───────────┐
                                          │  4 model XGBoost .json │
                                          │  (main + q10/q50/q90)  │
                                          │  + artefak JSON        │
                                          └────────────────────────┘
```

Tiga bagian:

| Folder      | Isi                                                            |
|-------------|----------------------------------------------------------------|
| `training/` | Script `train.py` — melatih ulang model dari CSV mentah        |
| `backend/`  | API FastAPI yang menyajikan model & menjalankan simulasi live  |
| `frontend/` | Dashboard React                                                |

---

## Tech Stack

| Layer      | Bahasa / Tools                                                  |
|------------|-------------------------------------------------------------------|
| Backend    | Python · FastAPI · Uvicorn · Pydantic                             |
| ML / Data  | XGBoost · pandas · NumPy · scikit-learn · SHAP · Optuna           |
| Frontend   | JavaScript (JSX) · React 18 · Vite · Recharts · CSS               |
| Deploy     | Railway / Render (backend) · Vercel / Netlify (frontend)          |

---

## Menjalankan Secara Lokal

### 1. Latih model (menghasilkan artefak di `backend/data/`)

```bash
cd training
pip install -r ../backend/requirements.txt optuna shap scikit-learn
python train.py
```

Ini menghasilkan: `model_main.json`, `model_q10/50/90.json`, dan sejumlah
file JSON (metrics, historical, forecast, feature importance).

> Model hasil training sudah disertakan di `backend/data/`, jadi langkah ini
> opsional kalau kamu cuma mau menjalankan app-nya.

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
cp ../training/master_dataset_godzilla_elnino_2000_2025.csv data/master_dataset.csv
uvicorn app.main:app --reload --port 8000
```

Buka http://localhost:8000/docs untuk dokumentasi API interaktif (Swagger).

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Buka http://localhost:5173. Vite otomatis mem-proxy `/api` ke backend.

---

## Endpoint API

| Method | Path                        | Fungsi                                     |
|--------|-----------------------------|--------------------------------------------|
| GET    | `/api/metrics`              | R², RMSE, MAE (train & test)               |
| GET    | `/api/historical?island=`   | Deret waktu SDCI + ONI per pulau           |
| GET    | `/api/historical-fit`       | Garis prediksi model pada data historis    |
| GET    | `/api/forecast`             | Proyeksi 2026 (skenario default)           |
| GET    | `/api/feature-importance`   | SHAP & gain feature importance             |
| GET    | `/api/islands`              | Ringkasan + status kekeringan 8 pulau      |
| GET    | `/api/simulate?oni_increment=` | Simulasi what-if real-time              |

---

## Testing

```bash
cd backend
pytest
```

---

## Deploy

- **Backend** → Railway / Render. Start command:
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Frontend** → Vercel / Netlify. Build: `npm run build`, output: `dist/`.
  Set env `VITE_API_URL` ke URL backend production.

---

## Catatan Teknis

- Model disimpan dalam **format native XGBoost (.json)**, bukan pickle —
  lebih aman & portabel antar versi.
- Feature engineering **identik** antara `training/train.py` dan
  `backend/app/features.py`. Ini penting: kalau pipeline fitur beda antara
  training & serving, prediksi bisa ngaco (*training-serving skew*).
- Simulasi *what-if* menghitung ulang fitur kinematika ONI dan menjalankan
  3 model kuantil setiap kali slider digeser.

---

## Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).

---

Data: CHIRPS · MODIS · NOAA OISST (2000–2025). Berdasarkan riset
"Forecasting Dampak Potensi Godzilla El Niño 2026" (UNNES, 2026).
