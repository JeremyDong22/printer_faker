#!/usr/bin/env python3
"""
Printer API Service v2.0 - Enhanced 24/7 POS Receipt Listener
With SQLite persistence, connection pooling, and reliability improvements
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
import sqlite3
from contextlib import contextmanager
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

# Load environment variables
load_dotenv()

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from dashboard import get_dashboard_html
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import hashlib

# Import the existing ESC/POS parser
from virtual_printer import ESCPOSParser, PlainTextRenderer

# Import the new order processor for local Supabase integration
try:
    from order_processor import OrderProcessor
    SUPABASE_ENABLED = True
except ImportError:
    SUPABASE_ENABLED = False
    print("⚠️ OrderProcessor not available, Supabase integration disabled")

app = Flask(__name__)
CORS(app)

# Rate limiting - generous limits for local monitoring
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10000 per hour", "50000 per day"],
    storage_uri="memory://"
)

# Authentication
API_PASSWORD = os.environ.get('PRINTER_API_PASSWORD', 'smartbcg')
API_PASSWORD_HASH = hashlib.sha256(API_PASSWORD.encode()).hexdigest()

# Configuration
MAX_CONCURRENT_CONNECTIONS = 50
CONNECTION_POOL_SIZE = 10
DATABASE_PATH = '/home/smartahc/smartice/printer_faker/receipts.db'
CLOUDFLARE_RETRY_QUEUE_SIZE = 1000
MAX_MEMORY_RECEIPTS = 500  # Keep last 500 in memory for fast access

def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            auth = request.args.get('auth')
        
        if not auth:
            return jsonify({'error': 'Authentication required'}), 401
        
        if hashlib.sha256(auth.encode()).hexdigest() != API_PASSWORD_HASH:
            logger.warning(f"Failed auth attempt from {get_remote_address()}")
            return jsonify({'error': 'Invalid password'}), 403
            
        return f(*args, **kwargs)
    return decorated_function

class DatabaseManager:
    """Manages SQLite database for receipt persistence"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self._local = threading.local()
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS receipts (
                    id TEXT PRIMARY KEY,
                    receipt_no TEXT,
                    timestamp TEXT,
                    plain_text TEXT,
                    raw_data BLOB,
                    source_ip TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    synced_to_cloudflare BOOLEAN DEFAULT 0
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_receipt_no ON receipts(receipt_no);
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON receipts(timestamp);
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at ON receipts(created_at);
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_synced ON receipts(synced_to_cloudflare);
            ''')
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Thread-safe connection context manager"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, timeout=30.0)
            self._local.conn.row_factory = sqlite3.Row
        try:
            yield self._local.conn
        except Exception as e:
            self._local.conn.rollback()
            raise e
        else:
            self._local.conn.commit()
    
    def save_receipt(self, receipt: Dict, raw_data: bytes = None, source_ip: str = None):
        """Save receipt to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO receipts 
                (id, receipt_no, timestamp, plain_text, raw_data, source_ip)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                receipt['id'],
                receipt.get('receipt_no', ''),
                receipt.get('timestamp', ''),
                receipt.get('plain_text', ''),
                raw_data,
                source_ip
            ))
    
    def get_recent_receipts(self, limit=10):
        """Get recent receipts from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, receipt_no, timestamp, plain_text, source_ip, created_at
                FROM receipts
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_unsynced_receipts(self, limit=100):
        """Get receipts not yet synced to Cloudflare"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, receipt_no, timestamp, plain_text, raw_data, source_ip
                FROM receipts
                WHERE synced_to_cloudflare = 0
                ORDER BY created_at ASC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_as_synced(self, receipt_ids):
        """Mark receipts as synced to Cloudflare"""
        if not receipt_ids:
            return
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?' for _ in receipt_ids])
            cursor.execute(f'''
                UPDATE receipts 
                SET synced_to_cloudflare = 1
                WHERE id IN ({placeholders})
            ''', receipt_ids)
    
    def cleanup_old_receipts(self, days=30):
        """Clean up receipts older than specified days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM receipts
                WHERE created_at < datetime('now', '-' || ? || ' days')
            ''', (days,))
            return cursor.rowcount

