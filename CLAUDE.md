# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Bluetooth virtual printer service that emulates a thermal printer to receive and capture print data from POS (Point of Sale) terminals. The service acts as a Bluetooth SPP (Serial Port Profile) server that POS machines can connect to as if it were a real printer.

## Key Functionality

- Creates a Bluetooth RFCOMM socket server
- Advertises itself as "Virtual Printer" using the SPP service UUID
- Accepts connections from POS terminals
- Receives print data and saves it to timestamped files (pos_print_YYYYMMDD_HHMMSS.txt)
- Sends ACK responses to simulate printer behavior
- Handles multiple sequential connections

## Development Setup

### Install Dependencies
```bash
pip3 install pybluez
```

Note: On macOS, you may need to install additional Bluetooth development libraries:
```bash
brew install bluez
```

On Linux (Ubuntu/Debian):
```bash
sudo apt-get install bluetooth libbluetooth-dev
```

### Running the Service
```bash
python3 bluetooth_printer.py
```

The service will start and display:
- Service name: Virtual Printer
- Port number being used
- Connection status updates

### Bluetooth Configuration
- Service UUID: 00001101-0000-1000-8000-00805F9B34FB (standard SPP UUID)
- Profile: SERIAL_PORT_PROFILE
- Protocol: RFCOMM

## Architecture Notes

The application uses a simple single-threaded blocking architecture:
1. Main server socket listens for connections
2. When a POS device connects, it enters a receive loop
3. Data is saved to timestamped files in the current directory
4. ACK byte (0x06) is sent back to acknowledge receipt
5. On disconnect, returns to listening for new connections

## Data Handling

- Received data is saved in binary format to preserve exact POS commands
- Files are named with timestamps for easy tracking
- Each print job creates a new file
- Files contain raw ESC/POS commands typical of thermal printers

## Testing

To test the service:
1. Ensure Bluetooth is enabled on your system
2. Run the service
3. From a POS terminal or testing device, scan for Bluetooth devices
4. Connect to "Virtual Printer"
5. Send print data
6. Check for created pos_print_*.txt files

## Common POS Commands Received

The service captures raw ESC/POS commands which typically include:
- Text formatting commands (bold, underline, font size)
- Paper cut commands
- Barcode/QR code data
- Receipt formatting