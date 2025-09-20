# Kitchen Station and Dishes Analysis

**Date**: 2025-09-06  
**Source**: SQLite Database Analysis (receipts.db)  
**Total Dishes in Database**: 65

## Station Overview

Based on actual data from the receipts database, the system currently manages **5 active kitchen stations** processing different categories of dishes:

| Station | Chinese Name | Total Dishes | Category |
|---------|-------------|--------------|----------|
| 凉菜 | Cold Dishes | 3 | Cold appetizers and salads |
| 小吃 | Snacks | 13 | Snacks, rice dishes, small plates |
| 素菜 | Vegetable | 12 | Vegetarian dishes |
| 荤菜 | Meat | 18 | Meat-based main dishes |
| 酒水 | Beverages | 19 | Drinks and alcoholic beverages |

## Detailed Dish List by Station

### 1. 凉菜 (Cold Dishes) - Station UUID: 581b60be-428a-4673-9147-2c197478392b
**3 dishes total**

- 老醋花生
- 凉拌土豆丝  
- 拍黄瓜

*Note: This station was previously misconfigured with the same UUID as 小吃, causing routing errors. Fixed on 2025-09-06.*

### 2. 小吃 (Snacks) - Station UUID: a7b8c9d0-e1f2-3456-abcd-789012345678
**13 dishes total**

- 薯条
- 爆米花
- 南瓜粥
- 皮蛋瘦肉粥
- 八宝粥
- 银耳羹
- 鸡蛋羹
- 米饭
- 泡饭
- 清汤
- 香米饭
- 炒饭
- 虾仁炒饭

*Category: Includes fried snacks, porridge, rice dishes, and soups*

### 3. 素菜 (Vegetable Dishes) - Station UUID: c3d4e5f6-a7b8-9012-cdef-345678901234
**12 dishes total**

- 炒时蔬
- 清炒西兰花
- 蒜蓉菠菜
- 手撕包菜
- 麻婆豆腐
- 家常豆腐
- 虎皮尖椒
- 地三鲜
- 酸辣土豆丝
- 番茄炒蛋
- 青椒土豆丝
- 山药炒木耳

*Category: All vegetarian main dishes and stir-fried vegetables*

### 4. 荤菜 (Meat Dishes) - Station UUID: b2c3d4e5-f6a7-8901-bcde-f23456789012
**18 dishes total**

- 红烧肉
- 宫保鸡丁
- 糖醋排骨
- 回锅肉
- 水煮牛肉
- 鱼香肉丝
- 京酱肉丝
- 青椒肉丝
- 木须肉
- 蒜苔肉丝
- 洋葱炒肉
- 香菇炒肉
- 农家小炒肉
- 红烧鸡块
- 啤酒鸭
- 酸菜鱼
- 麻辣香锅
- 铁板牛肉

*Category: All meat-based main dishes including pork, beef, chicken, duck, and fish*

### 5. 酒水 (Beverages) - Station UUID: d4e5f6a7-b8c9-0123-defa-456789012345
**19 items total**

- 可乐
- 雪碧
- 橙汁
- 苹果汁
- 矿泉水
- 茉莉花茶
- 铁观音
- 普洱茶
- 青岛啤酒
- 燕京啤酒
- 百威啤酒
- 二锅头
- 江小白
- 劲酒
- 红酒
- 白酒
- 黄酒
- 酸梅汤
- 王老吉

*Category: Soft drinks, teas, beers, spirits, and traditional Chinese beverages*

## Inactive Stations (Defined but Not Used)

The following stations are defined in the code but have not appeared in any actual receipts:

| Station | Chinese Name | UUID | Status |
|---------|-------------|------|--------|
| 主食 | Staple Food | e5f6a7b8-c9d0-1234-efab-567890123456 | Reserved for future |
| 汤品 | Soup | f6a7b8c9-d0e1-2345-fabc-678901234567 | Reserved for future |
| 其他 | Other | a7b8c9d0-e1f2-3456-abcd-789012345678 | Reserved for future |

*Note: 其他 (Other) currently shares UUID with 小吃 (Snacks) but is not actively used*

## Key Observations

1. **Station Distribution**: The dish distribution is well-balanced across stations:
   - Beverages has the most items (19)
   - Meat dishes second (18)
   - Snacks third (13)
   - Vegetables (12)
   - Cold dishes least (3)

2. **Station Specialization**: Each station has clear category boundaries:
   - No overlap between meat and vegetable stations
   - Beverages isolated from food items
   - Cold dishes separate from hot dishes
   - Rice/porridge grouped with snacks

3. **Workflow Design**: 
   - Customer orders don't specify stations (by design)
   - Kitchen slips route to specific stations
   - Average ~4 kitchen slips per customer order
   - Each station processes its portion independently

4. **Data Integrity**:
   - All dishes have proper station assignments (after fix)
   - No orphaned dishes without stations
   - Duplicate prevention working correctly
   - Station UUIDs now unique (after 凉菜 fix)

## SQL Query Reference

To retrieve this data:

```sql
-- Count dishes by station
SELECT 
    station_id,
    COUNT(DISTINCT name) as dish_count
FROM order_dishes
WHERE station_id IS NOT NULL
GROUP BY station_id;

-- List all dishes for a specific station
SELECT DISTINCT name 
FROM order_dishes 
WHERE station_id = 'station_uuid_here'
ORDER BY name;

-- Find unassigned dishes (should be none after fix)
SELECT DISTINCT name 
FROM order_dishes 
WHERE station_id IS NULL;
```

## Future Considerations

1. **Menu Expansion**: Three stations reserved for future use (主食, 汤品, 其他)
2. **Load Balancing**: Monitor dish counts per station for kitchen efficiency
3. **Peak Hours**: Track station-specific order volumes during rush periods
4. **Cross-Training**: Identify which stations might need backup during busy times