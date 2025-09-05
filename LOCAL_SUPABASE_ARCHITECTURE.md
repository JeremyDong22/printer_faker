# Local Supabase Integration Architecture
## Complete Order Flow - Direct POS to Supabase (No Cloudflare)

Generated: 2025-09-06

## Overview
This document describes the complete flow when a manual order is placed on the POS terminal, showing how data flows from the POS directly to Supabase without any Cloudflare Workers or Durable Objects.

## Architecture Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MANUAL ORDER FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

1️⃣ YOU PLACE ORDER ON POS TERMINAL
   ================================
   
   [POS Terminal Screen]
   ┌──────────────────┐
   │  桌号: 8         │
   │  野菜卷 x1       │
   │  木姜子牛肉 x2   │
   │  [确认订单]      │
   └──────────────────┘
           ↓
   
2️⃣ POS GENERATES TWO RECEIPTS
   ===========================
   
   A. CUSTOMER RECEIPT (客单)          B. KITCHEN SLIPS (制作分单)
   ┌─────────────────────┐             ┌─────────────────────┐
   │ 智慧餐厅            │             │ 智慧餐厅            │
   │ 桌号: 8             │             │ 制作分单            │
   │ ─────────────────── │             │ 档口: 荤菜          │
   │ 客单                │             │ 桌号: 8             │
   │ ─────────────────── │             │ ─────────────────── │
   │ 野菜卷181份18       │             │ 木姜子牛肉2/份      │
   │ 木姜子牛肉522份104  │             │ ─────────────────── │
   │ ─────────────────── │             │ 单号: K001          │
   │ 合计: 122           │             └─────────────────────┘
   │ 单号: C001          │             
   └─────────────────────┘             (May have multiple slips
                                        for different stations)
           ↓                                    ↓
           
3️⃣ POS SENDS ESC/POS DATA TO TCP PORT 9100
   ========================================
   
   [POS Terminal]                    [Your Local Server]
   192.168.x.x                       192.168.x.x:9100
        │                                   │
        │  ┌──────────────────────────┐    │
        ├──│ ESC/POS Binary Commands  │───►│ TCP Socket
        │  │ 0x1B 0x40 (Initialize)   │    │ Listening
        │  │ 0x1B 0x45 (Bold)         │    │
        │  │ Text bytes...             │    │
        │  │ 0x1D 0x56 (Cut paper)    │    │
        │  └──────────────────────────┘    │
        │                                   │
        │  ◄──── 0x06 (ACK) ───────────    │
        │  ◄──── 0x12 (Status OK) ─────    │
        └───────────────────────────────────┘

4️⃣ LOCAL PRINTER_API_SERVICE_V2 PROCESSING
   ========================================
   
   printer_api_service_v2.py @ localhost
   ┌─────────────────────────────────────────────────────────┐
   │                                                           │
   │  A. TCP Handler (port 9100)                              │
   │     └─► Receives raw ESC/POS data                        │
   │                                                           │
   │  B. ESCPOSParser                                         │
   │     └─► Converts binary to commands                      │
   │         [BOLD, TEXT("智慧餐厅"), LINE_FEED, CUT...]     │
   │                                                           │
   │  C. PlainTextRenderer                                    │
   │     └─► Converts to plain text                           │
   │         "智慧餐厅\n桌号: 8\n客单\n..."                  │
   │                                                           │
   │  D. ReceiptExtractor                                     │
   │     └─► Extracts receipt_no & timestamp                  │
   │         {receipt_no: "C001", timestamp: "2025-09-06..."}│
   │                                                           │
   │  E. SQLite Storage                                       │
   │     └─► Saves to receipts.db                             │
   │         INSERT INTO receipts VALUES (...)                │
   │                                                           │
   │  F. OrderProcessor (NEW!)                                │
   │     └─► Process receipt for Supabase                     │
   └─────────────────────────────────────────────────────────┘
                              ↓

