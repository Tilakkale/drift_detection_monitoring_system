# Industrial Data Drift Monitoring System

An end-to-end monitoring application for detecting changes in server telemetry and measuring their potential impact on ML systems. The repository combines a FastAPI service, SQLAlchemy persistence, drift and anomaly detection services, evaluation scripts, and a Streamlit operations dashboard.

## Capabilities

- PSI and Kolmogorov-Smirnov feature drift analysis
- Per-machine baselines for the Server Machine Dataset
- Isolation Forest, Local Outlier Factor, and One-Class SVM evaluation
- Persisted drift, monitoring, alert, and user models
- Interactive API documentation through OpenAPI/Swagger
- Streamlit dashboard for analysis, model evaluation, and monitoring views
- Reproducible training and evaluation scripts

## Architecture

```text
Server Machine Dataset
					|
					v
Training and evaluation scripts ---> persisted model artifacts
					|
					v
FastAPI API ---> drift services ---> SQLAlchemy database
		 ^                                  |
		 |                                  v
Streamlit dashboard <------------- monitoring results
```

## Technology

| Layer | Technology |
| --- | --- |
| API | Python 3.11, FastAPI, Uvicorn |
| Analytics | pandas, NumPy, SciPy, scikit-learn |
| Persistence | SQLAlchemy, SQLite locally, MySQL-ready configuration |
| Dashboard | Streamlit, Altair |
| Operations | Docker, Docker Compose, Alembic |

## Repository Layout

```text
backend/
	app/
		api/routes/       # Auth, drift, evaluation, and monitoring endpoints
		core/             # Configuration, security, logging, and dependencies
		database/         # SQLAlchemy engine and session setup
		models/           # Persistence models and generated evaluation figures
		services/         # Drift and inference business logic
	scripts/            # Training, evaluation, and comparison workflows
	tests/              # Automated tests
frontend/dashboard/   # Streamlit operational dashboard
dataset/              # Server Machine Dataset files
backend/Docker/       # Deployment configuration
```

## Quick Start

### 1. Install

```powershell
git clone https://github.com/Tilakkale/drift_detection_monitoring_system.git
Set-Location drift_detection_monitoring_system
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

### 2. Start the API

From the repository root:

```powershell
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The API listens on every network interface. On the same computer, use `http://127.0.0.1:8000`; on another device, use `http://<HOST-LAN-IP>:8000`. Use `/docs` for Swagger UI and `/health` for a readiness check.

### 3. Start the dashboard

In a second terminal with the virtual environment active:

```powershell
streamlit run frontend/dashboard/app.py
```

The dashboard uses `DRIFT_API_URL` when provided and otherwise defaults to `http://127.0.0.1:8000`. Select a machine, adjust PSI buckets, and run an analysis from the sidebar.

### 4. Run tests

```powershell
python -m pytest backend/tests -q
```

## API Surface

The service currently exposes route groups for:

- Authentication and user operations
- Drift analysis by machine and PSI bucket count
- Model evaluation
- Monitoring and persisted results

The authoritative request and response schemas are available at `http://localhost:8000/docs` after starting the API.

## Model Workflows

Training and comparison utilities are in `backend/scripts/`:

```powershell
python backend/scripts/train_models.py
python backend/scripts/evaluate_models.py
python backend/scripts/evaluate_ground_truth.py
```

Generated databases, logs, serialized models, and evaluation JSON are intentionally ignored by Git. Keep production artifacts in managed object storage or a model registry rather than committing them to the application repository.

## Dashboard Preview

The Streamlit front page exposes three operational views: **Drift Analysis**, **Model Evaluation**, and **Monitor**. The controls select a machine, configure PSI buckets, launch analysis, evaluate models, and submit a test batch for anomaly scoring.

![Machine 1 evaluation](docs/media/evaluation-machine-1.png)

![Machine 2 evaluation](docs/media/evaluation-machine-2.png)

### Video Demo

Add the recorded walkthrough to `docs/media/dashboard-demo.mp4` and keep this player in the README:

