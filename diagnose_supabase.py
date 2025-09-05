#!/usr/bin/env python3
"""
Diagnose Supabase connection issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 60)
print("Supabase Configuration Diagnostic")
print("=" * 60)

# Get credentials
url = os.environ.get('SUPABASE_URL', '')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

print(f"URL: {url}")
print(f"Key format: {key[:10]}... (length: {len(key)})")
print()

if key.startswith('sbp_'):
    print("⚠️  Key starts with 'sbp_' - this appears to be a Personal Access Token")
    print("   You need the JWT service role key instead.")
    print()
    print("To get the correct key:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to Settings → API")
    print("3. Copy the 'service_role' key (JWT format, starts with 'eyJ')")
    print("4. Update SUPABASE_SERVICE_ROLE_KEY in .env")
elif key.startswith('eyJ'):
    print("✅ Key appears to be in JWT format (correct)")
else:
    print("❌ Unknown key format")

print()
print("Note: The service role key should be a long JWT token that starts with 'eyJ'")
print("      It's different from personal access tokens (sbp_) or anon keys.")
print("=" * 60)