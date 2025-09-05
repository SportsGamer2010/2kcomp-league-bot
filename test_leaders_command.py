#!/usr/bin/env python3
"""Test script for the /leaders command functionality."""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock the settings
class MockSettings:
    GUILD_ID = 1234567890123456789
    ANNOUNCE_CHANNEL_ID = 9876543210987654321
    HISTORY_CHANNEL_ID = 1111111111111111111
    season_endpoints_list = [
        '/players?league=nba2k26s1',
        '/players?league=nba2k25s6',
        '/players?league=nba2k25s5'
    ]

# Mock the config module
import sys
sys.modules['core.config'] = Mock()
sys.modules['core.config'].settings = MockSettings()

# Mock the leaders module
class MockLeadersData:
    def __init__(self):
        self.points = [("Player1", 25.5), ("Player2", 24.0), ("Player3", 23.5)]
        self.rebounds = [("Player1", 12.0), ("Player2", 11.5), ("Player3", 10.0)]
        self.assists = [("Player1", 8.0), ("Player2", 7.5), ("Player3", 7.0)]

class MockLeadersModule:
    @staticmethod
    async def top_n_season_leaders(client, n=3):
        return MockLeadersData()
    
    @staticmethod
    async def top_n_career_leaders(client, season_queries, n=3):
        return MockLeadersData()
    
    @staticmethod
    def format_leaders_embed(leaders_data, scope="season"):
        embed = Mock()
        embed.title = f"{scope.title()} Leaders"
        embed.description = "Test leaders data"
        embed.fields = []
        return embed

sys.modules['core.leaders'] = MockLeadersModule()

from cogs.status import StatusCog

async def test_leaders_command():
    """Test the /leaders command functionality."""
    print("🧪 Testing /leaders Command Functionality")
    print("=" * 50)
    
    # Create mock bot
    mock_bot = Mock()
    mock_bot.http_client = Mock()
    
    # Create status cog
    status_cog = StatusCog(mock_bot)
    
    # Create mock interaction
    mock_interaction = Mock()
    mock_interaction.response = Mock()
    mock_interaction.followup = Mock()
    mock_interaction.followup.send = AsyncMock()
    
    # Test season leaders
    print("📊 Testing season leaders...")
    try:
        await status_cog.leaders(mock_interaction, "season")
        print("   ✅ Season leaders command executed successfully")
        print(f"   Followup send called: {mock_interaction.followup.send.called}")
    except Exception as e:
        print(f"   ❌ Season leaders failed: {e}")
    
    # Test career leaders
    print("\n📈 Testing career leaders...")
    try:
        await status_cog.leaders(mock_interaction, "career")
        print("   ✅ Career leaders command executed successfully")
        print(f"   Followup send called: {mock_interaction.followup.send.called}")
    except Exception as e:
        print(f"   ❌ Career leaders failed: {e}")
    
    print("\n🎉 /leaders command test completed!")

if __name__ == "__main__":
    asyncio.run(test_leaders_command())
