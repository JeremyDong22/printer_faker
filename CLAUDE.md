# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **24/7 Restaurant Order Management System** that captures and processes receipt data from POS terminals for real-time integration with cloud services (Cloudflare Workers and Supabase). The system provides a reliable TCP listener on port 9100 and REST API on port 5000 for restaurant kitchen and order management.

**Critical for Operations**: This service must maintain 99%+ uptime as it handles all restaurant orders and kitchen coordination.

## Project Architecture

### Core Components

```
printer_faker/
├── printer_api_service.py  # Main TCP/API service (PORT CONFLICT with virtual_printer.py!)
│   ├── ESCPOSParser        # ESC/POS command parser (imported from virtual_printer)
│   ├── ReceiptExtractor    # Extract receipt number and timestamp
│   ├── PrinterAPIService   # TCP server on port 9100
│   └── Flask API           # REST API on port 5000
├── virtual_printer.py      # DEPRECATED - DO NOT RUN (conflicts on port 9100)
├── printer_api_service_v2.py # Enhanced version with SQLite persistence (ready to deploy)
└── requirements.txt         # Python dependencies (Flask, pybluez2, pytest)
```

### Critical Services & Monitoring

```
System Services:
├── printer-api.service      # Main systemd service (no daily restarts!)
├── printer-monitor.service  # Health monitoring (auto-restart on issues)
├── auto_cleanup.sh          # Hourly cron to prevent file accumulation
└── logrotate.d/printer-api  # Log rotation (max 100MB, 7 days retention)
```

### Data Flow

1. **TCP Connection** → POS terminal connects to port 9100
2. **Data Reception** → Raw ESC/POS commands received via TCP
3. **Command Parsing** → ESCPOSParser interprets commands
4. **Data Storage** → Receipts stored in memory (deque) and optionally SQLite
5. **API Access** → REST API on port 5000 provides receipt data
6. **Cloud Integration** → Cloudflare Workers fetch data for Supabase processing

### File Output Structure

```
logs/
├── monitor.log              # Health monitoring logs
├── service_error.log        # Service errors (rotated daily, max 100MB)
└── backup/                  # Backup of cleaned logs

output/                      # Receipt data (auto-cleaned after 7 days)
├── raw_*.bin               # Raw ESC/POS data
└── parsed_*.txt            # Parsed receipt text
```

## Coding Principles

### Core Philosophy
**"Keep things as simple as possible, but not simpler"** - Einstein

### Test-Driven Development (TDD)

**MANDATORY: Follow the Red-Green-Refactor cycle for all new features**

```
1. RED: Write a failing test first
2. GREEN: Write minimal code to pass the test  
3. REFACTOR: Clean up while keeping tests green
```

#### TDD Workflow Example

```bash
# 1. RED - Write failing test
uv run python3 -m pytest tests/test_new_feature.py -v
# ✗ Test fails (expected)

# 2. GREEN - Implement minimal code
# Edit the implementation file...
uv run python3 -m pytest tests/test_new_feature.py -v
# ✓ Test passes

# 3. REFACTOR - Improve code quality
# Clean up implementation...
uv run python3 -m pytest tests/ -v
# ✓ All tests still pass
```

#### TDD Rules

1. **Never write production code without a failing test**
2. **Write only enough test code to fail**
3. **Write only enough production code to pass**
4. **Refactor only when tests are green**
5. **One test, one assertion (when possible)**

#### Test Structure

```python
# tests/test_escpos_parser.py
def test_should_parse_bold_command():
    """Test name describes expected behavior"""
    # Arrange
    parser = ESCPOSParser()
    data = b'\x1B\x45\x01'
    
    # Act
    result = parser.parse(data)
    
    # Assert
    assert result == [('BOLD', True)]
```

### Implementation Guidelines

1. **Single Responsibility**
   - Each class/function does ONE thing well
   - ESCPOSParser only parses, doesn't handle I/O
   - PrinterEmulator only manages connections, doesn't parse

2. **Explicit Over Implicit**
   ```python
   # Good: Clear, explicit
   def save_print_job(self, data: bytes, timestamp: str) -> str:
       filename = f"pos_print_{timestamp}.txt"
       
   # Bad: Implicit, unclear
   def save(self, d):
       f = f"pj_{time.time()}.txt"
   ```

