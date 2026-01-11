#!/bin/bash
# Start backend in background

PID_FILE=".pids/backend.pid"
LOG_FILE="logs/backend.log"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Backend already running (PID: $PID)"
        exit 0
    fi
fi

# Create directories
mkdir -p .pids logs

# Start backend
cd backend
../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "../$LOG_FILE" 2>&1 &
PID=$!
cd ..

# Save PID
echo "$PID" > "$PID_FILE"

echo "Backend started in background (PID: $PID)"
echo "  Logs: $LOG_FILE"
echo "  URL:  http://localhost:8000"