5️⃣ ORDER PROCESSOR LOGIC
   =====================
   
   order_processor.py
   ┌──────────────────────────────────────────────────────────┐
   │                                                            │
   │  1. Check Receipt Type:                                   │
   │     ┌─────────────────┐                                   │
   │     │ Is it 预结单?   │──Yes──► Skip (pre-checkout)       │
   │     └────────┬────────┘                                   │
   │              No                                            │
   │              ↓                                             │
   │     ┌─────────────────┐                                   │
   │     │ Is it 结账单?   │──Yes──► Skip (final checkout)     │
   │     └────────┬────────┘                                   │
   │              No                                            │
   │              ↓                                             │
   │     ┌─────────────────┐                                   │
   │     │ Is it 制作分单? │──Yes──► Process Kitchen Slip      │
   │     └────────┬────────┘         │                         │
   │              No                  │                         │
   │              ↓                   ↓                         │
   │     Process Customer Order   Extract Station (档口)       │
   │              │                   │                         │
   │              ↓                   ↓                         │
   │     Parse Dishes:           Map Station to UUID:          │
   │     "野菜卷181份18"         "荤菜" → "b2c3d4e5-f6a7..."  │
   │     ↓                           │                         │
   │     Extract: 野菜卷 x1          ↓                         │
   │                             Parse Kitchen Dishes:         │
   │                             "木姜子牛肉2/份"              │
   │                             ↓                             │
   │                             Extract: 木姜子牛肉 x2        │
   └──────────────────────────────────────────────────────────┘
                              ↓

6️⃣ SUPABASE DATABASE OPERATIONS
   =============================
   
   Direct HTTP Requests to Supabase (No Workers!)
   ┌──────────────────────────────────────────────────────────┐
   │                                                            │
   │  For Customer Order (客单):                               │
   │  ──────────────────────────                               │
   │  POST https://wdpeoyugsxqnpwwtkqsl.supabase.co/rest/v1/  │
   │                                                            │
   │  A. Insert into order_orders:                             │
   │     {                                                      │
   │       restaurant_id: "a1b2c3d4-e5f6-7890-abcd-ef123456",  │
   │       receipt_no: "C001",                                 │
   │       table_no: "8",                                      │
   │       order_type: "dine_in",                              │
   │       status: "pending",                                  │
   │       raw_data: {text: "full receipt text"},              │
   │       ordered_at: "2025-09-06T01:00:00"                   │
   │     } → Returns order_id: "uuid-here"                     │
   │                                                            │
   │  B. Insert into order_dishes:                             │
   │     [                                                      │
   │       {                                                    │
   │         order_id: "uuid-here",                            │
   │         name: "野菜卷",                                   │
   │         quantity: 1,                                      │
   │         station_id: null,                                 │
   │         table_no: "8",                                    │
   │         status: "pending"                                 │
   │       },                                                   │
   │       {                                                    │
   │         name: "木姜子牛肉",                               │
   │         quantity: 2,                                      │
   │         ...                                               │
   │       }                                                    │
   │     ]                                                      │
   │                                                            │
   │  For Kitchen Slip (制作分单):                             │
   │  ────────────────────────────                             │
   │  Insert into order_dishes only:                           │
   │     [                                                      │
   │       {                                                    │
   │         receipt_no: "K001",                               │
   │         name: "木姜子牛肉",                               │
   │         quantity: 2,                                      │
   │         station_id: "b2c3d4e5-f6a7-8901-bcde-f234567",    │
   │         table_no: "8",                                    │
   │         status: "pending"                                 │
   │       }                                                    │
   │     ]                                                      │
   └──────────────────────────────────────────────────────────┘
                              ↓

