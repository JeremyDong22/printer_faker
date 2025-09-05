#!/bin/bash
# Monitor printer service health and auto-restart if needed

# Thresholds
MAX_THREADS=500
MAX_FDS=800
MAX_CONNECTIONS=50

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_health() {
    # Get PID
    PID=$(pgrep -f "printer_api_service.py" | tail -1)
    
    if [ -z "$PID" ]; then
        echo -e "${RED}❌ Service not running!${NC}"
        return 1
    fi
    
    # Count threads
    THREADS=$(ps -eLf | grep -c $PID)
    
    # Count file descriptors
    FDS=$(lsof -p $PID 2>/dev/null | wc -l)
    
    # Count connections
    CONNECTIONS=$(ss -tn | grep -c ":9100")
    
    # Count CLOSE_WAIT
    CLOSE_WAIT=$(ss -tn | grep -c "CLOSE-WAIT.*9100")
    
    # Check error rate in last minute
    ERROR_COUNT=$(tail -1000 /home/smartahc/smartice/printer_faker/logs/service_error.log 2>/dev/null | grep -c "Too many open files")
    
    echo "========================================="
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Health Check"
    echo "========================================="
    echo -e "PID:         $PID"
    echo -e "Threads:     $THREADS (max: $MAX_THREADS)"
    echo -e "File Desc:   $FDS (max: $MAX_FDS)"
    echo -e "Connections: $CONNECTIONS (max: $MAX_CONNECTIONS)"
    echo -e "CLOSE_WAIT:  $CLOSE_WAIT"
    echo -e "Errors:      $ERROR_COUNT"
    
    # Check if restart needed
    NEEDS_RESTART=0
    REASON=""
    
    if [ $THREADS -gt $MAX_THREADS ]; then
        NEEDS_RESTART=1
        REASON="Too many threads ($THREADS > $MAX_THREADS)"
    elif [ $FDS -gt $MAX_FDS ]; then
        NEEDS_RESTART=1
        REASON="Too many file descriptors ($FDS > $MAX_FDS)"
    elif [ $CONNECTIONS -gt $MAX_CONNECTIONS ]; then
        NEEDS_RESTART=1
        REASON="Too many connections ($CONNECTIONS > $MAX_CONNECTIONS)"
    elif [ $ERROR_COUNT -gt 100 ]; then
        NEEDS_RESTART=1
        REASON="Too many errors ($ERROR_COUNT)"
    fi
    
    if [ $NEEDS_RESTART -eq 1 ]; then
        echo -e "${RED}⚠️  WARNING: $REASON${NC}"
        echo -e "${YELLOW}🔄 Auto-restarting service...${NC}"
        sudo systemctl restart printer-api.service
        sleep 5
        echo -e "${GREEN}✅ Service restarted${NC}"
        
        # Log the restart
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Auto-restarted: $REASON" >> /home/smartahc/smartice/printer_faker/logs/auto_restarts.log
    else
        echo -e "${GREEN}✅ Service healthy${NC}"
    fi
    
    echo ""
}

# Continuous monitoring mode
if [ "$1" == "watch" ]; then
    echo "Starting continuous monitoring (check every 30 seconds)..."
    echo "Press Ctrl+C to stop"
    while true; do
        clear
        check_health
        sleep 30
    done
else
    # Single check
    check_health
fi