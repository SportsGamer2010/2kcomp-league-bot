"""Records management cog for Discord bot."""

import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings
from core.records import compute_single_game_records, resolve_record_names, format_records_embed
from core.record_monitor import RecordMonitor
from core.utils import get_league_colors, create_branded_footer

logger = logging.getLogger(__name__)


class RecordsCog(commands.Cog):
    """Cog for records-related commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="records", description="Show single-game records")
    async def records(self, interaction: discord.Interaction):
        """Show single-game records."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            # Interaction already expired, can't respond
            logger.warning(f"Records command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring records command: {e}")
            return
        
        http_client = getattr(self.bot, 'http_client', None)
        if not http_client:
            await interaction.followup.send(
                "❌ Bot is not properly initialized. Please try again later.",
                ephemeral=True
            )
            return
        
        try:
            # Send initial progress message
            await interaction.followup.send("🔍 Scanning historical games for records... This may take a moment.", ephemeral=True)
            
            # Compute records
            records_data = await compute_single_game_records(http_client)
            
            if not records_data:
                await interaction.followup.send(
                    "❌ No records data available at the moment.",
                    ephemeral=True
                )
                return
            
            # Send progress update
            await interaction.followup.send("📊 Processing player and team names...", ephemeral=True)
            
            # Resolve player and team names with timeout
            import asyncio
            try:
                records_data = await asyncio.wait_for(
                    resolve_record_names(http_client, records_data), 
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ Name resolution timed out, showing results with available data...", ephemeral=True)
            
            # Format embed
            embed = format_records_embed(records_data)
            
            await interaction.followup.send(embed=discord.Embed.from_dict(embed))
            
            logger.info(f"Records command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in records command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching records. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="check-records", description="Check for new records (Admin only)")
    @app_commands.describe(force="Force check even if no new records")
    async def check_records(self, interaction: discord.Interaction, force: bool = False):
        """Check for new records and send notifications."""
        # Check if user has admin role
        if not any(role.id == settings.ADMIN_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        http_client = getattr(self.bot, 'http_client', None)
        if not http_client:
            await interaction.followup.send(
                "❌ Bot is not properly initialized. Please try again later.",
                ephemeral=True
            )
            return
        
        try:
            # Create a temporary record monitor to check for new records
            monitor = RecordMonitor(self.bot, http_client)
            
            # Load previous records
            previous_records = await monitor.load_previous_records()
            
            # Compute current records
            current_records = await compute_single_game_records(http_client)
            if current_records:
                current_records = await resolve_record_names(http_client, current_records)
                
                # Check for new records
                new_records = await monitor.check_for_new_records(current_records)
                
                if new_records:
                    await monitor.send_record_notification(new_records)
                    await interaction.followup.send(
                        f"✅ Found {len(new_records)} new record(s)! Notifications sent.",
                        ephemeral=True
                    )
                elif force:
                    await interaction.followup.send(
                        "ℹ️ No new records found, but check completed successfully.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "ℹ️ No new records found.",
                        ephemeral=True
                    )
                
                # Save current records
                await monitor.save_current_records(current_records)
            else:
                await interaction.followup.send(
                    "❌ Could not fetch current records.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error in check-records command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while checking records. Please try again later.",
                ephemeral=True
            )

    @app_commands.command(name="record-stats", description="Show record statistics (Admin only)")
    async def record_stats(self, interaction: discord.Interaction):
        """Show record statistics and monitoring info."""
        # Check if user has admin role
        if not any(role.id == settings.ADMIN_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        http_client = getattr(self.bot, 'http_client', None)
        if not http_client:
            await interaction.followup.send(
                "❌ Bot is not properly initialized. Please try again later.",
                ephemeral=True
            )
            return
        
        try:
            # Compute current records
            records_data = await compute_single_game_records(http_client)
            if records_data:
                records_data = await resolve_record_names(http_client, records_data)
                
                # Create stats embed
                colors = get_league_colors()
                embed = discord.Embed(
                    title="📊 2KCompLeague Record Statistics",
                    color=colors["success"],
                    description="**Current record monitoring status**\n*Real-time tracking of all-time single-game records*"
                )
                
                # Count records with proper data
                record_types = ['points', 'rebounds', 'assists', 'steals', 'blocks', 
                              'threes_made', 'threep_percent']
                
                total_records = 0
                records_with_names = 0
                records_with_urls = 0
                
                for record_type in record_types:
                    record = getattr(records_data, record_type, None)
                    if record:
                        total_records += 1
                        if record.holder and not record.holder.startswith("Player "):
                            records_with_names += 1
                        if hasattr(record, 'game_url') and record.game_url:
                            records_with_urls += 1
                
                embed.add_field(
                    name="Record Count",
                    value=f"Total Records: {total_records}\n"
                          f"With Real Names: {records_with_names}\n"
                          f"With URLs: {records_with_urls}",
                    inline=True
                )
                
                # Show top records
                top_records = []
                for record_type in ['points', 'rebounds', 'assists']:
                    record = getattr(records_data, record_type, None)
                    if record:
                        top_records.append(f"{record_type.title()}: {record.holder} - {record.value}")
                
                if top_records:
                    embed.add_field(
                        name="Top Records",
                        value="\n".join(top_records[:3]),
                        inline=True
                    )
                
                embed.set_footer(text="2KCompLeague | Record Monitor")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(
                    "❌ Could not fetch record statistics.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error in record-stats command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while fetching record statistics. Please try again later.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Set up the records cog."""
    await bot.add_cog(RecordsCog(bot))
    logger.info("Records cog loaded")
