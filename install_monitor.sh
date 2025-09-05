#!/bin/bash
# Install auto-monitoring service

echo "Installing auto-monitor service..."

# Copy service file
sudo cp auto_monitor.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the monitor
sudo systemctl enable auto_monitor.service
sudo systemctl start auto_monitor.service

echo "Monitor installed! Check status with:"
echo "sudo systemctl status auto_monitor.service"
echo ""
echo "View monitor logs with:"
echo "sudo journalctl -u auto_monitor.service -f"