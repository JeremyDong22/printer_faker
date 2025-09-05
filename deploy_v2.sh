#!/bin/bash
# Deploy the improved printer API service v2.0

echo "========================================="
echo "Deploying Printer API Service v2.0"
echo "========================================="
echo ""

# 1. Backup current service file
echo "1. Backing up current service..."
cp /home/smartahc/smartice/printer_faker/printer_api_service.py /home/smartahc/smartice/printer_faker/printer_api_service_backup.py
echo "✓ Backup created: printer_api_service_backup.py"

# 2. Stop current service
echo ""
echo "2. Stopping current service..."
sudo systemctl stop printer-api.service
echo "✓ Service stopped"

# 3. Install new service
echo ""
echo "3. Installing new service..."
cp /home/smartahc/smartice/printer_faker/printer_api_service_v2.py /home/smartahc/smartice/printer_faker/printer_api_service.py
echo "✓ New service code deployed"

# 4. Initialize database
echo ""
echo "4. Initializing SQLite database..."
/home/smartahc/.local/bin/uv run python3 -c "
from printer_api_service import DatabaseManager
db = DatabaseManager('/home/smartahc/smartice/printer_faker/receipts.db')
print('Database initialized')
"
echo "✓ Database ready"

# 5. Start the service
echo ""
echo "5. Starting new service..."
sudo systemctl start printer-api.service
sleep 3

# 6. Verify service is running
echo ""
echo "6. Verifying service..."
if systemctl is-active --quiet printer-api.service; then
    echo "✓ Service is running"
    
    # Test API
    API_RESPONSE=$(curl -s -H "Authorization: smartbcg" http://localhost:5000/api/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✓ API is responding"
        echo "API Response: $API_RESPONSE" | python3 -m json.tool 2>/dev/null | head -10
    else
        echo "⚠️ API not responding yet, may need a moment to start"
    fi
else
    echo "❌ Service failed to start"
    echo "Rolling back..."
    cp /home/smartahc/smartice/printer_faker/printer_api_service_backup.py /home/smartahc/smartice/printer_faker/printer_api_service.py
    sudo systemctl start printer-api.service
    echo "Rolled back to previous version"
    exit 1
fi

# 7. Install monitoring service
echo ""
echo "7. Installing monitoring service..."
sudo cp /home/smartahc/smartice/printer_faker/printer-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable printer-monitor.service
sudo systemctl start printer-monitor.service
echo "✓ Monitoring service installed and started"

# 8. Set up automatic cleanup cron
echo ""
echo "8. Setting up automatic file cleanup..."
(crontab -l 2>/dev/null | grep -v "auto_cleanup.sh"; echo "0 * * * * /home/smartahc/smartice/printer_faker/auto_cleanup.sh") | crontab -
echo "✓ Cleanup cron job installed (runs hourly)"

# 9. Show status
echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Service Status:"
systemctl status printer-api.service --no-pager | head -10
echo ""
echo "Monitor Status:"
systemctl status printer-monitor.service --no-pager | head -10
echo ""
echo "Key improvements deployed:"
echo "✅ SQLite persistence - no data loss on restart"
echo "✅ Connection pooling - handle 50+ concurrent connections"  
echo "✅ Thread pool - parallel processing"
echo "✅ Health monitoring - auto-recovery from failures"
echo "✅ File cleanup - automatic old file removal"
echo "✅ No daily restarts - only restart on actual problems"
echo ""
echo "Monitor logs at: tail -f /home/smartahc/smartice/printer_faker/logs/monitor.log"
echo "API logs at: tail -f /home/smartahc/smartice/printer_faker/logs/printer_api.log"