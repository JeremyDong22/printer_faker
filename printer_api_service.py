#!/usr/bin/env python3
"""
Printer API Service - 24/7 POS Receipt Listener with Real-time API
Listens on TCP port 9100 for POS data, serves API on port 5000
"""

import socket
import threading
import datetime
import uuid
import json
import re
import logging
from logging.handlers import RotatingFileHandler
from collections import deque
from typing import Dict, Optional, Any
import queue
import time
import os

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from functools import wraps
import hashlib

# Import the existing ESC/POS parser
from virtual_printer import ESCPOSParser, PlainTextRenderer

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Authentication
API_PASSWORD = "smartbcg"
API_PASSWORD_HASH = hashlib.sha256(API_PASSWORD.encode()).hexdigest()

def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            # Check URL parameter as fallback
            auth = request.args.get('auth')
        
        if not auth:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if password matches
        if hashlib.sha256(auth.encode()).hexdigest() != API_PASSWORD_HASH:
            return jsonify({'error': 'Invalid password'}), 403
            
        return f(*args, **kwargs)
    return decorated_function

class ReceiptExtractor:
    """Extract receipt number and timestamp from plain text"""
    
    def extract_receipt_info(self, plain_text: str) -> Dict[str, str]:
        """Extract receipt number (单号) and timestamp (时间) from receipt text"""
        lines = plain_text.split('\n')
        
        receipt_no = ""
        timestamp = ""
        
        for i, line in enumerate(lines):
            # Look for receipt number (单号)
            if '单号' in line and not receipt_no:
                # Try to extract number from same line with colon or space
                match = re.search(r'单号[：:\s]+(\d+)', line)
                if match:
                    receipt_no = match.group(1)
                else:
                    # Otherwise check next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if re.match(r'^\d+$', next_line):
                            receipt_no = next_line
            
            # Look for timestamp (时间)
            if '时间' in line and not timestamp:
                # Try to extract timestamp from same line
                match = re.search(r'时间[：:]\s*([^\n]+)', line)
                if match:
                    timestamp = match.group(1).strip()
                else:
                    # Check if timestamp is on same line without colon
                    match = re.search(r'时间\s+([^\n]+)', line)
                    if match:
                        timestamp = match.group(1).strip()
                    # Otherwise check next line
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # Check if next line looks like a timestamp
                        if re.match(r'^\d{4}-\d{2}-\d{2}', next_line) or \
                           re.match(r'^\d{2}/\d{2}/\d{4}', next_line):
                            timestamp = next_line
        
        return {
            'receipt_no': receipt_no,
            'timestamp': timestamp if timestamp else datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


class PrinterAPIService:
    """Main API service for 24/7 printer listening"""
    
    def __init__(self):
        # Memory storage (circular buffer of 500 receipts)
        self.receipts = deque(maxlen=500)
        self.receipt_extractor = ReceiptExtractor()
        self.escpos_parser = ESCPOSParser()
        self.plain_renderer = PlainTextRenderer()
        
        # Real-time streaming
        self.stream_queue = queue.Queue()
        self.stream_clients = []
        
        # Statistics
        self.stats = {
            'total_received': 0,
            'parse_errors': 0,
            'start_time': datetime.datetime.now(),
            'last_receipt_time': None
        }
        
        # Setup logging
        self.setup_logging()
        
        # TCP server flag
        self.running = True
        
        self.logger.info("="*60)
        self.logger.info("🖨️  Printer API Service Starting...")
        self.logger.info("="*60)
    
    def setup_logging(self):
        """Setup rotating log file"""
        os.makedirs('logs', exist_ok=True)
        
        # Create rotating file handler
        handler = RotatingFileHandler(
            'logs/api_debug.log',
            maxBytes=10*1024*1024,  # 10MB per file
            backupCount=1  # Keep 1 backup
        )
        
        # Set format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Setup logger
        self.logger = logging.getLogger('printer_api')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        
        # Also log to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def tcp_server(self, host='0.0.0.0', port=9100):
        """TCP server listening for printer data on port 9100"""
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((host, port))
            server_sock.listen(5)
            server_sock.settimeout(1.0)  # Allow checking self.running
            
            self.logger.info(f"📡 TCP Server listening on {host}:{port}")
            print(f"✅ TCP Server ready on port {port}")
            
            while self.running:
                try:
                    client_sock, client_addr = server_sock.accept()
                    # Handle connection in thread
                    thread = threading.Thread(
                        target=self.handle_printer_connection,
                        args=(client_sock, client_addr)
                    )
                    thread.daemon = True
                    thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"TCP Server error: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to start TCP server on port {port}: {e}")
            print(f"❌ Could not bind to port {port}. Is another service using it?")
        finally:
            server_sock.close()
    
    def handle_printer_connection(self, client_sock, client_addr):
        """Handle incoming printer data - using exact logic from virtual_printer.py"""
        # Don't log every connection - too noisy with POS status checks
        
        session_data = []
        last_data_time = time.time()
        idle_timeout = 30.0  # 30 seconds idle timeout like virtual_printer
        is_initialization = False
        
        try:
            client_sock.settimeout(1.0)  # 1 second socket timeout
            
            while True:
                try:
                    data = client_sock.recv(1024)
                    if not data:
                        # Check if really disconnected
                        if time.time() - last_data_time > idle_timeout:
                            break
                        continue
                    
                    last_data_time = time.time()
                    session_data.append(data)
                    
                    # Check for initialization sequence
                    if b'\x1b\x21' in data or b'\x1c\x21' in data or b'\x1d\x21' in data:
                        is_initialization = True
                    
                    # Generate smart response (handshaking)
                    response = self.get_response(data, is_initialization)
                    if response:
                        client_sock.send(response)
                        
                except socket.timeout:
                    # Don't disconnect immediately on timeout
                    if time.time() - last_data_time > idle_timeout:
                        break
                    continue
                except ConnectionResetError:
                    # POS disconnected (normal)
                    break
                    
        except ConnectionResetError:
            pass  # Normal disconnect
        except Exception as e:
            if "Connection reset by peer" not in str(e):
                self.logger.error(f"Connection error: {e}")
        finally:
            client_sock.close()
            
            # Process accumulated data (like virtual_printer does)
            if session_data:
                complete_data = b''.join(session_data)
                # Only log if it's actual receipt data, not status checks
                if len(complete_data) > 50:
                    self.logger.info(f"Session complete: {len(complete_data)} bytes from {client_addr[0]}")
                
                # Check if this is actual print content
                has_text = False
                has_cut = b'\x1D\x56' in complete_data  # Cut command
                has_init = b'\x1B\x40' in complete_data  # Init command
                
                # If has init or cut command, or data is large enough
                if (len(complete_data) > 50) or has_cut or has_init:
                    has_text = True
                    
                if has_text:
                    # Parse ESC/POS to plain text
                    try:
                        commands = self.escpos_parser.parse(complete_data)
                        plain_text = self.plain_renderer.render(commands)
                        
                        # Extract receipt info
                        receipt_info = self.receipt_extractor.extract_receipt_info(plain_text)
                        
                        # Create receipt object
                        receipt = {
                            'id': str(uuid.uuid4()),
                            'receipt_no': receipt_info['receipt_no'],
                            'timestamp': receipt_info['timestamp'],
                            'plain_text': plain_text
                        }
                        
                        # Store in memory
                        self.receipts.append(receipt)
                        
                        # Update stats
                        self.stats['total_received'] += 1
                        self.stats['last_receipt_time'] = datetime.datetime.now().isoformat()
                        
                        # Log success
                        self.logger.info(f"✅ Receipt processed - No: {receipt['receipt_no'] or 'N/A'}, ID: {receipt['id'][:8]}")
                        print(f"\n{'='*60}")
                        print(f"📋 Receipt #{self.stats['total_received']}")
                        print(f"📱 From: {client_addr[0]}")
                        print(f"📦 Size: {len(complete_data)} bytes")
                        print(f"🔢 Receipt No: {receipt['receipt_no'] or 'N/A'}")
                        print(f"="*60)
                        
                        # Send to real-time stream
                        self.broadcast_receipt(receipt)
                        
                    except Exception as e:
                        self.logger.error(f"Parse error: {e}")
                        self.stats['parse_errors'] += 1
                        
                        # Store with empty fields on error
                        receipt = {
                            'id': str(uuid.uuid4()),
                            'receipt_no': '',
                            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'plain_text': f"[Parse Error: {str(e)}]"
                        }
                        self.receipts.append(receipt)
                        print(f"⚠️ Parse error, stored with empty receipt_no")
                else:
                    # This is just a status query, ignore
                    self.logger.debug(f"Status query: {len(complete_data)} bytes")
    
    def get_response(self, data, is_initialization=False):
        """Generate response for ESC/POS commands (from virtual_printer.py)"""
        i = 0
        responses = []
        has_status_query = False
        
        while i < len(data):
            # DLE EOT status query
            if i + 2 < len(data) and data[i:i+2] == b'\x10\x04':
                cmd_type = data[i+2] if i+2 < len(data) else 0
                has_status_query = True
                if cmd_type == 1:
                    responses.append(b'\x16')  # Printer online
                elif cmd_type == 2:
                    responses.append(b'\x12')  # Paper OK
                elif cmd_type == 3:
                    responses.append(b'\x12')  # No error
                elif cmd_type == 4:
                    responses.append(b'\x12')  # Paper present
                else:
                    responses.append(b'\x16')
                i += 3
            else:
                i += 1
        
        # Return responses for status queries
        if responses:
            return b''.join(responses)
        
        # ACK for initialization
        if is_initialization:
            return b'\x06'
            
        # ACK for other data
        if len(data) > 0:
            return b'\x06'
            
        return None
    
    def broadcast_receipt(self, receipt):
        """Send receipt to all SSE stream clients"""
        # Add to stream queue
        self.stream_queue.put(receipt)
        
        # Notify all connected clients
        for client_queue in self.stream_clients:
            try:
                client_queue.put(receipt)
            except:
                pass
    
    def check_log_rotation(self):
        """Check if we need to rotate logs (every 2000 receipts)"""
        if self.stats['total_received'] % 2000 == 0 and self.stats['total_received'] > 0:
            self.logger.info(f"Log rotation at {self.stats['total_received']} receipts")
            # The RotatingFileHandler will handle this automatically based on size


