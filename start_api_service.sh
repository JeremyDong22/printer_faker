#!/bin/bash

# Start Printer API Service Script
# This starts the 24/7 printer listener with API

echo "======================================"
echo "🖨️  Starting Printer API Service"
echo "======================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create logs directory if needed
mkdir -p logs

# Install requirements if needed
echo "📦 Checking dependencies..."
uv pip install -q flask flask-cors pybluez2

# Kill any existing service on port 5000 or 9100
echo "🔍 Checking for existing services..."
lsof -ti:5000 | xargs -r kill -9 2>/dev/null
lsof -ti:9100 | xargs -r kill -9 2>/dev/null

# Start the service
echo "🚀 Starting API service..."
echo "======================================"
echo ""

# Run with unbuffered output
PYTHONUNBUFFERED=1 uv run python3 printer_api_service.py