"""Spotlight player commands."""

import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings
from core.spotlight import SpotlightSystem, create_spotlight_embed

logger = logging.getLogger(__name__)


class SpotlightCog(commands.Cog):
    """Cog for spotlight player functionality."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spotlight_system = None

    async def cog_load(self):
        """Initialize the spotlight system when cog loads."""
        try:
            http_client = getattr(self.bot, 'http_client', None)
            if http_client:
                self.spotlight_system = SpotlightSystem(http_client)
                logger.info("Spotlight system initialized")
            else:
                logger.warning("HTTP client not available for spotlight system")
        except Exception as e:
            logger.error(f"Error initializing spotlight system: {e}")

    @app_commands.command(name="spotlight", description="Get a random spotlight player")
    async def spotlight(self, interaction: discord.Interaction):
        """Display a random spotlight player."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Spotlight command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring spotlight command: {e}")
            return

        try:
            if not self.spotlight_system:
                await interaction.followup.send(
                    "❌ Spotlight system not available. Please try again later.",
                    ephemeral=True
                )
                return

            # Get spotlight player
            spotlight_data = await self.spotlight_system.get_spotlight_player()
            
            if spotlight_data:
                # Create embed for spotlight
                embed = discord.Embed(
                    title=spotlight_data["title"],
                    description=create_spotlight_embed(spotlight_data),
                    color=spotlight_data.get("color", 0xDC143C),
                    url=spotlight_data.get("player_url", "")
                )
                
                # Add thumbnail if available
                if spotlight_data.get("player_url"):
                    embed.set_thumbnail(url="https://2kcompleague.com/wp-content/uploads/2024/12/2kcomp-league-logo.png")
                
                await interaction.followup.send(embed=embed)
                logger.info(f"Spotlight command used by {interaction.user}")
            else:
                await interaction.followup.send(
                    "❌ No spotlight player available at this time. Please try again later.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in spotlight command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching spotlight player. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="career-leader", description="Get a career leader spotlight")
    async def career_leader(self, interaction: discord.Interaction):
        """Display a career leader spotlight."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Career leader command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring career leader command: {e}")
            return

        try:
            if not self.spotlight_system:
                await interaction.followup.send(
                    "❌ Spotlight system not available. Please try again later.",
                    ephemeral=True
                )
                return

            # Get all-time stats for career leader
            all_time_stats = await self.spotlight_system._get_all_time_stats()
            if not all_time_stats:
                await interaction.followup.send(
                    "❌ No career statistics available. Please try again later.",
                    ephemeral=True
                )
                return

            # Get career leader spotlight
            spotlight_data = await self.spotlight_system._get_career_leader_spotlight(all_time_stats)
            
            if spotlight_data:
                embed = discord.Embed(
                    title=spotlight_data["title"],
                    description=create_spotlight_embed(spotlight_data),
                    color=spotlight_data.get("color", 0xFFD700),
                    url=spotlight_data.get("player_url", "")
                )
                
                embed.set_thumbnail(url="https://2kcompleague.com/wp-content/uploads/2024/12/2kcomp-league-logo.png")
                
                await interaction.followup.send(embed=embed)
                logger.info(f"Career leader command used by {interaction.user}")
            else:
                await interaction.followup.send(
                    "❌ No career leader data available. Please try again later.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in career leader command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching career leader. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="record-holder", description="Get a record holder spotlight")
    async def record_holder(self, interaction: discord.Interaction):
        """Display a record holder spotlight."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Record holder command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring record holder command: {e}")
            return

        try:
            if not self.spotlight_system:
                await interaction.followup.send(
                    "❌ Spotlight system not available. Please try again later.",
                    ephemeral=True
                )
                return

            # Get records for record holder
            records = await self.spotlight_system._get_single_game_records()
            if not records:
                await interaction.followup.send(
                    "❌ No record data available. Please try again later.",
                    ephemeral=True
                )
                return

            # Get record holder spotlight
            spotlight_data = await self.spotlight_system._get_record_holder_spotlight(records)
            
            if spotlight_data:
                embed = discord.Embed(
                    title=spotlight_data["title"],
                    description=create_spotlight_embed(spotlight_data),
                    color=spotlight_data.get("color", 0xDC143C),
                    url=spotlight_data.get("player_url", "")
                )
                
                embed.set_thumbnail(url="https://2kcompleague.com/wp-content/uploads/2024/12/2kcomp-league-logo.png")
                
                # Add game link if available
                if spotlight_data.get("game_url"):
                    embed.add_field(
                        name="🎮 Game Details",
                        value=f"[View Game]({spotlight_data['game_url']})",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed)
                logger.info(f"Record holder command used by {interaction.user}")
            else:
                await interaction.followup.send(
                    "❌ No record holder data available. Please try again later.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in record holder command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching record holder. Please try again later.",
                    ephemeral=True
                )
            except:
                pass


async def setup(bot: commands.Bot):
    """Setup function for the spotlight cog."""
    await bot.add_cog(SpotlightCog(bot))
