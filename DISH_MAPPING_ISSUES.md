# Dish Mapping Issues and Solutions

**Date**: 2025-09-06  
**System**: POS Printer → SQLite → Supabase

## Summary of Issues

After analyzing dish mappings across all systems, we found several categories of issues:

## 1. ❌ Station Misassignments

### 老凯里非遗酸汤
- **Current**: In 汤品 station (UUID: f6a7b8c9-d0e1-2345-fabc-678901234567)
- **Should be**: In 小吃 station
- **Created**: 2025-08-26
- **Issue**: Assigned to non-existent station (汤品 doesn't exist in POS)
- **Solution**: Move to 小吃 station

## 2. ❌ Test Data in Production

Found 5 test dishes that should be removed:
- Test Realtime Dish - 实时测试菜品
- 🔥 测试红烧肉 (Test Dish)
- Test Realtime Dish - 12:02:28
- 🎯 REALTIME WORKING TEST
- 🔴 REALTIME TEST DISH
- 🚀 实时测试菜品
- 测试菜品 - 实时更新

**Solution**: Delete all test entries from production

## 3. ❌ Malformed/Partial Dishes

These are parsing errors where multi-line dishes were split incorrectly:

### Broken parentheses (multi-line parsing failure):
- **和牛）** - 3 orders (missing first part)
- **胸口）** - 41 orders (missing first part)
- **大地飞雪（M9纯血** - incomplete (missing closing parenthesis)
- **紫苏半边云（鲜牛** - incomplete

### Modifiers incorrectly stored as dishes:
- **-做法:冰1** - 20 orders (this is a modifier, not a dish)
- **-做法:冰2** - 5 orders (modifier)
- **-做法:冰3** - 1 order (modifier)
- **-五指毛桃山茶** - (modifier line starting with -)

### Truncated names:
- **(打包)五指毛桃山** - 1 order (truncated name)
- **(赠)可口可乐（听** - missing closing parenthesis

**Root Cause**: Multi-line parsing bug when dish names span multiple lines
**Solution**: Already fixed in code with parenthesis-aware parsing

## 4. ⚠️ Parsing Differences

### Number removal inconsistency:
- **Printer**: 紫苏半边云（鲜牛1胸口）
- **SQLite/Supabase**: 紫苏半边云（鲜牛胸口）
- **Issue**: The "1" is being removed during parsing
- **Impact**: Same dish appears as two different items

### Similar issues:
- (赠)可口可乐（听1） vs (赠)可口可乐（听）
- (赠)可口可乐（听2） vs (赠)可口可乐（听）

## 5. ⚠️ Dishes Only in Supabase

These dishes exist in Supabase but never appeared in recent receipts:

| Dish | First Seen | Station | Likely Cause |
|------|------------|---------|--------------|
| 贵阳非遗脆三丁 | 2025-09-02 | 凉菜 | Old menu item? |
| 血皮菜 | 2025-08-31 | 素菜 | Old menu item? |
| 鲜百合 | 2025-09-02 | 素菜 | Old menu item? |
| 净海老鱼花胶 | 2025-09-05 | 荤菜 | Possible parsing error |

## 6. ✅ Perfect Matches

Good news - these stations have perfect mapping:
- **小吃 station**: All 13 dishes map perfectly

## Recommended Actions

### Immediate Fixes Needed:

1. **Fix 老凯里非遗酸汤 station assignment**
```python
# Move from 汤品 to 小吃
UPDATE order_dishes 
SET station_id = 'a7b8c9d0-e1f2-3456-abcd-789012345678'
WHERE name = '老凯里非遗酸汤' 
AND station_id = 'f6a7b8c9-d0e1-2345-fabc-678901234567';
```

2. **Remove test dishes**
```python
DELETE FROM order_dishes 
WHERE name ILIKE '%test%' 
OR name LIKE '🔥%' 
OR name LIKE '🎯%' 
OR name LIKE '🔴%'
OR name LIKE '🚀%';
```

3. **Fix malformed dishes**
```python
# Delete partial dishes
DELETE FROM order_dishes 
WHERE name IN ('和牛）', '胸口）', '大地飞雪（M9纯血', '紫苏半边云（鲜牛');

# Delete modifiers stored as dishes
DELETE FROM order_dishes 
WHERE name LIKE '-%' 
OR name LIKE '-做法:%';
```

### Code Improvements:

1. **Enhance multi-line parsing** - Already implemented with parenthesis-aware logic

2. **Add validation to reject**:
   - Dishes starting with "-" (modifiers)
   - Dishes ending with unclosed parenthesis
   - Test dishes containing "test", "测试", etc.

3. **Standardize number handling**:
   - Decide whether to keep or remove numbers in dish names
   - Apply consistently across parsing

## Mapping Statistics

| System | Total Unique Dishes | Issues |
|--------|---------------------|--------|
| POS Printer | ~80 | Source of truth |
| SQLite | ~81 | Minor parsing differences |
| Supabase | ~120 | Contains test data + malformed entries |

## Perfect Mapping Goal

After fixes, we should have:
- ✅ No test dishes in production
- ✅ No malformed/partial dishes
- ✅ No dishes in non-existent stations (主食, 汤品, 其他)
- ✅ Consistent parsing between SQLite and Supabase
- ✅ All modifiers excluded from dish names