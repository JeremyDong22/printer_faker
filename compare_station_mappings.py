#!/usr/bin/env python3
"""
Compare station mappings between local SQLite and Supabase
"""

import os
import sqlite3
import json
from collections import defaultdict
from dotenv import load_dotenv

# Clear proxy settings
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)

from supabase import create_client

load_dotenv()

# Station UUIDs from order_processor.py
STATION_MAP = {
    '荤菜': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
    '素菜': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
    '酒水': 'd4e5f6a7-b8c9-0123-defa-456789012345',
    '主食': 'e5f6a7b8-c9d0-1234-efab-567890123456',
    '汤品': 'f6a7b8c9-d0e1-2345-fabc-678901234567',
    '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',
    '凉菜': '581b60be-428a-4673-9147-2c197478392b',
    '其他': 'a7b8c9d0-e1f2-3456-abcd-789012345678'  # Same as 小吃
}

# Reverse mapping
UUID_TO_NAME = {v: k for k, v in STATION_MAP.items()}
UUID_TO_NAME['a7b8c9d0-e1f2-3456-abcd-789012345678'] = '小吃/其他'  # Handle duplicate

def get_local_data():
    """Get station data from local SQLite"""
    conn = sqlite3.connect('receipts.db')
    cursor = conn.cursor()
    
    # Get all receipts with station info
    cursor.execute('''
        SELECT plain_text, created_at 
        FROM receipts 
        WHERE plain_text LIKE '%档口:%'
        ORDER BY created_at DESC
    ''')
    
    receipts = cursor.fetchall()
    
    # Parse stations and dishes
    station_dishes = defaultdict(set)
    
    for text, created in receipts:
        # Extract station name
        station_name = None
        for line in text.split('\n'):
            if '档口:' in line or '档口：' in line:
                station_name = line.split(':')[-1].strip()
                break
        
        if station_name and station_name in STATION_MAP:
            # Parse dishes from this receipt
            lines = text.split('\n')
            for i, line in enumerate(lines):
                # Look for dish patterns
                if '/' in line and any(unit in line for unit in ['份', '瓶', '听', '盒', '个', '碗', '杯', '位']):
                    # Extract dish name
                    dish = line.split('/')[0].strip()
                    
                    # Handle multi-line dishes
                    if '（' in dish and '）' not in dish:
                        # Check next line
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if '）' in next_line and '/' not in next_line:
                                dish = dish + next_line
                    
                    # Clean up dish name
                    dish = dish.replace('(退)', '').strip()
                    if dish and not dish.startswith('-') and len(dish) > 1:
                        # Remove trailing numbers
                        import re
                        dish = re.sub(r'\d+$', '', dish).strip()
                        station_dishes[station_name].add(dish)
    
    conn.close()
    return station_dishes

def get_supabase_data():
    """Get station data from Supabase"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print('Missing Supabase credentials')
        return {}
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all dishes with station assignments
    result = supabase.table('order_dishes').select('name, station_id').execute()
    
    # Group by station
    station_dishes = defaultdict(set)
    
    for item in result.data:
        if item['station_id']:
            station_name = UUID_TO_NAME.get(item['station_id'], item['station_id'])
            station_dishes[station_name].add(item['name'])
    
    return station_dishes

def main():
    print("=" * 80)
    print("STATION MAPPINGS COMPARISON: Local SQLite vs Supabase")
    print("=" * 80)
    
    # Show the station UUID mappings
    print("\n📋 STATION UUID MAPPINGS (from order_processor.py):")
    print("-" * 80)
    for name, uuid in STATION_MAP.items():
        status = "🟢" if name in ['荤菜', '素菜', '酒水', '小吃', '凉菜'] else "⚫"
        print(f"{status} {name:6} → {uuid}")
    
    # Get data from both sources
    print("\n📊 FETCHING DATA...")
    local_dishes = get_local_data()
    supabase_dishes = get_supabase_data()
    
    # Compare each station
    print("\n" + "=" * 80)
    print("DISHES BY STATION COMPARISON")
    print("=" * 80)
    
    all_stations = set(list(local_dishes.keys()) + list(supabase_dishes.keys()))
    
    for station in sorted(all_stations):
        local = local_dishes.get(station, set())
        supa = supabase_dishes.get(station, set())
        
        print(f"\n🏪 {station}")
        print("-" * 40)
        
        if station in STATION_MAP:
            print(f"UUID: {STATION_MAP[station]}")
        
        print(f"Local SQLite: {len(local)} unique dishes")
        print(f"Supabase:     {len(supa)} unique dishes")
        
        # Find differences
        only_local = local - supa
        only_supa = supa - local
        both = local & supa
        
        if both and len(both) <= 10:
            print(f"\n✅ In both ({len(both)}):")
            for dish in sorted(both)[:10]:
                print(f"   - {dish}")
        elif both:
            print(f"\n✅ In both: {len(both)} dishes")
            print("   Examples:", ", ".join(sorted(both)[:5]))
        
        if only_local:
            print(f"\n📍 Only in Local SQLite ({len(only_local)}):")
            for dish in sorted(only_local)[:5]:
                print(f"   - {dish}")
            if len(only_local) > 5:
                print(f"   ... and {len(only_local) - 5} more")
        
        if only_supa:
            print(f"\n☁️  Only in Supabase ({len(only_supa)}):")
            for dish in sorted(only_supa)[:5]:
                print(f"   - {dish}")
            if len(only_supa) > 5:
                print(f"   ... and {len(only_supa) - 5} more")
    
    # Special focus on 小吃 station
    print("\n" + "=" * 80)
    print("🔍 DETAILED ANALYSIS: 小吃 (SNACKS) STATION")
    print("=" * 80)
    
    snacks_local = local_dishes.get('小吃', set())
    snacks_supa = supabase_dishes.get('小吃/其他', set())
    
    print(f"\nLocal SQLite 小吃 dishes ({len(snacks_local)}):")
    for dish in sorted(snacks_local):
        print(f"  - {dish}")
    
    print(f"\nSupabase 小吃 dishes ({len(snacks_supa)}):")
    for dish in sorted(snacks_supa):
        print(f"  - {dish}")
    
    # Check for cold dishes
    cold_dishes = ['老醋花生', '凉拌土豆丝', '拍黄瓜', '木姜子鸡爪']
    found_cold_local = [d for d in cold_dishes if d in snacks_local]
    found_cold_supa = [d for d in cold_dishes if d in snacks_supa]
    
    if found_cold_local:
        print(f"\n⚠️  Cold dishes still in Local 小吃: {found_cold_local}")
    else:
        print("\n✅ No cold dishes in Local 小吃")
    
    if found_cold_supa:
        print(f"⚠️  Cold dishes still in Supabase 小吃: {found_cold_supa}")
    else:
        print("✅ No cold dishes in Supabase 小吃")

if __name__ == "__main__":
    main()