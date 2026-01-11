#!/bin/bash
# Quick service setup script for Change-Driven Development

set -e

echo "==========================================="
echo "Change-Driven Development Service Setup"
echo "==========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "ERROR: Do not run this script as root or with sudo"
   echo "The script will ask for sudo password when needed"
   exit 1
fi

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    exit 1
fi

if ! command -v task &> /dev/null; then
    echo "ERROR: Task is not installed"
    echo "Install it from: https://taskfile.dev/installation/"
    exit 1
fi

echo "✓ All prerequisites found"
echo ""

# Run setup
echo "Running setup (this may take a few minutes)..."
task setup

echo ""
echo "Creating log directory..."
mkdir -p logs

echo ""
echo "Installing systemd services (requires sudo)..."
sudo cp systemd/cdd-backend.service /etc/systemd/system/
sudo cp systemd/cdd-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
read -p "Enable services to start on boot? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl enable cdd-backend
    sudo systemctl enable cdd-frontend
    echo "✓ Services enabled for auto-start"
fi

echo ""
read -p "Start services now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl start cdd-backend
    sudo systemctl start cdd-frontend
    echo "✓ Services started"
    
    echo ""
    echo "Waiting for services to initialize..."
    sleep 3
    
    echo ""
    echo "Service status:"
    sudo systemctl status cdd-backend --no-pager || true
    echo ""
    sudo systemctl status cdd-frontend --no-pager || true
fi

echo ""
echo "==========================================="
echo "Setup Complete!"
echo "==========================================="
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  task service-status    - Check service status"
echo "  task service-logs      - View logs"
echo "  task service-restart   - Restart services"
echo "  task service-stop      - Stop services"
echo ""
echo "See SERVICE_SETUP.md for more information"
echo ""
