# Supabase Integration Architecture

## Overview
The printer_faker system now uses direct Supabase integration instead of Cloudflare Workers. This provides simpler, more reliable order processing for the restaurant POS system.

## Key Components

### OrderProcessor (order_processor.py)
- Processes receipts locally using Python
- Distinguishes between customer orders (客单) and kitchen slips (制作分单)
- Handles multi-line dish names with parentheses
- Uses Supabase Python SDK with RLS-enabled anon key
- Implements exponential backoff for retries

### Station Mapping
```python
STATION_MAP = {
    '荤菜': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
    '素菜': 'c3d4e5f6-a789-0123-cdef-234567890123',
    '凉菜': 'd4e5f6a7-8901-2345-def0-345678901234',
    '面点': 'e5f6a789-0123-4567-ef01-456789012345',
    '汤羹': 'f6a78901-2345-6789-f012-567890123456',
    '酒水饮料': 'a7890123-4567-89ab-0123-678901234567'
}
```

### Environment Configuration (.env)
```
SUPABASE_URL=https://wdpeoyugsxqnpwwtkqsl.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Multi-line Dish Parsing Fix
Handles cases where long dish names with parentheses span multiple lines:
- Detects unclosed parenthesis in dish line
- Checks next line for closing parenthesis
- Combines lines to preserve full dish name
- Example: "紫苏半边云（鲜牛胸口）" won't be split

## Data Flow
1. POS terminal → TCP port 9100
2. ESCPOSParser extracts receipt data
3. OrderProcessor analyzes receipt type
4. Direct Supabase write (no Workers needed)
5. Dashboard polls /api/recent for live updates