#!/bin/bash

# LinkedIn Jobs Tracker - Startup Script
# This script helps you start all the necessary services

echo "🚀 Starting LinkedIn Jobs Tracker..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   redis-server"
    exit 1
fi

# Check if LinkedIn Jobs API is running
if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "❌ LinkedIn Jobs API is not running. Please start it first:"
    echo "   cd .. && python fastapi_example.py"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Start Django development server
echo "🌐 Starting Django development server..."
python manage.py runserver &
DJANGO_PID=$!

# Start Celery worker with beat in the same process
echo "👷⏰ Starting Celery worker with beat..."
celery -A django_jobs_app worker --beat --loglevel=info &
CELERY_PID=$!

# Start Celery flower (optional)
echo "🌸 Starting Celery flower..."
celery -A django_jobs_app flower &
FLOWER_PID=$!

echo ""
echo "🎉 All services started successfully!"
echo ""
echo "📱 Django Web Interface: http://localhost:8000"
echo "🔗 LinkedIn Jobs API: http://localhost:8001"
echo "🌸 Celery Flower: http://localhost:5555"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $DJANGO_PID $CELERY_PID $FLOWER_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for any process to exit
wait
