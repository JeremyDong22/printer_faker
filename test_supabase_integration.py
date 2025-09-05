#!/usr/bin/env python3
"""
Test script for local Supabase integration
Run this to verify the OrderProcessor works correctly
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from order_processor import OrderProcessor

def test_integration():
    """Test the Supabase integration with sample receipts"""
    
    print("=" * 60)
    print("Testing Local Supabase Integration")
    print("=" * 60)
    
    # Check environment variables
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or supabase_url == 'https://your-project.supabase.co':
        print("❌ SUPABASE_URL not configured")
        print("   Please set SUPABASE_URL in .env file")
        return False
    
    if not supabase_key or supabase_key == 'your-service-role-key-here':
        print("❌ SUPABASE_SERVICE_ROLE_KEY not configured")
        print("   Please set SUPABASE_SERVICE_ROLE_KEY in .env file")
        return False
    
    print(f"✅ Supabase URL: {supabase_url}")
    print("✅ Supabase Key: [CONFIGURED]")
    print()
    
    # Initialize processor
    try:
        processor = OrderProcessor()
        print("✅ OrderProcessor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize OrderProcessor: {e}")
        return False
    
    # Test receipt 1: Customer order (客单)
    customer_receipt = {
        'receipt_no': 'TEST_LOCAL_001',
        'timestamp': datetime.now().isoformat(),
        'plain_text': '''智慧餐厅
桌号: 12
--------------------------------
客单
--------------------------------
菜品单价数量小计
野菜卷181份18
木姜子鲜黄牛肉521份52
酸汤肥牛682份136
--------------------------------
菜品价格合计: 206
--------------------------------
单号: TEST_LOCAL_001
时间: 2025-09-06 01:00:00'''
    }
    
    print("Testing Customer Order...")
    try:
        result = processor.process_receipt(customer_receipt)
        print(f"✅ Customer order processed: {result}")
        print(f"   - Order ID: {result.get('order_id', 'N/A')}")
        print(f"   - Table: {result.get('table_no', 'N/A')}")
        print(f"   - Dishes: {result.get('dish_count', 0)}")
    except Exception as e:
        print(f"❌ Customer order failed: {e}")
    
    print()
    
    # Test receipt 2: Kitchen slip (制作分单)
    kitchen_receipt = {
        'receipt_no': 'TEST_LOCAL_002',
        'timestamp': datetime.now().isoformat(),
        'plain_text': '''智慧餐厅
制作分单
--------------------------------
档口: 荤菜
桌号: 12
--------------------------------
菜品数量
木姜子鲜黄牛肉1/份
酸汤肥牛2/份
--------------------------------
单号: TEST_LOCAL_002
时间: 2025-09-06 01:00:00'''
    }
    
    print("Testing Kitchen Slip...")
    try:
        result = processor.process_receipt(kitchen_receipt)
        print(f"✅ Kitchen slip processed: {result}")
        print(f"   - Station: {result.get('station', 'N/A')}")
        print(f"   - Table: {result.get('table_no', 'N/A')}")
        print(f"   - Dishes: {result.get('dish_count', 0)}")
    except Exception as e:
        print(f"❌ Kitchen slip failed: {e}")
    
    print()
    
    # Test receipt 3: Pre-checkout (should skip)
    precheckout_receipt = {
        'receipt_no': 'TEST_LOCAL_003',
        'timestamp': datetime.now().isoformat(),
        'plain_text': '''智慧餐厅
预结单
--------------------------------
桌号: 12
总计: 206元'''
    }
    
    print("Testing Pre-checkout Bill (should skip)...")
    try:
        result = processor.process_receipt(precheckout_receipt)
        print(f"✅ Pre-checkout handled: {result}")
    except Exception as e:
        print(f"❌ Pre-checkout failed: {e}")
    
    print()
    print("=" * 60)
    print("Integration test complete!")
    print("Check your Supabase dashboard for the test orders.")
    print("=" * 60)
    
    # Stop the processor
    processor.stop()
    
    return True

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = test_integration()
    sys.exit(0 if success else 1)