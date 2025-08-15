#!/usr/bin/env python3
"""
Test client for Printer API Service
Shows how to connect to the SSE stream from another application
"""

import requests
import json
import sys
import time

def test_health(base_url):
    """Test health endpoint"""
    print("Testing /api/health...")
    response = requests.get(f"{base_url}/api/health")
    data = response.json()
    print(f"  Status: {data['status']}")
    print(f"  Receipts in memory: {data['receipts_count']}")
    print(f"  Total received: {data['total_received']}")
    print()

def test_recent(base_url):
    """Test recent receipts"""
    print("Testing /api/recent...")
    response = requests.get(f"{base_url}/api/recent")
    receipts = response.json()
    print(f"  Found {len(receipts)} recent receipts")
    
    if receipts:
        latest = receipts[-1]
        print(f"  Latest receipt:")
        print(f"    Receipt No: {latest.get('receipt_no', 'N/A')}")
        print(f"    Timestamp: {latest.get('timestamp', 'N/A')}")
        print(f"    Text preview: {latest.get('plain_text', '')[:50]}...")
    print()

def test_stream(base_url):
    """Connect to SSE stream"""
    print("Connecting to real-time stream...")
    print("(Press Ctrl+C to stop)")
    print("-" * 40)
    
    try:
        # Use requests with stream=True for SSE
        response = requests.get(f"{base_url}/api/stream", stream=True)
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    
                    if data.get('type') == 'connected':
                        print("✅ Stream connected!")
                    else:
                        # New receipt
                        print(f"\n📋 New Receipt:")
                        print(f"   ID: {data['id'][:8]}")
                        print(f"   Receipt No: {data.get('receipt_no', 'N/A')}")
                        print(f"   Time: {data.get('timestamp', 'N/A')}")
                        print(f"   Text: {data.get('plain_text', '')[:100]}...")
                        print("-" * 40)
                        
    except KeyboardInterrupt:
        print("\n\nStream disconnected.")
    except Exception as e:
        print(f"Error: {e}")

def test_search(base_url, receipt_no):
    """Test search by receipt number"""
    print(f"Searching for receipt no: {receipt_no}...")
    response = requests.get(f"{base_url}/api/search", params={'no': receipt_no})
    results = response.json()
    
    if results:
        print(f"  Found {len(results)} matching receipts")
        for r in results:
            print(f"    ID: {r['id'][:8]}, Time: {r['timestamp']}")
    else:
        print("  No matching receipts found")
    print()

def main():
    # Default to localhost, but allow custom URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print("="*50)
    print("🖨️  Printer API Test Client")
    print("="*50)
    print(f"Testing API at: {base_url}")
    print()
    
    # Run tests
    test_health(base_url)
    test_recent(base_url)
    
    # Example search
    # test_search(base_url, "240815001")
    
    # Connect to stream
    print("\nWould you like to connect to the real-time stream? (y/n)")
    if input().lower() == 'y':
        test_stream(base_url)

if __name__ == '__main__':
    main()