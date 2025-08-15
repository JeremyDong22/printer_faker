#!/bin/bash

echo "======================================"
echo "🔧 Installing Printer API as System Service"
echo "======================================"
echo ""
echo "This will install both the API and tunnel as system services"
echo "They will auto-start on boot and run in background"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo ./install_service.sh"
    exit 1
fi

# Get the current directory and user
INSTALL_DIR=$(pwd)
INSTALL_USER=$SUDO_USER

echo "Installing from: $INSTALL_DIR"
echo "Running as user: $INSTALL_USER"
echo ""

# 1. Create systemd service for API
echo "Creating API service..."
cat > /etc/systemd/system/printer-api.service <<EEOF
[Unit]
Description=Printer API Service
After=network.target

[Service]
Type=simple
User=$INSTALL_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=/home/$INSTALL_USER/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/$INSTALL_USER/.local/bin/uv run python3 $INSTALL_DIR/printer_api_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EEOF

# 2. Install cloudflared as service (if not already)
echo "Setting up Cloudflare tunnel service..."
if ! systemctl list-units --full -all | grep -q "cloudflared.service"; then
    cloudflared service install
fi

# Update cloudflared config
mkdir -p /etc/cloudflared
cat > /etc/cloudflared/config.yml <<EEOF
tunnel: smartprinter-api
credentials-file: /home/$INSTALL_USER/.cloudflared/a6974762-15aa-4ee8-8c0b-de0d06b37424.json

ingress:
  - hostname: printer.smartice.ai
    service: http://localhost:5000
  - service: http_status:404
EEOF

# 3. Enable and start services
echo "Enabling services..."
systemctl daemon-reload
systemctl enable printer-api.service
systemctl enable cloudflared

echo "Starting services..."
systemctl start printer-api.service
systemctl start cloudflared

sleep 3

# 4. Check status
echo ""
echo "======================================"
echo "✅ Installation Complete!"
echo "======================================"
echo ""
echo "Service Status:"
systemctl status printer-api.service --no-pager | head -n 5
echo ""
systemctl status cloudflared --no-pager | head -n 5
echo ""
echo "======================================"
echo "Your API is now running as a system service!"
echo ""
echo "🌐 Access at: https://printer.smartice.ai"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status printer-api    # Check API status"
echo "  sudo systemctl status cloudflared     # Check tunnel status"
echo "  sudo journalctl -u printer-api -f    # View API logs"
echo "  sudo journalctl -u cloudflared -f    # View tunnel logs"
echo "  sudo systemctl restart printer-api   # Restart API"
echo "  sudo systemctl stop printer-api      # Stop API"
echo "======================================"
