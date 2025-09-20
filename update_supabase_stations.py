#!/usr/bin/env python3
"""
Update Supabase kitchen_stations table with corrected station UUIDs
"""

import os
import sys
from dotenv import load_dotenv

# Clear proxy settings that cause issues with httpx
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)

from supabase import create_client

load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print('❌ Missing Supabase credentials in .env file')
    sys.exit(1)

# Create Supabase client
print(f"Connecting to Supabase...")
supabase = create_client(supabase_url, supabase_key)

# Define correct station mappings
CORRECT_STATIONS = {
    '荤菜': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',  # Meat dishes
    '素菜': 'c3d4e5f6-a7b8-9012-cdef-345678901234',  # Vegetable dishes
    '酒水': 'd4e5f6a7-b8c9-0123-defa-456789012345',  # Beverages
    '主食': 'e5f6a7b8-c9d0-1234-efab-567890123456',  # Staple food (reserved)
    '汤品': 'f6a7b8c9-d0e1-2345-fabc-678901234567',  # Soup (reserved)
    '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',  # Snacks
    '凉菜': '581b60be-428a-4673-9147-2c197478392b',  # Cold dishes (FIXED UUID)
}

def check_and_update_stations():
    """Check current stations and update if needed"""
    
    try:
        # Get current stations from Supabase
        result = supabase.table('kitchen_stations').select('*').execute()
        existing = {s['name']: s['id'] for s in result.data}
        
        print("\n📊 Current Supabase kitchen_stations:")
        print("=" * 60)
        for station in result.data:
            status = "✓" if station['id'] == CORRECT_STATIONS.get(station['name']) else "❌"
            print(f"{status} {station['name']:10} → {station['id']}")
        
        # Check what needs updating
        updates_needed = []
        inserts_needed = []
        
        for name, correct_id in CORRECT_STATIONS.items():
            if name not in existing:
                inserts_needed.append((name, correct_id))
            elif existing[name] != correct_id:
                updates_needed.append((name, correct_id, existing[name]))
        
        # Perform updates
        if updates_needed:
            print("\n🔧 Updates needed:")
            print("-" * 60)
            for name, new_id, old_id in updates_needed:
                print(f"  {name}: {old_id} → {new_id}")
                
                # Special handling for 凉菜 (cold dishes)
                if name == '凉菜':
                    print(f"\n  ⚠️  Updating 凉菜 (cold dishes) station...")
                    
                    # First check if the new UUID already exists
                    check = supabase.table('kitchen_stations').select('*').eq('id', new_id).execute()
                    if check.data:
                        print(f"  ❌ UUID {new_id} already exists for station: {check.data[0]['name']}")
                        print("     Cannot update - would create duplicate")
                    else:
                        # Delete the old entry
                        delete_result = supabase.table('kitchen_stations').delete().eq('name', name).execute()
                        print(f"  ✓ Deleted old entry for {name}")
                        
                        # Insert with new UUID
                        insert_data = {
                            'id': new_id,
                            'name': name,
                            'restaurant_id': '51ac675f-f6d0-4706-8fb1-07536c85f5ba',
                            'display_name': '凉菜档',
                            'sort_order': 7,
                            'is_active': True
                        }
                        insert_result = supabase.table('kitchen_stations').insert(insert_data).execute()
                        print(f"  ✓ Inserted {name} with new UUID: {new_id}")
        
        # Perform inserts
        if inserts_needed:
            print("\n➕ Inserts needed:")
            print("-" * 60)
            for name, station_id in inserts_needed:
                print(f"  {name}: {station_id}")
                
                insert_data = {
                    'id': station_id,
                    'name': name,
                    'restaurant_id': '51ac675f-f6d0-4706-8fb1-07536c85f5ba',
                    'display_name': f'{name}档',
                    'sort_order': list(CORRECT_STATIONS.keys()).index(name) + 1,
                    'is_active': name in ['荤菜', '素菜', '酒水', '小吃', '凉菜']
                }
                
                try:
                    result = supabase.table('kitchen_stations').insert(insert_data).execute()
                    print(f"  ✓ Inserted {name}")
                except Exception as e:
                    print(f"  ❌ Failed to insert {name}: {e}")
        
        if not updates_needed and not inserts_needed:
            print("\n✅ All stations are correctly configured!")
        else:
            # Verify final state
            print("\n📊 Final Supabase kitchen_stations:")
            print("=" * 60)
            result = supabase.table('kitchen_stations').select('*').order('sort_order').execute()
            for station in result.data:
                status = "✓" if station['id'] == CORRECT_STATIONS.get(station['name']) else "?"
                active = "🟢" if station.get('is_active') else "⚫"
                print(f"{status} {active} {station['name']:10} → {station['id']}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_and_update_stations()