3. **Fail Fast, Fail Clearly**
   ```python
   # Always validate early and provide clear error messages
   if not bluetooth.is_valid_address(addr):
       raise ValueError(f"Invalid Bluetooth address: {addr}")
   ```

4. **No Premature Optimization**
   - Start with simple, readable code
   - Profile before optimizing
   - Document any necessary complexity

5. **Minimal Dependencies**
   - Only pybluez2 for Bluetooth functionality
   - Standard library for everything else
   - No unnecessary abstractions

6. **Clear State Management**
   ```python
   # State should be obvious and tracked
   self.is_connected = False
   self.current_job = None
   self.print_queue = queue.Queue()
   ```

## Development Workflow with uv

### IMPORTANT: Always Use uv for Python

**Never use plain `python` or `python3` commands. Always use `uv run`.**

### Environment Management

```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt

# Add new dependency
uv pip install package_name
uv pip freeze > requirements.txt
```

### Running Code

```bash
# Always use uv run for Python execution
uv run python3 virtual_printer.py
uv run python3 test_setup.py

# Interactive Python shell
uv run python3

# Run with environment variables
PYTHONUNBUFFERED=1 uv run python3 -u virtual_printer.py
```

### Testing - TDD Workflow

**Use the TDD helper script for the Red-Green-Refactor cycle:**

```bash
# TDD Cycle
./tdd.sh red      # 1. Write failing test
./tdd.sh green    # 2. Make test pass
./tdd.sh refactor # 3. Clean up code

# Other testing commands
./tdd.sh watch    # Auto-run tests on file changes
./tdd.sh coverage # Generate HTML coverage report
./tdd.sh new feature_name # Create new test file

# Direct pytest commands (always with uv)
uv run python3 -m pytest tests/ -v
uv run python3 -m pytest --cov=. --cov-report=html
uv run python3 -m pytest tests/test_escpos_parser.py::TestESCPOSParser -v
```

**Test file naming convention:**
- Test files: `tests/test_*.py`
- Test classes: `Test*`
- Test functions: `test_should_*` or `test_*`

### Scripts Usage

All scripts use `uv run` internally:
- `./run.sh` - Main execution with uv
- `./monitor.sh` - Verbose monitoring with uv
- `./test_setup.py` - Verification with uv

### Dependency Management

```bash
# View installed packages
uv pip list

# Update specific package
uv pip install --upgrade pybluez2

# Reinstall all dependencies
uv pip install -r requirements.txt --force-reinstall

# Check for outdated packages
uv pip list --outdated
```

### Proxy Configuration

The project respects system proxy settings:
```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=socks://127.0.0.1:7891/
```

Monitor scripts automatically configure proxy settings.

## Key Functionality

### Production Service (printer_api_service.py)
- TCP server on port 9100 for POS connections
- REST API on port 5000 with endpoints:
  - `/api/health` - Service health check
  - `/api/receipts` - Get recent receipts (requires auth)
  - `/api/stats` - Service statistics
- In-memory storage with 500-receipt buffer
- Cloudflare tunnel integration for secure remote access
- Authentication via `Authorization` header

### Enhanced Version (printer_api_service_v2.py - Ready to Deploy)
- SQLite persistence for receipt history
- Connection pooling (max 50 connections)
- Thread management with proper resource limits
- Automatic database cleanup (30-day retention)

## Development Setup

### System Dependencies

On Linux (Ubuntu/Debian):
```bash
sudo apt-get install bluetooth libbluetooth-dev python3-dev
```

On macOS:
```bash
brew install bluez
```

### Python Environment Setup

**ALWAYS use uv for Python management:**

```bash
# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Create virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt

# Run the service
uv run python3 virtual_printer.py
```

### Quick Start

```bash
# Production service is managed by systemd
sudo systemctl status printer-api.service
sudo systemctl restart printer-api.service

# View logs
journalctl -u printer-api.service -f
tail -f logs/monitor.log

# Manual testing
curl -H "Authorization: smartbcg" http://localhost:5000/api/health
```

**WARNING**: Never run virtual_printer.py in production - it conflicts with printer_api_service.py on port 9100!

### Network Configuration
- TCP Port 9100: POS printer protocol (ESC/POS over TCP)
- HTTP Port 5000: REST API for monitoring and data access
- Cloudflare Tunnel: Secure remote access to API
- Authentication: Password in Authorization header

