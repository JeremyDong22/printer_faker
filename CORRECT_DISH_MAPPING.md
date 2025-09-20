# Correct Dish Mapping Reference

**Generated**: 2025-09-06  
**Purpose**: Define the CORRECT dish mappings from POS to Supabase

## Station Mappings (Only 5 Real Stations)

| Station | UUID | Description |
|---------|------|-------------|
| 荤菜 | `b2c3d4e5-f6a7-8901-bcde-f23456789012` | Meat dishes |
| 素菜 | `c3d4e5f6-a7b8-9012-cdef-345678901234` | Vegetable dishes |
| 酒水 | `d4e5f6a7-b8c9-0123-defa-456789012345` | Beverages |
| 小吃 | `a7b8c9d0-e1f2-3456-abcd-789012345678` | Snacks & rice |
| 凉菜 | `581b60be-428a-4673-9147-2c197478392b` | Cold dishes |

## ✅ CORRECT Dish Assignments (From POS Analysis)

### 荤菜 Station (16 dishes)
```
乌鱼片
云山雪花吊龙
净水鲜虾
安格斯雪花牛
木姜子鲜黄牛肉
野蒜酥五花趾
过油响皮
海鲜拼盘
牛肉
净海老鱼花胶
鲜虾
老鱼花胶
大地飞雪（M9纯血和牛）
紫苏半边云（鲜牛胸口）
豪猪
草原熏羔羊
```

### 素菜 Station (11 dishes)
```
彩云土豆
山药
石磨黑豆腐
三脆碗
野篮子菌菇组合
甜笋（刺身级）
藕
青岩黄金豆腐
鲜花饼
鲜黄花
野菜
```

### 酒水 Station (19 dishes)
```
五指毛桃山茶
柠檬山茶
野刺梨山茶
可口可乐（听）
光明Look酸奶
加多宝（听）
百岁山
纯生
炸酒
老雪花
新疆老浓黑
茅台啤酒
青岛啤酒
凯里亮欢寨米酒
岩博人民小酒
仁怀小糊涂
茅酒
仁怀20
仁怀30
```

### 小吃 Station (13 dishes)
```
老凯里非遗酸汤
干巴菌炒饭
雪顶冰淇淋玉米粑
怪噜洋芋
火烧云铜锅油焖鸡
白米饭
野菜卷
山玫瑰炸乳扇
傣村手撕罗非鱼
苗侗空气丸子
糟辣椒炒饭
息烽虎皮猪蹄
贵州非遗丝娃娃 (Note: POS sends as 凉菜 but appears here)
```

### 凉菜 Station (3 dishes confirmed)
```
木姜子鸡爪
贵州非遗丝娃娃
野佐料擂椒皮蛋
```

## ❌ WRONG - Items to Remove/Fix

### 1. Test Dishes (Should NOT exist)
```
🔴 REALTIME TEST DISH
🔥 测试红烧肉 (Test Dish)
🎯 REALTIME WORKING TEST
Test Realtime Dish - 实时测试菜品
Test Realtime Dish - 12:02:28
🚀 实时测试菜品
测试菜品 - 实时更新
```

### 2. Malformed Dishes (Parsing errors)
```
和牛） - Should be part of: 大地飞雪（M9纯血和牛）
胸口） - Should be part of: 紫苏半边云（鲜牛胸口）
大地飞雪（M9纯血 - Missing closing parenthesis
紫苏半边云（鲜牛 - Missing closing parenthesis
(打包)五指毛桃山 - Truncated name
(赠)可口可乐（听 - Missing closing parenthesis
```

### 3. Modifiers (NOT dishes)
```
-做法:冰1
-做法:冰2
-做法:冰3
-五指毛桃山茶
```

### 4. Number Variations (Should be standardized)
```
紫苏半边云（鲜牛1胸口） → 紫苏半边云（鲜牛胸口）
(赠)可口可乐（听1） → (赠)可口可乐（听）
(赠)可口可乐（听2） → (赠)可口可乐（听）
```

## 📊 Summary of Issues

| Issue Type | Count | Action Needed |
|------------|-------|---------------|
| Test dishes | 7+ | DELETE |
| Malformed dishes | 6+ | DELETE |
| Modifiers as dishes | 4+ | DELETE |
| Wrong station | 0 (老凯里非遗酸汤 fixed) | ✅ |
| Number variations | 3+ | STANDARDIZE |
| Non-existent stations | 3 (主食,汤品,其他) | REMOVE FROM CODE |

## 🎯 Goal State

After cleanup, we should have:
- **~62 unique dishes** total (not 100+)
- **5 stations** only (no 汤品, 主食, 其他)
- **No test data**
- **No malformed entries**
- **No modifiers as dishes**
- **Consistent naming** (no number variations)

## Validation Query

To check if mapping is correct:
```sql
-- Should return 0 rows
SELECT name FROM order_dishes 
WHERE name LIKE '%test%' 
   OR name LIKE '-%'
   OR name LIKE '%）' AND name NOT LIKE '%（%'
   OR name LIKE '%（' AND name NOT LIKE '%）%'
   OR station_id IN (
     'e5f6a7b8-c9d0-1234-efab-567890123456', -- 主食 (doesn't exist)
     'f6a7b8c9-d0e1-2345-fabc-678901234567'  -- 汤品 (doesn't exist)
   );
```