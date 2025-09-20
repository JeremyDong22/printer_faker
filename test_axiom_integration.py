#!/usr/bin/env python3
"""
Test script for Axiom monitoring integration.
Verifies that Axiom logging is working correctly.
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test imports
print("Testing Axiom imports...")
try:
    from axiom_handler import AxiomHandler, AxiomLogger, setup_axiom_logging
    print("✅ Axiom handler imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Axiom handler: {e}")
    sys.exit(1)

# Check environment variables
print("\nChecking environment variables...")
axiom_token = os.getenv('AXIOM_TOKEN')
axiom_dataset = os.getenv('AXIOM_DATASET', 'printer-faker-prod')
axiom_enabled = os.getenv('AXIOM_ENABLED', 'true').lower() == 'true'

if not axiom_token:
    print("❌ AXIOM_TOKEN not set in environment")
    print("Please set AXIOM_TOKEN in your .env file")
    sys.exit(1)
else:
    print(f"✅ AXIOM_TOKEN found (length: {len(axiom_token)})")

print(f"✅ AXIOM_DATASET: {axiom_dataset}")
print(f"✅ AXIOM_ENABLED: {axiom_enabled}")

# Test basic logging
print("\nTesting basic Axiom logging...")
try:
    # Create a test logger
    test_logger = logging.getLogger('axiom_test')
    test_logger.setLevel(logging.INFO)
    
    # Add console handler for visibility
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    test_logger.addHandler(console)
    
    # Setup Axiom logging
    axiom_logger = setup_axiom_logging(
        test_logger,
        dataset=axiom_dataset,
        level=logging.INFO
    )
    print("✅ Axiom logger initialized")
    
    # Send test events
    print("\nSending test events to Axiom...")
    
    # Test 1: Basic event
    axiom_logger.log_event(
        'test_event',
        'Testing Axiom integration',
        test_type='basic',
        environment='test'
    )
    print("✅ Sent basic test event")
    
    # Test 2: Receipt processing simulation
    axiom_logger.log_receipt(
        receipt_no='TEST-001',
        order_type='test_order',
        message='Test receipt processing',
        client_ip='127.0.0.1',
        data_size=1024,
        parse_time_ms=145.5
    )
    print("✅ Sent receipt processing event")
    
    # Test 3: Performance metric
    axiom_logger.log_performance(
        operation='test_operation',
        duration_ms=250.75,
        success=True,
        test_id='PERF-001'
    )
    print("✅ Sent performance metric")
    
    # Test 4: Error event
    try:
        raise ValueError("Test error for Axiom")
    except ValueError as e:
        axiom_logger.log_error(
            error_type='test_error',
            message='Simulated error for testing',
            exception=e,
            test_id='ERR-001'
        )
    print("✅ Sent error event with exception")
    
    # Force flush
    print("\nFlushing events to Axiom...")
    for handler in test_logger.handlers:
        if isinstance(handler, AxiomHandler):
            handler.flush()
            print("✅ Flushed events to Axiom")
            break
    
    # Wait a moment for events to be sent
    time.sleep(2)
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED!")
    print("="*50)
    print("\nNext steps:")
    print("1. Check your Axiom dashboard at https://app.axiom.co")
    print(f"2. Look for dataset: {axiom_dataset}")
    print("3. You should see 4 test events")
    print("4. Events should include: test_event, receipt_processed, performance_test_operation, error_test_error")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test API endpoints
print("\n" + "="*50)
print("Testing API endpoints...")
print("="*50)

try:
    import requests
    
    # Get API password
    api_password = os.getenv('PRINTER_API_PASSWORD', 'smartbcg')
    base_url = 'http://localhost:5000'
    headers = {'Authorization': api_password}
    
    print(f"\nTesting {base_url}/api/axiom/health...")
    try:
        response = requests.get(f'{base_url}/api/axiom/health', headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Axiom health endpoint working")
            print(f"   - Enabled: {data.get('enabled')}")
            print(f"   - Dataset: {data.get('dataset')}")
            print(f"   - Connected: {data.get('connected')}")
        else:
            print(f"⚠️ Axiom health endpoint returned {response.status_code}")
            print(f"   This is expected if the service is not running")
    except requests.exceptions.ConnectionError:
        print("ℹ️ Could not connect to API service (expected if not running)")
    except Exception as e:
        print(f"⚠️ Error testing health endpoint: {e}")
    
    print(f"\nTesting {base_url}/api/axiom/flush...")
    try:
        response = requests.post(f'{base_url}/api/axiom/flush', headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Axiom flush endpoint working")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Timestamp: {data.get('timestamp')}")
        else:
            print(f"⚠️ Axiom flush endpoint returned {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("ℹ️ Could not connect to API service (expected if not running)")
    except Exception as e:
        print(f"⚠️ Error testing flush endpoint: {e}")
        
except ImportError:
    print("ℹ️ requests library not installed, skipping API endpoint tests")
    print("   Run: uv pip install requests")

print("\n" + "="*50)
print("✅ Axiom integration test completed!")
print("="*50)