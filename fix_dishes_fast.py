#!/usr/bin/env python3
"""
Fast version - Fix critical dish mapping issues
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
SNACKS_UUID = 'a7b8c9d0-e1f2-3456-abcd-789012345678'
SOUP_UUID = 'f6a7b8c9-d0e1-2345-fabc-678901234567'

def fix_critical_issues():
    """Fix only the most critical issues quickly"""
    
    print("\n" + "=" * 70)
    print("FIXING CRITICAL DISH ISSUES")
    print("=" * 70)
    
    # 1. Fix 老凯里非遗酸汤
    print("\n1. Fixing 老凯里非遗酸汤...")
    try:
        result = supabase.table('order_dishes').update({
            'station_id': SNACKS_UUID
        }).eq('name', '老凯里非遗酸汤').eq('station_id', SOUP_UUID).execute()
        
        if result.data:
            print(f"   ✅ Fixed {len(result.data)} orders")
        else:
            print("   ✓ Already fixed or not found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Delete test dishes (batch delete)
    print("\n2. Removing test dishes...")
    test_names = [
        'Test Realtime Dish - 实时测试菜品',
        'Test Realtime Dish - 12:02:28',
        '🔥 测试红烧肉 (Test Dish)',
        '🎯 REALTIME WORKING TEST',
        '🔴 REALTIME TEST DISH',
        '🚀 实时测试菜品',
        '测试菜品 - 实时更新'
    ]
    
    for name in test_names:
        try:
            result = supabase.table('order_dishes').delete().eq('name', name).execute()
            if result.data:
                print(f"   ✅ Deleted: {name}")
        except:
            pass
    
    # 3. Delete worst malformed dishes
    print("\n3. Removing malformed dishes...")
    malformed = ['和牛）', '胸口）', '-做法:冰1', '-做法:冰2', '-做法:冰3']
    
    for name in malformed:
        try:
            result = supabase.table('order_dishes').delete().eq('name', name).execute()
            if result.data:
                print(f"   ✅ Deleted: {name} ({len(result.data)} orders)")
        except:
            pass
    
    print("\n✅ Critical fixes completed!")

if __name__ == "__main__":
    fix_critical_issues()