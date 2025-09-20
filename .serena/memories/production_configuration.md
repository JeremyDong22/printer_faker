# Production Configuration

## Active Services
- **Main Service**: printer_api_service_v2.py (NOT v1)
- **WSGI Server**: Gunicorn with gthread workers
- **Database**: SQLite for receipt storage + direct Supabase writes
- **Dashboard**: Enhanced with live updates at localhost:5000

## System Services
```bash
# Main service (systemd)
/etc/systemd/system/printer-api.service

# Uses uv to run Gunicorn
ExecStart=/home/smartahc/.local/bin/uv run gunicorn -c gunicorn_config.py wsgi:application

# Auto-restart on failure
Restart=always
RestartSec=5
```

## Ports and Authentication
- **TCP 9100**: POS printer protocol (ESC/POS)
- **HTTP 5000**: REST API and dashboard
- **Auth Header**: Authorization: smartbcg
- **Sudo Password**: smartbcg

## Critical Files
- **printer_api_service_v2.py**: Main service (production)
- **order_processor.py**: Supabase integration
- **gunicorn_config.py**: WSGI configuration
- **wsgi.py**: Gunicorn entry point
- **.env**: Supabase credentials
- **dashboard.py**: Live monitoring UI

## Maintenance Commands
```bash
# Service management
sudo systemctl status printer-api.service
sudo systemctl restart printer-api.service
journalctl -u printer-api.service -f

# Check health
curl -H "Authorization: smartbcg" http://localhost:5000/api/health

# Monitor threads (should be ~14)
ps aux | grep -E "(gunicorn|python)" | grep -v grep | wc -l

# Clean old files (automated via cron)
find output/ -name "*.bin" -mtime +7 -delete
```

## Never Run These
- **virtual_printer.py** - Conflicts on port 9100
- **printer_api_service.py** (v1) - Deprecated, use v2