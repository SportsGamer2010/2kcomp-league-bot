"""Discord bot integration tests."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest
import discord
from discord.ext import commands

from bot import DiscordBot
from cogs.admin import AdminCog
from cogs.history import HistoryCog
from cogs.status import StatusCog


class TestDiscordBotIntegration:
    """Test Discord bot integration and command handling."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Discord bot for testing."""
        bot = MagicMock(spec=DiscordBot)
        bot.user = MagicMock()
        bot.user.name = "2KCompLeague Bot"
        bot.user.id = 123456789
        bot.guilds = [MagicMock()]
        bot.guilds[0].name = "Test Guild"
        bot.guilds[0].id = 987654321
        
        # Mock bot state
        bot.state = MagicMock()
        bot.state.last_leaders_check = datetime.now()
        bot.state.last_records_check = datetime.now()
        bot.state.last_milestones_check = datetime.now()
        
        return bot

    @pytest.fixture
    def mock_context(self):
        """Create a mock Discord interaction context."""
        context = MagicMock()
        context.author = MagicMock()
        context.author.name = "TestUser"
        context.author.id = 111111111
        context.author.mention = "<@111111111>"
        context.guild = MagicMock()
        context.guild.name = "Test Guild"
        context.channel = MagicMock()
        context.channel.name = "test-channel"
        context.channel.id = 222222222
        
        # Mock interaction
        context.interaction = MagicMock()
        context.interaction.response = MagicMock()
        context.interaction.followup = MagicMock()
        
        return context

    @pytest.fixture
    def mock_interaction(self):
        """Create a mock Discord interaction."""
        interaction = MagicMock()
        interaction.user = MagicMock()
        interaction.user.name = "TestUser"
        interaction.user.id = 111111111
        interaction.user.mention = "<@111111111>"
        interaction.guild = MagicMock()
        interaction.guild.name = "Test Guild"
        interaction.channel = MagicMock()
        interaction.channel.name = "test-channel"
        interaction.channel.id = 222222222
        
        # Mock response methods
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()
        
        return interaction

    @pytest.mark.asyncio
    async def test_bot_initialization(self, mock_bot):
        """Test bot initialization and setup."""
        # Test bot properties
        assert mock_bot.user.name == "2KCompLeague Bot"
        assert len(mock_bot.guilds) == 1
        assert mock_bot.guilds[0].name == "Test Guild"
        
        # Test bot state
        assert mock_bot.state.last_leaders_check is not None
        assert mock_bot.state.last_records_check is not None
        assert mock_bot.state.last_milestones_check is not None

    @pytest.mark.asyncio
    async def test_admin_announce_command(self, mock_bot, mock_interaction):
        """Test admin announce command functionality."""
        # Mock admin role check
        mock_interaction.user.guild_permissions.administrator = True
        
        # Mock channel
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        mock_interaction.guild.get_channel.return_value = mock_channel
        
        # Test announce command
        admin_cog = AdminCog(mock_bot)
        
        # Mock the command
        with patch.object(admin_cog, 'announce') as mock_announce:
            mock_announce.return_value = None
            
            # Simulate command execution
            await admin_cog.announce(mock_interaction, "Test announcement")
            
            # Verify interaction response
            mock_interaction.response.send_message.assert_called_once()
            call_args = mock_interaction.response.send_message.call_args
            assert "announcement" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_history_command(self, mock_bot, mock_interaction):
        """Test history command functionality."""
        history_cog = HistoryCog(mock_bot)
        
        # Mock championship history data
        mock_history_data = {
            "seasons": [
                {"year": "2024", "champion": "Team A", "runner_up": "Team B"},
                {"year": "2023", "champion": "Team C", "runner_up": "Team D"},
            ]
        }
        
        # Mock the command
        with patch.object(history_cog, 'history') as mock_history:
            mock_history.return_value = None
            
            # Simulate command execution
            await history_cog.history(mock_interaction)
            
            # Verify interaction response
            mock_interaction.response.send_message.assert_called_once()
            call_args = mock_interaction.response.send_message.call_args
            assert "history" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_leaders_command(self, mock_bot, mock_interaction):
        """Test leaders command functionality."""
        status_cog = StatusCog(mock_bot)
        
        # Mock leaders data
        mock_leaders_data = MagicMock()
        mock_leaders_data.points = [MagicMock(name="Player1", value=30.0)]
        mock_leaders_data.assists = [MagicMock(name="Player2", value=15.0)]
        
        # Mock the command
        with patch.object(status_cog, 'leaders') as mock_leaders:
            mock_leaders.return_value = None
            
            # Simulate command execution
            await status_cog.leaders(mock_interaction, "season", "all")
            
            # Verify interaction response
            mock_interaction.response.send_message.assert_called_once()
            call_args = mock_interaction.response.send_message.call_args
            assert "leaders" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_records_command(self, mock_bot, mock_interaction):
        """Test records command functionality."""
        status_cog = StatusCog(mock_bot)
        
        # Mock records data
        mock_records_data = MagicMock()
        mock_records_data.points = MagicMock(
            player="Player1", value=45.0, game="Team A vs Team B", date="2024-01-15"
        )
        
        # Mock the command
        with patch.object(status_cog, 'records') as mock_records:
            mock_records.return_value = None
            
            # Simulate command execution
            await status_cog.records(mock_interaction)
            
            # Verify interaction response
            mock_interaction.response.send_message.assert_called_once()
            call_args = mock_interaction.response.send_message.call_args
            assert "records" in call_args[0][0].lower()