## Technical Architecture

### Design Pattern: Simple Event Loop

The application follows the principle of simplicity with a single-threaded blocking architecture:

```python
while True:
    connection = wait_for_connection()  # Blocking
    while connection.is_active():
        data = receive_data()            # Blocking
        process_and_save(data)
        send_acknowledgment()
```

**Why this design?**
- Thermal printers process one job at a time
- POS terminals expect synchronous responses
- Eliminates threading complexity
- Easy to debug and maintain

## Data Handling

- Received data is saved in binary format to preserve exact POS commands
- Files are named with timestamps for easy tracking
- Each print job creates a new file
- Files contain raw ESC/POS commands typical of thermal printers

## Testing

### Setup Verification
```bash
# Always use uv run for testing
uv run python3 test_setup.py
```

### Production Testing
1. Check service status: `sudo systemctl status printer-api.service`
2. Test health endpoint: `curl -H "Authorization: smartbcg" http://localhost:5000/api/health`
3. Check monitoring: `tail -f logs/monitor.log`
4. Send test data to port 9100: `echo "Test receipt" | nc localhost 9100`
5. View receipts: `curl -H "Authorization: smartbcg" http://localhost:5000/api/receipts`
6. Check Cloudflare tunnel: `pgrep -f cloudflared`

### Monitoring
```bash
# Terminal 1: Run the printer
./monitor.sh

# Terminal 2: Watch logs
./watch_logs.sh
```

## Common POS Commands Received

The service captures raw ESC/POS commands which typically include:
- Text formatting commands (bold, underline, font size)
- Paper cut commands
- Barcode/QR code data
- Receipt formatting

## Critical Operational Issues Resolved

### Problems Fixed (September 2025)
1. **File Descriptor Exhaustion** - 2,700+ accumulated files in /output directory
   - Solution: Implemented hourly auto_cleanup.sh cron job
   - Files older than 7 days are automatically deleted
   
2. **Daily Service Interruptions** - printer-api-restart.timer causing 2 AM downtime
   - Solution: Disabled timer, implemented smart health monitoring instead
   
3. **Port Conflicts** - virtual_printer.py and printer_api_service.py both using port 9100
   - Solution: Identified conflict, documented to never run virtual_printer.py in production
   
4. **Disk Space Exhaustion** - 5.4GB service_error.log from health check logging every 10 seconds
   - Solution: Truncated log, implemented logrotate with 100MB limit and 7-day retention
   - Changed systemd service to use journald instead of file logging
   
5. **Lack of Persistence** - In-memory storage lost on restart
   - Solution: Created printer_api_service_v2.py with SQLite persistence (ready to deploy)

### Monitoring and Maintenance

```bash
# Check service health
sudo systemctl status printer-api.service
sudo systemctl status printer-monitor.service

# View recent logs
journalctl -u printer-api.service -n 100
tail -f logs/monitor.log

# Check disk usage
du -sh /home/smartahc/smartice/printer_faker/

# Manual cleanup if needed
find output/ -name "*.bin" -mtime +7 -delete
find output/ -name "*.txt" -mtime +7 -delete

# Test API endpoints
curl -H "Authorization: smartbcg" http://localhost:5000/api/health
curl -H "Authorization: smartbcg" http://localhost:5000/api/stats
```

### Service Recovery Procedures

If service fails:
1. Check monitor logs: `tail -100 logs/monitor.log`
2. Check system journal: `journalctl -u printer-api.service -n 50`
3. Verify no port conflicts: `sudo lsof -i:9100` and `sudo lsof -i:5000`
4. Restart if needed: `sudo systemctl restart printer-api.service`
5. Monitor will auto-restart on actual failures (not on schedule)

## Best Practices for Contributors

1. **Always use uv** - Never run Python directly
2. **Keep it simple** - Avoid unnecessary abstractions
3. **Test first** - Run `test_setup.py` before making changes
4. **Document clearly** - Code should be self-explanatory
5. **Handle errors gracefully** - Fail fast with clear messages
6. **One change at a time** - Small, focused commits
7. **Monitor verbose output** - Use `./monitor.sh` during development
8. **Never run virtual_printer.py in production** - Conflicts with main service
9. **Check disk space regularly** - Monitor log and output directories
10. **Use health monitoring** - Don't schedule restarts, let monitor handle issues