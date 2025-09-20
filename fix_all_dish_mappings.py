#!/usr/bin/env python3
"""
Fix ALL dish mapping issues in Supabase to achieve perfect mapping
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Clear proxy settings
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)

from supabase import create_client

load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print('❌ Missing Supabase credentials')
    sys.exit(1)

print("Connecting to Supabase...")
supabase = create_client(supabase_url, supabase_key)

# Station UUIDs
STATIONS = {
    '荤菜': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
    '素菜': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
    '酒水': 'd4e5f6a7-b8c9-0123-defa-456789012345',
    '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',
    '凉菜': '581b60be-428a-4673-9147-2c197478392b',
    '汤品': 'f6a7b8c9-d0e1-2345-fabc-678901234567',  # Doesn't exist in POS
}

def fix_issues():
    """Fix all dish mapping issues"""
    
    print("\n" + "=" * 70)
    print("FIXING ALL DISH MAPPING ISSUES")
    print("=" * 70)
    
    total_fixed = 0
    total_deleted = 0
    
    # =========================================
    # 1. Fix 老凯里非遗酸汤 (move from 汤品 to 小吃)
    # =========================================
    print("\n1. Fixing 老凯里非遗酸汤 station assignment...")
    try:
        wrong_soup = supabase.table('order_dishes').select('id').eq('name', '老凯里非遗酸汤').eq('station_id', STATIONS['汤品']).execute()
        
        if wrong_soup.data:
            for record in wrong_soup.data:
                update_result = supabase.table('order_dishes').update({
                    'station_id': STATIONS['小吃'],
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', record['id']).execute()
                
                if update_result.data:
                    total_fixed += 1
            
            print(f"   ✅ Moved {len(wrong_soup.data)} orders from 汤品 to 小吃")
        else:
            print("   ✓ Already in correct station or not found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # =========================================
    # 2. Delete all test dishes
    # =========================================
    print("\n2. Removing test dishes...")
    test_patterns = [
        'Test Realtime Dish%',
        '%测试%',
        '🔥%',
        '🎯%', 
        '🔴%',
        '🚀%',
        '%TEST%'
    ]
    
    for pattern in test_patterns:
        try:
            test_dishes = supabase.table('order_dishes').select('id').ilike('name', pattern).execute()
            if test_dishes.data:
                for record in test_dishes.data:
                    supabase.table('order_dishes').delete().eq('id', record['id']).execute()
                    total_deleted += 1
                print(f"   ✅ Deleted {len(test_dishes.data)} dishes matching '{pattern}'")
        except Exception as e:
            print(f"   ❌ Error deleting {pattern}: {e}")
    
    # =========================================
    # 3. Delete malformed/partial dishes
    # =========================================
    print("\n3. Removing malformed/partial dishes...")
    malformed_dishes = [
        '和牛）',           # Missing opening part
        '胸口）',           # Missing opening part  
        '大地飞雪（M9纯血',   # Missing closing parenthesis
        '紫苏半边云（鲜牛',   # Missing closing parenthesis
        '(打包)五指毛桃山',   # Truncated
        '(赠)可口可乐（听',   # Missing closing parenthesis
    ]
    
    for dish in malformed_dishes:
        try:
            bad_dishes = supabase.table('order_dishes').select('id').eq('name', dish).execute()
            if bad_dishes.data:
                for record in bad_dishes.data:
                    supabase.table('order_dishes').delete().eq('id', record['id']).execute()
                    total_deleted += 1
                print(f"   ✅ Deleted {len(bad_dishes.data)} orders of '{dish}'")
        except Exception as e:
            print(f"   ❌ Error deleting {dish}: {e}")
    
    # =========================================
    # 4. Delete modifiers stored as dishes
    # =========================================
    print("\n4. Removing modifiers incorrectly stored as dishes...")
    modifier_patterns = [
        '-做法:%',
        '-五指毛桃山茶',
        '-%'
    ]
    
    for pattern in modifier_patterns:
        try:
            modifiers = supabase.table('order_dishes').select('id, name').like('name', pattern).execute()
            if modifiers.data:
                unique_modifiers = set(m['name'] for m in modifiers.data)
                for modifier in unique_modifiers:
                    # Delete each unique modifier
                    del_result = supabase.table('order_dishes').delete().eq('name', modifier).execute()
                    print(f"   ✅ Deleted modifier: '{modifier}'")
                    total_deleted += len([m for m in modifiers.data if m['name'] == modifier])
        except Exception as e:
            print(f"   ❌ Error deleting modifiers {pattern}: {e}")
    
    # =========================================
    # 5. Standardize number variations
    # =========================================
    print("\n5. Standardizing dish name variations...")
    variations_to_fix = [
        ('紫苏半边云（鲜牛1胸口）', '紫苏半边云（鲜牛胸口）'),
        ('(赠)可口可乐（听1）', '(赠)可口可乐（听）'),
        ('(赠)可口可乐（听2）', '(赠)可口可乐（听）'),
        ('(赠)光明Look酸奶(', '(赠)光明Look酸奶'),
    ]
    
    for old_name, new_name in variations_to_fix:
        try:
            variants = supabase.table('order_dishes').select('id').eq('name', old_name).execute()
            if variants.data:
                for record in variants.data:
                    update_result = supabase.table('order_dishes').update({
                        'name': new_name,
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('id', record['id']).execute()
                    
                    if update_result.data:
                        total_fixed += 1
                print(f"   ✅ Standardized {len(variants.data)} orders: '{old_name}' → '{new_name}'")
        except Exception as e:
            print(f"   ❌ Error standardizing {old_name}: {e}")
    
    # =========================================
    # 6. Clean up whitespace issues
    # =========================================
    print("\n6. Cleaning up whitespace and formatting issues...")
    try:
        # Get all dishes
        all_dishes = supabase.table('order_dishes').select('id, name').execute()
        
        whitespace_fixed = 0
        for dish in all_dishes.data:
            clean_name = dish['name'].strip()
            # Remove multiple spaces
            import re
            clean_name = re.sub(r'\s+', ' ', clean_name)
            
            if clean_name != dish['name']:
                try:
                    supabase.table('order_dishes').update({
                        'name': clean_name,
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('id', dish['id']).execute()
                    whitespace_fixed += 1
                except:
                    pass
        
        if whitespace_fixed > 0:
            print(f"   ✅ Fixed whitespace in {whitespace_fixed} dishes")
            total_fixed += whitespace_fixed
    except Exception as e:
        print(f"   ❌ Error fixing whitespace: {e}")
    
    # =========================================
    # Summary
    # =========================================
    print("\n" + "=" * 70)
    print(f"SUMMARY:")
    print(f"  ✅ Fixed: {total_fixed} dishes")
    print(f"  🗑️  Deleted: {total_deleted} invalid entries")
    print(f"  📊 Total changes: {total_fixed + total_deleted}")
    print("=" * 70)
    
    return total_fixed, total_deleted

def verify_fixes():
    """Verify that fixes were successful"""
    print("\n" + "=" * 70)
    print("VERIFYING FIXES")
    print("=" * 70)
    
    issues = []
    
    # Check if 老凯里非遗酸汤 is still in wrong station
    wrong_soup = supabase.table('order_dishes').select('id', count='exact').eq('name', '老凯里非遗酸汤').eq('station_id', STATIONS['汤品']).execute()
    if wrong_soup.count > 0:
        issues.append(f"老凯里非遗酸汤 still in 汤品: {wrong_soup.count}")
    
    # Check for test dishes
    test_check = supabase.table('order_dishes').select('id', count='exact').ilike('name', '%test%').execute()
    if test_check.count > 0:
        issues.append(f"Test dishes still exist: {test_check.count}")
    
    # Check for malformed dishes
    malformed_check = supabase.table('order_dishes').select('name').or_('name.eq.和牛）,name.eq.胸口）,name.like.-%').execute()
    if malformed_check.data:
        unique_malformed = set(d['name'] for d in malformed_check.data)
        issues.append(f"Malformed dishes still exist: {unique_malformed}")
    
    if issues:
        print("⚠️  Issues remaining:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ All issues fixed successfully!")
    
    # Show current statistics
    print("\n📊 Current dish statistics:")
    
    # Count by station
    for station_name, station_id in STATIONS.items():
        if station_name in ['荤菜', '素菜', '酒水', '小吃', '凉菜']:  # Only real stations
            count = supabase.table('order_dishes').select('id', count='exact').eq('station_id', station_id).execute()
            print(f"   {station_name}: {count.count} dishes")
    
    # Count NULL station (customer orders)
    null_count = supabase.table('order_dishes').select('id', count='exact').is_('station_id', 'null').execute()
    print(f"   Customer orders (NULL): {null_count.count} dishes")

if __name__ == "__main__":
    print("This script will fix ALL dish mapping issues in Supabase")
    print("Actions to perform:")
    print("  1. Move 老凯里非遗酸汤 from 汤品 to 小吃")
    print("  2. Delete all test dishes")
    print("  3. Delete malformed/partial dishes")
    print("  4. Delete modifiers stored as dishes")
    print("  5. Standardize dish name variations")
    print("  6. Clean up whitespace issues")
    
    response = input("\nProceed with ALL fixes? (yes/no): ")
    if response.lower() == 'yes':
        fixed, deleted = fix_issues()
        if fixed > 0 or deleted > 0:
            verify_fixes()
    else:
        print("Cancelled.")