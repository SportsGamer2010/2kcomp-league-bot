#!/usr/bin/env python3
"""Test Discord token validity."""

import os
import discord
from dotenv import load_dotenv

# Load .env file
load_dotenv()

async def test_token():
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ DISCORD_TOKEN not found in environment")
        return
    
    print(f"Token length: {len(token)}")
    print(f"Token starts with: {token[:5]}...")
    
    try:
        # Test the token
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f"✅ Bot logged in as {client.user}")
            print(f"✅ Connected to {len(client.guilds)} guild(s)")
            await client.close()
        
        await client.start(token)
        
    except discord.LoginFailure:
        print("❌ Invalid token - check your Discord token")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_token())
