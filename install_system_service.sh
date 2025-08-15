#!/bin/bash

echo "======================================"
echo "🔧 Installing Printer API as System Service"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo ./install_system_service.sh"
    exit 1
fi

# Stop any existing services
echo "Stopping existing services..."
systemctl stop printer-api 2>/dev/null
systemctl stop printer-faker 2>/dev/null
systemctl stop cloudflared 2>/dev/null

# Remove old service files
rm -f /etc/systemd/system/printer-faker.service

# Install printer API service
echo "Installing Printer API service..."
cp printer-api.service /etc/systemd/system/
chmod 644 /etc/systemd/system/printer-api.service

# Install cloudflared service
echo "Setting up Cloudflare tunnel service..."
if ! systemctl list-units --full -all | grep -q "cloudflared.service"; then
    cloudflared service install
fi

# Configure cloudflared
mkdir -p /etc/cloudflared
cat > /etc/cloudflared/config.yml <<EOF
tunnel: smartprinter-api
credentials-file: /home/smartahc/.cloudflared/a6974762-15aa-4ee8-8c0b-de0d06b37424.json

ingress:
  - hostname: printer.smartice.ai
    service: http://localhost:5000
  - service: http_status:404
EOF

# Reload systemd
systemctl daemon-reload

# Enable services to start on boot
echo "Enabling auto-start on boot..."
systemctl enable printer-api.service
systemctl enable cloudflared.service

# Start services
echo "Starting services..."
systemctl start printer-api.service
sleep 3
systemctl start cloudflared.service

# Check status
echo ""
echo "======================================"
echo "✅ Installation Complete!"
echo "======================================"
echo ""

echo "Service Status:"
systemctl status printer-api --no-pager | head -10
echo ""
systemctl status cloudflared --no-pager | head -10

echo ""
echo "======================================"
echo "🔐 API Authentication Required"
echo "======================================"
echo "Password: smartbcg"
echo ""
echo "Usage examples:"
echo "  curl -H 'Authorization: smartbcg' https://printer.smartice.ai/api/health"
echo "  curl 'https://printer.smartice.ai/api/recent?auth=smartbcg'"
echo ""
echo "======================================"
echo "📍 Your API is running at:"
echo "   https://printer.smartice.ai"
echo "======================================"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status printer-api"
echo "  sudo systemctl restart printer-api"
echo "  sudo journalctl -u printer-api -f"
echo "======================================"