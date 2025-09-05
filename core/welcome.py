"""Welcome message functionality for the Discord bot."""

import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import List, Optional

import discord
from discord.ext import commands

from .config import settings
from .spotlight import SpotlightSystem, create_spotlight_embed

logger = logging.getLogger(__name__)


class WelcomeMessage:
    """Handles welcome messages and startup notifications."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.nba2k26_season1_date = datetime(2024, 10, 1, 0, 0, 0, tzinfo=timezone.utc)  # October 1, 2024
        self.spotlight_system = None

    def get_countdown_to_season1(self) -> str:
        """Calculate and format countdown to NBA 2K26 Season 1."""
        now = datetime.now(timezone.utc)
        time_diff = self.nba2k26_season1_date - now
        
        if time_diff.total_seconds() <= 0:
            return "🎉 **NBA 2K26 Season 1 is LIVE!** 🎉"
        
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"⏰ **{days} days, {hours} hours, {minutes} minutes** until NBA 2K26 Season 1!"
        elif hours > 0:
            return f"⏰ **{hours} hours, {minutes} minutes** until NBA 2K26 Season 1!"
        else:
            return f"⏰ **{minutes} minutes** until NBA 2K26 Season 1!"

    def create_welcome_embed(self) -> discord.Embed:
        """Create the welcome message embed."""
        embed = discord.Embed(
            title="🏀 Welcome to 2KCompLeague! 🏀",
            description="The official Discord bot for 2KCompLeague is now online!",
            color=0x00ff00,  # Green color
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add countdown
        embed.add_field(
            name="📅 NBA 2K26 Season 1 Countdown",
            value=self.get_countdown_to_season1(),
            inline=False
        )
        
        # Add registration reminder
        embed.add_field(
            name="📝 Team Registration",
            value="**Teams and Free Agents:** Don't forget to register at [2kcompleague.com/register](https://2kcompleague.com/register) to secure your spot for Season 1!",
            inline=False
        )
        
        # Add bot features
        embed.add_field(
            name="🤖 Bot Features",
            value="• `/leaders` - View season and career leaders\n• `/records` - Check single-game records\n• `/status` - Bot status and info\n• `/help` - All available commands",
            inline=False
        )
        
        # Add footer
        embed.set_footer(
            text="2KCompLeague Discord Bot • Ready to serve!",
            icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png"  # Replace with actual bot avatar URL
        )
        
        return embed

    async def get_random_text_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        """Get a random text channel from the guild."""
        try:
            # Get all text channels where the bot can send messages
            text_channels = [
                channel for channel in guild.text_channels
                if channel.permissions_for(guild.me).send_messages
                and not channel.name.startswith(('bot-', 'admin-', 'log-', 'mod-'))  # Exclude certain channels
            ]
            
            if not text_channels:
                logger.warning(f"No suitable text channels found in guild {guild.name}")
                return None
            
            # Return a random channel
            return random.choice(text_channels)
            
        except Exception as e:
            logger.error(f"Error getting random text channel: {e}")
            return None

    async def send_welcome_message(self) -> bool:
        """Send welcome message to a random channel."""
        try:
            guild = self.bot.get_guild(settings.GUILD_ID)
            if not guild:
                logger.error(f"Guild with ID {settings.GUILD_ID} not found")
                return False
            
            # Get a random text channel
            channel = await self.get_random_text_channel(guild)
            if not channel:
                logger.error("No suitable channel found for welcome message")
                return False
            
            # Create and send the welcome embed
            embed = self.create_welcome_embed()
            await channel.send(embed=embed)
            
            logger.info(f"Welcome message sent to #{channel.name} in {guild.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
            return False

    async def send_startup_notification(self) -> bool:
        """Send a startup notification with spotlight player."""
        try:
            guild = self.bot.get_guild(settings.GUILD_ID)
            if not guild:
                return False
            
            channel = await self.get_random_text_channel(guild)
            if not channel:
                return False
            
            # Initialize spotlight system if not already done
            if not self.spotlight_system:
                http_client = getattr(self.bot, 'http_client', None)
                if http_client:
                    self.spotlight_system = SpotlightSystem(http_client)
            
            # Get spotlight player
            spotlight_data = None
            if self.spotlight_system:
                try:
                    spotlight_data = await self.spotlight_system.get_spotlight_player()
                except Exception as e:
                    logger.error(f"Error getting spotlight player: {e}")
            
            # Create startup message
            message = (
                f"🤖 **2KCompLeague Bot is back online!**\n\n"
                f"{self.get_countdown_to_season1()}\n\n"
                f"📝 **Teams & Free Agents:** Register at [2kcompleague.com/register](https://2kcompleague.com/register)\n"
                f"Use `/commands` to see all available commands!\n\n"
            )
            
            # Add spotlight player if available
            if spotlight_data:
                spotlight_message = create_spotlight_embed(spotlight_data)
                message += f"---\n{spotlight_message}"
            else:
                message += "---\n🌟 **2KCompLeague Spotlight**\n*Spotlight feature coming soon!*"
            
            await channel.send(message)
            logger.info(f"Startup notification with spotlight sent to #{channel.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
            return False


async def send_welcome_on_startup(bot: commands.Bot) -> None:
    """Send welcome message when bot starts up."""
    try:
        # Wait a bit for the bot to fully initialize
        await asyncio.sleep(5)
        
        welcome = WelcomeMessage(bot)
        success = await welcome.send_startup_notification()
        
        if success:
            logger.info("✅ Welcome message sent successfully on startup")
        else:
            logger.warning("⚠️ Failed to send welcome message on startup")
            
    except Exception as e:
        logger.error(f"Error in welcome startup process: {e}")
