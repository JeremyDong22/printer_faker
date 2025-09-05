#!/bin/bash
# Continuous health monitoring service for Printer API
# Only restarts when actual problems detected, not on schedule

# Configuration
CHECK_INTERVAL=60           # Check every 60 seconds
MAX_THREADS=500            # Max threads before restart
MAX_FDS=800               # Max file descriptors before restart  
MAX_CONNECTIONS=50         # Max connections before restart
MAX_CLOSE_WAIT=20         # Max CLOSE_WAIT connections
MAX_ERROR_RATE=100        # Max errors per check period
API_URL="http://localhost:5000/api/health"
API_PASSWORD="smartbcg"

# Log file
LOG_FILE="/home/smartahc/smartice/printer_faker/logs/monitor.log"
ERROR_LOG="/home/smartahc/smartice/printer_faker/logs/monitor_error.log"

# Ensure log directory exists
mkdir -p /home/smartahc/smartice/printer_faker/logs

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

check_health() {
    local needs_restart=0
    local restart_reasons=""
    
    # Get PID
    PID=$(pgrep -f "printer_api_service.py" | tail -1)
    
    if [ -z "$PID" ]; then
        log_message "ERROR: Service not running! Starting it..."
        sudo systemctl start printer-api.service
        sleep 5
        return
    fi
    
    # Check API endpoint (suppress output to reduce logging)
    API_RESPONSE=$(curl -s -H "Authorization: $API_PASSWORD" "$API_URL" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$API_RESPONSE" ]; then
        log_message "WARNING: API not responding"
        needs_restart=1
        restart_reasons="${restart_reasons}API not responding; "
    fi
    
    # Count threads
    THREADS=$(ps -eLf | grep -c "$PID" 2>/dev/null || echo "0")
    if [ "$THREADS" -gt "$MAX_THREADS" ]; then
        needs_restart=1
        restart_reasons="${restart_reasons}Too many threads ($THREADS>$MAX_THREADS); "
    fi
    
    # Count file descriptors
    FDS=$(lsof -p "$PID" 2>/dev/null | wc -l || echo "0")
    if [ "$FDS" -gt "$MAX_FDS" ]; then
        needs_restart=1
        restart_reasons="${restart_reasons}Too many FDs ($FDS>$MAX_FDS); "
    fi
    
    # Count TCP connections
    CONNECTIONS=$(ss -tn | grep -c ":9100" || echo "0")
    if [ "$CONNECTIONS" -gt "$MAX_CONNECTIONS" ]; then
        needs_restart=1
        restart_reasons="${restart_reasons}Too many connections ($CONNECTIONS>$MAX_CONNECTIONS); "
    fi
    
    # Count CLOSE_WAIT connections
    CLOSE_WAIT=$(ss -tn | grep -c "CLOSE-WAIT.*:9100" || echo "0")
    if [ "$CLOSE_WAIT" -gt "$MAX_CLOSE_WAIT" ]; then
        needs_restart=1
        restart_reasons="${restart_reasons}Too many CLOSE_WAIT ($CLOSE_WAIT>$MAX_CLOSE_WAIT); "
    fi
    
    # Check error rate
    if [ -f "$ERROR_LOG" ]; then
        ERROR_COUNT=$(tail -500 "$ERROR_LOG" 2>/dev/null | grep -c "Too many open files\|Connection pool exhausted" || echo "0")
        if [ "$ERROR_COUNT" -gt "$MAX_ERROR_RATE" ]; then
            needs_restart=1
            restart_reasons="${restart_reasons}High error rate ($ERROR_COUNT>$MAX_ERROR_RATE); "
        fi
    fi
    
    # Check Cloudflare tunnel
    TUNNEL_RUNNING=$(pgrep -f "cloudflared tunnel" | wc -l)
    if [ "$TUNNEL_RUNNING" -eq 0 ]; then
        log_message "WARNING: Cloudflare tunnel not running, attempting restart"
        # Try to restart tunnel (you may need to adjust this command)
        nohup cloudflared tunnel run smartprinter-api > /dev/null 2>&1 &
    fi
    
    # Log current status
    log_message "Status: PID=$PID, Threads=$THREADS, FDs=$FDS, Conn=$CONNECTIONS, CLOSE_WAIT=$CLOSE_WAIT, Errors=$ERROR_COUNT"
    
    # Restart if needed
    if [ "$needs_restart" -eq 1 ]; then
        log_message "RESTART REQUIRED: $restart_reasons"
        log_message "Restarting printer-api service..."
        
        # Graceful restart
        sudo systemctl restart printer-api.service
        sleep 10  # Wait for service to stabilize
        
        # Verify restart successful
        NEW_PID=$(pgrep -f "printer_api_service.py" | tail -1)
        if [ -n "$NEW_PID" ]; then
            log_message "Service restarted successfully (new PID: $NEW_PID)"
        else
            log_message "ERROR: Service failed to restart!"
            # Try once more
            sudo systemctl start printer-api.service
        fi
    fi
}

# Main monitoring loop
log_message "Health monitor started (checking every ${CHECK_INTERVAL}s)"

while true; do
    check_health
    sleep "$CHECK_INTERVAL"
done