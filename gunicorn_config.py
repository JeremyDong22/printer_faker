# Gunicorn configuration for Printer API Service v2
bind = "0.0.0.0:5000"
workers = 2  # 2 workers for redundancy, but keep low for resource efficiency
threads = 2  # 2 threads per worker = 4 total threads max
timeout = 30  # 30 second timeout for requests
keepalive = 5  # 5 second keepalive
max_requests = 1000  # Restart workers after 1000 requests to prevent memory leaks
max_requests_jitter = 50  # Randomize restart between 950-1050 requests
preload_app = True  # Load app before forking workers
worker_class = "gthread"  # Use gthread workers for thread support

# Limit request line size to prevent DoS
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Access log format
accesslog = "-"  # Log to stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
errorlog = "-"  # Log errors to stderr

# Worker process naming
proc_name = "printer-api-v2"

# Server mechanics
daemon = False  # Don't daemonize (systemd handles this)
pidfile = None  # No pidfile (systemd handles this)
umask = 0  # Current umask
user = None  # Current user
group = None  # Current group
tmp_upload_dir = None

# SSL/Security (if needed later)
# keyfile = None
# certfile = None

# Hook to start services only in master process
def when_ready(server):
    """Called just after the server is started."""
    # Import here to avoid circular dependency
    from printer_api_service_v2 import service
    import time
    
    server.log.info("Starting Printer API Service v2 components in master...")
    print("Starting Printer API Service v2 components...")
    
    # Start all services (TCP server, Cloudflare queue, cleanup)
    service.start()
    
    # Give services time to start
    time.sleep(2)
    print("All services started successfully")
    server.log.info("All services started successfully")