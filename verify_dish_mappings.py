#!/usr/bin/env python3
"""
Verify dish mappings from POS Printer → SQLite → Supabase
"""

import os
import sqlite3
from collections import defaultdict
from dotenv import load_dotenv
import re

# Clear proxy settings
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)

from supabase import create_client

load_dotenv()

def get_printer_dishes():
    """Extract dishes directly from receipt text in SQLite"""
    conn = sqlite3.connect('receipts.db')
    cursor = conn.cursor()
    
    # Get all kitchen slips (have station assignments)
    cursor.execute('''
        SELECT plain_text 
        FROM receipts 
        WHERE plain_text LIKE '%档口:%'
        ORDER BY created_at DESC
        LIMIT 500
    ''')
    
    printer_dishes = defaultdict(set)  # station -> set of dishes
    
    for (text,) in cursor.fetchall():
        # Extract station
        station = None
        lines = text.split('\n')
        for line in lines:
            if '档口:' in line or '档口：' in line:
                station = line.split(':')[-1].strip()
                break
        
        if not station:
            continue
            
        # Extract dishes (look for quantity pattern)
        for i, line in enumerate(lines):
            if '/' in line and any(unit in line for unit in ['份', '瓶', '听', '盒', '个', '碗', '杯', '位']):
                # Get dish name
                dish = line.split('/')[0].strip()
                
                # Handle multi-line dishes
                if '（' in dish and '）' not in dish:
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if '）' in next_line and '/' not in next_line:
                            dish = dish + next_line
                
                # Clean up
                dish = dish.replace('(退)', '').strip()
                dish = re.sub(r'^\d+', '', dish).strip()  # Remove leading numbers
                dish = re.sub(r'\d+$', '', dish).strip()  # Remove trailing numbers
                
                if dish and not dish.startswith('-') and len(dish) > 1:
                    printer_dishes[station].add(dish)
    
    conn.close()
    return printer_dishes

def get_sqlite_dishes():
    """Get dishes from SQLite (what we parsed)"""
    conn = sqlite3.connect('receipts.db')
    cursor = conn.cursor()
    
    # Since dishes column is deprecated/null, we need to re-parse
    # This should match what order_processor.py does
    cursor.execute('''
        SELECT plain_text 
        FROM receipts 
        WHERE plain_text LIKE '%档口:%'
        ORDER BY created_at DESC
        LIMIT 500
    ''')
    
    sqlite_dishes = defaultdict(set)
    
    for (text,) in cursor.fetchall():
        # This simulates order_processor.py parsing
        station = None
        for line in text.split('\n'):
            if '档口:' in line or '档口：' in line:
                station = line.split(':')[-1].strip()
                break
        
        if not station:
            continue
        
        # Parse dishes like order_processor does
        lines = text.split('\n')
        for i, line in enumerate(lines):
            trimmed = line.strip()
            if '/' in trimmed and any(unit in trimmed for unit in ['份', '瓶', '听', '盒', '个', '碗', '杯', '位']):
                dish_line = re.sub(r'\d+\/[份瓶听盒个碗杯位].*$', '', trimmed).strip()
                
                # Multi-line handling
                if '（' in dish_line and '）' not in dish_line:
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if '）' in next_line and not re.search(r'\d+\/[份瓶听盒个碗杯位]', next_line):
                            dish_line = dish_line + next_line
                
                dish_line = re.sub(r'^\(退\)', '', dish_line).strip()
                
                if dish_line and len(dish_line) > 1:
                    sqlite_dishes[station].add(dish_line)
    
    conn.close()
    return sqlite_dishes

