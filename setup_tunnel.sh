#!/bin/bash

# Cloudflare Tunnel Setup Script
# Sets up and runs a quick tunnel for internet access

echo "======================================"
echo "☁️  Cloudflare Tunnel Setup"
echo "======================================"

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."
    
    # Detect architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    elif [ "$ARCH" = "aarch64" ]; then
        CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    else
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
    fi
    
    # Download and install
    wget -q "$CLOUDFLARED_URL" -O cloudflared
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    
    echo "✅ cloudflared installed"
fi

# Check if API service is running
if ! curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "⚠️  API service not running on port 5000"
    echo "   Please start the service first:"
    echo "   ./start_api_service.sh"
    echo ""
    echo "   Then run this script in another terminal."
    exit 1
fi

echo "✅ API service detected on port 5000"
echo ""
echo "🌍 Starting Cloudflare Quick Tunnel..."
echo "======================================"
echo ""
echo "Your public URL will appear below:"
echo "(It will look like: https://xxxxx.trycloudflare.com)"
echo ""
echo "Share this URL to access your API from anywhere!"
echo "======================================"
echo ""

# Start the tunnel
cloudflared tunnel --url http://localhost:5000