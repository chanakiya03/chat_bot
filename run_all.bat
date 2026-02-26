@echo off
setlocal
echo ==========================================
echo    COLLEGEBOT - UNIFIED STARTUP
echo ==========================================

:: 0. Kill existing processes on ports 8000 and 3000
echo [*] Cleaning up existing server processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /F /PID %%a 2>nul

:: 1. Sync Data
echo [*] Syncing database and question banks...
call venv\Scripts\python backend\manage.py sync_data

:: 2. Start Backend
echo [*] Launching Backend (Daphne)...
start "CollegeBot Backend" cmd /k "cd backend && ..\venv\Scripts\python -m daphne -p 8000 college_chat_backend.asgi:application"

:: 3. Start Frontend
echo [*] Launching Frontend (Next.js)...
start "CollegeBot Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo SUCCESS: Both servers are starting in separate windows.
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
echo ==========================================
pause
