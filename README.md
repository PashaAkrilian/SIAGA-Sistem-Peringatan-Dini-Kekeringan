# SIAGA — Indonesia Drought Early Warning System

**SDCI Early Warning System** — an interactive, machine-learning-powered
dashboard for forecasting drought risk across Indonesia (Godzilla El Niño
2026 scenario).

[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Model](https://img.shields.io/badge/Model-XGBoost-brightgreen?style=flat-square&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![Domain](https://img.shields.io/badge/Domain-Climate%20Intelligence-red?style=flat-square)](#)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)

A full-stack web application that turns XGBoost research (drought forecasting
under the Godzilla El Niño 2026 scenario) into a usable product: an
interactive dashboard with a real-time projection simulator.

Built from the research notebook `godzila-el-nino.ipynb` into a deployable
**Python (FastAPI) + React** application, complete with JWT authentication,
automated tests, Docker support, and production deployment configs.

## Live Demo

- **Dashboard:** https://frontend-nu-silk-76.vercel.app
- **API:** https://siaga-backend-production-381a.up.railway.app (interactive docs at `/docs`)

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Running Locally](#running-locally)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Testing](#testing)
- [Deployment](#deployment)
- [Technical Notes](#technical-notes)
- [License](#license)

---

## Architecture

```
┌──────────────────┐     REST/JSON      ┌────────────────────┐
│  React + Vite     │ ◄────────────────► │  FastAPI            │
│  (dashboard)      │                     │  (model serving)    │
│  recharts         │                     │                     │
└──────────────────┘                     └─────────┬──────────┘
                                                     │ load once
                                          ┌──────────┴───────────┐
                                          │  4 XGBoost .json      │
                                          │  models (main +       │
                                          │  q10/q50/q90)         │
                                          │  + JSON artifacts      │
                                          └────────────────────────┘
```

Three main parts:

| Folder      | Contents                                                       |
|-------------|------------------------------------------------------------------|
| `training/` | `train.py` — retrains the model from the raw CSV dataset         |
| `backend/`  | FastAPI service that serves the model and runs live simulations  |
| `frontend/` | React dashboard                                                   |

---

## Tech Stack

| Layer      | Language / Tools                                                    |
|------------|-----------------------------------------------------------------------|
| Backend    | Python · FastAPI · Uvicorn · Pydantic                                 |
| Auth       | PyJWT · bcrypt · SQLite (stdlib `sqlite3`)                             |
| ML / Data  | XGBoost · pandas · NumPy · scikit-learn · SHAP · Optuna               |
| Frontend   | JavaScript (JSX) · React 18 · Vite · Recharts · CSS                   |
| Deploy     | Docker · Railway / Render (backend) · Vercel / Netlify (frontend)     |

---

## Running Locally

### 1. Train the model (generates artifacts in `backend/data/`)

```bash
cd training
pip install -r ../backend/requirements.txt optuna shap scikit-learn
python train.py
```

This produces `model_main.json`, `model_q10/50/90.json`, and a set of JSON
artifacts (metrics, historical data, forecast, feature importance).

> Trained model artifacts are already included in `backend/data/`, so this
> step is optional if you just want to run the app.

### 2. Backend

```bash
cd backend
pip install -r requirements-dev.txt   # requirements.txt + pytest/httpx for local dev
cp ../training/master_dataset_godzilla_elnino_2000_2025.csv data/master_dataset.csv
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive API documentation (Swagger).
The **Authorize** button there accepts a JWT issued by `/api/auth/login` —
see [Authentication](#authentication) below.

### Docker (optional — runs backend and frontend together)

```bash
docker compose up --build
```

Backend at http://localhost:8000, frontend at http://localhost:5173.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite automatically proxies `/api` requests to
the backend.

---

## API Endpoints

| Method | Path                            | Purpose                                   |
|--------|----------------------------------|--------------------------------------------|
| GET    | `/api/metrics`                  | R², RMSE, MAE (train & test)               |
| GET    | `/api/historical?island=`       | Historical SDCI + ONI time series per island |
| GET    | `/api/historical-fit`           | Model fit line on historical data          |
| GET    | `/api/forecast`                 | 2026 projection (default scenario)         |
| GET    | `/api/feature-importance`       | SHAP & gain feature importance             |
| GET    | `/api/islands`                  | Summary + drought status for 8 islands     |
| GET    | `/api/simulate?oni_increment=`  | Real-time what-if simulation               |

All endpoints above are public (read-only dashboard, no login required). The
authentication endpoints are listed separately below.

---

## Authentication

The dashboard itself stays public, but there is a separate JWT-based login
system that protects the admin surface (`/api/admin/*`):

| Method | Path                  | Purpose                                             |
|--------|-----------------------|------------------------------------------------------|
| POST   | `/api/auth/register`  | Register a new user (`{username, password}`)        |
| POST   | `/api/auth/login`     | Log in (form-encoded), returns a JWT access token   |
| GET    | `/api/auth/me`        | Return the currently authenticated user             |
| GET    | `/api/admin/stats`    | Admin-only stats (requires a token with `is_admin`)  |

New users are not admins by default. To promote a user to admin (useful for
local testing):
```bash
cd backend
python -m app.auth.promote_admin <username>
```

The `SECRET_KEY` used to sign JWTs comes from the `SECRET_KEY` environment
variable (an insecure default is used for local dev only). See
[DEPLOY.md](DEPLOY.md) for how to generate a production secret key.

---

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

---

## Deployment

- **Backend** → Railway / Render (via Docker — see `backend/Dockerfile` and
  `backend/railway.json`). Start command:
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
  Required env vars: `SECRET_KEY`, `ENVIRONMENT=production`,
  `CORS_ALLOWED_ORIGINS=<frontend-url>`.
- **Frontend** → Vercel (`frontend/vercel.json` already included) / Netlify.
  Build command: `npm run build`, output directory: `dist/`. Set the
  `VITE_API_URL` env var to the production backend URL.

Full step-by-step instructions are in [DEPLOY.md](DEPLOY.md).

---

## Technical Notes

- Models are stored in **native XGBoost format (.json)**, not pickle — safer
  and more portable across versions.
- Feature engineering is **identical** between `training/train.py` and
  `backend/app/features.py`. This matters: if the feature pipeline diverges
  between training and serving, predictions can silently degrade
  (*training-serving skew*).
- The what-if simulation recomputes ONI kinematic features and re-runs all
  three quantile models live every time the slider moves.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

Data sources: CHIRPS · MODIS · NOAA OISST (2000–2025). Based on the research
"Forecasting the Potential Impact of the Godzilla El Niño 2026" (UNNES, 2026).
