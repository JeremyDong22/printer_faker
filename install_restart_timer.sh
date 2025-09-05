#!/bin/bash
# Install systemd timer for daily restart at 2 AM

echo "Installing printer API restart timer..."

# Copy service and timer files
sudo cp printer-api-restart.service /etc/systemd/system/
sudo cp printer-api-restart.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the timer
sudo systemctl enable printer-api-restart.timer
sudo systemctl start printer-api-restart.timer

# Check status
echo ""
echo "Timer installed! Status:"
sudo systemctl status printer-api-restart.timer --no-pager

echo ""
echo "Next restart scheduled for:"
sudo systemctl list-timers printer-api-restart.timer --no-pager