class CloudflareQueue:
    """Manages retry queue for Cloudflare transmissions"""
    
    def __init__(self, db_manager, max_size=1000):
        self.db_manager = db_manager
        self.max_size = max_size
        self.retry_queue = queue.Queue(maxsize=max_size)
        self.worker_thread = None
        self.running = False
    
    def start(self):
        """Start the retry worker thread"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._retry_worker, daemon=True)
        self.worker_thread.start()
    
    def stop(self):
        """Stop the retry worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _retry_worker(self):
        """Worker thread that retries failed Cloudflare transmissions"""
        while self.running:
            try:
                # Get unsynced receipts from database
                unsynced = self.db_manager.get_unsynced_receipts(limit=10)
                
                if unsynced:
                    # TODO: Send to Cloudflare worker endpoint
                    # For now, just mark as synced after "sending"
                    receipt_ids = [r['id'] for r in unsynced]
                    # Here you would actually send to Cloudflare
                    # If successful:
                    # self.db_manager.mark_as_synced(receipt_ids)
                    pass
                
                # Sleep before next retry
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Cloudflare retry worker error: {e}")
                time.sleep(60)  # Wait longer on error

class ConnectionPool:
    """Manages a pool of connections with proper resource management"""
    
    def __init__(self, max_connections=50):
        self.max_connections = max_connections
        self.active_connections = 0
        self.lock = threading.Lock()
        self.connection_semaphore = threading.Semaphore(max_connections)
    
    def acquire(self):
        """Acquire a connection slot"""
        if not self.connection_semaphore.acquire(timeout=5):
            raise Exception("Connection pool exhausted")
        with self.lock:
            self.active_connections += 1
            return self.active_connections
    
    def release(self):
        """Release a connection slot"""
        with self.lock:
            self.active_connections = max(0, self.active_connections - 1)
        self.connection_semaphore.release()
    
    def get_status(self):
        """Get pool status"""
        with self.lock:
            return {
                'active': self.active_connections,
                'max': self.max_connections,
                'available': self.max_connections - self.active_connections
            }

