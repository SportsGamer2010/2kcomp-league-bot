#!/usr/bin/env python3
"""Main Discord bot application for 2KCompLeague."""

import asyncio
import logging
import signal
import sys
from typing import Optional
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

from core.config import settings
from core.logging import setup_logging
from core.http import HTTPClient, create_http_session, close_http_session
from core.sportspress import fetch_players_for_season
from core.leaders import top_n_season_leaders, top_n_career_leaders, format_leaders_embed
from core.records import compute_single_game_records, format_records_embed
from core.milestones import scan_and_detect_crossings, format_milestone_embed
from core.persistence import (
    state_manager, 
    update_leaders_in_state, 
    update_milestones_in_state,
    get_last_leaders_from_state,
    get_milestone_state_from_persistence
)
from core.welcome import send_welcome_on_startup
from core.record_monitor import start_record_monitor
from core.notification_system import start_notification_system
from core.health_server import start_health_server
from core.health import HealthChecker

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# Global variables
http_client: Optional[HTTPClient] = None
announce_channel: Optional[discord.TextChannel] = None
history_channel: Optional[discord.TextChannel] = None
health_server = None


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    global announce_channel, history_channel
    
    logger.info(f"Bot logged in as {bot.user}")
    logger.info(f"Connected to {len(bot.guilds)} guild(s)")
    
    # Get channels
    guild = bot.get_guild(settings.GUILD_ID)
    if guild:
        announce_channel = guild.get_channel(settings.ANNOUNCE_CHANNEL_ID)
        history_channel = guild.get_channel(settings.HISTORY_CHANNEL_ID)
        
        if announce_channel:
            logger.info(f"Announce channel: {announce_channel.name}")
        else:
            logger.error(f"Could not find announce channel {settings.ANNOUNCE_CHANNEL_ID}")
            
        if history_channel:
            logger.info(f"History channel: {history_channel.name}")
        else:
            logger.error(f"Could not find history channel {settings.HISTORY_CHANNEL_ID}")
    
    # Load cogs
    await bot.load_extension("cogs.admin")
    await bot.load_extension("cogs.status")
    await bot.load_extension("cogs.records")
    await bot.load_extension("cogs.history")
    await bot.load_extension("cogs.player")
    await bot.load_extension("cogs.milestones")
    await bot.load_extension("cogs.league")
    await bot.load_extension("cogs.game_analysis")
    await bot.load_extension("cogs.polls")
    await bot.load_extension("cogs.notifications")
    await bot.load_extension("cogs.spotlight")
    await bot.load_extension("cogs.achievements")
    
    # Start background tasks
    leaders_monitor.start()
    milestones_monitor.start()
    records_monitor.start()
    
    logger.info("Background tasks started")
    logger.info("All cogs loaded")
    
    # Sync command tree to fix signature mismatches
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
    
    # Send welcome message
    asyncio.create_task(send_welcome_on_startup(bot))
    
    # Start record monitoring
    if http_client:
        asyncio.create_task(start_record_monitor(bot, http_client))
    
    # Start notification system
    if http_client:
        asyncio.create_task(start_notification_system(bot, http_client))
    
    # Start health server
    global health_server
    try:
        health_checker = HealthChecker()
        health_server = await start_health_server(health_checker, bot)
        logger.info(f"Health server started at {health_server.get_url()}")
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
        return
    
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param}")
        return
    
    logger.error(f"Command error: {error}", exc_info=error)
    await ctx.send("❌ An error occurred while processing your command.")


@tasks.loop(seconds=settings.POLL_INTERVAL_SECONDS)
async def leaders_monitor():
    """Monitor for changes in season leaders."""
    global http_client
    
    if not http_client or not announce_channel:
        return
    
    try:
        logger.debug("Checking for leaders changes...")
        
        # Get current leaders
        current_leaders = await top_n_season_leaders(http_client)
        if not current_leaders:
            logger.warning("No current leaders data available")
            return
        
        # Get last known leaders
        last_leaders = get_last_leaders_from_state()
        
        # Check for changes
        changes = []
        for stat in ["points", "assists", "rebounds", "steals", "blocks", "threes_made"]:
            current_list = getattr(current_leaders, stat, [])
            last_list = getattr(last_leaders, stat, [])
            
            if current_list != last_list:
                changes.append(stat)
        
        if changes:
            logger.info(f"Leaders changes detected: {changes}")
            
            # Create embed for changes
            embed = format_leaders_embed(current_leaders, "Season Leaders")
            embed["title"] = "🏆 Season Leaders Update"
            embed["description"] = f"Changes detected in: {', '.join(changes)}"
            
            await announce_channel.send(embed=discord.Embed.from_dict(embed))
            
            # Update state
            update_leaders_in_state(current_leaders)
            
        else:
            logger.debug("No leaders changes detected")
            
    except Exception as e:
        logger.error(f"Error in leaders monitor: {e}")


