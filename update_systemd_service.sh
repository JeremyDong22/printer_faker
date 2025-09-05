#!/bin/bash
# Script to update systemd service with environment file support

cat << 'EOF' | sudo tee /etc/systemd/system/printer-api.service > /dev/null
[Unit]
Description=Printer API Service - POS Receipt Capture
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=5
User=smartahc
WorkingDirectory=/home/smartahc/smartice/printer_faker
Environment="PATH=/home/smartahc/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
# Load environment variables from .env file if it exists
EnvironmentFile=-/home/smartahc/smartice/printer_faker/.env
ExecStart=/home/smartahc/.local/bin/uv run gunicorn -c /home/smartahc/smartice/printer_faker/gunicorn_config.py wsgi:application
StandardOutput=journal
StandardError=journal

# Restart configuration
StartLimitBurst=5
StartLimitInterval=60s

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd service file updated with environment support"
echo "Run the following commands to apply changes:"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl restart printer-api.service"