"""Admin commands for the Discord bot."""

import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings
from core.welcome import WelcomeMessage

logger = logging.getLogger(__name__)


class AdminCog(commands.Cog):
    """Admin commands for bot management."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors in admin commands."""
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You don't have permission to use admin commands.",
                ephemeral=True
            )
        else:
            logger.error(f"Admin command error: {error}")
            await interaction.response.send_message(
                "❌ An error occurred while processing your command.",
                ephemeral=True
            )
    
    def has_admin_role(self, member: discord.Member) -> bool:
        """Check if a member has the admin role."""
        return any(role.name == settings.ADMIN_ROLE for role in member.roles)
    
    @app_commands.command(name="admin-announce", description="Send an announcement to the announce channel")
    @app_commands.describe(
        message="The announcement message to send",
        ping="Whether to ping @everyone (default: false)"
    )
    async def announce(
        self, 
        interaction: discord.Interaction, 
        message: str, 
        ping: bool = False
    ):
        """Send an announcement to the announce channel."""
        # Check permissions
        if not self.has_admin_role(interaction.user):
            await interaction.response.send_message(
                f"❌ You need the '{settings.ADMIN_ROLE}' role to use this command.",
                ephemeral=True
            )
            return
        
        # Get announce channel
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a guild.",
                ephemeral=True
            )
            return
        
        announce_channel = guild.get_channel(settings.ANNOUNCE_CHANNEL_ID)
        if not announce_channel:
            await interaction.response.send_message(
                "❌ Announce channel not found.",
                ephemeral=True
            )
            return
        
        try:
            # Create embed
            embed = discord.Embed(
                title="📢 League Announcement",
                description=message,
                color=0x00ff00,  # Green
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Announced by {interaction.user.display_name}")
            
            # Send announcement
            content = "@everyone" if ping else None
            await announce_channel.send(content=content, embed=embed)
            
            # Confirm to user
            await interaction.response.send_message(
                f"✅ Announcement sent to {announce_channel.mention}",
                ephemeral=True
            )
            
            logger.info(f"Announcement sent by {interaction.user}: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to send announcement: {e}")
            await interaction.response.send_message(
                "❌ Failed to send announcement.",
                ephemeral=True
            )
    
    @app_commands.command(name="admin-status", description="Check bot status and configuration")
    async def status(self, interaction: discord.Interaction):
        """Check bot status and configuration."""
        # Check permissions
        if not self.has_admin_role(interaction.user):
            await interaction.response.send_message(
                f"❌ You need the '{settings.ADMIN_ROLE}' role to use this command.",
                ephemeral=True
            )
            return
        
        try:
            # Get bot info
            guild = interaction.guild
            announce_channel = guild.get_channel(settings.ANNOUNCE_CHANNEL_ID) if guild else None
            history_channel = guild.get_channel(settings.HISTORY_CHANNEL_ID) if guild else None
            
            # Create status embed
            embed = discord.Embed(
                title="🤖 Bot Status",
                color=0x0099ff,
                timestamp=discord.utils.utcnow()
            )
            
            # Bot info
            embed.add_field(
                name="Bot Info",
                value=f"**Name**: {self.bot.user.name}\n"
                      f"**ID**: {self.bot.user.id}\n"
                      f"**Uptime**: {self.get_uptime()}",
                inline=False
            )
            
            # Channel status
            channels_status = []
            if announce_channel:
                channels_status.append(f"✅ Announce: {announce_channel.mention}")
            else:
                channels_status.append(f"❌ Announce: Not found (ID: {settings.ANNOUNCE_CHANNEL_ID})")
            
            if history_channel:
                channels_status.append(f"✅ History: {history_channel.mention}")
            else:
                channels_status.append(f"❌ History: Not found (ID: {settings.HISTORY_CHANNEL_ID})")
            
            embed.add_field(
                name="Channels",
                value="\n".join(channels_status),
                inline=False
            )
            
            # Configuration
            embed.add_field(
                name="Configuration",
                value=f"**Poll Interval**: {settings.POLL_INTERVAL_SECONDS}s\n"
                      f"**Records Interval**: {settings.RECORDS_POLL_INTERVAL_SECONDS}s\n"
                      f"**Admin Role**: {settings.ADMIN_ROLE}",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Failed to get bot status: {e}")
            await interaction.response.send_message(
                "❌ Failed to get bot status.",
                ephemeral=True
            )
    
    @app_commands.command(name="admin-welcome", description="Send welcome message with countdown")
    @app_commands.describe(channel="Channel to send welcome message to (optional)")
    async def welcome(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """Send welcome message with NBA 2K26 Season 1 countdown."""
        try:
            # Check if user has admin role
            if not any(role.name == settings.ADMIN_ROLE for role in interaction.user.roles):
                await interaction.response.send_message(
                    f"❌ You need the `{settings.ADMIN_ROLE}` role to use this command.",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer(ephemeral=True)
            
            # Create welcome message instance
            welcome_msg = WelcomeMessage(self.bot)
            
            if channel:
                # Send to specified channel
                embed = welcome_msg.create_welcome_embed()
                await channel.send(embed=embed)
                await interaction.followup.send(
                    f"✅ Welcome message sent to {channel.mention}!",
                    ephemeral=True
                )
            else:
                # Send to random channel
                success = await welcome_msg.send_welcome_message()
                if success:
                    await interaction.followup.send(
                        "✅ Welcome message sent to a random channel!",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Failed to send welcome message. Check bot logs.",
                        ephemeral=True
                    )
                    
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
            await interaction.followup.send(
                "❌ Failed to send welcome message.",
                ephemeral=True
            )

    @app_commands.command(name="admin-sync", description="Sync slash commands with Discord (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        """Sync slash commands with Discord."""
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.NotFound:
            # Interaction already expired, can't respond
            logger.warning(f"Sync command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring sync command: {e}")
            return
        
        try:
            synced = await self.bot.tree.sync()
            await interaction.followup.send(
                f"✅ Successfully synced {len(synced)} command(s) with Discord.",
                ephemeral=True
            )
            logger.info(f"Commands synced by {interaction.user}: {len(synced)} commands")
        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to sync commands: {str(e)}",
                ephemeral=True
            )
            logger.error(f"Command sync failed: {e}")

    @app_commands.command(name="admin-clear-commands", description="Clear all global commands and sync only this bot's commands (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def clear_commands(self, interaction: discord.Interaction):
        """Clear all global commands and sync only this bot's commands."""
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.NotFound:
            # Interaction already expired, can't respond
            logger.warning(f"Clear commands interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring clear commands: {e}")
            return
        
        try:
            # First, clear all global commands by syncing with guild=None
            await self.bot.tree.sync(guild=None)
            logger.info("Cleared all global commands")
            
            # Then sync this bot's commands
            synced = await self.bot.tree.sync()
            
            await interaction.followup.send(
                f"✅ Successfully cleared all global commands and synced {len(synced)} command(s) from this bot.\n"
                f"**Note:** This only affects your view. Other users will still see their bot commands.",
                ephemeral=True
            )
            logger.info(f"Commands cleared and synced by {interaction.user}: {len(synced)} commands")
        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to clear and sync commands: {str(e)}",
                ephemeral=True
            )
            logger.error(f"Command clear and sync failed: {e}")

    @app_commands.command(name="admin-test", description="Test command to verify admin commands work")
    @app_commands.default_permissions(administrator=True)
    async def test_clear(self, interaction: discord.Interaction):
        """Test command to verify admin commands work."""
        await interaction.response.send_message("✅ Test command works!", ephemeral=True)

    def get_uptime(self) -> str:
        """Get bot uptime as a formatted string."""
        # This is a simplified version - in a real implementation,
        # you'd track the start time
        return "Running"


async def setup(bot: commands.Bot):
    """Set up the admin cog."""
    await bot.add_cog(AdminCog(bot))
    logger.info("Admin cog loaded")
