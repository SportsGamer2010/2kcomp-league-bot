"""Notification management commands."""

import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings

logger = logging.getLogger(__name__)


class NotificationsCog(commands.Cog):
    """Notification management commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def has_admin_role(self, user: discord.Member) -> bool:
        """Check if user has admin role."""
        if not user or not hasattr(user, 'roles'):
            return False
        return any(role.name == settings.ADMIN_ROLE for role in user.roles)
    
    @app_commands.command(name="notifications", description="Manage notification system")
    @app_commands.describe(
        action="Action to perform",
        message="Custom message for manual notification (optional)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Status", value="status"),
        app_commands.Choice(name="Test", value="test"),
        app_commands.Choice(name="Weekly Summary", value="weekly"),
        app_commands.Choice(name="Manual Alert", value="manual")
    ])
    async def notifications(
        self,
        interaction: discord.Interaction,
        action: str,
        message: Optional[str] = None
    ):
        """Manage the notification system."""
        # Check permissions
        if not self.has_admin_role(interaction.user):
            await interaction.response.send_message(
                f"❌ You need the '{settings.ADMIN_ROLE}' role to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            if action == "status":
                await self._show_notification_status(interaction)
            elif action == "test":
                await self._test_notification_system(interaction)
            elif action == "weekly":
                await self._send_weekly_summary(interaction)
            elif action == "manual":
                await self._send_manual_alert(interaction, message)
            else:
                await interaction.followup.send(
                    "❌ Invalid action. Use: status, test, weekly, or manual",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error in notifications command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while processing the notification command.",
                ephemeral=True
            )
    
    async def _show_notification_status(self, interaction: discord.Interaction):
        """Show notification system status."""
        try:
            # Get announce channel
            channel = self.bot.get_channel(settings.ANNOUNCE_CHANNEL_ID)
            channel_status = "✅ Connected" if channel else "❌ Not Found"
            
            # Create status embed
            embed = discord.Embed(
                title="🔔 Notification System Status",
                description="Current status of the notification system",
                color=0x0099ff,
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="📢 Announce Channel",
                value=f"{channel_status}\nChannel ID: {settings.ANNOUNCE_CHANNEL_ID}",
                inline=True
            )
            
            embed.add_field(
                name="🤖 Bot Status",
                value=f"✅ Online\nUptime: {self._get_uptime()}",
                inline=True
            )
            
            embed.add_field(
                name="📊 Monitoring",
                value="✅ Active\n• Game Events\n• Stat Milestones\n• Record Breakers\n• Weekly Summaries",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Milestone Thresholds",
                value="• Points: 20, 30, 40, 50, 60, 70+\n• Assists: 10, 15, 20, 25+\n• Rebounds: 10, 15, 20, 25, 30+\n• Steals: 5, 7, 10+\n• Blocks: 3, 5, 7, 10+\n• 3PM: 5, 7, 10, 15+",
                inline=False
            )
            
            embed.add_field(
                name="🔥 Record Alerts",
                value="• 50+ Points\n• 20+ Assists\n• 20+ Rebounds\n• 8+ Steals\n• 5+ Blocks\n• 10+ 3-Pointers",
                inline=False
            )
            
            embed.set_footer(text="2KCompLeague | Notification System")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing notification status: {e}")
            await interaction.followup.send(
                "❌ Error retrieving notification status.",
                ephemeral=True
            )
    
    async def _test_notification_system(self, interaction: discord.Interaction):
        """Test the notification system with a sample notification."""
        try:
            # Get announce channel
            channel = self.bot.get_channel(settings.ANNOUNCE_CHANNEL_ID)
            if not channel:
                await interaction.followup.send(
                    "❌ Announce channel not found. Please check configuration.",
                    ephemeral=True
                )
                return
            
            # Create test embed
            embed = discord.Embed(
                title="🧪 Test Notification",
                description="This is a test of the notification system!",
                color=0x00FF00,
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="✅ System Check",
                value="• Notification system is working\n• Channel connectivity confirmed\n• Embed formatting successful",
                inline=False
            )
            
            embed.add_field(
                name="📊 What to Expect",
                value="• Real-time stat milestone alerts\n• Record-breaking notifications\n• Weekly league summaries\n• Game event updates",
                inline=False
            )
            
            embed.set_footer(text="2KCompLeague | Test Notification")
            
            # Send test notification
            await channel.send(embed=embed)
            
            await interaction.followup.send(
                "✅ Test notification sent successfully!",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error testing notification system: {e}")
            await interaction.followup.send(
                "❌ Error sending test notification.",
                ephemeral=True
            )
    
    async def _send_weekly_summary(self, interaction: discord.Interaction):
        """Manually send a weekly summary."""
        try:
            # Get announce channel
            channel = self.bot.get_channel(settings.ANNOUNCE_CHANNEL_ID)
            if not channel:
                await interaction.followup.send(
                    "❌ Announce channel not found.",
                    ephemeral=True
                )
                return
            
            # Create weekly summary embed
            embed = discord.Embed(
                title="📊 Weekly League Summary",
                description="Here's what happened in 2KCompLeague this week!",
                color=0x0099ff,
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="🏀 Top Performers",
                value="• Check `/leaders season` for this week's top performers\n• Use `/leaders career` for all-time leaders",
                inline=False
            )
            
            embed.add_field(
                name="🔥 Record Breakers",
                value="• Check `/records` for all-time single-game records\n• New records are highlighted in real-time!",
                inline=False
            )
            
            embed.add_field(
                name="📈 League Standings",
                value="• Check the [Season 1 Standings](https://2kcompleague.com/table/nba2k26-season-1-standings/)\n• Season starts October 1st!",
                inline=False
            )
            
            embed.add_field(
                name="📊 Season Stats",
                value="• View [Season 1 Stats](https://2kcompleague.com/list/nba2k26-season-1-stats/)\n• Track your progress throughout the season!",
                inline=False
            )
            
            embed.set_footer(text="2KCompLeague | Powered by SportsPress")
            
            # Send weekly summary
            await channel.send(embed=embed)
            
            await interaction.followup.send(
                "✅ Weekly summary sent successfully!",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error sending weekly summary: {e}")
            await interaction.followup.send(
                "❌ Error sending weekly summary.",
                ephemeral=True
            )
    
    async def _send_manual_alert(self, interaction: discord.Interaction, message: Optional[str]):
        """Send a manual alert notification."""
        try:
            if not message:
                await interaction.followup.send(
                    "❌ Please provide a message for the manual alert.",
                    ephemeral=True
                )
                return
            
            # Get announce channel
            channel = self.bot.get_channel(settings.ANNOUNCE_CHANNEL_ID)
            if not channel:
                await interaction.followup.send(
                    "❌ Announce channel not found.",
                    ephemeral=True
                )
                return
            
            # Create manual alert embed
            embed = discord.Embed(
                title="📢 Manual Alert",
                description=message,
                color=0xFF6B35,  # Orange
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="👤 Sent By",
                value=f"{interaction.user.display_name}",
                inline=True
            )
            
            embed.set_footer(text="2KCompLeague | Manual Alert")
            
            # Send manual alert
            await channel.send(embed=embed)
            
            await interaction.followup.send(
                "✅ Manual alert sent successfully!",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error sending manual alert: {e}")
            await interaction.followup.send(
                "❌ Error sending manual alert.",
                ephemeral=True
            )
    
    def _get_uptime(self) -> str:
        """Get bot uptime."""
        try:
            uptime = discord.utils.utcnow() - self.bot.start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "Unknown"


async def setup(bot: commands.Bot):
    """Set up the notifications cog."""
    await bot.add_cog(NotificationsCog(bot))
    logger.info("Notifications cog loaded")
