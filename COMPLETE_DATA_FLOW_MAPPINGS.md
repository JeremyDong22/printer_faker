# Complete Data Flow and Mappings Documentation

**System**: POS Printer → SQLite → Supabase  
**Date**: 2025-09-06  
**Purpose**: Document the complete data flow from POS terminals through local processing to Supabase

## 1. POS Printer Output (Source)

### Receipt Types

#### Customer Order (客单)
```
小票编号: 140877542509060048
桌号: 包间-包间
订单类型: 客户订单
时间: 2025-09-06 18:45:00

菜品列表:
红烧肉               份1份68
宫保鸡丁             份1份58
老醋花生             份1份18
米饭                 份2份6

合计: 150元
```
**Key**: No station assignment (档口) in customer orders

#### Kitchen Slip (制作分单)
```
制作分单 - 荤菜档
档口: 荤菜
桌号: 包间-包间
单号: 140877542509060048

菜品数量
红烧肉1/份
宫保鸡丁1/份

制作时间: 18:45
```
**Key**: Has station assignment (档口: X)

### Station Names in POS
The POS system uses these Chinese station names:
- **荤菜** - Meat dishes station
- **素菜** - Vegetable dishes station  
- **酒水** - Beverages station
- **小吃** - Snacks station
- **凉菜** - Cold dishes station

## 2. TCP Reception & SQLite Storage

### Process Flow
```
POS Terminal
    ↓ (ESC/POS commands over TCP)
Port 9100 (printer_api_service_v2.py)
    ↓ (ESCPOSParser)
Plain Text Extraction
    ↓ (ReceiptExtractor)
SQLite Database (receipts.db)
```

### SQLite Schema
```sql
CREATE TABLE receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_no TEXT,           -- e.g., "140877542509060048"
    timestamp TEXT,             -- ISO format
    plain_text TEXT,           -- Full receipt text
    raw_data BLOB,             -- Original ESC/POS binary
    dishes TEXT,               -- JSON array (deprecated)
    created_at TEXT,           -- Database insertion time
    processed BOOLEAN DEFAULT 0
);
```

### Sample SQLite Record
```json
{
  "id": 12345,
  "receipt_no": "140877542509060048",
  "timestamp": "2025-09-06T18:45:00",
  "plain_text": "制作分单 - 荤菜档\n档口: 荤菜\n桌号: 包间-包间\n...",
  "raw_data": "<binary ESC/POS data>",
  "dishes": null,
  "created_at": "2025-09-06T10:45:00Z",
  "processed": 0
}
```

## 3. Order Processing (order_processor.py)

### Station Mapping (STATION_MAP)
```python
STATION_MAP = {
    '荤菜': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
    '素菜': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
    '酒水': 'd4e5f6a7-b8c9-0123-defa-456789012345',
    '主食': 'e5f6a7b8-c9d0-1234-efab-567890123456',  # Reserved
    '汤品': 'f6a7b8c9-d0e1-2345-fabc-678901234567',  # Reserved
    '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',
    '凉菜': '581b60be-428a-4673-9147-2c197478392b',  # Fixed 2025-09-06
    '其他': 'a7b8c9d0-e1f2-3456-abcd-789012345678'   # Same as 小吃
}
```

### Cold Dishes Override
```python
COLD_DISHES_OVERRIDE = {
    '贵州非遗丝娃娃',  # Always → 凉菜
    '野佐料擂椒皮蛋',  # Always → 凉菜
    '贵阳非遗脆三丁',  # Always → 凉菜
    '木姜子鸡爪',      # Always → 凉菜
    '老醋花生',        # Always → 凉菜
    '凉拌土豆丝',      # Always → 凉菜
    '拍黄瓜',         # Always → 凉菜
    '凉拌黄瓜',       # Always → 凉菜
    '凉拌海带丝',      # Always → 凉菜
}
```

### Processing Logic

#### For Customer Orders (客单)
```python
# Detection: "订单类型: 客户订单" in text
# Action: Create order in order_orders table
# Station: NULL (by design - customers don't specify stations)

order_data = {
    'restaurant_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'receipt_no': receipt_no,
    'table_no': table_no,
    'station_id': NULL,  # Always NULL for customer orders
    'order_type': 'dine_in',
    'status': 'pending'
}
→ INSERT INTO order_orders
```

