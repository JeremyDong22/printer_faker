# Project Overview - Printer Faker

## System Type
24/7 Restaurant Order Management System - Critical production service for capturing POS receipt data

## Current Status (September 2025)
- **Operational**: Service running stable after major fixes
- **Uptime**: Near 100% after resolving multiple critical issues
- **Disk Usage**: Reduced from 5.5GB to 82MB after cleanup

## Architecture
- **Main Service**: printer_api_service.py
  - TCP server on port 9100 for POS connections
  - REST API on port 5000 for monitoring/data access
  - In-memory storage (deque with 500 receipt buffer)
- **Enhanced Version**: printer_api_service_v2.py (ready to deploy)
  - SQLite persistence
  - Connection pooling
  - Better resource management

## Critical Issues Resolved
1. **File Descriptor Exhaustion** - Fixed with auto_cleanup.sh hourly cron
2. **Daily 2 AM Downtime** - Disabled timer, using smart monitoring instead
3. **Port 9100 Conflict** - Documented, virtual_printer.py deprecated
4. **5.4GB Log File** - Implemented logrotate, switched to journald
5. **No Persistence** - Created v2 with SQLite (ready to deploy)

## Integration Points
- Cloudflare Workers for data parsing
- Supabase for data persistence
- Cloudflare tunnel for secure remote access

## Key Files
- printer_api_service.py - Main production service
- monitor_health_service.sh - Smart health monitoring
- auto_cleanup.sh - Hourly cleanup cron
- /etc/logrotate.d/printer-api - Log rotation config