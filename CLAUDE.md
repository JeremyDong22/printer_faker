# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **24/7 Restaurant Order Management System** that captures and processes receipt data from POS terminals for direct integration with Supabase (no longer uses Cloudflare Workers). The system provides a reliable TCP listener on port 9100 and REST API on port 5000 for restaurant kitchen and order management with local order processing.

**Critical for Operations**: This service must maintain 99%+ uptime as it handles all restaurant orders and kitchen coordination.

## Project Architecture

### Core Components

```
printer_faker/
├── printer_api_service.py  # DEPRECATED - Use V2 instead
├── printer_api_service_v2.py # PRODUCTION VERSION - SQLite persistence + Supabase integration
│   ├── ESCPOSParser        # ESC/POS command parser
│   ├── ReceiptExtractor    # Extract receipt number and timestamp  
│   ├── PrinterAPIService   # TCP server on port 9100 (singleton in master process)
│   ├── Flask API           # REST API on port 5000 (no SSE endpoints)
│   └── OrderProcessor      # Local Supabase integration (replaces Cloudflare Workers)
├── order_processor.py      # Supabase order processing logic
│   ├── Parse receipts      # Customer orders (客单) and kitchen slips (制作分单)
│   ├── Station mapping     # Chinese names to UUIDs
│   └── Direct DB writes    # Using Supabase Python SDK with RLS
├── virtual_printer.py      # DEPRECATED - DO NOT RUN (conflicts on port 9100)
├── dashboard.py            # Enhanced monitoring dashboard
│   ├── Live updates        # 5-second polling (no SSE)
│   └── Order details       # Click to view full receipt
└── requirements.txt        # Python dependencies (Flask, supabase, httpx, gunicorn)
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
4. **Data Storage** → Receipts stored in SQLite with 30-day retention
5. **Order Processing** → OrderProcessor analyzes receipts locally
6. **Supabase Upload** → Direct database writes using Python SDK with RLS
7. **API Access** → REST API on port 5000 provides receipt data (polling-based)

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

### Production Service (printer_api_service_v2.py - IN PRODUCTION)
- TCP server on port 9100 for POS connections (singleton in master process)
- REST API on port 5000 with endpoints:
  - `/api/health` - Service health check
  - `/api/receipts` - Get recent receipts (requires auth)
  - `/api/recent` - Get recent receipts with limit
  - `/api/stats` - Service statistics
  - `/` - Dashboard with live updates
- SQLite persistence for receipt history (30-day retention)
- Direct Supabase integration:
  - OrderProcessor analyzes receipts locally
  - Customer orders (客单) create order records
  - Kitchen slips (制作分单) update station assignments
  - Multi-line dish name parsing support
- Gunicorn WSGI server with gthread workers
- Thread pool limited to ~14 threads total
- Authentication via `Authorization` header

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

## Station and Dish Mappings (Updated 2025-09-06)

### ✅ VERIFIED: Only 5 Real Stations Exist in POS
```python
STATION_MAP = {
    '荤菜': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',  # Meat - 18 dishes
    '素菜': 'c3d4e5f6-a7b8-9012-cdef-345678901234',  # Vegetable - 12 dishes
    '酒水': 'd4e5f6a7-b8c9-0123-defa-456789012345',  # Beverages - 20 dishes
    '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',  # Snacks - 13 dishes
    '凉菜': '581b60be-428a-4673-9147-2c197478392b',  # Cold dishes - 3 dishes (UUID FIXED)
    # WARNING: 主食, 汤品, 其他 DO NOT EXIST in POS - DO NOT ADD!
}
```

### POS → SQLite Mapping: PERFECT ✅
- **66 unique dishes** from 1,089 receipts analyzed
- **Zero parsing errors** detected
- **Zero duplicates** - each dish maps to exactly one station
- **100% station extraction** success rate

### Key Fixes Applied (2025-09-06)
1. **凉菜 UUID Fixed**: Was duplicate of 小吃, now unique `581b60be-428a-4673-9147-2c197478392b`
2. **Cold Dishes Corrected**: 贵州非遗丝娃娃, 野佐料擂椒皮蛋, 贵阳非遗脆三丁 moved to 凉菜
3. **Test Data Removed**: All test dishes deleted from production
4. **Malformed Entries Fixed**: Partial dishes like "胸口）" removed

## Critical Operational Issues Resolved

### Problems Fixed (September 20, 2025)
1. **Duplicate Key Crash Loop** - Service crashing on duplicate receipt processing
   - Issue: POS terminal retries failed receipts every 5 seconds, causing duplicate key violations in Supabase
   - Error: `duplicate key value violates unique constraint "idx_order_dishes_unique"` and `"unique_receipt_version"`
   - Impact: Service crashed every time a duplicate receipt was processed, creating infinite crash-restart loop
   - Root Cause: No error handling for database constraint violations - service crashed instead of gracefully handling duplicates
   - Solution: Added comprehensive duplicate key handling in order_processor.py:
     - Kitchen slip processing (lines 653-667): Catch duplicates, log warning, return success status
     - Customer order processing (lines 710-726): Handle order duplicates gracefully
     - Customer dish processing (lines 747-755): Skip duplicate dishes with warning
   - Result: **CRASH LOOP ELIMINATED** - Service now stable with POS retries
   - Files modified: order_processor.py (2025-09-20 17:28 - Added: duplicate key handling in order_processor.py with timestamp)

2. **Log Size Explosion Prevention** - Confirmed log rotation working optimally
   - Previous Issue: 5.4GB log files causing disk space exhaustion
   - Current Status: Largest file only 3.8MB, proper compression and 7-day retention active
   - Logrotate Configuration: `/etc/logrotate.d/printer-api` working correctly
   - Daily rotation with 100MB limit and compression prevents future disk issues

### Problems Fixed (September 9, 2025)
1. **Combo Meal Parsing** - Kitchen slips with combo meals failing
   - Issue: Long combo names like "美团团购-入野·双人放松Chill套餐" split across lines
   - Error: Duplicate key violations when saving combo names as dishes
   - Solution: Skip combo headers, only process actual dish sub-items (with '-' prefix)
   - Impact: Kitchen stations now see only actual dishes, not marketing names
   - Branch: fix/combo-meal-parsing pushed to GitHub

2. **XCloudSDK CPU Hog** - Runaway process consuming 100% CPU
   - Issue: XCloudSDKDemo_CLI stuck in infinite loop trying to connect to non-existent IP camera
   - Impact: Consuming full CPU core for 10+ days (14,255 CPU hours!)
   - Solution: Killed process, disabled binary, removed log file
   - Prevention: Renamed binary to .disabled and removed execute permissions

### Problems Fixed (September 7, 2025)
1. **Timestamp Parsing Error** - Customer orders failing to save to Supabase
   - Issue: Timestamps had Chinese prefix "打印时间: 2025-09-06 22:24:38"
   - Error: `invalid input syntax for type timestamp with time zone`
   - Solution: Added `parse_timestamp()` method in order_processor.py (lines 304-336)
   - Impact: ALL customer orders now save correctly, enabling table view feature
   - Files modified: order_processor.py line 500

2. **Return Dish Handling** - No support for cancelled/returned dishes (退菜)
   - Issue: Return slips were processed as regular orders or ignored
   - Solution: Complete return dish workflow implementation:
     - Extended Dish dataclass with `is_return` field (lines 22-28)
     - Added `is_return_slip()` and `extract_return_reason()` detection methods (lines 175-182)
     - Updated `parse_kitchen_slip_dishes()` to detect "(退)" prefix (lines 270-302)
     - Created `process_return_slip()` method for complete workflow (lines 435-529)
     - Modified main processing flow to check for return slips (lines 417-418)
   - Impact: Kitchen won't prepare returned dishes, accurate billing with audit trail

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
   - Solution: Created printer_api_service_v2.py with SQLite persistence (now in production)

6. **SSE Thread Explosion** - Each SSE connection created permanent threads
   - Solution: Removed SSE endpoints completely, dashboard uses 5-second polling
   
7. **Cloudflare Workers Overhead** - Unnecessary complexity for single-location setup
   - Solution: Eliminated Workers/DO, process orders locally with direct Supabase writes
   
8. **Multi-line Dish Names** - Long dish names split across lines in receipts
   - Solution: Implemented parenthesis-aware multi-line parsing

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

**Note: As of September 20, 2025, the main crash loop issue has been fixed. Service should remain stable even with POS retries.**

If service fails:
1. Check monitor logs: `tail -100 logs/monitor.log`
2. Check system journal: `journalctl -u printer-api.service -n 50`
3. Verify no port conflicts: `sudo lsof -i:9100` and `sudo lsof -i:5000`
4. Check for duplicate key errors in logs: `tail -50 logs/printer_api_error.log`
5. Restart if needed: `sudo systemctl restart printer-api.service`
6. Monitor will auto-restart on actual failures (not on schedule)

**Common Issues (Post-Fix):**
- **POS Retries**: Normal behavior - POS connects every 5 seconds, service handles gracefully
- **Duplicate Warnings**: Expected - duplicate receipts logged as warnings, service continues
- **Supabase Errors**: Check network connectivity and API keys if processing fails

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