#### For Kitchen Slips (制作分单)
```python
# Detection: "制作分单" in text
# Action: Parse station and dishes, insert to order_dishes

# Step 1: Extract station
station_match = re.search(r'档口[:：]\s*([^\n]+)', text)
station_name = "荤菜"  # Example

# Step 2: Map to UUID
station_id = STATION_MAP[station_name]  # → "b2c3d4e5-f6a7-8901-bcde-f23456789012"

# Step 3: Check cold dishes override
if dish_name in COLD_DISHES_OVERRIDE:
    station_id = STATION_MAP['凉菜']  # → "581b60be-428a-4673-9147-2c197478392b"

# Step 4: Insert each dish
dish_data = {
    'restaurant_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'receipt_no': receipt_no,
    'name': dish_name,
    'quantity': quantity,
    'station_id': station_id,  # UUID from mapping
    'table_no': table_no,
    'status': 'pending'
}
→ INSERT INTO order_dishes
```

## 4. Supabase Tables

### order_orders Table
```sql
CREATE TABLE order_orders (
    id UUID PRIMARY KEY,
    restaurant_id UUID,        -- Fixed: a1b2c3d4-e5f6-7890-abcd-ef1234567890
    receipt_no TEXT,           -- e.g., "140877542509060048"
    table_no TEXT,            -- e.g., "包间-包间"
    order_type TEXT,          -- 'dine_in'
    status TEXT,              -- 'pending', 'preparing', 'completed'
    raw_data JSONB,           -- Full receipt text
    ordered_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### order_dishes Table
```sql
CREATE TABLE order_dishes (
    id UUID PRIMARY KEY,
    restaurant_id UUID,        -- Fixed: a1b2c3d4-e5f6-7890-abcd-ef1234567890
    receipt_no TEXT,           -- Links to order
    name TEXT,                -- Dish name
    quantity INTEGER,
    station_id UUID,          -- From STATION_MAP or NULL
    table_no TEXT,
    status TEXT,              -- 'pending', 'preparing', 'completed'
    prep_time_minutes INTEGER,
    urgency_level TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## 5. Complete Mapping Examples

### Example 1: Meat Dish (红烧肉)
```
POS Printer:        "档口: 荤菜"
                         ↓
SQLite:            plain_text contains "档口: 荤菜"
                         ↓
order_processor:   '荤菜' → 'b2c3d4e5-f6a7-8901-bcde-f23456789012'
                         ↓
Supabase:          station_id = 'b2c3d4e5-f6a7-8901-bcde-f23456789012'
```

### Example 2: Cold Dish (木姜子鸡爪)
```
POS Printer:        "档口: 凉菜"
                         ↓
SQLite:            plain_text contains "档口: 凉菜"
                         ↓
order_processor:   '凉菜' → '581b60be-428a-4673-9147-2c197478392b'
                         ↓
                   Check: '木姜子鸡爪' in COLD_DISHES_OVERRIDE? Yes
                   (Override not needed since already correct)
                         ↓
Supabase:          station_id = '581b60be-428a-4673-9147-2c197478392b'
```

### Example 3: Misclassified Cold Dish (Before Fix)
```
POS Printer:        "档口: 凉菜"
                         ↓
SQLite:            plain_text contains "档口: 凉菜"
                         ↓
order_processor:   '凉菜' → 'a7b8c9d0-e1f2-3456-abcd-789012345678' (WRONG!)
                   (This was 小吃's UUID due to duplicate)
                         ↓
Supabase:          station_id = 'a7b8c9d0-e1f2-3456-abcd-789012345678'
                   (Appeared as 小吃 station)
```

### Example 4: Customer Order
```
POS Printer:        No 档口 field (customer order)
                         ↓
SQLite:            plain_text contains "订单类型: 客户订单"
                         ↓
order_processor:   Identified as customer order
                   → Insert to order_orders (not order_dishes)
                   → station_id = NULL (by design)
                         ↓
Supabase:          order_orders.station_id = NULL
```

## 6. Station Summary

| Chinese | English | UUID | Status | Dishes Count |
|---------|---------|------|--------|--------------|
| 荤菜 | Meat | `b2c3d4e5-f6a7-8901-bcde-f23456789012` | ✅ Active | 18 |
| 素菜 | Vegetable | `c3d4e5f6-a7b8-9012-cdef-345678901234` | ✅ Active | 12 |
| 酒水 | Beverages | `d4e5f6a7-b8c9-0123-defa-456789012345` | ✅ Active | 19 |
| 小吃 | Snacks | `a7b8c9d0-e1f2-3456-abcd-789012345678` | ✅ Active | 13 |
| 凉菜 | Cold Dishes | `581b60be-428a-4673-9147-2c197478392b` | ✅ Active | 3+ |
| 主食 | Staple Food | `e5f6a7b8-c9d0-1234-efab-567890123456` | ⚫ Reserved | 0 |
| 汤品 | Soup | `f6a7b8c9-d0e1-2345-fabc-678901234567` | ⚫ Reserved | 0 |
| 其他 | Other | `a7b8c9d0-e1f2-3456-abcd-789012345678` | ⚫ Reserved | 0 |

## 7. Data Validation Rules

### Receipt Processing
1. **Customer orders** → Always NULL station_id
2. **Kitchen slips** → Must have valid station from STATION_MAP
3. **Unknown stations** → Reject with error (no default assignment)
4. **Cold dishes** → Override to 凉菜 regardless of source station

### Duplicate Prevention
- Primary key: `receipt_no` + `dish_name` + `station_id`
- Duplicate attempts logged but not inserted
- Expected behavior for retried receipts

### Station Assignment Priority
1. Check COLD_DISHES_OVERRIDE first
2. Use station from receipt text (档口: X)
3. No fallback - error if station not found

## 8. Historical Issues & Fixes

### Issue 1: Duplicate UUID (Fixed 2025-09-06)
- **Problem**: 凉菜 and 小吃 had same UUID
- **Impact**: 23 cold dish orders wrongly assigned
- **Fix**: New UUID for 凉菜: `581b60be-428a-4673-9147-2c197478392b`

### Issue 2: Multi-line Dish Names
- **Problem**: Long dish names split across lines
- **Example**: "木姜子鸡爪（特色" on line 1, "凉菜）" on line 2
- **Fix**: Parenthesis-aware parsing to concatenate lines

### Issue 3: NULL Station IDs
- **Not a problem**: Customer orders intentionally have NULL
- **Design**: Only kitchen slips get station assignments
- **Ratio**: ~4 kitchen slips per customer order

## 9. Monitoring & Debugging

### Check Receipt Flow
```bash
# Recent receipts in SQLite
sqlite3 receipts.db "SELECT receipt_no, datetime(created_at, 'localtime'), 
  CASE WHEN plain_text LIKE '%客单%' THEN 'Customer' ELSE 'Kitchen' END as type
  FROM receipts ORDER BY created_at DESC LIMIT 10;"

# Check station assignments
sqlite3 receipts.db "SELECT DISTINCT 
  substr(plain_text, instr(plain_text, '档口:'), 20) as station
  FROM receipts WHERE plain_text LIKE '%档口:%';"
```

### Verify Supabase Mapping
```sql
-- Check station distribution
SELECT station_id, COUNT(*) as count
FROM order_dishes
WHERE station_id IS NOT NULL
GROUP BY station_id
ORDER BY count DESC;

-- Find misclassified dishes
SELECT name, station_id
FROM order_dishes
WHERE name IN ('贵州非遗丝娃娃', '野佐料擂椒皮蛋', '贵阳非遗脆三丁')
  AND station_id != '581b60be-428a-4673-9147-2c197478392b';
```

## 10. System Architecture

```
┌─────────────┐     TCP:9100      ┌──────────────────────┐
│ POS Terminal├──────────────────→│ printer_api_service  │
└─────────────┘   ESC/POS cmds    │   - TCP Listener     │
                                   │   - ESCPOSParser     │
                                   │   - Receipt Storage  │
                                   └─────────┬────────────┘
                                             │
                                             ↓ SQLite
                                   ┌──────────────────────┐
                                   │   receipts.db        │
                                   │   - receipt_no       │
                                   │   - plain_text       │
                                   │   - raw_data         │
                                   └─────────┬────────────┘
                                             │
                                             ↓ Process
                                   ┌──────────────────────┐
                                   │  order_processor.py  │
                                   │   - Parse receipts   │
                                   │   - Map stations     │
                                   │   - Apply overrides  │
                                   └─────────┬────────────┘
                                             │
                                             ↓ HTTPS
                                   ┌──────────────────────┐
                                   │     Supabase         │
                                   │   - order_orders     │
                                   │   - order_dishes     │
                                   │   - kitchen_stations │
                                   └──────────────────────┘
```

---

**Last Updated**: 2025-09-06 21:50 CST  
**Version**: 2.0 (Post-UUID fix)