# Initialize service
service = PrinterAPIService()

# Flask API Routes

@app.route('/api/health', methods=['GET'])
@require_auth
def health_check():
    """Health check endpoint"""
    uptime = (datetime.datetime.now() - service.stats['start_time']).total_seconds()
    
    return jsonify({
        'status': 'ok',
        'receipts_count': len(service.receipts),
        'total_received': service.stats['total_received'],
        'parse_errors': service.stats['parse_errors'],
        'uptime_seconds': int(uptime),
        'last_receipt': service.stats['last_receipt_time']
    })

@app.route('/api/recent', methods=['GET'])
@require_auth
def get_recent():
    """Get last 10 receipts for testing"""
    recent = list(service.receipts)[-10:]
    return jsonify(recent)

@app.route('/api/receipts', methods=['GET'])
@require_auth
def get_all_receipts():
    """Get all stored receipts (up to 500)"""
    return jsonify(list(service.receipts))

@app.route('/api/search', methods=['GET'])
@require_auth
def search_receipts():
    """Search receipts by receipt number"""
    receipt_no = request.args.get('no', '')
    
    if not receipt_no:
        return jsonify({'error': 'Please provide receipt number with ?no=XXX'}), 400
    
    results = [
        r for r in service.receipts 
        if r['receipt_no'] == receipt_no
    ]
    
    return jsonify(results)

