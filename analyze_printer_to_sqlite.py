#!/usr/bin/env python3
"""
Analyze POS Printer → SQLite mapping completeness and uniqueness
Focus only on local data flow, not Supabase
"""

import sqlite3
import re
from collections import defaultdict
from datetime import datetime, timedelta

def analyze_printer_receipts():
    """Analyze raw printer receipts in SQLite"""
    conn = sqlite3.connect('receipts.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("POS PRINTER → SQLite MAPPING ANALYSIS")
    print("=" * 80)
    
    # Get recent receipts (last 7 days)
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
    
    cursor.execute('''
        SELECT plain_text, receipt_no, created_at
        FROM receipts 
        WHERE created_at > ?
        ORDER BY created_at DESC
    ''', (seven_days_ago,))
    
    all_receipts = cursor.fetchall()
    print(f"\n📊 Analyzing {len(all_receipts)} receipts from last 7 days\n")
    
    # Categorize receipts
    customer_orders = []
    kitchen_slips = []
    
    for text, receipt_no, created_at in all_receipts:
        if '客单' in text or '订单类型: 客户订单' in text:
            customer_orders.append((text, receipt_no, created_at))
        elif '制作分单' in text or '档口' in text:
            kitchen_slips.append((text, receipt_no, created_at))
    
    print(f"Receipt Types:")
    print(f"  Customer Orders (客单): {len(customer_orders)}")
    print(f"  Kitchen Slips (制作分单): {len(kitchen_slips)}")
    print(f"  Other/Unknown: {len(all_receipts) - len(customer_orders) - len(kitchen_slips)}")
    
    # Analyze kitchen slips (they have station assignments)
    station_dishes = defaultdict(set)  # station -> set of unique dishes
    all_dishes = set()
    parsing_issues = []
    
    print("\n" + "=" * 80)
    print("ANALYZING KITCHEN SLIPS (Station → Dishes)")
    print("=" * 80)
    
    for text, receipt_no, created_at in kitchen_slips:
        # Extract station
        station = None
        lines = text.split('\n')
        
        for line in lines:
            if '档口:' in line or '档口：' in line:
                station = line.split(':')[-1].strip()
                break
        
        if not station:
            parsing_issues.append(f"No station found in receipt {receipt_no}")
            continue
        
        # Extract dishes using the same logic as order_processor.py
        for i, line in enumerate(lines):
            trimmed = line.strip()
            
            # Skip empty lines and modifiers
            if not trimmed or trimmed.startswith('-'):
                continue
            
            # Look for dish pattern: "dish_name + number + / + unit"
            if '/' in trimmed and any(unit in trimmed for unit in ['份', '瓶', '听', '盒', '个', '碗', '杯', '位']):
                # Extract dish name by removing quantity/unit part
                dish_line = re.sub(r'\d+\/[份瓶听盒个碗杯位].*$', '', trimmed).strip()
                
                # Handle multi-line dishes (parenthesis aware)
                if '（' in dish_line and '）' not in dish_line:
                    # Look for continuation on next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if '）' in next_line and '/' not in next_line:
                            dish_line = dish_line + next_line
                            
                # Remove (退) prefix for returned dishes
                dish_line = re.sub(r'^\(退\)', '', dish_line).strip()
                
                # Validate dish name
                if dish_line and len(dish_line) > 1:
                    # Check for potential issues
                    if dish_line.endswith('）') and '（' not in dish_line:
                        parsing_issues.append(f"Orphan closing parenthesis: '{dish_line}' in {receipt_no}")
                    elif dish_line.endswith('（'):
                        parsing_issues.append(f"Unclosed parenthesis: '{dish_line}' in {receipt_no}")
                    elif dish_line.startswith('-'):
                        parsing_issues.append(f"Modifier as dish: '{dish_line}' in {receipt_no}")
                    else:
                        # Good dish
                        station_dishes[station].add(dish_line)
                        all_dishes.add(dish_line)
    
    # Print station summary
    print("\n📍 Stations Found in Printer Data:")
    for station in sorted(station_dishes.keys()):
        dishes = station_dishes[station]
        print(f"\n{station} Station: {len(dishes)} unique dishes")
        # Show first 10 dishes as examples
        for dish in sorted(dishes)[:10]:
            print(f"  - {dish}")
        if len(dishes) > 10:
            print(f"  ... and {len(dishes) - 10} more")
    
    # Check for duplicate dishes across stations
    print("\n" + "=" * 80)
    print("CHECKING FOR DISHES IN MULTIPLE STATIONS")
    print("=" * 80)
    
    dish_to_stations = defaultdict(set)
    for station, dishes in station_dishes.items():
        for dish in dishes:
            dish_to_stations[dish].add(station)
    
    duplicates = {dish: stations for dish, stations in dish_to_stations.items() if len(stations) > 1}
    
    if duplicates:
        print("\n⚠️  Dishes appearing in multiple stations:")
        for dish, stations in sorted(duplicates.items()):
            print(f"  {dish}: {', '.join(sorted(stations))}")
    else:
        print("\n✅ No dishes appear in multiple stations (good!)")
    
    # Analyze customer orders
    print("\n" + "=" * 80)
    print("ANALYZING CUSTOMER ORDERS")
    print("=" * 80)
    
    customer_dishes = set()
    for text, receipt_no, created_at in customer_orders[:50]:  # Sample first 50
        lines = text.split('\n')
        for line in lines:
            # Customer order format: "dish_name  spaces  份1份68" or similar
            # Look for pattern with price at end
            match = re.match(r'^(.+?)\s{2,}[份瓶听盒个碗杯位]\d+[份瓶听盒个碗杯位]\d+', line.strip())
            if match:
                dish_name = match.group(1).strip()
                if dish_name and not dish_name[0].isdigit():
                    customer_dishes.add(dish_name)
    
    print(f"\nFound {len(customer_dishes)} unique dishes in customer orders")
    
    # Compare customer dishes with kitchen dishes
    only_in_customer = customer_dishes - all_dishes
    only_in_kitchen = all_dishes - customer_dishes
    
    if only_in_customer:
        print(f"\n⚠️  Dishes only in customer orders (not in kitchen): {len(only_in_customer)}")
        for dish in sorted(only_in_customer)[:5]:
            print(f"  - {dish}")
    
    if only_in_kitchen:
        print(f"\n⚠️  Dishes only in kitchen slips (not in customer): {len(only_in_kitchen)}")
        for dish in sorted(only_in_kitchen)[:5]:
            print(f"  - {dish}")
    
    # Report parsing issues
    if parsing_issues:
        print("\n" + "=" * 80)
        print("PARSING ISSUES DETECTED")
        print("=" * 80)
        unique_issues = list(set(parsing_issues))[:20]
        for issue in unique_issues:
            print(f"  ❌ {issue}")
        if len(parsing_issues) > 20:
            print(f"  ... and {len(parsing_issues) - 20} more issues")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Total unique dishes from kitchen slips: {len(all_dishes)}")
    print(f"✅ Total stations: {len(station_dishes)}")
    print(f"✅ Stations: {', '.join(sorted(station_dishes.keys()))}")
    
    if not parsing_issues and not duplicates:
        print("\n🎯 PERFECT: No parsing issues or duplicates detected!")
    else:
        print(f"\n⚠️  Issues found: {len(parsing_issues)} parsing issues, {len(duplicates)} duplicate dishes")
    
    conn.close()
    
    # Return data for further analysis
    return {
        'stations': dict(station_dishes),
        'all_dishes': all_dishes,
        'parsing_issues': parsing_issues,
        'duplicates': duplicates
    }

if __name__ == "__main__":
    result = analyze_printer_receipts()
    
    # Write results to file for reference
    with open('printer_sqlite_mapping.txt', 'w', encoding='utf-8') as f:
        f.write("POS PRINTER → SQLite MAPPING\n")
        f.write("=" * 60 + "\n\n")
        
        for station, dishes in sorted(result['stations'].items()):
            f.write(f"{station} Station ({len(dishes)} dishes):\n")
            for dish in sorted(dishes):
                f.write(f"  - {dish}\n")
            f.write("\n")
        
        if result['parsing_issues']:
            f.write("\nParsing Issues:\n")
            for issue in result['parsing_issues'][:50]:
                f.write(f"  - {issue}\n")
    
    print("\n📝 Results saved to printer_sqlite_mapping.txt")