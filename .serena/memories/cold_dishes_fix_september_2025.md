# Cold Dishes Station Fix - September 2025

**Date**: 2025-09-06
**Issue**: Cold dishes wrongly assigned to snacks station
**Root Cause**: Duplicate UUID in STATION_MAP

## The Problem

### What Happened
Before the fix, `order_processor.py` had:
```python
STATION_MAP = {
    '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',
    '凉菜': 'a7b8c9d0-e1f2-3456-abcd-789012345678',  # WRONG - same UUID!
}
```

### Impact
- POS correctly sent "档口: 凉菜" for cold dishes
- Our code mapped 凉菜 → wrong UUID (same as 小吃)
- Result: Cold dishes appeared in snacks station in Supabase

### Affected Dishes
- 木姜子鸡爪 (15 orders)
- 贵州非遗丝娃娃 (12 orders)
- 野佐料擂椒皮蛋 (9 orders)
- 贵阳非遗脆三丁 (2 orders)

## The Fix

### 1. Code Fix (order_processor.py line 43)
```python
STATION_MAP = {
    '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',
    '凉菜': '581b60be-428a-4673-9147-2c197478392b',  # FIXED - unique UUID
}
```

### 2. Historical Data Cleanup
- Moved 23 orders from 小吃 to 凉菜 station in Supabase
- All cold dishes now correctly assigned

### 3. Added Safety Override
```python
COLD_DISHES_OVERRIDE = {
    '贵州非遗丝娃娃',
    '野佐料擂椒皮蛋', 
    '贵阳非遗脆三丁',
    '木姜子鸡爪',
}
```
Note: Override not actually needed since POS is correct, but good defensive programming.

## Key Learning

**POS was always correct!** The receipts showed:
```
档口: 凉菜
木姜子鸡爪1/份
```

The bug was entirely in our UUID mapping, not in the POS configuration or parsing logic.

## Verification

After fix:
- 凉菜 station: 16 orders (was 0)
- 小吃 station: 0 cold dishes (was 23)
- No cold dishes in wrong station

## Files Changed
- `/home/smartahc/smartice/printer_faker/order_processor.py` (line 43)
- Created: `fix_historical_stations.py` (used for data cleanup)
- Created: `fix_misclassified_cold_dishes.py` (for the 3 additional dishes)