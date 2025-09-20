#!/usr/bin/env python3
"""
Fix dishes that are wrongly classified in 小吃 but should be in 凉菜
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

# Dishes that should be in cold dishes station
DISHES_TO_MOVE = [
    '贵州非遗丝娃娃',  # Traditional cold vegetable wrap
    '野佐料擂椒皮蛋',  # Cold preserved egg with mashed pepper
    '贵阳非遗脆三丁',  # Cold crispy diced vegetables
]

# Station UUIDs
SNACKS_UUID = 'a7b8c9d0-e1f2-3456-abcd-789012345678'  # 小吃 (wrong)
COLD_DISHES_UUID = '581b60be-428a-4673-9147-2c197478392b'  # 凉菜 (correct)

def fix_misclassified_dishes():
    """Move misclassified cold dishes from snacks to cold dishes station"""
    
    print("\n" + "=" * 70)
    print("FIXING MISCLASSIFIED COLD DISHES")
    print("=" * 70)
    
    total_fixed = 0
    
    for dish_name in DISHES_TO_MOVE:
        try:
            # Find wrongly assigned dishes
            wrong_dishes = supabase.table('order_dishes').select('id, name, station_id').eq('name', dish_name).eq('station_id', SNACKS_UUID).execute()
            
            if wrong_dishes.data:
                count = len(wrong_dishes.data)
                print(f"\n📍 {dish_name}: Found {count} orders in 小吃 (wrong station)")
                
                # Update each record
                for record in wrong_dishes.data:
                    try:
                        # Update station_id to correct UUID
                        update_result = supabase.table('order_dishes').update({
                            'station_id': COLD_DISHES_UUID,
                            'updated_at': datetime.utcnow().isoformat()
                        }).eq('id', record['id']).execute()
                        
                        if update_result.data:
                            print(f"   ✅ Fixed order ID: {record['id']}")
                            total_fixed += 1
                        else:
                            print(f"   ❌ Failed to fix order ID: {record['id']}")
                            
                    except Exception as e:
                        print(f"   ❌ Error fixing order {record['id']}: {e}")
            else:
                # Check if dish exists at all
                exists = supabase.table('order_dishes').select('id', count='exact').eq('name', dish_name).execute()
                if exists.count > 0:
                    # Check if already in cold dishes
                    correct = supabase.table('order_dishes').select('id', count='exact').eq('name', dish_name).eq('station_id', COLD_DISHES_UUID).execute()
                    if correct.count > 0:
                        print(f"\n✓ {dish_name}: Already correctly in 凉菜 ({correct.count} orders)")
                    else:
                        # Check if NULL (customer orders)
                        null_count = supabase.table('order_dishes').select('id', count='exact').eq('name', dish_name).is_('station_id', 'null').execute()
                        if null_count.count > 0:
                            print(f"\n- {dish_name}: {null_count.count} customer orders (NULL station, correct)")
                else:
                    print(f"\n- {dish_name}: Not found in database")
                    
        except Exception as e:
            print(f"\n❌ Error processing {dish_name}: {e}")
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: Fixed {total_fixed} dish orders")
    print("=" * 70)
    
    # Verify the fix
    print("\nVerifying the fix...")
    for dish_name in DISHES_TO_MOVE:
        try:
            # Count in wrong station
            wrong = supabase.table('order_dishes').select('id', count='exact').eq('name', dish_name).eq('station_id', SNACKS_UUID).execute()
            # Count in correct station
            correct = supabase.table('order_dishes').select('id', count='exact').eq('name', dish_name).eq('station_id', COLD_DISHES_UUID).execute()
            
            if wrong.count > 0 or correct.count > 0:
                status = "✅" if wrong.count == 0 else "⚠️"
                print(f"{status} {dish_name}: {wrong.count} in 小吃 (should be 0), {correct.count} in 凉菜 (correct)")
                
        except Exception as e:
            print(f"❌ Error verifying {dish_name}: {e}")

if __name__ == "__main__":
    print("This script will move misclassified cold dishes from 小吃 to 凉菜 station")
    print("Dishes to move:")
    for dish in DISHES_TO_MOVE:
        print(f"  - {dish}")
    
    response = input("\nProceed with the fix? (yes/no): ")
    if response.lower() == 'yes':
        fix_misclassified_dishes()
    else:
        print("Cancelled.")