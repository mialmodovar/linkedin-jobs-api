@echo off
REM LinkedIn Jobs Tracker - Startup Script for Windows
REM This script helps you start all the necessary services

echo 🚀 Starting LinkedIn Jobs Tracker...

REM Check if Redis is running
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ❌ Redis is not running. Please start Redis first
    pause
    exit /b 1
)

REM Check if LinkedIn Jobs API is running
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo ❌ LinkedIn Jobs API is not running. Please start it first
    echo    cd .. ^&^& python fastapi_example.py
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Start Django development server
echo 🌐 Starting Django development server...
start "Django Server" cmd /k "python manage.py runserver"

REM Start Celery worker
echo 👷 Starting Celery worker...
start "Celery Worker" cmd /k "celery -A django_jobs_app worker --loglevel=info"

REM Start Celery beat
echo ⏰ Starting Celery beat...
start "Celery Beat" cmd /k "celery -A django_jobs_app beat --loglevel=info"

REM Start Celery flower
echo 🌸 Starting Celery flower...
start "Celery Flower" cmd /k "celery -A django_jobs_app flower"

echo.
echo 🎉 All services started successfully!
echo.
echo 📱 Django Web Interface: http://localhost:8000
echo 🔗 LinkedIn Jobs API: http://localhost:8001
echo 🌸 Celery Flower: http://localhost:5555
echo.
echo Press any key to exit...
pause >nul
