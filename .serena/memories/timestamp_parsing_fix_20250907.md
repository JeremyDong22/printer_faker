# Timestamp Parsing Fix - September 7, 2025

## Problem
Customer orders (客单) were failing to save to the `order_orders` table in Supabase with the error:
```
invalid input syntax for type timestamp with time zone: "打印时间: 2025-09-06 22:24:38"
```

## Impact
- **ALL customer orders were failing** to save to database
- No order-to-dish relationships could be established  
- Table view feature couldn't work without order records
- Only kitchen slips (制作分单) were working since they don't use timestamps

## Root Cause
The POS system outputs timestamps with Chinese prefix "打印时间: " which Supabase couldn't parse as a valid timestamp.

## Solution
Added `parse_timestamp()` method in `order_processor.py` (lines 304-336):

```python
def parse_timestamp(self, timestamp_str: Optional[str]) -> str:
    """Parse timestamp from various formats to ISO format"""
    if not timestamp_str:
        return datetime.utcnow().isoformat()
    
    # Handle Chinese format: "打印时间: 2025-09-06 22:24:38"
    if '打印时间' in timestamp_str:
        # Extract just the date/time part
        match = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', timestamp_str)
        if match:
            # Convert to ISO format
            dt = datetime.strptime(match.group(), '%Y-%m-%d %H:%M:%S')
            return dt.isoformat() + 'Z'
    
    # Already in correct format
    if 'T' in timestamp_str:
        return timestamp_str
    
    # Fallback
    return datetime.utcnow().isoformat()
```

## Implementation
Modified line 500 in `process_customer_order()`:
```python
# BEFORE:
'ordered_at': receipt_data.get('timestamp', datetime.utcnow().isoformat()),

# AFTER:  
'ordered_at': self.parse_timestamp(receipt_data.get('timestamp')),
```

## Testing
Created `test_timestamp_fix.py` to verify parsing of various timestamp formats.

## Result
- ✅ Customer orders now save correctly to database
- ✅ Table view feature can access order-dish relationships
- ✅ Complete order tracking restored

## Service Status
Service was restarted at 21:48 CST on September 7, 2025 with the fix active.