class ReceiptExtractor:
    """Extract receipt number and timestamp from plain text"""
    
    def extract_receipt_info(self, plain_text: str) -> Dict[str, str]:
        """Extract receipt number and timestamp from receipt text"""
        lines = plain_text.split('\n')
        receipt_no = ""
        timestamp = ""
        
        for i, line in enumerate(lines):
            if '单号' in line and not receipt_no:
                match = re.search(r'单号[：:\s]+(\d+)', line)
                if match:
                    receipt_no = match.group(1)
                elif i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.match(r'^\d+$', next_line):
                        receipt_no = next_line
            
            if '时间' in line and not timestamp:
                match = re.search(r'时间[：:]\s*([^\n]+)', line)
                if match:
                    timestamp = match.group(1).strip()
                elif i + 1 < len(lines):
                    timestamp = lines[i + 1].strip()
        
        return {
            'receipt_no': receipt_no,
            'timestamp': timestamp or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

class PrinterAPIService:
    """Main API Service with enhanced reliability"""
    
    def __init__(self):
        # Initialize logging
        self.setup_logging()
        
        # Database manager
        self.db_manager = DatabaseManager(DATABASE_PATH)
        
        # Connection pool
        self.connection_pool = ConnectionPool(MAX_CONCURRENT_CONNECTIONS)
        
        # Thread pool for handling connections
        self.executor = ThreadPoolExecutor(max_workers=CONNECTION_POOL_SIZE)
        
        # Cloudflare retry queue
        self.cloudflare_queue = CloudflareQueue(self.db_manager)
        
        # In-memory cache for recent receipts (fast access)
        self.receipts = deque(maxlen=MAX_MEMORY_RECEIPTS)
        
        # ESC/POS parser
        self.escpos_parser = ESCPOSParser()
        self.plain_renderer = PlainTextRenderer()
        self.receipt_extractor = ReceiptExtractor()
        
        # Initialize OrderProcessor for local Supabase integration
        self.order_processor = None
        if SUPABASE_ENABLED:
            try:
                self.order_processor = OrderProcessor()
                self.logger.info("✅ Supabase OrderProcessor initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize OrderProcessor: {e}")
        
        # Statistics
        self.stats = {
            'start_time': datetime.datetime.now(),
            'total_received': 0,
            'parse_errors': 0,
            'last_receipt_time': None,
            'supabase_processed': 0,
            'supabase_errors': 0
        }
        
        # Load stats from database
        self.load_stats()
        
        # Real-time streaming
        self.stream_queue = queue.Queue(maxsize=100)
        # SSE streaming removed - use polling or webhooks instead
        
        # Shutdown flag
        self.running = True
        
    def setup_logging(self):
        """Setup rotating file logging"""
        self.logger = logging.getLogger('printer_api')
        self.logger.setLevel(logging.INFO)
        
        # Ensure log directory exists
        os.makedirs('logs', exist_ok=True)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            'logs/printer_api.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)
        
        # Error handler
        error_handler = RotatingFileHandler(
            'logs/printer_api_error.log',
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - %(exc_info)s')
        )
        self.logger.addHandler(error_handler)
    
    def load_stats(self):
        """Load statistics from database"""
        recent = self.db_manager.get_recent_receipts(limit=MAX_MEMORY_RECEIPTS)
        if recent:
            self.receipts = deque(recent, maxlen=MAX_MEMORY_RECEIPTS)
            # Count total from database
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM receipts')
                self.stats['total_received'] = cursor.fetchone()['count']
    
    def start(self):
        """Start all services"""
        # Start Cloudflare retry queue
        self.cloudflare_queue.start()
        
        # Start TCP server in a thread
        tcp_thread = threading.Thread(target=self.tcp_server, daemon=True)
        tcp_thread.start()
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=self.periodic_cleanup, daemon=True)
        cleanup_thread.start()
        
        self.logger.info("✅ Printer API Service v2.0 started")
        print("✅ Printer API Service v2.0 started")
        print(f"📡 TCP Server on port 9100")
        print(f"🌐 API Server on port 5000")
        print(f"💾 Database: {DATABASE_PATH}")
        print(f"🔄 Connection Pool: {MAX_CONCURRENT_CONNECTIONS} max")
    
    def stop(self):
        """Gracefully stop all services"""
        self.running = False
        self.cloudflare_queue.stop()
        if self.order_processor:
            self.order_processor.stop()
        self.executor.shutdown(wait=True, timeout=10)
        self.logger.info("Service stopped gracefully")
    
    def periodic_cleanup(self):
        """Periodic cleanup of old data"""
        while self.running:
            try:
                # Clean up old receipts (older than 30 days)
                deleted = self.db_manager.cleanup_old_receipts(days=30)
                if deleted > 0:
                    self.logger.info(f"Cleaned up {deleted} old receipts")
                
                # Sleep for 1 hour
                time.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
                time.sleep(3600)
    
    def tcp_server(self):
        """Enhanced TCP server with connection pooling"""
        port = 9100
        
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('0.0.0.0', port))
            server_sock.listen(50)
            server_sock.settimeout(1.0)
            
            self.logger.info(f"TCP server listening on port {port}")
            
            while self.running:
                try:
                    client_sock, client_addr = server_sock.accept()
                    
                    # Try to acquire connection from pool
                    try:
                        conn_id = self.connection_pool.acquire()
                        # Handle in thread pool
                        self.executor.submit(
                            self.handle_connection_wrapper,
                            client_sock,
                            client_addr,
                            conn_id
                        )
                    except Exception as e:
                        # Pool exhausted, reject connection
                        self.logger.warning(f"Connection pool exhausted, rejecting {client_addr}")
                        client_sock.close()
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"TCP server error: {e}")
                        time.sleep(1)
                        
        except Exception as e:
            self.logger.error(f"Failed to start TCP server: {e}")
        finally:
            server_sock.close()
    
    def handle_connection_wrapper(self, client_sock, client_addr, conn_id):
        """Wrapper to ensure connection pool cleanup"""
        try:
            self.handle_printer_connection(client_sock, client_addr)
        finally:
            self.connection_pool.release()
    
    def handle_printer_connection(self, client_sock, client_addr):
        """Handle incoming printer data with proper resource management"""
        session_data = []
        
        try:
            client_sock.settimeout(1.0)
            client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            last_data_time = time.time()
            idle_timeout = 30.0
            
            while True:
                try:
                    data = client_sock.recv(1024)
                    if not data:
                        break
                    
                    last_data_time = time.time()
                    session_data.append(data)
                    
                    # Send response
                    response = self.get_response(data)
                    if response:
                        client_sock.send(response)
                        
                except socket.timeout:
                    if time.time() - last_data_time > idle_timeout:
                        break
                    continue
                    
        except Exception as e:
            if "Connection reset" not in str(e):
                self.logger.error(f"Connection error: {e}")
        finally:
            try:
                client_sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            client_sock.close()
            
            # Process data
            if session_data:
                self.process_receipt_data(session_data, client_addr[0])
    
    def process_receipt_data(self, session_data, source_ip):
        """Process and store receipt data"""
        complete_data = b''.join(session_data)
        
        if len(complete_data) < 50:
            return  # Too small, probably just status query
        
        try:
            # Parse ESC/POS
            commands = self.escpos_parser.parse(complete_data)
            plain_text = self.plain_renderer.render(commands)
            
            # Extract info
            receipt_info = self.receipt_extractor.extract_receipt_info(plain_text)
            
            # Create receipt
            receipt = {
                'id': str(uuid.uuid4()),
                'receipt_no': receipt_info['receipt_no'],
                'timestamp': receipt_info['timestamp'],
                'plain_text': plain_text
            }
            
            # Save to database
            self.db_manager.save_receipt(receipt, complete_data, source_ip)
            
            # Add to memory cache
            self.receipts.append(receipt)
            
            # Update stats
            self.stats['total_received'] += 1
            self.stats['last_receipt_time'] = datetime.datetime.now().isoformat()
            
            # Broadcast
            self.broadcast_receipt(receipt)
            
            # Process to Supabase if enabled
            if self.order_processor:
                try:
                    result = self.order_processor.process_receipt(receipt)
                    self.stats['supabase_processed'] += 1
                    self.logger.info(f"✅ Supabase processed: {result}")
                except Exception as e:
                    self.stats['supabase_errors'] += 1
                    self.logger.error(f"Supabase processing error: {e}")
            
            self.logger.info(f"✅ Receipt saved: {receipt['receipt_no'] or 'N/A'}")
            
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            self.stats['parse_errors'] += 1
    
    def get_response(self, data):
        """Generate proper ESC/POS response emulating a real thermal printer"""
        # DLE EOT n - Real-time status transmission
        if b'\x10\x04\x01' in data:  # Printer status
            # Status byte: 0x12 = Online, lid closed, no errors
            # Bit 2: 0 = Lid closed, 1 = Lid open
            # Bit 3: 0 = Online, 1 = Offline
            # Bit 5: 0 = No error, 1 = Error
            return b'\x12'  # Printer ready, lid closed
        elif b'\x10\x04\x02' in data:  # Offline status
            return b'\x12'  # Not offline
        elif b'\x10\x04\x03' in data:  # Error status
            return b'\x12'  # No errors
        elif b'\x10\x04\x04' in data:  # Paper roll status
            return b'\x12'  # Paper OK
        elif b'\x10\x04' in data:  # General status query
            # Send all status bytes: printer OK, lid closed, paper present
            return b'\x10\x0F\x00\x00'  # All systems normal
        elif b'\x1D\x49' in data:  # Get printer ID
            return b'TM-T88V\x00'  # Emulate Epson TM-T88V
        elif b'\x1B\x40' in data:  # Initialize printer
            return b'\x06'  # ACK
        elif b'\x1B\x64' in data:  # Feed n lines
            return b'\x06'  # ACK
        elif b'\x1D\x56' in data:  # Cut paper
            return b'\x06'  # ACK
        elif len(data) > 0:
            return b'\x06'  # General ACK
        return None
    
    def broadcast_receipt(self, receipt):
        """SSE broadcasting removed - data available via polling /api/receipts"""
        pass  # Keep method for backward compatibility, but it's a no-op now