7️⃣ RESULT & MONITORING
   ===================
   
   A. Success Path:
   ┌──────────────────────────────────────────────────────────┐
   │ ✅ Supabase Returns 200 OK                                │
   │ ✅ Stats Updated: supabase_processed++                    │
   │ ✅ Log: "Supabase processed: {order_id: uuid}"            │
   │ ✅ Kitchen Display Updates (via Supabase subscription)    │
   └──────────────────────────────────────────────────────────┘
   
   B. Failure Path:
   ┌──────────────────────────────────────────────────────────┐
   │ ❌ Supabase Returns Error (network/auth/etc)              │
   │ ❌ Stats Updated: supabase_errors++                       │
   │ ⚠️  Added to Retry Queue                                  │
   │ 🔄 Background Thread Retries:                             │
   │    - After 5 seconds                                      │
   │    - Then 10, 20, 40, 80 seconds (exponential backoff)   │
   │    - Max 5 minutes between retries                        │
   │ 💾 Saved in SQLite for recovery                           │
   └──────────────────────────────────────────────────────────┘

8️⃣ MONITORING ENDPOINTS
   ====================
   
   Dashboard: http://localhost:5000/
   ┌──────────────────────────────────────────────────────────┐
   │ 🖨️ Printer Monitor Dashboard                              │
   │                                                            │
   │ Service Status: 🟢 Online                                 │
   │ Total Receipts: 8                                         │
   │ Supabase Processed: 1                                     │
   │ Supabase Errors: 0                                        │
   │                                                            │
   │ Recent Receipts:                                           │
   │ ├─ C001 | 2025-09-06 01:00:00 | 桌号: 8...              │
   │ └─ K001 | 2025-09-06 01:00:01 | 制作分单...             │
   └──────────────────────────────────────────────────────────┘
   
   API Stats: curl -H "Authorization: smartbcg" localhost:5000/api/stats
   {
     "supabase_enabled": true,
     "supabase_processed": 1,
     "supabase_errors": 0,
     "total_receipts": 8
   }
