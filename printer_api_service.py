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
import struct
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import hashlib

# Import the existing ESC/POS parser
from virtual_printer import ESCPOSParser, PlainTextRenderer

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Rate limiting - generous limits for local monitoring
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10000 per hour", "50000 per day"],  # Much higher for monitoring
    storage_uri="memory://"
)

# Authentication - Use environment variable or strong default
API_PASSWORD = os.environ.get('PRINTER_API_PASSWORD', 'DWiVVeSQtM8/S8uTlQzcg6rlJQg/H6SSHxYNnll56zo=')
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
            # Log failed attempts
            logger.warning(f"Failed auth attempt from {get_remote_address()}")
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
        
        # No threading needed - handle connections sequentially like a real printer
        
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
                    
                    # Set aggressive timeout to prevent hanging
                    client_sock.settimeout(5.0)  # 5 second timeout for all operations
                    
                    # Handle connection directly - no threads at all
                    try:
                        self.handle_printer_connection(client_sock, client_addr)
                    except socket.timeout:
                        self.logger.warning(f"Connection from {client_addr} timed out")
                    except Exception as e:
                        self.logger.error(f"Error handling connection from {client_addr}: {e}")
                    finally:
                        # Always close the connection after handling
                        try:
                            client_sock.shutdown(socket.SHUT_RDWR)
                        except:
                            pass
                        try:
                            client_sock.close()
                        except:
                            pass
                        
                except socket.timeout:
                    continue
                except OSError as e:
                    if e.errno == 24:  # Too many open files
                        self.logger.error(f"File descriptor limit reached! Sleeping...")
                        time.sleep(5)  # Wait 5 seconds before retrying
                    else:
                        self.logger.error(f"TCP Server error: {e}")
                        time.sleep(1)  # Brief pause on other errors
                except Exception as e:
                    self.logger.error(f"TCP Server error: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to start TCP server on port {port}: {e}")
            print(f"❌ Could not bind to port {port}. Is another service using it?")
        finally:
            server_sock.close()
    
    def handle_printer_connection(self, client_sock, client_addr):
        """Handle incoming printer data - using exact logic from virtual_printer.py"""
        # Don't log every connection - too noisy with POS status checks
        
        # Set socket options to prevent file descriptor leaks
        client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Don't use SO_LINGER - let the OS handle proper TCP closure
        # client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 
        #                        struct.pack('ii', 1, 0))  # This can cause CLOSE-WAIT
        
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
                        # Empty data means connection closed by peer
                        break  # Exit immediately, don't wait for timeout
                        # Remove the sleep and timeout check here
                    
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
                    # Check if we've been idle too long
                    if time.time() - last_data_time > idle_timeout:
                        break
                    # No sleep needed - timeout already provides delay
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
            try:
                client_sock.shutdown(socket.SHUT_RDWR)
            except:
                pass  # Socket may already be closed
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
    """Enhanced web dashboard for monitoring"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Printer Monitor Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 { 
                color: white;
                font-size: 2.5rem;
                margin-bottom: 30px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }
            .dashboard {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .card h3 {
                margin-bottom: 15px;
                color: #667eea;
            }
            .stat-value {
                font-size: 2rem;
                font-weight: bold;
                color: #333;
            }
            .stat-label {
                color: #666;
                font-size: 0.9rem;
                margin-top: 5px;
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
                animation: pulse 2s infinite;
            }
            .status-online { background: #48bb78; }
            .status-offline { background: #f56565; }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            .receipt-list {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                max-height: 80vh;  /* 80% of viewport height */
                overflow-y: auto;
                scroll-behavior: smooth;
            }
            .receipt-item {
                padding: 15px;
                border-bottom: 1px solid #e2e8f0;
                transition: all 0.2s;
                cursor: pointer;
                position: relative;
            }
            .receipt-item:hover {
                background: #f7fafc;
                transform: translateX(5px);
                box-shadow: -2px 0 0 0 #667eea;
            }
            .receipt-item::after {
                content: '→';
                position: absolute;
                right: 15px;
                top: 50%;
                transform: translateY(-50%);
                color: #cbd5e0;
                font-size: 1.2rem;
                opacity: 0;
                transition: opacity 0.2s;
            }
            .receipt-item:hover::after {
                opacity: 1;
            }
            .receipt-item.new {
                animation: highlight 1s;
            }
            @keyframes highlight {
                0% { background: #bee3f8; }
                100% { background: transparent; }
            }
            .receipt-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
            }
            .receipt-no {
                font-weight: bold;
                color: #667eea;
            }
            .receipt-time {
                color: #718096;
                font-size: 0.9rem;
            }
            .receipt-preview {
                color: #4a5568;
                font-size: 0.85rem;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .controls {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            button {
                background: white;
                color: #667eea;
                border: 2px solid #667eea;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s;
            }
            button:hover {
                background: #667eea;
                color: white;
            }
            button.active {
                background: #667eea;
                color: white;
            }
            .search-box {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            input {
                flex: 1;
                padding: 10px;
                border: 2px solid #e2e8f0;
                border-radius: 5px;
                font-size: 16px;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            .receipt-detail {
                display: none;
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-top: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                border: 2px solid #667eea;
                animation: slideIn 0.3s ease-out;
            }
            .receipt-detail.show {
                display: block;
            }
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            .receipt-content {
                background: #f7fafc;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                white-space: pre-wrap;
                word-break: break-word;
                max-height: 400px;
                overflow-y: auto;
                font-size: 0.9rem;
            }
            .close-detail {
                float: right;
                cursor: pointer;
                font-size: 1.5rem;
                color: #718096;
            }
            .close-detail:hover {
                color: #2d3748;
            }
            .auth-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
            }
            .auth-modal.show {
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .auth-form {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                width: 90%;
                max-width: 400px;
            }
            .auth-form h2 {
                margin-bottom: 20px;
                color: #667eea;
            }
            .auth-form input {
                width: 100%;
                margin-bottom: 15px;
            }
            .auth-form button {
                width: 100%;
            }
            .error-message {
                color: #f56565;
                margin-top: 10px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🖨️ Printer Monitor Dashboard</h1>
            
            <div class="dashboard">
                <div class="card">
                    <h3>Service Status</h3>
                    <div>
                        <span class="status-indicator status-online"></span>
                        <span id="status-text">Online</span>
                    </div>
                    <div class="stat-label" id="uptime">Uptime: Loading...</div>
                </div>
                
                <div class="card">
                    <h3>Total Receipts</h3>
                    <div class="stat-value" id="total-receipts">0</div>
                    <div class="stat-label">Processed Today</div>
                </div>
                
                <div class="card">
                    <h3>Last Receipt</h3>
                    <div id="last-receipt-time">-</div>
                    <div class="stat-label">Receipt Time</div>
                </div>
                
                <div class="card">
                    <h3>Parse Errors</h3>
                    <div class="stat-value" id="parse-errors">0</div>
                    <div class="stat-label">Total Errors</div>
                </div>
            </div>
            
            <div class="controls">
                <button onclick="toggleStream()" id="stream-btn">Start Live Stream</button>
                <button onclick="loadRecent()">Load Recent</button>
                <button onclick="clearDisplay()">Clear Display</button>
                <button onclick="exportReceipts()">Export All</button>
                <button onclick="logout()" style="background: #f56565; border-color: #f56565;">Logout</button>
            </div>
            
            <div class="search-box">
                <input type="text" id="search-input" placeholder="Search by receipt number..." onkeypress="if(event.key==='Enter') searchReceipt()">
                <button onclick="searchReceipt()">Search</button>
            </div>
            
            <div class="receipt-list" id="receipt-list">
                <h3 style="margin-bottom: 15px;">Recent Receipts</h3>
                <div id="receipts-container"></div>
            </div>
            
            <div class="receipt-detail" id="receipt-detail">
                <span class="close-detail" onclick="closeDetail()">&times;</span>
                <h3>Receipt Details</h3>
                <div id="detail-info"></div>
                <div class="receipt-content" id="detail-content"></div>
            </div>
        </div>
        
        <div class="auth-modal" id="auth-modal">
            <div class="auth-form">
                <h2>🔐 Authentication Required</h2>
                <p style="margin-bottom: 20px; color: #718096;">Please enter the API password to access the dashboard</p>
                <input type="password" id="auth-password" placeholder="Hint: smartbcg" onkeypress="if(event.key==='Enter') authenticate()">
                <button onclick="authenticate()">Login</button>
                <div class="error-message" id="auth-error">Invalid password. Please try again.</div>
            </div>
        </div>
        
        <script>
            let eventSource = null;
            let receipts = [];
            let apiPassword = localStorage.getItem('apiPassword') || '';
            let isAuthenticated = false;
            
            async function updateStatus() {
                if (!isAuthenticated) return;
                
                try {
                    const res = await fetch('/api/health', {
                        headers: { 'Authorization': apiPassword }
                    });
                    if (!res.ok) {
                        isAuthenticated = false;
                        showAuthPrompt();
                        return;
                    }
                    const data = await res.json();
                    
                    document.getElementById('total-receipts').textContent = data.total_received || 0;
                    document.getElementById('parse-errors').textContent = data.parse_errors || 0;
                    
                    if (data.last_receipt) {
                        const lastTime = new Date(data.last_receipt);
                        document.getElementById('last-receipt-time').textContent = lastTime.toLocaleTimeString();
                    }
                    
                    const uptime = data.uptime_seconds || 0;
                    const hours = Math.floor(uptime / 3600);
                    const minutes = Math.floor((uptime % 3600) / 60);
                    document.getElementById('uptime').textContent = `Uptime: ${hours}h ${minutes}m`;
                } catch (error) {
                    console.error('Failed to update status:', error);
                }
            }
            
            async function loadRecent() {
                if (!isAuthenticated) return;
                
                try {
                    const res = await fetch('/api/recent', {
                        headers: { 'Authorization': apiPassword }
                    });
                    if (!res.ok) {
                        isAuthenticated = false;
                        showAuthPrompt();
                        return;
                    }
                    const data = await res.json();
                    receipts = data;
                    displayReceipts(data);
                } catch (error) {
                    console.error('Failed to load recent:', error);
                }
            }
            
            function displayReceipts(receiptList) {
                const container = document.getElementById('receipts-container');
                container.innerHTML = '';
                
                receiptList.slice().reverse().forEach(receipt => {
                    const item = createReceiptElement(receipt);
                    container.appendChild(item);
                });
            }
            
            function createReceiptElement(receipt, isNew = false) {
                const item = document.createElement('div');
                item.className = 'receipt-item' + (isNew ? ' new' : '');
                item.style.cursor = 'pointer';
                item.onclick = () => showDetail(receipt);
                
                const preview = receipt.plain_text ? 
                    receipt.plain_text.split('\\n')[0].substring(0, 100) : 
                    '[Empty Receipt]';
                
                item.innerHTML = `
                    <div class="receipt-header">
                        <span class="receipt-no">Receipt #${receipt.receipt_no || 'N/A'}</span>
                        <span class="receipt-time">${receipt.timestamp}</span>
                    </div>
                    <div class="receipt-preview">${preview}...</div>
                `;
                
                return item;
            }
            
            function showDetail(receipt) {
                const detail = document.getElementById('receipt-detail');
                const info = document.getElementById('detail-info');
                const content = document.getElementById('detail-content');
                
                // Format the receipt info
                info.innerHTML = `
                    <div style="display: grid; grid-template-columns: auto 1fr; gap: 10px; margin-bottom: 15px;">
                        <strong>Receipt Number:</strong> <span style="color: #667eea; font-size: 1.1em;">${receipt.receipt_no || 'N/A'}</span>
                        <strong>Timestamp:</strong> <span>${receipt.timestamp}</span>
                        <strong>Receipt ID:</strong> <span style="font-family: monospace; font-size: 0.9em;">${receipt.id}</span>
                    </div>
                `;
                
                // Display the full receipt content
                content.textContent = receipt.plain_text || '[No content available]';
                
                // Show the detail panel with animation
                detail.classList.add('show');
                detail.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            
            function closeDetail() {
                document.getElementById('receipt-detail').classList.remove('show');
            }
            
            function toggleStream() {
                if (!isAuthenticated && !eventSource) return;
                
                const btn = document.getElementById('stream-btn');
                
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                    btn.textContent = 'Start Live Stream';
                    btn.classList.remove('active');
                } else {
                    eventSource = new EventSource('/api/stream?auth=' + encodeURIComponent(apiPassword));
                    btn.textContent = 'Stop Live Stream';
                    btn.classList.add('active');
                    
                    eventSource.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        if (data.type !== 'connected') {
                            const container = document.getElementById('receipts-container');
                            const item = createReceiptElement(data, true);
                            container.insertBefore(item, container.firstChild);
                            
                            // Update stats
                            updateStatus();
                            
                            // Keep only last 50 items in view
                            while (container.children.length > 50) {
                                container.removeChild(container.lastChild);
                            }
                        }
                    };
                    
                    eventSource.onerror = () => {
                        console.error('Stream error');
                    };
                }
            }
            
            function clearDisplay() {
                document.getElementById('receipts-container').innerHTML = '';
            }
            
            async function searchReceipt() {
                if (!isAuthenticated) return;
                
                const searchTerm = document.getElementById('search-input').value;
                if (!searchTerm) return;
                
                try {
                    const res = await fetch(`/api/search?no=${encodeURIComponent(searchTerm)}`, {
                        headers: { 'Authorization': apiPassword }
                    });
                    if (!res.ok) {
                        isAuthenticated = false;
                        showAuthPrompt();
                        return;
                    }
                    const data = await res.json();
                    
                    if (data.length > 0) {
                        displayReceipts(data);
                    } else {
                        alert('No receipts found with that number');
                    }
                } catch (error) {
                    console.error('Search failed:', error);
                }
            }
            
            async function exportReceipts() {
                if (!isAuthenticated) return;
                
                try {
                    const res = await fetch('/api/receipts', {
                        headers: { 'Authorization': apiPassword }
                    });
                    if (!res.ok) {
                        isAuthenticated = false;
                        showAuthPrompt();
                        return;
                    }
                    const data = await res.json();
                    
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `receipts_${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                } catch (error) {
                    console.error('Export failed:', error);
                }
            }
            
            function showAuthPrompt() {
                document.getElementById('auth-modal').classList.add('show');
                document.getElementById('auth-password').focus();
            }
            
            async function authenticate() {
                const password = document.getElementById('auth-password').value;
                if (!password) return;
                
                // Test the password
                try {
                    const res = await fetch('/api/health', {
                        headers: { 'Authorization': password }
                    });
                    
                    if (res.ok) {
                        // Password is correct
                        apiPassword = password;
                        isAuthenticated = true;
                        localStorage.setItem('apiPassword', password);
                        document.getElementById('auth-modal').classList.remove('show');
                        document.getElementById('auth-error').style.display = 'none';
                        
                        // Start the dashboard
                        updateStatus();
                        loadRecent();
                        setInterval(updateStatus, 10000);
                    } else {
                        // Wrong password
                        document.getElementById('auth-error').style.display = 'block';
                        document.getElementById('auth-password').value = '';
                    }
                } catch (error) {
                    console.error('Auth error:', error);
                    document.getElementById('auth-error').style.display = 'block';
                }
            }
            
            function logout() {
                localStorage.removeItem('apiPassword');
                apiPassword = '';
                isAuthenticated = false;
                location.reload();
            }
            
            // Initialize - always verify the password works
            async function initialize() {
                if (apiPassword) {
                    // Test if stored password still works
                    try {
                        const res = await fetch('/api/health', {
                            headers: { 'Authorization': apiPassword }
                        });
                        if (res.ok) {
                            // Password is valid, start the dashboard
                            isAuthenticated = true;
                            updateStatus();
                            loadRecent();
                            setInterval(updateStatus, 10000);
                        } else {
                            // Stored password is invalid
                            localStorage.removeItem('apiPassword');
                            apiPassword = '';
                            showAuthPrompt();
                        }
                    } catch (error) {
                        console.error('Auth check failed:', error);
                        showAuthPrompt();
                    }
                } else {
                    // No password stored
                    showAuthPrompt();
                }
            }
            
            // Start initialization
            initialize();
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
    
    # Start Flask API server without threading (to prevent thread explosion with SSE)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=False)


if __name__ == '__main__':
    main()