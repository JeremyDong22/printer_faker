#!/bin/bash
# Auto cleanup old receipt files to prevent disk/fd exhaustion
# Run this every hour via cron or systemd timer

LOG_FILE="/home/smartahc/smartice/printer_faker/logs/cleanup.log"
OUTPUT_DIR="/home/smartahc/smartice/printer_faker/output"
MAX_AGE_DAYS=7  # Keep files for 7 days max

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting cleanup" >> "$LOG_FILE"

# Count files before cleanup
BEFORE_COUNT=$(find "$OUTPUT_DIR" -type f \( -name "raw_*.bin" -o -name "receipt_plain_*.txt" \) 2>/dev/null | wc -l)

# Delete files older than MAX_AGE_DAYS
find "$OUTPUT_DIR" -type f \( -name "raw_*.bin" -o -name "receipt_plain_*.txt" \) -mtime +$MAX_AGE_DAYS -delete 2>/dev/null

# Count files after cleanup
AFTER_COUNT=$(find "$OUTPUT_DIR" -type f \( -name "raw_*.bin" -o -name "receipt_plain_*.txt" \) 2>/dev/null | wc -l)

DELETED=$((BEFORE_COUNT - AFTER_COUNT))
echo "$(date '+%Y-%m-%d %H:%M:%S') - Deleted $DELETED files (Before: $BEFORE_COUNT, After: $AFTER_COUNT)" >> "$LOG_FILE"

# Also clean up if too many files accumulate (emergency cleanup)
if [ "$AFTER_COUNT" -gt 1000 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: Too many files ($AFTER_COUNT), performing emergency cleanup" >> "$LOG_FILE"
    # Delete files older than 1 day
    find "$OUTPUT_DIR" -type f \( -name "raw_*.bin" -o -name "receipt_plain_*.txt" \) -mtime +1 -delete 2>/dev/null
    NEW_COUNT=$(find "$OUTPUT_DIR" -type f \( -name "raw_*.bin" -o -name "receipt_plain_*.txt" \) 2>/dev/null | wc -l)
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Emergency cleanup complete. Remaining: $NEW_COUNT files" >> "$LOG_FILE"
fi

# Rotate log file if too large
if [ -f "$LOG_FILE" ] && [ $(stat -c%s "$LOG_FILE") -gt 1048576 ]; then  # 1MB
    mv "$LOG_FILE" "$LOG_FILE.old"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Log rotated" > "$LOG_FILE"
fi