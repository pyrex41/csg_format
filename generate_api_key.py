#!/usr/bin/env python3
"""
Generate a secure API key for permanent authentication.
"""

import secrets

# Generate a secure random API key
api_key = secrets.token_urlsafe(32)

print("\n" + "="*60)
print("🔑 STATIC API KEY GENERATED")
print("="*60)
print(f"\nAPI Key: {api_key}")
print("\n" + "="*60)
print("\n📋 Add this to your backend .env file:")
print(f"API_KEY={api_key}")
print("\n📋 Add this to your frontend .env file:")
print(f"VITE_API_TOKEN={api_key}")
print("\n📋 Use in API requests:")
print(f"Authorization: Bearer {api_key}")
print("\n" + "="*60)
print("\n✅ This API key NEVER expires")
print("✅ Works even after server restarts")
print("✅ Can be revoked by changing API_KEY in .env")
print("="*60 + "\n")
