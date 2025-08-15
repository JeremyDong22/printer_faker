#!/bin/bash

echo "======================================"
echo "🚀 Starting Complete Printer API System"
echo "======================================"
echo ""

# Check if API service is already running
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  API service already running on port 5000"
    echo "   Stopping it first..."
    lsof -ti:5000 | xargs -r kill -9 2>/dev/null
    sleep 2
fi

if lsof -Pi :9100 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Service already running on port 9100"
    echo "   Stopping it first..."
    lsof -ti:9100 | xargs -r kill -9 2>/dev/null
    sleep 2
fi

# Start API service in background
echo "📡 Starting API Service..."
./start_api_service.sh &
API_PID=$!

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
for i in {1..10}; do
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        echo "✅ API service is ready!"
        break
    fi
    sleep 1
done

# Start Cloudflare tunnel
echo ""
echo "🌍 Starting Cloudflare Tunnel..."
echo "======================================"
echo ""

# Check if tunnel is configured
if [ ! -f ~/.cloudflared/a6974762-15aa-4ee8-8c0b-de0d06b37424.json ]; then
    echo "⚠️  Tunnel not configured. Using quick tunnel instead..."
    echo ""
    echo "Your temporary public URL will appear below:"
    echo "======================================"
    cloudflared tunnel --url http://localhost:5000
else
    echo "Starting permanent tunnel to: https://printer.smartice.ai"
    echo "======================================"
    cloudflared tunnel run smartprinter-api
fi