```html
<video controls width="100%" src="docs/media/dashboard-demo.mp4">
	Your browser does not support embedded video.
</video>
```

GitHub also supports video attachments in issues and pull requests. Upload the MP4 there, copy the generated asset URL, and replace the `src` above if repository-hosted video is not rendered by the target GitHub view.

## Network Access Without Localhost

To open the application from another computer or phone on the same Wi-Fi/LAN, first find the Windows host address:

```powershell
ipconfig
```

Find the active adapter's IPv4 address, for example `192.168.1.25`, then open two PowerShell terminals from the repository root:

```powershell
$env:DRIFT_API_URL = "http://192.168.1.25:8000"
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

```powershell
$env:DRIFT_API_URL = "http://192.168.1.25:8000"
streamlit run frontend/dashboard/app.py --server.address 0.0.0.0 --server.port 8502
```

Replace `192.168.1.25` with the actual host IPv4 address. From the other device, open `http://192.168.1.25:8502`. Test the API with `http://192.168.1.25:8000/health`.

If Windows Firewall blocks access, allow inbound TCP ports `8000` and `8502` for private networks, or run an elevated PowerShell rule:

```powershell
New-NetFirewallRule -DisplayName "Drift Monitoring API and Dashboard" -Direction Inbound -Protocol TCP -LocalPort 8000,8502 -Action Allow -Profile Private
```

This LAN setup is suitable for a controlled internal demo. Do not expose the development servers directly to the public Internet; use a TLS reverse proxy, authentication, restricted CORS, and managed secrets for production.

## Production Deployment

For a public or industrial deployment, place the services behind a DNS name and TLS reverse proxy, use managed MySQL, restrict CORS to the dashboard origin, store secrets in a secret manager, add authentication and audit logging, and run the API and dashboard as separate containers or services. Do not expose the development server directly to the Internet.

Local development defaults are defined in `backend/app/core/config.py`. Do not commit secrets. For a production deployment, provide environment-specific database credentials, restrict CORS origins, place the API behind TLS termination, and run migrations before serving traffic.

Docker assets are under `backend/Docker/`. Validate the compose configuration against the target environment before deployment because database credentials, volumes, health checks, and secrets are environment-specific.

## Production Alerting

The monitoring workflow is designed to turn drift and anomaly results into actionable alerts for operations teams. The `alerts` table stores the alert record needed for traceability:

| Field | Purpose |
| --- | --- |
| `machine_id` | Server or monitored asset that produced the signal |
| `alert_type` | Drift, anomaly, or other detector category |
| `severity` | Operational priority such as `medium` or `high` |
| `message` | Human-readable incident context |
| `resolved` | Whether the alert has been closed |
| `created_at` | UTC creation timestamp for audit history |

The `/monitor` endpoint accepts a batch of production-shaped telemetry, validates the expected 38 features, scores it with the machine-specific Isolation Forest model, and returns anomaly count, anomaly fraction, score, and severity. This response is the handoff point for an alert worker or event pipeline.

### Recommended production flow

```text
Telemetry agent -> authenticated ingestion -> /monitor
				      |
				      v
			      anomaly/drift policy
				      |
	     +------------------------+------------------------+
	     v                        v                        v
       persist Alert            email/webhook             incident system
       with audit fields        notification              (PagerDuty/SNS)
```

For a production deployment, implement the dispatcher as a durable background worker or queue consumer. Apply deduplication and cooldown windows per machine and alert type, retry transient delivery failures, record delivery status and correlation IDs, and provide an authenticated resolve/acknowledge workflow. Notifications should use environment-managed SMTP, webhook, or cloud notification credentials; never place secrets in the README, source code, or committed `.env` files.

Recommended alert policies:

- `high`: high-confidence PSI drift or a severe anomaly score; page the on-call team.
- `medium`: sustained moderate drift or repeated anomalies within a time window; create a ticket or team notification.
- `resolved`: close only after the signal returns below the configured threshold for a defined recovery window.

The current repository provides the alert data model and monitoring response. Email, webhook, queue delivery, alert deduplication, and on-call integration must be connected to the deployment's approved production services before enabling paging.