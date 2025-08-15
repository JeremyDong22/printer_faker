#!/bin/bash

echo "======================================"
echo "🧹 Cleaning Up Old Services & Files"
echo "======================================"
echo ""

# Check if running as root for service operations
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Please run with sudo to remove system services:"
    echo "   sudo ./uninstall_service.sh"
    exit 1
fi

echo "Step 1: Removing old system service..."
echo "----------------------------------------"

# Stop the old service if running
if systemctl is-active --quiet printer-faker.service; then
    echo "Stopping printer-faker.service..."
    systemctl stop printer-faker.service
fi

# Disable the service
if systemctl is-enabled --quiet printer-faker.service 2>/dev/null; then
    echo "Disabling printer-faker.service..."
    systemctl disable printer-faker.service
fi

# Remove the service file
if [ -f /etc/systemd/system/printer-faker.service ]; then
    echo "Removing service file..."
    rm -f /etc/systemd/system/printer-faker.service
    systemctl daemon-reload
    echo "✅ Old service removed"
else
    echo "✅ No old service file found"
fi

echo ""
echo "Step 2: Service cleanup complete!"
echo ""
echo "======================================"
echo "✅ System service cleanup done!"
echo "======================================"
echo ""
echo "Next, run ./cleanup_files.sh to remove old Python files"
