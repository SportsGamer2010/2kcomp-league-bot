"""Achievement commands for double-doubles and triple-doubles."""

import logging
from typing import List

import discord
from discord.ext import commands
from discord import app_commands

from core.records import compute_single_game_records, resolve_record_names
from core.utils import create_branded_footer, get_league_branding

logger = logging.getLogger(__name__)


class AchievementsCog(commands.Cog):
    """Commands for displaying player achievements like double-doubles and triple-doubles."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.branding = get_league_branding()

    @app_commands.command(name="doubledoubles", description="Show all double-doubles in league history")
    @app_commands.default_permissions()
    async def doubledoubles(self, interaction: discord.Interaction):
        """Show all double-doubles in league history."""
        await interaction.response.defer()
        
        try:
            # Get HTTP client from bot
            http_client = getattr(self.bot, 'http_client', None)
            if not http_client:
                await interaction.followup.send(
                    "❌ HTTP client not available. Please try again later.",
                    ephemeral=True
                )
                return

            # Send initial message
            await interaction.followup.send("🔍 Scanning historical games for double-doubles... This may take a moment.", ephemeral=True)

            # Compute records to get double-doubles
            records = await compute_single_game_records(http_client)
            
            # Send update
            await interaction.followup.send("📊 Processing player and team names...", ephemeral=True)
            
            # Only resolve names for double-doubles to speed up the process
            import asyncio
            try:
                # Set a longer timeout for name resolution (60 seconds)
                records = await asyncio.wait_for(
                    resolve_record_names(http_client, records), 
                    timeout=60.0  # Increased to 60 seconds
                )
            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ Name resolution timed out, showing results with available data...", ephemeral=True)

            if not records.double_doubles:
                await interaction.followup.send(
                    "📊 No double-doubles found in league history.",
                    ephemeral=True
                )
                return

            # Create embed
            embed = self._create_double_doubles_embed(records.double_doubles)
            await interaction.followup.send(embed=embed)
            
            logger.info(f"Double-doubles command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in double-doubles command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching double-doubles. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="tripledoubles", description="Show all triple-doubles in league history")
    @app_commands.default_permissions()
    async def tripledoubles(self, interaction: discord.Interaction):
        """Show all triple-doubles in league history."""
        await interaction.response.defer()
        
        try:
            # Get HTTP client from bot
            http_client = getattr(self.bot, 'http_client', None)
            if not http_client:
                await interaction.followup.send(
                    "❌ HTTP client not available. Please try again later.",
                    ephemeral=True
                )
                return

            # Send initial message
            await interaction.followup.send("🔍 Scanning historical games for triple-doubles... This may take a moment.", ephemeral=True)

            # Compute records to get triple-doubles
            records = await compute_single_game_records(http_client)
            
            # Send update
            await interaction.followup.send("📊 Processing player and team names...", ephemeral=True)
            
            # Only resolve names for triple-doubles to speed up the process
            import asyncio
            try:
                # Set a longer timeout for name resolution (60 seconds)
                records = await asyncio.wait_for(
                    resolve_record_names(http_client, records), 
                    timeout=60.0  # Increased to 60 seconds
                )
            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ Name resolution timed out, showing results with available data...", ephemeral=True)

            if not records.triple_doubles:
                await interaction.followup.send(
                    "👑 No triple-doubles found in league history.",
                    ephemeral=True
                )
                return

            # Debug: Log the first few triple-doubles to see what data we have
            logger.info(f"Found {len(records.triple_doubles)} triple-doubles")
            for i, td in enumerate(records.triple_doubles[:3]):  # Log first 3
                logger.info(f"Triple-double {i+1}: player='{td.player}', player_url='{getattr(td, 'player_url', 'None')}', categories={td.categories}")

            # Create embed
            embed = self._create_triple_doubles_embed(records.triple_doubles)
            await interaction.followup.send(embed=embed)
            
            logger.info(f"Triple-doubles command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in triple-doubles command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching triple-doubles. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    def _create_double_doubles_embed(self, double_doubles: List) -> discord.Embed:
        """Create an embed for double-doubles."""
        embed = discord.Embed(
            title="🔥 2KCompLeague Double-Doubles",
            description="**Players who achieved 10+ in 2 statistical categories in a single game**\n*Click player names for profiles, click game links for match details*",
            color=self.branding["colors"]["secondary"]
        )
        embed.set_footer(text=create_branded_footer())

        # Sort by date (most recent first)
        sorted_dds = sorted(double_doubles, key=lambda x: x.date, reverse=True)

        # Limit to first 15 double-doubles to avoid Discord limits
        limited_dds = sorted_dds[:15]
        
        # Split into smaller chunks to avoid Discord field limits
        chunk_size = 3  # Reduced to 3 entries per field
        max_fields = 5  # Limit to 5 fields to stay under Discord's limits
        
        for i in range(0, min(len(limited_dds), max_fields * chunk_size), chunk_size):
            chunk = limited_dds[i:i + chunk_size]
            
            field_value = ""
            for dd in chunk:
                # Make player name clickable if we have a player URL
                if hasattr(dd, 'player_url') and dd.player_url:
                    player_display = f"[**{dd.player}**]({dd.player_url})"
                else:
                    player_display = f"**{dd.player}**"
                
                # Format the categories and values (shorter format)
                category_display = []
                for cat in dd.categories:
                    if cat in dd.values:
                        category_display.append(f"{cat.title()}: {int(dd.values[cat])}")
                
                # Truncate long game names
                game_name = dd.game if len(dd.game) <= 30 else dd.game[:27] + "..."
                
                field_value += f"{player_display} - {', '.join(category_display)}\n"
                field_value += f"Game: {game_name} ({dd.date})\n"
                if hasattr(dd, 'game_url') and dd.game_url:
                    field_value += f"[View Game]({dd.game_url})\n"
                field_value += "\n"
            
            # Ensure field value doesn't exceed 1024 characters
            if len(field_value) > 1000:  # Leave some buffer
                field_value = field_value[:997] + "..."
            
            field_name = f"Double-Doubles (Part {i//chunk_size + 1})" if i > 0 else "Double-Doubles"
            embed.add_field(
                name=field_name,
                value=field_value.strip(),
                inline=False
            )

        # Add summary if we limited the results
        if len(sorted_dds) > 15:
            embed.add_field(
                name="📊 Summary",
                value=f"Showing the 15 most recent double-doubles out of {len(sorted_dds)} total.",
                inline=False
            )

        return embed

    def _create_triple_doubles_embed(self, triple_doubles: List) -> discord.Embed:
        """Create an embed for triple-doubles."""
        embed = discord.Embed(
            title="👑 2KCompLeague Triple-Doubles",
            description="**Players who achieved 10+ in 3 statistical categories in a single game**\n*Click player names for profiles, click game links for match details*",
            color=self.branding["colors"]["primary"]
        )
        embed.set_footer(text=create_branded_footer())

        # Sort by date (most recent first)
        sorted_tds = sorted(triple_doubles, key=lambda x: x.date, reverse=True)

        # Limit to first 15 triple-doubles to avoid Discord limits
        limited_tds = sorted_tds[:15]
        
        # Split into smaller chunks to avoid Discord field limits
        chunk_size = 3  # Reduced to 3 entries per field
        max_fields = 5  # Limit to 5 fields to stay under Discord's limits
        
        for i in range(0, min(len(limited_tds), max_fields * chunk_size), chunk_size):
            chunk = limited_tds[i:i + chunk_size]
            
            field_value = ""
            for td in chunk:
                # Debug: Log what we're working with
                logger.info(f"Processing triple-double: player='{td.player}', has_player_url={hasattr(td, 'player_url')}, player_url={getattr(td, 'player_url', 'None')}")
                
                # Make player name clickable if we have a player URL
                if hasattr(td, 'player_url') and td.player_url:
                    player_display = f"[**{td.player}**]({td.player_url})"
                else:
                    player_display = f"**{td.player}**"
                
                # Format the categories and values (shorter format)
                category_display = []
                for cat in td.categories:
                    if cat in td.values:
                        category_display.append(f"{cat.title()}: {int(td.values[cat])}")
                
                # Truncate long game names
                game_name = td.game if len(td.game) <= 30 else td.game[:27] + "..."
                
                field_value += f"{player_display} - {', '.join(category_display)}\n"
                field_value += f"Game: {game_name} ({td.date})\n"
                if hasattr(td, 'game_url') and td.game_url:
                    field_value += f"[View Game]({td.game_url})\n"
                field_value += "\n"
            
            # Ensure field value doesn't exceed 1024 characters
            if len(field_value) > 1000:  # Leave some buffer
                field_value = field_value[:997] + "..."
            
            field_name = f"Triple-Doubles (Part {i//chunk_size + 1})" if i > 0 else "Triple-Doubles"
            embed.add_field(
                name=field_name,
                value=field_value.strip(),
                inline=False
            )

        # Add summary if we limited the results
        if len(sorted_tds) > 15:
            embed.add_field(
                name="📊 Summary",
                value=f"Showing the 15 most recent triple-doubles out of {len(sorted_tds)} total.",
                inline=False
            )

        return embed


async def setup(bot: commands.Bot):
    """Set up the achievements cog."""
    await bot.add_cog(AchievementsCog(bot))
    
    # List all commands in the tree for debugging
    all_commands = [cmd.name for cmd in bot.tree.get_commands()]
    logger.info(f"All commands in bot tree: {all_commands}")
    
    logger.info("Achievements cog loaded successfully")
