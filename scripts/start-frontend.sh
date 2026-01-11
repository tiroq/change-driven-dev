#!/bin/bash
# Start frontend in background

PID_FILE=".pids/frontend.pid"
LOG_FILE="logs/frontend.log"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Frontend already running (PID: $PID)"
        exit 0
    fi
fi

# Create directories
mkdir -p .pids logs

# Check if frontend is set up
if [ ! -d "frontend/node_modules" ]; then
    echo "Error: Frontend not set up. Run: task setup-frontend"
    exit 1
fi

# Load nvm if available
if [ -f "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh"
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "Error: npm not found. Please install Node.js and npm:"
    echo "  - Via nvm (recommended): https://github.com/nvm-sh/nvm"
    echo "  - Via apt: sudo apt install npm nodejs"
    exit 1
fi

# Start frontend in background
cd frontend
npm run dev > "../$LOG_FILE" 2>&1 &
PID=$!
cd ..

# Save PID
echo "$PID" > "$PID_FILE"

echo "Frontend started in background (PID: $PID)"
echo "  Logs: $LOG_FILE"
echo "  URL:  http://localhost:5173"