```

## Timeline Example

```
T+0.000s  : You press "确认订单" on POS
T+0.010s  : POS generates receipts
T+0.050s  : POS connects to 192.168.x.x:9100
T+0.100s  : TCP server receives ESC/POS data
T+0.110s  : Parser converts to plain text
T+0.120s  : Receipt saved to SQLite
T+0.130s  : OrderProcessor analyzes receipt type
T+0.140s  : Dishes parsed and extracted
T+0.200s  : HTTP POST to Supabase API
T+0.350s  : Supabase returns success
T+0.360s  : Stats updated, logs written
T+0.400s  : Kitchen display updates (via subscription)
```

## Key Technical Details

### 1. Receipt Types and Processing

| Receipt Type | Chinese | Action | Database Operations |
|-------------|---------|--------|-------------------|
| Customer Order | 客单 | Process fully | Insert to `order_orders` + `order_dishes` |
| Kitchen Slip | 制作分单 | Process dishes | Insert to `order_dishes` only |
| Pre-checkout | 预结单 | Skip | None |
| Final Checkout | 结账单 | Skip | Log event only |

### 2. Station Mapping

The system maps Chinese station names to UUID identifiers:

```python
STATION_MAP = {
    '荤菜': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
    '素菜': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
    '酒水': 'd4e5f6a7-b8c9-0123-defa-456789012345',
    '主食': 'e5f6a7b8-c9d0-1234-efab-567890123456',
    '汤品': 'f6a7b8c9-d0e1-2345-fabc-678901234567',
    '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',
    '凉菜': 'a7b8c9d0-e1f2-3456-abcd-789012345678',
    '其他': 'a7b8c9d0-e1f2-3456-abcd-789012345678'
}
```

### 3. Dish Parsing Patterns

#### Customer Order Format (客单)
```
Input:  "野菜卷181份18"
Pattern: dish_name + price + quantity + unit + subtotal
Output: {name: "野菜卷", quantity: 1}
```

#### Kitchen Slip Format (制作分单)
```
Input:  "木姜子鲜黄牛肉1/份"
Pattern: dish_name + quantity + "/" + unit
Output: {name: "木姜子鲜黄牛肉", quantity: 1}
```

### 4. Supabase Tables Structure

#### order_orders table
```json
{
  "id": "uuid",
  "restaurant_id": "fixed-uuid",
  "receipt_no": "string",
  "table_no": "string",
  "order_type": "dine_in",
  "status": "pending",
  "raw_data": {"text": "full receipt"},
  "ordered_at": "timestamp",
  "source": "printer_api"
}
```

#### order_dishes table
```json
{
  "id": "uuid",
  "order_id": "uuid (nullable for kitchen slips)",
  "restaurant_id": "fixed-uuid",
  "receipt_no": "string",
  "name": "dish name",
  "quantity": "integer",
  "station_id": "uuid (null for customer orders)",
  "table_no": "string",
  "status": "pending",
  "prep_time_minutes": 10,
  "urgency_level": "normal"
}
```

### 5. Error Handling & Recovery

1. **Automatic Retry Queue**
   - Exponential backoff: 5s, 10s, 20s, 40s, 80s, max 300s
   - Runs in background thread
   - Persists across service restarts

2. **SQLite Backup**
   - All receipts saved locally first
   - Can replay failed receipts
   - 30-day retention policy

3. **Monitoring**
   - Real-time stats at `/api/stats`
   - Web dashboard at port 5000
   - Logs in `/logs/printer_api.log`

## Key Improvements Over Previous Architecture

| Aspect | Old (Workers + DO) | New (Local Only) |
|--------|-------------------|-----------------|
| Architecture | POS → Local → DO → Worker → Supabase | POS → Local → Supabase |
| Latency | ~500ms | ~200ms |
| Cost | $5-10/month | $0 |
| Complexity | 4 layers | 2 layers |
| Points of Failure | 4 | 2 |
| Debugging | Distributed logs | Single log file |
| Recovery | Manual | Automatic |

## Files and Components

### Core Files
- `/home/smartahc/smartice/printer_faker/printer_api_service_v2.py` - Main service
- `/home/smartahc/smartice/printer_faker/order_processor.py` - Supabase integration
- `/home/smartahc/smartice/printer_faker/.env` - Configuration
- `/home/smartahc/smartice/printer_faker/receipts.db` - Local storage

### Service Management
- `sudo systemctl status printer-api.service` - Check status
- `sudo systemctl restart printer-api.service` - Restart
- `journalctl -u printer-api.service -f` - View logs

### API Endpoints
- `GET /` - Web dashboard
- `GET /api/health` - Health check
- `GET /api/stats` - Statistics (requires auth)
- `GET /api/receipts` - Recent receipts (requires auth)
- `GET /api/recent` - Last 10 receipts (requires auth)

## Frontend Integration Notes

### What Changed for Frontend
1. **No more SSE endpoint** - Remove SSE connection code
2. **No more Worker calls** - All data comes from Supabase directly
3. **Real-time updates** - Use Supabase subscriptions instead of SSE
4. **Same data structure** - Tables and fields unchanged

### Recommended Frontend Changes
1. Remove SSE listener code
2. Remove Worker API calls
3. Use Supabase real-time subscriptions for updates
4. Connect directly to Supabase for all data

### Supabase Connection
```javascript
// Frontend should connect directly to Supabase
const supabase = createClient(
  'https://wdpeoyugsxqnpwwtkqsl.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' // anon key
)

// Subscribe to changes
supabase
  .channel('orders')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'order_orders'
  }, (payload) => {
    console.log('New order:', payload.new)
  })
  .subscribe()
```

## Contact & Support

For questions about this architecture:
- Check logs: `tail -f /home/smartahc/smartice/printer_faker/logs/printer_api.log`
- Monitor service: `http://localhost:5000/`
- Test integration: `uv run python3 test_supabase_integration.py`

---
*This document describes the complete local-only architecture implemented on 2025-09-06, eliminating all Cloudflare dependencies.*