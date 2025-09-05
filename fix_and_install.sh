#!/bin/bash

echo "======================================"
echo "🔧 Fixing and Installing Services"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo ./fix_and_install.sh"
    exit 1
fi

# Step 1: Kill all existing processes
echo "Step 1: Stopping all existing processes..."
pkill -f printer_api_service 2>/dev/null
pkill -f virtual_printer 2>/dev/null
pkill -f "python.*9100" 2>/dev/null
pkill -f "python.*5000" 2>/dev/null
lsof -ti:5000 | xargs -r kill -9 2>/dev/null
lsof -ti:9100 | xargs -r kill -9 2>/dev/null
sleep 2

# Step 2: Stop existing services
echo "Step 2: Stopping existing services..."
systemctl stop printer-api 2>/dev/null
systemctl stop printer-faker 2>/dev/null
systemctl disable printer-api 2>/dev/null
systemctl disable printer-faker 2>/dev/null

# Step 3: Install cloudflared if not exists
echo "Step 3: Installing cloudflared..."
if ! command -v cloudflared &> /dev/null; then
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
    echo "✅ cloudflared installed"
else
    echo "✅ cloudflared already installed"
fi

# Step 4: Install printer API service
echo "Step 4: Installing Printer API service..."
cp printer-api.service /etc/systemd/system/
chmod 644 /etc/systemd/system/printer-api.service

# Step 5: Create cloudflared service
echo "Step 5: Creating cloudflared service..."
cat > /etc/systemd/system/cloudflared.service <<EOF
[Unit]
Description=Cloudflare Tunnel
After=network.target printer-api.service
Wants=printer-api.service

[Service]
Type=simple
User=smartahc
WorkingDirectory=/home/smartahc
ExecStart=/usr/local/bin/cloudflared tunnel run smartprinter-api
Restart=always
RestartSec=5
Environment="HOME=/home/smartahc"

[Install]
WantedBy=multi-user.target
EOF

# Step 6: Configure cloudflared
echo "Step 6: Configuring cloudflared..."
mkdir -p /home/smartahc/.cloudflared
chown -R smartahc:smartahc /home/smartahc/.cloudflared

# Step 7: Reload and enable services
echo "Step 7: Enabling services..."
systemctl daemon-reload
systemctl enable printer-api.service
systemctl enable cloudflared.service

# Step 8: Start services
echo "Step 8: Starting services..."
systemctl start printer-api.service
sleep 5  # Give API time to start
systemctl start cloudflared.service

# Step 9: Check status
echo ""
echo "======================================"
echo "✅ Installation Complete!"
echo "======================================"
echo ""

echo "Service Status:"
echo ""
echo "Printer API Service:"
systemctl status printer-api --no-pager | head -10
echo ""
echo "Cloudflare Tunnel Service:"
systemctl status cloudflared --no-pager | head -10

echo ""
echo "======================================"
echo "🔐 API Authentication"
echo "======================================"
echo "Password: smartbcg"
echo ""
echo "Test locally:"
echo "  curl -H 'Authorization: smartbcg' http://localhost:5000/api/health"
echo ""
echo "Test from internet:"
echo "  curl -H 'Authorization: smartbcg' https://printer.smartice.ai/api/health"
echo ""
echo "======================================"
echo "📍 Your API endpoints:"
echo "   Local: http://localhost:5000"
echo "   Public: https://printer.smartice.ai"
echo "======================================"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status printer-api"
echo "  sudo systemctl status cloudflared"
echo "  sudo systemctl restart printer-api"
echo "  sudo journalctl -u printer-api -f"
echo "  sudo journalctl -u cloudflared -f"
echo "======================================"