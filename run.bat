@echo off
title College Chatbot Launcher
color 0A

echo ============================================
echo    COLLEGE CHATBOT - Starting All Services
echo ============================================
echo.

:: ── Start Backend ────────────────────────────────────────
echo [1/2] Starting Django Backend...
start "Django Backend" cmd /k "cd /d D:\projects\college_chat\backend && venv310\Scripts\activate && python manage.py runserver"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak > nul

:: ── Start Frontend ───────────────────────────────────────
echo [2/2] Starting Next.js Frontend...
start "Next.js Frontend" cmd /k "cd /d D:\projects\college_chat\frontend && npm run dev"

echo.
echo ============================================
echo  Backend  : http://127.0.0.1:8000
echo  Frontend : http://localhost:3000
echo ============================================
echo.
echo Both servers are starting in separate windows.
echo Close those windows to stop the servers.
echo.
pause