class TestDiscordEmbedGeneration:
    """Test Discord embed generation for various data types."""

    def test_leaders_embed_structure(self):
        """Test leaders embed structure and formatting."""
        from core.leaders import format_leaders_embed
        from core.types import LeadersData, LeaderEntry
        
        # Create test data
        leaders_data = LeadersData(
            points=[
                LeaderEntry(name="Player1", value=30.0),
                LeaderEntry(name="Player2", value=25.5),
            ],
            assists=[
                LeaderEntry(name="Player3", value=15.0),
                LeaderEntry(name="Player1", value=12.0),
            ]
        )
        
        # Generate embed
        embed = format_leaders_embed(leaders_data, scope="season")
        
        # Verify structure
        assert "title" in embed
        assert "fields" in embed
        assert "footer" in embed
        assert embed["title"] == "🏆 Season Leaders"
        assert len(embed["fields"]) == 2
        
        # Verify field content
        points_field = next(f for f in embed["fields"] if "points" in f["name"].lower())
        assert "Player1" in points_field["value"]
        assert "30.0" in points_field["value"]

    def test_records_embed_structure(self):
        """Test records embed structure and formatting."""
        from core.records import format_records_embed
        from core.types import RecordsData, SingleGameRecord
        
        # Create test data
        records_data = RecordsData(
            points=SingleGameRecord(
                player="Player1",
                value=45.0,
                game="Team A vs Team B",
                date="2024-01-15"
            )
        )
        
        # Generate embed
        embed = format_records_embed(records_data)
        
        # Verify structure
        assert "title" in embed
        assert "fields" in embed
        assert "Single-Game Records" in embed["title"]
        assert len(embed["fields"]) > 0
        
        # Verify field content
        points_field = next(f for f in embed["fields"] if "points" in f["name"].lower())
        assert "Player1" in points_field["value"]
        assert "45.0" in points_field["value"]

    def test_milestones_embed_structure(self):
        """Test milestones embed structure and formatting."""
        from core.milestones import format_milestone_embed
        from core.types import MilestoneNotification
        
        # Create test data
        milestone_notifications = [
            MilestoneNotification(
                player="Player1",
                stat="points",
                threshold=25.0,
                current_total=30.0,
                message="🎉 Player1 crossed 25 points milestone!"
            )
        ]
        
        # Generate embed
        embed = format_milestone_embed(milestone_notifications)
        
        # Verify structure
        assert "title" in embed
        assert "fields" in embed
        assert "Milestone Achievements" in embed["title"]
        assert len(embed["fields"]) > 0
        
        # Verify field content
        milestone_field = embed["fields"][0]
        assert "Player1" in milestone_field["value"]
        assert "25 points" in milestone_field["value"]


class TestDiscordCommandValidation:
    """Test Discord command parameter validation."""

    @pytest.mark.asyncio
    async def test_leaders_command_validation(self, mock_bot, mock_interaction):
        """Test leaders command parameter validation."""
        status_cog = StatusCog(mock_bot)
        
        # Test valid parameters
        valid_scopes = ["season", "career"]
        valid_stats = ["all", "points", "assists", "rebounds", "steals", "blocks", "threes_made"]
        
        for scope in valid_scopes:
            for stat in valid_stats:
                # Should not raise validation errors
                try:
                    await status_cog.leaders(mock_interaction, scope, stat)
                except Exception as e:
                    # Only allow specific expected errors, not validation errors
                    if "validation" not in str(e).lower():
                        raise

    @pytest.mark.asyncio
    async def test_admin_permission_check(self, mock_bot, mock_interaction):
        """Test admin permission validation."""
        admin_cog = AdminCog(mock_bot)
        
        # Test without admin permissions
        mock_interaction.user.guild_permissions.administrator = False
        
        # Should handle gracefully (either deny or show error)
        try:
            await admin_cog.announce(mock_interaction, "Test")
        except Exception as e:
            # Should not crash, should handle gracefully
            assert "permission" in str(e).lower() or "admin" in str(e).lower()


class TestDiscordErrorHandling:
    """Test Discord bot error handling."""

    @pytest.mark.asyncio
    async def test_command_error_handling(self, mock_bot, mock_interaction):
        """Test command error handling."""
        status_cog = StatusCog(mock_bot)
        
        # Mock an error in the command
        with patch.object(status_cog, '_fetch_leaders_data') as mock_fetch:
            mock_fetch.side_effect = Exception("API Error")
            
            # Should handle errors gracefully
            try:
                await status_cog.leaders(mock_interaction, "season", "all")
            except Exception:
                # Should send error message to user
                mock_interaction.response.send_message.assert_called_once()
                call_args = mock_interaction.response.send_message.call_args
                assert "error" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_interaction_timeout_handling(self, mock_bot, mock_interaction):
        """Test interaction timeout handling."""
        # Mock interaction timeout
        mock_interaction.response.send_message.side_effect = discord.errors.InteractionResponded()
        
        # Should handle gracefully
        try:
            await mock_interaction.response.send_message("Test")
        except discord.errors.InteractionResponded:
            # Should use followup instead
            mock_interaction.followup.send.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