@tasks.loop(seconds=settings.POLL_INTERVAL_SECONDS)
async def milestones_monitor():
    """Monitor for milestone crossings."""
    global http_client
    
    if not http_client or not announce_channel:
        return
    
    try:
        logger.debug("Checking for milestone crossings...")
        
        # Get current milestone state
        last_totals, milestones_sent = get_milestone_state_from_persistence()
        
        # Scan for crossings
        notifications, updated_totals, updated_milestones = await scan_and_detect_crossings(
            http_client, last_totals, milestones_sent
        )
        
        if notifications:
            logger.info(f"Found {len(notifications)} new milestone crossings")
            
            # Create embed
            embed = format_milestone_embed(notifications)
            if embed:
                await announce_channel.send(embed=discord.Embed.from_dict(embed))
            
            # Update state
            update_milestones_in_state(updated_totals, updated_milestones)
            
        else:
            logger.debug("No new milestone crossings detected")
            
    except Exception as e:
        logger.error(f"Error in milestones monitor: {e}")


@tasks.loop(seconds=settings.RECORDS_POLL_INTERVAL_SECONDS)
async def records_monitor():
    """Monitor for new single-game records."""
    global http_client
    
    if not http_client or not announce_channel:
        return
    
    try:
        logger.debug("Checking for new records...")
        
        # Compute current records
        current_records = await compute_single_game_records(http_client)
        if not current_records:
            logger.warning("No current records data available")
            return
        
        # TODO: Compare with previous records and detect changes
        # For now, just log that we're checking
        logger.debug("Records check completed")
        
    except Exception as e:
        logger.error(f"Error in records monitor: {e}")


@leaders_monitor.before_loop
async def before_leaders_monitor():
    """Wait for bot to be ready before starting leaders monitor."""
    await bot.wait_until_ready()


@milestones_monitor.before_loop
async def before_milestones_monitor():
    """Wait for bot to be ready before starting milestones monitor."""
    await bot.wait_until_ready()


@records_monitor.before_loop
async def before_records_monitor():
    """Wait for bot to be ready before starting records monitor."""
    await bot.wait_until_ready()


async def setup_http_client():
    """Set up the HTTP client."""
    global http_client
    
    try:
        session = await create_http_session()
        http_client = HTTPClient(session)
        # Make HTTP client accessible to the bot instance
        bot.http_client = http_client
        logger.info("HTTP client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize HTTP client: {e}")
        raise


async def cleanup_http_client():
    """Clean up the HTTP client."""
    global http_client
    
    if http_client:
        await close_http_session(http_client.session)
        logger.info("HTTP client cleaned up")


async def cleanup_health_server():
    """Clean up the health server."""
    global health_server
    
    if health_server:
        await health_server.stop()
        logger.info("Health server stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    
    # Stop background tasks
    leaders_monitor.cancel()
    milestones_monitor.cancel()
    records_monitor.cancel()
    
    # Run cleanup
    asyncio.create_task(cleanup_http_client())
    asyncio.create_task(cleanup_health_server())
    asyncio.create_task(bot.close())
    
    sys.exit(0)


async def main():
    """Main application entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Set up HTTP client
        await setup_http_client()
        
        # Debug token information
        token = settings.DISCORD_TOKEN
        logger.info(f"Token length: {len(token) if token else 'None'}")
        logger.info(f"Token starts with: {token[:5] if token and len(token) > 5 else 'None'}")
        logger.info(f"Token contains dots: {'.' in token if token else 'None'}")
        logger.info(f"Token has spaces: {' ' in token if token else 'None'}")
        logger.info(f"Token has quotes: {'"' in token or "'" in token if token else 'None'}")
        
        # Start the bot
        logger.info("Starting Discord bot...")
        await bot.start(settings.DISCORD_TOKEN)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
    finally:
        # Cleanup
        await cleanup_http_client()
        await cleanup_health_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        sys.exit(1)
