# Data Drift Detection and Monitoring System

## Overview

Machine learning models in production often become unreliable when incoming real-world data changes over time, causing prediction accuracy to decrease without immediate detection.

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