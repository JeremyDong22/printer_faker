# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Bluetooth virtual printer service that emulates a thermal printer to receive and capture print data from POS (Point of Sale) terminals. The service acts as a Bluetooth SPP (Serial Port Profile) server that POS machines can connect to as if it were a real printer.

## Project Architecture

### Core Components

```
printer_faker/
├── virtual_printer.py      # Main application entry point
│   ├── ESCPOSParser        # ESC/POS command parser class
│   ├── PrinterEmulator     # Bluetooth server and printer logic
│   └── PrintJobManager     # Queue management for print jobs
├── requirements.txt         # Python dependencies (pybluez2)
├── run.sh                  # Main execution script using uv
├── monitor.sh              # Verbose monitoring script
├── watch_logs.sh           # Real-time log viewer
└── test_setup.py           # Setup verification script
```

### Data Flow

1. **Bluetooth Advertisement** → Virtual Printer broadcasts as SPP device
2. **POS Connection** → POS terminal connects via RFCOMM
3. **Data Reception** → Raw ESC/POS commands received
4. **Command Parsing** → ESCPOSParser interprets commands
5. **Data Storage** → Print jobs saved to timestamped files
6. **ACK Response** → Emulator sends acknowledgment to POS

### File Output Structure

```
pos_print_YYYYMMDD_HHMMSS.txt  # Raw print data files
logs/printer_YYYYMMDD_HHMMSS.log  # Verbose operation logs
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

- Creates a Bluetooth RFCOMM socket server
- Advertises itself as "Virtual Printer" using the SPP service UUID
- Accepts connections from POS terminals
- Receives print data and saves it to timestamped files (pos_print_YYYYMMDD_HHMMSS.txt)
- Sends ACK responses to simulate printer behavior
- Handles multiple sequential connections

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
# Option 1: Use the run script (recommended)
./run.sh

# Option 2: Use monitor script for verbose output
./monitor.sh

# Option 3: Direct uv run
uv run python3 virtual_printer.py
```

The service will start and display:
- Service name: Virtual Printer
- Port number being used
- Connection status updates

### Bluetooth Configuration
- Service UUID: 00001101-0000-1000-8000-00805F9B34FB (standard SPP UUID)
- Profile: SERIAL_PORT_PROFILE
- Protocol: RFCOMM

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

### Integration Testing
1. Ensure Bluetooth is enabled: `systemctl status bluetooth`
2. Run the service: `uv run python3 virtual_printer.py`
3. From a POS terminal, scan for Bluetooth devices
4. Connect to "Virtual Printer"
5. Send print data
6. Verify files created: `ls -la pos_print_*.txt`

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

## Best Practices for Contributors

1. **Always use uv** - Never run Python directly
2. **Keep it simple** - Avoid unnecessary abstractions
3. **Test first** - Run `test_setup.py` before making changes
4. **Document clearly** - Code should be self-explanatory
5. **Handle errors gracefully** - Fail fast with clear messages
6. **One change at a time** - Small, focused commits
7. **Monitor verbose output** - Use `./monitor.sh` during development