# Initialize service
service = PrinterAPIService()

# Flask routes
@app.route('/')
def index():
    """Web dashboard for monitoring"""
    return get_dashboard_html()

@app.route('/api/health', methods=['GET'])
@require_auth
def health_check():
    """Enhanced health check with connection pool status"""
    uptime = (datetime.datetime.now() - service.stats['start_time']).total_seconds()
    pool_status = service.connection_pool.get_status()
    
    return jsonify({
        'status': 'ok',
        'version': '2.0',
        'receipts_count': len(service.receipts),
        'total_received': service.stats['total_received'],
        'parse_errors': service.stats['parse_errors'],
        'uptime_seconds': int(uptime),
        'last_receipt': service.stats['last_receipt_time'],
        'connection_pool': pool_status
    })

@app.route('/api/recent', methods=['GET'])
@require_auth
def get_recent():
    """Get recent receipts from database"""
    limit = request.args.get('limit', 10, type=int)
    recent = service.db_manager.get_recent_receipts(limit=min(limit, 100))
    return jsonify(recent)

@app.route('/api/receipts', methods=['GET'])
@require_auth
def get_all_receipts():
    """Get all cached receipts"""
    return jsonify(list(service.receipts))

@app.route('/api/search', methods=['GET'])
@require_auth
def search_receipts():
    """Search receipts in database"""
    receipt_no = request.args.get('no', '')
    
    if not receipt_no:
        return jsonify({'error': 'Please provide receipt number'}), 400
    
    with service.db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, receipt_no, timestamp, plain_text, created_at
            FROM receipts
            WHERE receipt_no = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (receipt_no,))
        results = [dict(row) for row in cursor.fetchall()]
    
    return jsonify(results)

