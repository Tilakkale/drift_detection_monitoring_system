@echo off
REM Launch the Drift Monitoring app on its own port (8502)
REM This app is pinned to port 8502 via .streamlit/config.toml so it
REM never collides with the Asthma app on port 8501.

cd /d c:\drift_monitoring_system
call venv\Scripts\activate.bat
streamlit run frontend/dashboard/app.py
pause

