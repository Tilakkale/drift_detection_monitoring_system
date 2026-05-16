# Data Drift Detection and Monitoring System

## Overview

This project provides a backend monitoring system that helps track production data behavior, detect potential data drift issues early, and support reliable ML system monitoring using FastAPI, MySQL, Docker, and scalable backend architecture.
The system focuses on backend architecture, API services, database integration, and Docker-based deployment for scalable ML monitoring workflows.

Current implementation includes:
- FastAPI backend setup
- MySQL database integration
- SQLAlchemy ORM connection
- Swagger API documentation
- Docker containerization
- Docker Compose setup
- WSL2 Docker environment support

---

## Tech Stack

- Python 3.11
- FastAPI
- MySQL
- SQLAlchemy
- Docker
- Docker Compose
- Uvicorn
- Streamlit (frontend prototype support)

---


## Project Structure

```text
drift_monitoring_system/
│
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── database/         # DB connection/session
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Drift logic & business layer
│   │   ├── utils/            # Utility/helper functions
│   │   └── main.py           # FastAPI entry point
│   │
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker/
│   └── docker-compose.yml
│
├── data/                     # Datasets
├── docs/                     # Documentation
├── notebooks/                # Experimentation & EDA
├── frontend/                 # Future dashboard/frontend
├── scripts/                  # Utility scripts
│
├── .gitignore
└── README.md
```

---

# Setup — Step by Step

## Step 1 — Clone Repository

```bash
git clone https://github.com/Tilakkale/drift_detection_monitoring_system.git

cd drift_detection_monitoring_system
```

---

## Step 2 — Create Virtual Environment

```bash
python -m venv venv
```

---

## Step 3 — Activate Environment

### Windows

```bash
venv\Scripts\activate
```

---

## Step 4 — Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

---

## Step 5 — Configure Docker & WSL2

- Install Docker Desktop
- Enable WSL2 integration
- Verify Docker Engine is running

Check Docker status:

```bash
docker --version
docker compose version
docker ps
```

---

## Step 6 — Run FastAPI Backend

```bash
uvicorn backend.app.main:app --reload
```

---

## Step 7 — Open Swagger API Documentation

```text
http://localhost:8000/docs
```

---

## Step 8 — Run Docker Containers

```bash
docker compose -f docker/docker-compose.yml up --build
```

---