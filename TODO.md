# Task: Separate Asthma app and Drift app URLs

## Problem
Both the asthma app (`C:\major_project`) and drift app (`c:\drift_monitoring_system`) run on the
same default Streamlit port **8501**, causing them to collide — the browser shows whichever app
answers first, so the drift app appears to show the asthma app.

## Steps
- [x] 1. Diagnose the port conflict (found 4 Python processes on port 8501)
- [x] 2. Kill all 4 conflicting Python processes (PIDs: 17836, 17852, 20444, 21564)
- [x] 3. Pin drift app to its own port (8502) via `.streamlit/config.toml`
- [x] 4. Create `run_asthma.bat` (port 8501) and `run_drift.bat` (port 8502) helper scripts
- [x] 5. Launch both apps and verify they open at separate URLs
- [x] 6. Start FastAPI backend on port 8000 (fixes "API Offline")

## Result
All apps now run simultaneously on separate ports:
- 🫁 Asthma app → **http://localhost:8501**
- 📊 Drift app → **http://localhost:8502**
- ⚙️ Backend API → **http://localhost:8000**

