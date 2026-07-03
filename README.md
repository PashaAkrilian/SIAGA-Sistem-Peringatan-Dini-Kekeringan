# SIAGA — Indonesia Drought Early Warning System

**SIAGA (SDCI Early Warning System)** is a full-stack web application for forecasting drought risk across Indonesia under the **Godzilla El Niño 2026** scenario.

The platform transforms our XGBoost-based climate research into an interactive product, enabling users to monitor drought conditions, explore historical climate data, and perform real-time El Niño simulations through a modern web dashboard.

Built with **FastAPI, React, and XGBoost**, the system includes JWT authentication, automated testing, Docker support, and production-ready deployment configurations.

[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Model](https://img.shields.io/badge/Model-XGBoost-brightgreen?style=flat-square)](https://xgboost.readthedocs.io/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)

---

## Live Demo

- **Dashboard:** https://frontend-nu-silk-76.vercel.app
- **API:** https://siaga-backend-production-381a.up.railway.app
- **Swagger Docs:** `/docs`

---

## Architecture

```text
React + Vite
      │
      ▼
 FastAPI REST API
      │
      ▼
XGBoost Models
(Main + Quantile)
```

The project consists of three main components:

| Folder | Description |
|---------|-------------|
| `training/` | Model training and feature engineering pipeline |
| `backend/` | FastAPI service, authentication, and model serving |
| `frontend/` | React-based interactive dashboard |

---

## Key Features

- Interactive drought monitoring dashboard
- Real-time El Niño what-if simulation
- XGBoost-based SDCI forecasting models
- Quantile prediction intervals (Q10, Q50, Q90)
- SHAP explainability and feature importance analysis
- JWT authentication and admin endpoints
- Automated testing with PyTest
- Docker-ready deployment
- Railway and Vercel integration

---

## Tech Stack

| Layer | Technologies |
|---------|----------------|
| Frontend | React, Vite, Recharts |
| Backend | FastAPI, Uvicorn, Pydantic |
| Machine Learning | XGBoost, Optuna, SHAP, Scikit-Learn |
| Authentication | JWT, bcrypt, SQLite |
| Deployment | Docker, Railway, Vercel |

---

## Running Locally

### Backend

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker compose up --build
```

---

## API Endpoints

| Method | Endpoint | Description |
|----------|----------------------------|-----------------------------|
| GET | `/api/metrics` | Model evaluation metrics |
| GET | `/api/historical` | Historical SDCI and ONI data |
| GET | `/api/forecast` | 2026 drought projections |
| GET | `/api/feature-importance` | SHAP feature importance |
| GET | `/api/islands` | Island-level drought summary |
| GET | `/api/simulate` | Real-time El Niño simulation |

---

## Authentication

The public dashboard is accessible without login, while administrative endpoints are protected using JWT authentication.

Supported endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/admin/stats`

---

## Deployment

- **Backend:** Railway / Render (Docker)
- **Frontend:** Vercel / Netlify
- **Containerization:** Docker Compose
- **Environment Management:** `.env` + production secrets

Detailed deployment instructions are available in `DEPLOY.md`.

---

## Authors

Developed by:

- **Dimas Pasha Akrilian**

**Universitas Negeri Semarang (UNNES)**

---

## License

This project is licensed under the **MIT License**.

---

**Data Sources:** CHIRPS, MODIS, NOAA OISST (2000–2025)

**Research Basis:** *Forecasting the Potential Impact of the Godzilla El Niño 2026 on National Drought Risk Using XGBoost and Spatio-Temporal Climate Kinematics* (UNNES, 2026).
