#!/usr/bin/env python3
"""
Generate a static authentication token directly.
"""

import sys
sys.path.insert(0, '.')

from auth.auth import create_session

# Create a session for admin user
session = create_session("admin")

print("\n" + "="*60)
print("🔑 AUTHENTICATION TOKEN GENERATED")
print("="*60)
print(f"\nToken: {session['token']}")
print(f"Expires: {session['expires_at']}")
print("\n" + "="*60)
print("\n📋 Add this to your frontend .env file:")
print(f"VITE_API_TOKEN={session['token']}")
print("\n📋 Or use in API requests:")
print(f"Authorization: Bearer {session['token']}")
print("\n" + "="*60)
print("\n⚠️  Note: This token expires in 24 hours")
print("="*60 + "\n")
