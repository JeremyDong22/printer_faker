# Operational Commands - Printer Faker

## Service Management
```bash
# Check service status
sudo systemctl status printer-api.service
sudo systemctl status printer-monitor.service

# Restart service (only if needed)
sudo systemctl restart printer-api.service

# View logs
journalctl -u printer-api.service -f
tail -f logs/monitor.log
```

## Health Monitoring
```bash
# Test API health
curl -H "Authorization: smartbcg" http://localhost:5000/api/health

# Get service stats
curl -H "Authorization: smartbcg" http://localhost:5000/api/stats

# Get recent receipts
curl -H "Authorization: smartbcg" http://localhost:5000/api/receipts
```

## Maintenance Tasks
```bash
# Check disk usage
du -sh /home/smartahc/smartice/printer_faker/

# Manual cleanup (if auto_cleanup fails)
find output/ -name "*.bin" -mtime +7 -delete
find output/ -name "*.txt" -mtime +7 -delete

# Truncate large logs (emergency)
echo "" > logs/service_error.log
```

## Troubleshooting
```bash
# Check for port conflicts
sudo lsof -i:9100
sudo lsof -i:5000

# Check if monitor is running
ps aux | grep monitor_health

# Check Cloudflare tunnel
pgrep -f cloudflared

# View cron jobs
crontab -l | grep printer_faker
```

## Testing
```bash
# Send test data to TCP port
echo "Test receipt data" | nc localhost 9100

# Check if files are being cleaned
ls -la output/ | wc -l  # Should be < 1000
```

## Important Notes
- NEVER run virtual_printer.py (conflicts on port 9100)
- Monitor service auto-restarts on failures (no scheduled restarts)
- Logs rotate automatically (max 100MB, 7 days retention)
- Files in output/ deleted after 7 days automatically