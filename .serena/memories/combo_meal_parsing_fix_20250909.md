# Combo Meal Parsing Fix - September 9, 2025

## Problem
Combo meals (套餐) from group buying platforms like Meituan were causing processing errors:
1. Long combo names split across lines in kitchen slips
2. Combo names being saved as dishes instead of actual food items
3. Duplicate key violations when multiple stations tried to insert same combo name

### Example of Split Combo Name
```
美团团购-入野·双1/份
人放松Chill套餐
```
Should be: "美团团购-入野·双人放松Chill套餐"

## Root Cause
- Combo meals are marketing names containing multiple actual dishes
- Kitchen slips were trying to save combo names as dishes
- Each station slip for same combo caused duplicate key error
- Long names (31+ chars) split mid-word across lines

## Solution Implemented
Updated `parse_kitchen_slip_dishes()` in order_processor.py:

### 1. Combo Detection
- Detect combo headers by keywords: '美团团购', '套餐', 'Chill'
- Set `combo_meal_active` flag when combo detected
- Combine split combo names across lines

### 2. Skip Combo Headers
- Don't save combo name to database
- Only process sub-items (lines starting with '-')
- These are the actual dishes kitchens need to prepare

### 3. Process Actual Dishes
```python
if trimmed.startswith('-'):
    if combo_meal_active:
        # Process the actual dish from combo meal
        sub_item = trimmed[1:].strip()  # Remove "-" prefix
        # Extract dish name and quantity
        # Save actual dish like "木姜子鲜黄牛肉"
```

## Examples
### Combo Meal in Customer Order
```
美团团购-入野·双人放松Chill套餐  230元
  -木姜子鲜黄牛肉
  -安格斯雪花牛
  -手工水晶滑肉
  (18 more items...)
```

### Kitchen Slip Processing
**Before Fix**: Tried to save "美团团购-入野·双" → Duplicate key error
**After Fix**: Saves "木姜子鲜黄牛肉", "安格斯雪花牛", etc.

## Testing
Successfully tested with:
- Receipt 140877542509080012 (problematic combo)
- Regular multi-line dishes still work
- Service running in production since 16:17

## Git Branch
Created feature branch: `fix/combo-meal-parsing`
Pushed to: https://github.com/JeremyDong22/printer_faker.git

## Key Insight
Combo meals are NOT new dishes - they're pre-defined sets of existing menu items at special prices. Kitchen stations only need the actual dish names, not marketing names.