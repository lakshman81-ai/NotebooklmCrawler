@echo off
echo ===================================================
echo   ORCHESTRATION COCKPIT - V2 LAUNCHER
echo ===================================================
echo [1] Starting Backend Bridge (FastAPI)...
start "Cockpit Backend" .venv\Scripts\python bridge.py
echo [2] Starting Frontend UI (Vite dev server)...
cd frontend
start "Cockpit Frontend" npm run dev
echo ===================================================
echo Done! Please wait for the browser to open or visit
echo http://localhost:5173
echo ===================================================
pause
