#!/usr/bin/env python3
"""Local setup script for the 2KCompLeague Discord Bot."""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env.local file from template."""
    template_file = Path("env.local.example")
    env_file = Path(".env.local")
    
    if not template_file.exists():
        print("❌ Template file 'env.local.example' not found!")
        return False
    
    if env_file.exists():
        print("⚠️  .env.local already exists. Skipping creation.")
        return True
    
    # Copy template to .env.local
    try:
        with open(template_file, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Created .env.local from template")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env.local: {e}")
        return False

def check_requirements():
    """Check if required dependencies are installed."""
    try:
        import discord
        import aiohttp
        import pydantic
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_data_directory():
    """Ensure data directory exists."""
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir()
        print("✅ Created data directory")
    else:
        print("✅ Data directory exists")
    return True

def main():
    """Main setup function."""
    print("🚀 Setting up 2KCompLeague Discord Bot for local testing...")
    print("=" * 60)
    
    # Check dependencies
    if not check_requirements():
        return False
    
    # Create data directory
    if not check_data_directory():
        return False
    
    # Create environment file
    if not create_env_file():
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Local setup completed!")
    print("\n📋 Next steps:")
    print("1. Edit .env.local with your Discord bot credentials:")
    print("   - DISCORD_TOKEN: Your bot token from Discord Developer Portal")
    print("   - GUILD_ID: Your Discord server ID")
    print("   - ANNOUNCE_CHANNEL_ID: Channel ID for announcements")
    print("   - HISTORY_CHANNEL_ID: Channel ID for history")
    print("\n2. Run the bot:")
    print("   python bot.py")
    print("\n3. Test health endpoints:")
    print("   curl http://localhost:8080/health")
    print("\n💡 Need help? Check README.md for detailed setup instructions")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
