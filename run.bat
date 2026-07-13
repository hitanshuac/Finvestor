@echo off
echo Starting Finvestor Enterprise (FastAPI + Streamlit)...

if exist ".venv\Scripts\activate" (
    set "ACTIVATE_CMD=.venv\Scripts\activate && "
) else if exist "venv\Scripts\activate" (
    set "ACTIVATE_CMD=venv\Scripts\activate && "
) else (
    set "ACTIVATE_CMD="
)

echo Starting FastAPI Backend (Port 8000)...
start "Finvestor API (FastAPI)" cmd /k "%ACTIVATE_CMD% uvicorn api.server:app --port 8000"

echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul

echo Starting Streamlit Frontend (Port 8501)...
start "Finvestor UI (Streamlit)" cmd /k "%ACTIVATE_CMD% streamlit run main.py --server.port 8501"

pause
