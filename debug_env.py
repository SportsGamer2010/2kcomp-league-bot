#!/usr/bin/env python3
"""Debug script to check environment variables."""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=== Environment Variables Debug ===")
print(f"DISCORD_TOKEN: {'SET' if os.getenv('DISCORD_TOKEN') else 'NOT SET'}")
print(f"GUILD_ID: {'SET' if os.getenv('GUILD_ID') else 'NOT SET'}")
print(f"ANNOUNCE_CHANNEL_ID: {'SET' if os.getenv('ANNOUNCE_CHANNEL_ID') else 'NOT SET'}")
print(f"HISTORY_CHANNEL_ID: {'SET' if os.getenv('HISTORY_CHANNEL_ID') else 'NOT SET'}")

if os.getenv('DISCORD_TOKEN'):
    token = os.getenv('DISCORD_TOKEN')
    print(f"Token length: {len(token)}")
    print(f"Token starts with: {token[:5]}...")
    print(f"Token contains dots: {'.' in token}")
    print(f"Token has spaces: {' ' in token}")
    print(f"Token has quotes: {'"' in token or "'" in token}")

print("\n=== All Environment Variables ===")
for key, value in os.environ.items():
    if 'DISCORD' in key or 'GUILD' in key or 'CHANNEL' in key:
        print(f"{key}: {value[:10]}..." if len(value) > 10 else f"{key}: {value}")
