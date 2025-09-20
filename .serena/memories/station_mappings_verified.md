# Station Mappings - Verified Perfect State

**Date Verified**: 2025-09-06
**Status**: ✅ PERFECT POS → SQLite mapping

## Only 5 Real Stations Exist in POS

```python
STATION_MAP = {
    '荤菜': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',  # Meat - 18 dishes
    '素菜': 'c3d4e5f6-a7b8-9012-cdef-345678901234',  # Vegetable - 12 dishes
    '酒水': 'd4e5f6a7-b8c9-0123-defa-456789012345',  # Beverages - 20 dishes
    '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',  # Snacks - 13 dishes
    '凉菜': '581b60be-428a-4673-9147-2c197478392b',  # Cold dishes - 3 dishes
}
```

## DO NOT USE These Fake Stations
- 主食 (Staple food) - DOES NOT EXIST in POS
- 汤品 (Soup) - DOES NOT EXIST in POS  
- 其他 (Other) - DOES NOT EXIST in POS

## Perfect Mapping Statistics
- **66 unique dishes** correctly parsed
- **5 stations** from actual printer data
- **Zero parsing errors**
- **Zero duplicates**
- **100% unique mapping** - each dish belongs to exactly one station

## Key Issues Fixed (2025-09-06)

### 1. 凉菜 UUID Duplicate Fixed
- **Problem**: 凉菜 and 小吃 had same UUID `a7b8c9d0-e1f2-3456-abcd-789012345678`
- **Solution**: 凉菜 now has unique UUID `581b60be-428a-4673-9147-2c197478392b`
- **Impact**: 23 cold dish orders corrected

### 2. Cold Dishes Reassigned
These 3 dishes moved from 小吃 to 凉菜:
- 贵州非遗丝娃娃 (12 orders)
- 野佐料擂椒皮蛋 (9 orders)
- 贵阳非遗脆三丁 (2 orders)

POS was always sending them correctly to 凉菜, but our duplicate UUID caused misrouting.

### 3. Test Data Cleanup
Removed from production:
- Test Realtime Dish variants
- 测试 dishes
- Emoji test dishes (🔥, 🎯, 🔴, 🚀)

### 4. Malformed Entries Fixed
Deleted parsing errors:
- 和牛） - orphan closing parenthesis (41 orders)
- 胸口） - orphan closing parenthesis (3 orders)
- Modifiers like -做法:冰1, -做法:冰2

## Validation
Run this to verify perfect mapping:
```bash
uv run python3 analyze_printer_to_sqlite.py
```

Should show:
- Total unique dishes: 66
- Total stations: 5
- No parsing issues
- No duplicates