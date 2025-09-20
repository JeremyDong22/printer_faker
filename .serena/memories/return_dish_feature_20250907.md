# Return Dish Feature Implementation - September 7, 2025

## Overview
Implemented complete return dish (退菜) handling for when customers cancel or exchange items. Previously, return slips were either ignored or processed as regular dishes.

## Real Return Slip Format
```
退菜单
(分单)
桌号: B区-B3
菜品数量
(退)五指毛桃山茶1/份

退菜原因: 换团购

单号: 140877542509070050
操作人: 刘运（管理员）
时间: 2025-09-07 20:07:45
```

## Implementation Details

### 1. Extended Dish Dataclass (lines 22-28)
```python
@dataclass
class Dish:
    name: str
    quantity: int
    station_id: Optional[str] = None
    is_return: bool = False  # NEW: Track returned dishes
```

### 2. Detection Methods (lines 175-182)
```python
def is_return_slip(self, text: str) -> bool:
    """Check if this is a return dish slip (退菜单)"""
    return '退菜单' in text or '退菜原因' in text

def extract_return_reason(self, text: str) -> Optional[str]:
    """Extract return reason from receipt"""
    match = re.search(r'退菜原因[:：]\s*([^\n]+)', text)
    return match.group(1).strip() if match else None
```

### 3. Updated Dish Parsing (lines 270-302)
The `parse_kitchen_slip_dishes()` method now:
- Detects "(退)" prefix on dish names
- Sets `is_return=True` for returned dishes
- Removes prefix to get clean dish name

```python
if '(退)' in trimmed:
    is_return = True
    trimmed_for_name = trimmed.replace('(退)', '')
```

### 4. Return Processing Method (lines 435-529)
`process_return_slip()` handles the complete return workflow:

#### For Matched Returns:
```python
# Find original dish in database
result = self.supabase.table('order_dishes').select("*").eq(
    'table_no', table_no
).eq('name', dish.name).in_(
    'status', ['pending', 'preparing']
).order('created_at', desc=True).limit(1).execute()

# Update status to 'returned'
self.supabase.table('order_dishes').update({
    'status': 'returned',
    'updated_at': datetime.utcnow().isoformat()
}).eq('id', dish_record['id']).execute()
```

#### For Unmatched Returns:
```python
# Create negative quantity record
self.supabase.table('order_dishes').insert({
    'restaurant_id': self.RESTAURANT_ID,
    'receipt_no': receipt_data.get('receipt_no'),
    'name': dish.name,
    'quantity': -dish.quantity,  # Negative indicates return
    'table_no': table_no,
    'status': 'returned',
    'station_id': None,
    'prep_time_minutes': 0,
    'urgency_level': 'normal'
}).execute()
```

### 5. Main Processing Flow Update (lines 417-418)
```python
# Check if this is a return slip
if self.is_return_slip(text):
    return self.process_return_slip(receipt_data, text, table_no)
```

## Database Operations

### Status Flow
- Original dish: `pending` → `preparing` → `returned`
- Return creates audit trail with reason
- Negative quantity for unmatched returns

### Key Benefits
- ✅ Kitchen won't prepare returned dishes
- ✅ Accurate billing with returns tracked
- ✅ Complete audit trail with return reasons
- ✅ Inventory reconciliation support

## Testing
Created `test_return_dish.py` to verify:
- Return slip detection
- Dish parsing with "(退)" prefix
- Database status updates
- Negative quantity handling

## Service Status
Service was restarted at 21:48 CST on September 7, 2025 with return dish handling active.

## Files Modified
- `/home/smartahc/smartice/printer_faker/order_processor.py`
  - Lines 22-28: Dish dataclass
  - Lines 175-182: Return detection methods
  - Lines 270-302: Dish parsing updates
  - Lines 417-418: Main flow update
  - Lines 435-529: Return processing method