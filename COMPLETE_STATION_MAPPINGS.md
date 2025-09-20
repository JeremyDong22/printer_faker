# Complete Station Mappings Documentation

**System**: Printer Faker → Supabase Integration  
**Date**: 2025-09-06

## Station UUID Mappings (order_processor.py)

These are the official station mappings used to convert Chinese station names to UUIDs:

| Station Name | UUID | Status | Description |
|-------------|------|--------|-------------|
| **荤菜** | `b2c3d4e5-f6a7-8901-bcde-f23456789012` | 🟢 Active | Meat dishes |
| **素菜** | `c3d4e5f6-a7b8-9012-cdef-345678901234` | 🟢 Active | Vegetable dishes |
| **酒水** | `d4e5f6a7-b8c9-0123-defa-456789012345` | 🟢 Active | Beverages |
| **小吃** | `a7b8c9d0-e1f2-3456-abcd-789012345678` | 🟢 Active | Snacks |
| **凉菜** | `581b60be-428a-4673-9147-2c197478392b` | 🟢 Active | Cold dishes (FIXED) |
| ~~**主食**~~ | `e5f6a7b8-c9d0-1234-efab-567890123456` | ❌ Not in POS | Never appears in receipts |
| ~~**汤品**~~ | `f6a7b8c9-d0e1-2345-fabc-678901234567` | ❌ Not in POS | Never appears in receipts |
| ~~**其他**~~ | `a7b8c9d0-e1f2-3456-abcd-789012345678` | ❌ Not in POS | Never appears in receipts |

## Data Flow & Mapping Process

```
POS Terminal Receipt
    ↓
TCP Port 9100 (printer_api_service_v2.py)
    ↓
SQLite Database (receipts.db)
    ↓
order_processor.py
    ├─ Extract station name: "档口: 小吃"
    ├─ Map via STATION_MAP: 小吃 → a7b8c9d0-e1f2-3456-abcd-789012345678
    └─ Insert to Supabase with station_id UUID
```

## Station Dish Assignments Comparison

### 🏪 小吃 (Snacks) Station
**UUID**: `a7b8c9d0-e1f2-3456-abcd-789012345678`

| Source | Dish Count | Dishes |
|--------|------------|--------|
| **Local SQLite** | 13 | 老凯里非遗酸汤, 干巴菌炒饭, 雪顶冰淇淋玉米粑, 怪噜洋芋, 火烧云铜锅油焖鸡, 白米饭, 野菜卷, 山玫瑰炸乳扇, 傣村手撕罗非鱼, 苗侗空气丸子, 糟辣椒炒饭, 息烽虎皮猪蹄, (赠)野菜卷 |
| **Supabase** | 16 | Same as above + 贵州非遗丝娃娃, 贵阳非遗脆三丁, 野佐料擂椒皮蛋 |

**Note**: In Supabase, this station appears as "小吃/其他" due to the duplicate UUID with 其他.

### 🏪 凉菜 (Cold Dishes) Station
**UUID**: `581b60be-428a-4673-9147-2c197478392b`

| Source | Dish Count | Dishes |
|--------|------------|--------|
| **Local SQLite** | 3 | 木姜子鸡爪, 贵州非遗丝娃娃, 野佐料擂椒皮蛋 |
| **Supabase** | 1 | 木姜子鸡爪 |

**Issue**: Some dishes (贵州非遗丝娃娃, 野佐料擂椒皮蛋) are in 凉菜 locally but in 小吃 in Supabase.

### 🏪 荤菜 (Meat) Station
**UUID**: `b2c3d4e5-f6a7-8901-bcde-f23456789012`

| Source | Dish Count | Sample Dishes |
|--------|------------|---------------|
| **Local SQLite** | 18 | 乌鱼片, 云山雪花吊龙, 安格斯雪花牛, 净水鲜虾, 野蒜酥五花趾... |
| **Supabase** | 33 | Same core dishes + test entries |

### 🏪 素菜 (Vegetable) Station
**UUID**: `c3d4e5f6-a7b8-9012-cdef-345678901234`

| Source | Dish Count | Sample Dishes |
|--------|------------|---------------|
| **Local SQLite** | 13 | 彩云土豆, 山药, 三脆碗, 石磨黑豆腐, 甜笋（刺身级）... |
| **Supabase** | 14 | Same + 鲜百合, 实时测试菜品 |

### 🏪 酒水 (Beverages) Station
**UUID**: `d4e5f6a7-b8c9-0123-defa-456789012345`

| Source | Dish Count | Sample Dishes |
|--------|------------|---------------|
| **Local SQLite** | 21 | 五指毛桃山茶, 柠檬山茶, 野刺梨山茶, 可口可乐, 加多宝... |
| **Supabase** | 40 | Same core beverages + variations |

### 🏪 汤品 (Soup) Station - ANOMALY
**UUID**: `f6a7b8c9-d0e1-2345-fabc-678901234567`

| Source | Dish Count | Dishes |
|--------|------------|--------|
| **Local SQLite** | 0 | None |
| **Supabase** | 1 | 老凯里非遗酸汤 |

**Issue**: 老凯里非遗酸汤 is in 汤品 in Supabase but in 小吃 locally. This is likely a misclassification.

## Key Findings

1. **Mapping Consistency**: The core mapping logic works correctly - station names from receipts are converted to UUIDs consistently.

2. **Data Discrepancies**: 
   - Some dishes appear in different stations between local and Supabase
   - 老凯里非遗酸汤 is incorrectly in 汤品 station in Supabase (should be 小吃)
   - 贵州非遗丝娃娃 and 野佐料擂椒皮蛋 are split between 凉菜 (local) and 小吃 (Supabase)

3. **Cold Dishes Fix**: Successfully removed all traditional cold dishes (老醋花生, 凉拌土豆丝, 拍黄瓜, 木姜子鸡爪) from 小吃 station.

4. **Station Usage**:
   - **5 REAL stations from POS**: 荤菜, 素菜, 酒水, 小吃, 凉菜
   - **3 FAKE stations in code only**: 主食, 汤品, 其他 (never appear in receipts)

## Status Update (Confirmed & Fixed)

1. **✅ Fixed Cold Dishes Classification**: 
   - 贵州非遗丝娃娃, 野佐料擂椒皮蛋, and 贵阳非遗脆三丁 confirmed as COLD DISHES
   - POS correctly sends them with "档口: 凉菜"
   - 23 historical orders moved from 小吃 to 凉菜 station
   - Cold dishes override added in code for safety

2. **⚠️ 老凯里非遗酸汤**: Currently in 汤品 in Supabase but should be in 小吃 (it's a specialty sour soup, not a cold dish)

3. **📝 Cleanup Needed**: Remove 主食, 汤品, 其他 from code - they don't exist in POS system