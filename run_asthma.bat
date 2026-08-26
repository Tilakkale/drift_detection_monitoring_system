@echo off
REM Launch the Asthma app on its own port (8501)
REM Located at C:\major_project - uses its own virtual environment.
REM This app stays on the default Streamlit port 8501.

cd /d c:\major_project
call .venv\Scripts\activate.bat
streamlit run app.py
pause

