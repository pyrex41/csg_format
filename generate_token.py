#!/usr/bin/env python3
"""
Generate an authentication token for the CSG Format API.

Usage:
    python generate_token.py
    python generate_token.py --username admin --password changeme
"""

import requests
import argparse
import os
from dotenv import load_dotenv

load_dotenv()

def generate_token(base_url: str, username: str, password: str):
    """Generate an authentication token by logging in."""

    login_url = f"{base_url}/api/auth/login"

    payload = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(login_url, json=payload)
        response.raise_for_status()

        data = response.json()

        if data.get("success"):
            print("\n✅ Authentication successful!")
            print(f"\n🔑 Token: {data['token']}")
            print(f"⏰ Expires at: {data['expires_at']}")
            print(f"\n📋 Use this token in your API requests:")
            print(f"   Authorization: Bearer {data['token']}")
            print(f"\n🌐 Example curl command:")
            print(f"   curl -H 'Authorization: Bearer {data['token']}' {base_url}/api/db/applications")
            return data['token']
        else:
            print(f"❌ Login failed: {data.get('detail', 'Unknown error')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to API: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Generate an authentication token')
    parser.add_argument('--url',
                       default='http://127.0.0.1:8001',
                       help='API base URL (default: http://127.0.0.1:8001)')
    parser.add_argument('--username',
                       default=os.getenv('ADMIN_USERNAME', 'admin'),
                       help='Username (default: from ADMIN_USERNAME env or "admin")')
    parser.add_argument('--password',
                       default=os.getenv('ADMIN_PASSWORD', 'changeme'),
                       help='Password (default: from ADMIN_PASSWORD env or "changeme")')

    args = parser.parse_args()

    print(f"🔐 Generating token for {args.username}...")
    print(f"🌐 API URL: {args.url}")

    generate_token(args.url, args.username, args.password)

if __name__ == "__main__":
    main()
