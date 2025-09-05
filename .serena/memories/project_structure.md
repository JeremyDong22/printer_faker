# Project Structure

## Directory Layout
```
printer_faker/
├── .git/                           # Git repository
├── .serena/                        # Serena MCP configuration
├── logs/                           # Runtime logs directory
├── output/                         # Captured print jobs output
├── .env                            # Environment variables (sensitive)
├── .gitignore                      # Git ignore patterns
│
├── Core Application Files
│   ├── virtual_printer.py         # Main Bluetooth printer emulator
│   ├── printer_api_service.py     # REST API service
│   ├── test_api_client.py         # API client for testing
│   └── requirements.txt           # Python dependencies
│
├── Documentation
│   ├── CLAUDE.md                  # AI assistant guidelines
│   ├── API_USAGE.md               # API documentation
│   └── API_SETUP_GUIDE.md         # API setup instructions
│
├── Service Configuration
│   ├── printer-api.service        # Main systemd service
│   ├── printer-api-restart.service # Restart service
│   ├── printer-api-restart.timer  # Restart timer
│   └── auto_monitor.service       # Auto-monitoring service
│
├── Installation Scripts
│   ├── install_service.sh         # Install main service
│   ├── install_system_service.sh  # Install system service
│   ├── install_monitor.sh         # Install monitor
│   ├── install_restart_timer.sh   # Install restart timer
│   ├── fix_and_install.sh         # Fix and install all
│   └── uninstall_service.sh       # Uninstall services
│
├── Utility Scripts
│   ├── start_api_service.sh       # Start API service
│   ├── start_all.sh               # Start all services
│   ├── monitor_health.sh          # Health monitoring
│   ├── cleanup_files.sh           # Clean old files
│   ├── setup_tunnel.sh            # Setup Cloudflare tunnel
│   └── setup_permanent_tunnel.sh  # Permanent tunnel setup
│
└── External Dependencies
    └── cloudflared-binary          # Cloudflare tunnel binary
```

## Missing But Referenced Files
These files are mentioned in CLAUDE.md but don't exist yet:
- `run.sh` - Main execution script
- `monitor.sh` - Verbose monitoring script  
- `watch_logs.sh` - Real-time log viewer
- `test_setup.py` - Setup verification script
- `tdd.sh` - TDD helper script
- `tests/` directory - Test files

## File Categories

### Core Python Files
- `virtual_printer.py`: Bluetooth SPP server implementation
- `printer_api_service.py`: Flask-based REST API (modified, not committed)
- `test_api_client.py`: Testing client for API

### Configuration Files
- `.env`: Contains sensitive data like API passwords
- `requirements.txt`: Python package dependencies
- Various `.service` files: systemd service configurations

### Shell Scripts
- Installation scripts: Set up system services
- Utility scripts: Monitor, clean, and manage the service
- Tunnel scripts: Configure Cloudflare secure access

### Output Directories
- `logs/`: Service logs with timestamps
- `output/`: Captured POS print data files

## Data Flow
1. POS Terminal → Bluetooth → virtual_printer.py
2. virtual_printer.py → pos_print_*.txt files
3. printer_api_service.py → Read files → REST API
4. API clients → HTTPS requests → JSON responses

## Service Architecture
- Main printer service runs as systemd service
- API service provides remote monitoring
- Cloudflare tunnel enables secure remote access
- Auto-restart timer ensures reliability