@app.route('/api/stream', methods=['GET'])
@require_auth
def stream_receipts():
    """Server-Sent Events endpoint for real-time receipts"""
    def generate():
        # Create a queue for this client
        client_queue = queue.Queue()
        service.stream_clients.append(client_queue)
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Stream connected'})}\n\n"
            
            # Keep connection alive and send receipts
            while True:
                try:
                    # Wait for new receipt (with timeout for keepalive)
                    receipt = client_queue.get(timeout=30)
                    yield f"data: {json.dumps(receipt)}\n\n"
                except queue.Empty:
                    # Send keepalive
                    yield f": keepalive\n\n"
                    
        finally:
            # Remove client queue on disconnect
            if client_queue in service.stream_clients:
                service.stream_clients.remove(client_queue)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )

@app.route('/')
def index():
    """Simple web interface for testing"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Printer API Service</title>
        <style>
            body { 
                font-family: 'Courier New', monospace; 
                max-width: 1200px; 
                margin: 50px auto; 
                padding: 20px;
                background: #1a1a1a;
                color: #0f0;
            }
            h1 { color: #0f0; text-shadow: 0 0 10px #0f0; }
            .status { 
                background: #000; 
                padding: 15px; 
                border: 1px solid #0f0;
                margin: 20px 0;
                border-radius: 5px;
            }
            .endpoint { 
                background: #0a0a0a; 
                padding: 10px; 
                margin: 10px 0; 
                border-left: 3px solid #0f0;
            }
            code { 
                background: #000; 
                padding: 2px 5px; 
                color: #0ff;
            }
            button {
                background: #000;
                color: #0f0;
                border: 1px solid #0f0;
                padding: 10px 20px;
                cursor: pointer;
                margin: 5px;
            }
            button:hover {
                background: #0f0;
                color: #000;
            }
            #stream-output {
                background: #000;
                border: 1px solid #0f0;
                padding: 10px;
                height: 300px;
                overflow-y: auto;
                margin: 20px 0;
                font-size: 12px;
            }
            .receipt-item {
                border-bottom: 1px solid #030;
                padding: 5px 0;
            }
        </style>
    </head>
    <body>
        <h1>🖨️ Printer API Service</h1>
        <div class="status" id="status">
            Loading status...
        </div>
        
        <h2>API Endpoints:</h2>
        <div class="endpoint">
            <strong>GET /api/health</strong> - Service health and statistics
        </div>
        <div class="endpoint">
            <strong>GET /api/recent</strong> - Last 10 receipts (for testing)
        </div>
        <div class="endpoint">
            <strong>GET /api/receipts</strong> - All stored receipts (max 500)
        </div>
        <div class="endpoint">
            <strong>GET /api/search?no=XXX</strong> - Search by receipt number
        </div>
        <div class="endpoint">
            <strong>GET /api/stream</strong> - Real-time SSE stream
        </div>
        
        <h3>Test Controls:</h3>
        <button onclick="testHealth()">Test Health</button>
        <button onclick="testRecent()">Get Recent</button>
        <button onclick="toggleStream()" id="stream-btn">Start Stream</button>
        
        <h3>Real-time Stream Output:</h3>
        <div id="stream-output"></div>
        
        <script>
            let eventSource = null;
            
            async function testHealth() {
                const res = await fetch('/api/health');
                const data = await res.json();
                document.getElementById('status').innerHTML = 
                    '<h3>Service Status: <span style="color: #0f0;">● Online</span></h3>' +
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            }
            
            async function testRecent() {
                const res = await fetch('/api/recent');
                const data = await res.json();
                alert('Recent receipts (check console)');
                console.log(data);
            }
            
            function toggleStream() {
                const btn = document.getElementById('stream-btn');
                const output = document.getElementById('stream-output');
                
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                    btn.textContent = 'Start Stream';
                    output.innerHTML += '<div style="color: #f00;">Stream disconnected</div>';
                } else {
                    eventSource = new EventSource('/api/stream');
                    btn.textContent = 'Stop Stream';
                    
                    eventSource.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        if (data.type === 'connected') {
                            output.innerHTML += '<div style="color: #0ff;">Stream connected!</div>';
                        } else {
                            const item = document.createElement('div');
                            item.className = 'receipt-item';
                            item.innerHTML = 
                                'Receipt No: ' + (data.receipt_no || 'N/A') + 
                                ' | Time: ' + data.timestamp + 
                                ' | ID: ' + data.id.substring(0, 8);
                            output.appendChild(item);
                            output.scrollTop = output.scrollHeight;
                        }
                    };
                    
                    eventSource.onerror = () => {
                        output.innerHTML += '<div style="color: #f00;">Stream error</div>';
                    };
                }
            }
            
            // Load status on page load
            testHealth();
        </script>
    </body>
    </html>
    """
    return html


def main():
    """Main entry point"""
    # Start TCP server in background thread
    tcp_thread = threading.Thread(target=service.tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()
    
    # Wait a moment for TCP to start
    time.sleep(1)
    
    print("\n" + "="*60)
    print("🌐 Printer API Service Ready")
    print("="*60)
    print("📍 Local Access:")
    print("   http://localhost:5000")
    print("\n📡 API Endpoints:")
    print("   /api/health  - Service health")
    print("   /api/recent  - Last 10 receipts") 
    print("   /api/receipts - All receipts")
    print("   /api/search?no=XXX - Search by receipt number")
    print("   /api/stream  - Real-time SSE stream")
    print("\n🌍 For Internet Access:")
    print("   Run in another terminal:")
    print("   cloudflared tunnel --url http://localhost:5000")
    print("="*60)
    print("\n✅ Service running! Press Ctrl+C to stop.\n")
    
    # Start Flask API server
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)


if __name__ == '__main__':
    main()