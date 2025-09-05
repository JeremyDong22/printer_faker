#!/bin/bash
# Fix the daily restart issue that causes downtime

echo "========================================="
echo "Fixing Daily Restart Timer Issue"
echo "========================================="

# Disable the daily restart timer (causes predictable downtime)
echo "1. Disabling daily restart timer..."
sudo systemctl stop printer-api-restart.timer
sudo systemctl disable printer-api-restart.timer
echo "✓ Daily restart timer disabled"

# Keep the service but only for manual restarts
echo "2. Service can still be manually restarted if needed"

# Show current status
echo ""
echo "Current timer status:"
systemctl status printer-api-restart.timer --no-pager | grep -E "Active|Loaded"

echo ""
echo "✅ Fix complete! The API will no longer restart daily at 2 AM"
echo "The service will only restart based on health monitoring"