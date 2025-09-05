# Suggested Commands for Development

## Environment Setup
```bash
# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Create virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt
```

## Running the Application

### Main Printer Service
```bash
# Direct execution with uv (ALWAYS use uv run)
uv run python3 virtual_printer.py

# With environment variables for debugging
PYTHONUNBUFFERED=1 uv run python3 -u virtual_printer.py
```

### API Service
```bash
# Start the API service
uv run python3 printer_api_service.py

# Or use system service
./start_api_service.sh
```

## Testing Commands (TDD Workflow)

### If test scripts exist:
```bash
# TDD Cycle
./tdd.sh red      # 1. Write failing test
./tdd.sh green    # 2. Make test pass
./tdd.sh refactor # 3. Clean up code

# Other testing
./tdd.sh watch    # Auto-run tests on file changes
./tdd.sh coverage # Generate HTML coverage report
./tdd.sh new feature_name # Create new test file
```

### Direct pytest commands (always with uv)
```bash
# Run all tests
uv run python3 -m pytest tests/ -v

# Run with coverage
uv run python3 -m pytest --cov=. --cov-report=html

# Run specific test file
uv run python3 -m pytest tests/test_escpos_parser.py -v

# Run specific test class
uv run python3 -m pytest tests/test_escpos_parser.py::TestESCPOSParser -v
```

## Monitoring and Debugging
```bash
# Monitor Bluetooth service
systemctl status bluetooth

# Check recent logs
ls -la logs/

# Watch specific log file
tail -f logs/printer_*.log

# Test API endpoints
curl -H "Authorization: smartbcg" https://printer.smartice.ai/api/health
curl -H "Authorization: smartbcg" https://printer.smartice.ai/api/recent
```

## Service Management
```bash
# Install as system service
./install_system_service.sh

# Start/stop/restart service
sudo systemctl start printer-api.service
sudo systemctl stop printer-api.service
sudo systemctl restart printer-api.service

# Check service status
sudo systemctl status printer-api.service

# View service logs
sudo journalctl -u printer-api.service -f
```

## Development Utilities
```bash
# List installed packages
uv pip list

# Update specific package
uv pip install --upgrade pybluez2

# Reinstall all dependencies
uv pip install -r requirements.txt --force-reinstall

# Check for outdated packages
uv pip list --outdated

# Interactive Python shell (for testing imports)
uv run python3
```

## Git Commands
```bash
# Check status
git status

# Stage changes
git add .

# Commit with message
git commit -m "message"

# Push to remote
git push origin main
```

## File Management
```bash
# List print outputs
ls -la pos_print_*.txt

# List logs
ls -la logs/

# Clean up old files (if cleanup script exists)
./cleanup_files.sh
```

## System Utilities (Linux)
```bash
# Check Bluetooth devices
hcitool dev
hcitool scan

# Check RFCOMM connections
rfcomm -a

# Monitor system resources
htop
top

# Check disk usage
df -h
du -sh *
```

## Proxy Configuration (if needed)
```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=socks://127.0.0.1:7891/
```

## IMPORTANT REMINDERS
- **ALWAYS use `uv run` instead of plain `python` or `python3`**
- **Follow TDD: Write test first, then code**
- **Test the setup before making changes: `uv run python3 test_setup.py`**
- **Check CLAUDE.md for detailed project guidelines**