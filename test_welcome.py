#!/usr/bin/env python3
"""Test script for the welcome message functionality."""

import asyncio
import logging
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock the settings
class MockSettings:
    GUILD_ID = 1234567890123456789
    ANNOUNCE_CHANNEL_ID = 9876543210987654321
    HISTORY_CHANNEL_ID = 1111111111111111111

# Mock the config module
import sys
from unittest.mock import patch
sys.modules['core.config'] = Mock()
sys.modules['core.config'].settings = MockSettings()

from core.welcome import WelcomeMessage

async def test_welcome_message():
    """Test the welcome message functionality."""
    print("🧪 Testing Welcome Message Functionality")
    print("=" * 50)
    
    # Create mock bot
    mock_bot = Mock()
    mock_bot.get_guild = Mock()
    
    # Create mock guild
    mock_guild = Mock()
    mock_guild.name = "Test Guild"
    mock_guild.text_channels = []
    
    # Create mock channel
    mock_channel = Mock()
    mock_channel.name = "general"
    mock_channel.permissions_for = Mock()
    mock_channel.send = AsyncMock()
    
    # Set up permissions
    mock_permissions = Mock()
    mock_permissions.send_messages = True
    mock_channel.permissions_for.return_value = mock_permissions
    
    # Add channel to guild
    mock_guild.text_channels = [mock_channel]
    mock_bot.get_guild.return_value = mock_guild
    
    # Create welcome message instance
    welcome = WelcomeMessage(mock_bot)
    
    # Test countdown calculation
    print("📅 Testing countdown calculation...")
    countdown = welcome.get_countdown_to_season1()
    print(f"   Countdown: {countdown}")
    
    # Test embed creation
    print("\n🎨 Testing embed creation...")
    embed = welcome.create_welcome_embed()
    print(f"   Embed title: {embed.title}")
    print(f"   Embed color: {embed.color}")
    print(f"   Number of fields: {len(embed.fields)}")
    
    # Test random channel selection
    print("\n🎯 Testing random channel selection...")
    channel = await welcome.get_random_text_channel(mock_guild)
    if channel:
        print(f"   Selected channel: #{channel.name}")
    else:
        print("   No suitable channel found")
    
    # Test welcome message sending
    print("\n📤 Testing welcome message sending...")
    success = await welcome.send_welcome_message()
    if success:
        print("   ✅ Welcome message sent successfully!")
        print(f"   Channel.send called: {mock_channel.send.called}")
    else:
        print("   ❌ Failed to send welcome message")
    
    print("\n🎉 Welcome message test completed!")

if __name__ == "__main__":
    asyncio.run(test_welcome_message())