def get_supabase_dishes():
    """Get dishes from Supabase"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print('Missing Supabase credentials')
        return {}
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Get recent dishes with station info
    result = supabase.table('order_dishes').select('name, station_id').execute()
    
    # Map UUID to station name
    UUID_TO_STATION = {
        'b2c3d4e5-f6a7-8901-bcde-f23456789012': '荤菜',
        'c3d4e5f6-a7b8-9012-cdef-345678901234': '素菜',
        'd4e5f6a7-b8c9-0123-defa-456789012345': '酒水',
        'a7b8c9d0-e1f2-3456-abcd-789012345678': '小吃',
        '581b60be-428a-4673-9147-2c197478392b': '凉菜',
        'e5f6a7b8-c9d0-1234-efab-567890123456': '主食',  # Shouldn't exist
        'f6a7b8c9-d0e1-2345-fabc-678901234567': '汤品',  # Shouldn't exist
    }
    
    supabase_dishes = defaultdict(set)
    unknown_stations = set()
    
    for item in result.data:
        if item['station_id']:
            station = UUID_TO_STATION.get(item['station_id'])
            if station:
                supabase_dishes[station].add(item['name'])
            else:
                unknown_stations.add(item['station_id'])
        else:
            # NULL station (customer orders)
            supabase_dishes['NULL'].add(item['name'])
    
    if unknown_stations:
        print(f"Warning: Unknown station UUIDs in Supabase: {unknown_stations}")
    
    return supabase_dishes

def compare_mappings():
    """Compare dish mappings across all systems"""
    print("=" * 80)
    print("DISH MAPPING VERIFICATION: POS Printer → SQLite → Supabase")
    print("=" * 80)
    
    print("\n📡 Fetching data from all sources...")
    printer = get_printer_dishes()
    sqlite = get_sqlite_dishes()
    supabase = get_supabase_dishes()
    
    # Get all stations
    all_stations = set(list(printer.keys()) + list(sqlite.keys()) + list(supabase.keys()))
    all_stations.discard('NULL')  # Remove NULL (customer orders)
    
    print(f"\nFound {len(all_stations)} stations: {', '.join(sorted(all_stations))}")
    
    # Detailed comparison by station
    perfect_match = True
    
    for station in sorted(all_stations):
        print(f"\n{'='*60}")
        print(f"🏪 Station: {station}")
        print(f"{'='*60}")
        
        p_dishes = printer.get(station, set())
        sq_dishes = sqlite.get(station, set())
        sp_dishes = supabase.get(station, set())
        
        print(f"  Printer:  {len(p_dishes)} dishes")
        print(f"  SQLite:   {len(sq_dishes)} dishes")
        print(f"  Supabase: {len(sp_dishes)} dishes")
        
        # Check if all match
        if p_dishes == sq_dishes == sp_dishes:
            print("  ✅ PERFECT MATCH - All dishes identical across systems")
        else:
            perfect_match = False
            
            # Find discrepancies
            all_dishes = p_dishes | sq_dishes | sp_dishes
            
            print("\n  ⚠️  DISCREPANCIES FOUND:")
            print("  " + "-" * 40)
            
            issues = []
            
            for dish in sorted(all_dishes):
                in_printer = '✓' if dish in p_dishes else '✗'
                in_sqlite = '✓' if dish in sq_dishes else '✗'
                in_supabase = '✓' if dish in sp_dishes else '✗'
                
                if not (in_printer == in_sqlite == in_supabase == '✓'):
                    status = f"  Printer:{in_printer} SQLite:{in_sqlite} Supabase:{in_supabase}"
                    issues.append(f"  {dish:30} {status}")
            
            # Show first 10 issues
            for issue in issues[:10]:
                print(issue)
            
            if len(issues) > 10:
                print(f"  ... and {len(issues)-10} more discrepancies")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if perfect_match:
        print("✅ PERFECT: All dishes map correctly across all systems!")
    else:
        print("⚠️  ISSUES FOUND: Some dishes have mapping discrepancies")
        
        # Analyze common patterns
        print("\nCommon Issues:")
        
        # Check for NULL station dishes
        if 'NULL' in supabase and len(supabase['NULL']) > 0:
            print(f"  - {len(supabase['NULL'])} dishes with NULL station (customer orders)")
        
        # Check for fake stations
        fake_stations = {'主食', '汤品', '其他'}
        for fake in fake_stations:
            if fake in supabase and len(supabase[fake]) > 0:
                print(f"  - {len(supabase[fake])} dishes in non-existent '{fake}' station")
    
    # Show some NULL station dishes
    if 'NULL' in supabase:
        print(f"\nSample dishes with NULL station (customer orders):")
        for dish in list(supabase['NULL'])[:5]:
            print(f"  - {dish}")

if __name__ == "__main__":
    compare_mappings()