@app.route('/api/stats', methods=['GET'])
@require_auth
def get_stats():
    """Get detailed statistics"""
    with service.db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Total receipts
        cursor.execute('SELECT COUNT(*) as total FROM receipts')
        total = cursor.fetchone()['total']
        
        # Today's receipts
        cursor.execute('''
            SELECT COUNT(*) as today 
            FROM receipts 
            WHERE date(created_at) = date('now')
        ''')
        today = cursor.fetchone()['today']
        
        # Unsynced receipts
        cursor.execute('SELECT COUNT(*) as unsynced FROM receipts WHERE synced_to_cloudflare = 0')
        unsynced = cursor.fetchone()['unsynced']
    
    pool_status = service.connection_pool.get_status()
    
    return jsonify({
        'total_receipts': total,
        'today_receipts': today,
        'unsynced_receipts': unsynced,
        'parse_errors': service.stats['parse_errors'],
        'supabase_processed': service.stats.get('supabase_processed', 0),
        'supabase_errors': service.stats.get('supabase_errors', 0),
        'supabase_enabled': service.order_processor is not None,
        'connection_pool': pool_status,
        'memory_cache_size': len(service.receipts)
    })

# SSE endpoint removed - using polling or webhooks instead
# The SSE endpoint was causing thread exhaustion and performance issues

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    print("\\n🛑 Shutting down gracefully...")
    service.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Start services
    service.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)