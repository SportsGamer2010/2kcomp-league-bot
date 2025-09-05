"""Game monitoring system for real-time notifications and analysis."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

import discord

from .config import settings
from .http import HTTPClient
from .utils import format_number, get_league_colors, get_league_emojis, create_branded_footer

logger = logging.getLogger(__name__)


@dataclass
class GameNotification:
    """Represents a game notification."""
    type: str  # 'season_high', 'record_breaker', 'game_complete'
    title: str
    description: str
    color: int
    fields: List[Dict[str, str]]
    footer: str
    thumbnail: Optional[str] = None


class GameMonitor:
    """Monitors games for notifications and analysis."""

    def __init__(self, bot):
        self.bot = bot
        self.http_client: Optional[HTTPClient] = None
        self.last_checked: Optional[datetime] = None
        self.processed_games: Set[str] = set()
        self.current_season_highs: Dict[str, Dict] = {}
        self.notification_channels: List[int] = []

    async def start_monitoring(self):
        """Start the game monitoring system."""
        self.http_client = getattr(self.bot, 'http_client', None)
        if not self.http_client:
            logger.error("HTTP client not available for game monitoring")
            return

        logger.info("Game monitoring system started")
        
        # Initialize current season highs
        await self._initialize_season_highs()
        
        # Start monitoring loop
        while True:
            try:
                await self._check_for_new_games()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in game monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _check_for_new_games(self):
        """Check for new games and send notifications."""
        try:
            # Get recent events (last 2 hours)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=2)
            
            events = await self._fetch_events_in_range(start_time, end_time)
            
            for event in events:
                event_id = str(event.get('id', ''))
                
                # Skip if we've already processed this game
                if event_id in self.processed_games:
                    continue
                
                # Process the new game
                await self._process_new_game(event)
                self.processed_games.add(event_id)
                
        except Exception as e:
            logger.error(f"Error checking for new games: {e}")

    async def _process_new_game(self, event: Dict):
        """Process a new game and generate notifications."""
        try:
            # Check for season highs
            season_high_notifications = await self._check_season_highs(event)
            
            # Check for record breakers
            record_notifications = await self._check_record_breakers(event)
            
            # Send notifications
            all_notifications = season_high_notifications + record_notifications
            
            for notification in all_notifications:
                await self._send_notification(notification)
                
        except Exception as e:
            logger.error(f"Error processing new game: {e}")

    async def _check_season_highs(self, event: Dict) -> List[GameNotification]:
        """Check if the game contains any season highs."""
        notifications = []
        
        try:
            # This would need to be implemented based on your event data structure
            # For now, return placeholder logic
            
            # Example: Check if any player achieved a season high
            # You would extract player stats from the event and compare with current season highs
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error checking season highs: {e}")
            return []

    async def _check_record_breakers(self, event: Dict) -> List[GameNotification]:
        """Check if the game contains any record breakers."""
        notifications = []
        
        try:
            # This would need to be implemented based on your event data structure
            # For now, return placeholder logic
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error checking record breakers: {e}")
            return []

    async def _send_notification(self, notification: GameNotification):
        """Send a notification to configured channels."""
        try:
            embed = discord.Embed(
                title=notification.title,
                description=notification.description,
                color=notification.color
            )
            
            for field in notification.fields:
                embed.add_field(
                    name=field['name'],
                    value=field['value'],
                    inline=field.get('inline', False)
                )
            
            embed.set_footer(text=notification.footer)
            
            if notification.thumbnail:
                embed.set_thumbnail(url=notification.thumbnail)
            
            # Send to all configured channels
            for channel_id in self.notification_channels:
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"Error sending notification to channel {channel_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    async def _fetch_events_in_range(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Fetch events within a time range."""
        try:
            url = f"{settings.SPORTSPRESS_BASE}/events"
            params = {
                'after': start_time.isoformat(),
                'before': end_time.isoformat(),
                'per_page': 50,
                'orderby': 'date',
                'order': 'desc'
            }
            
            events = await self.http_client.get_json(url, params=params)
            return events if isinstance(events, list) else []
            
        except Exception as e:
            logger.error(f"Error fetching events in range: {e}")
            return []

    async def _initialize_season_highs(self):
        """Initialize current season highs from existing games."""
        try:
            # Get current month's events
            now = datetime.now()
            first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            if now.month == 12:
                last_day = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
            
            events = await self._fetch_events_in_range(first_day, last_day)
            
            # Process all events to build season highs
            for event in events:
                await self._update_season_highs_from_event(event)
                
            logger.info(f"Initialized season highs from {len(events)} games")
            
        except Exception as e:
            logger.error(f"Error initializing season highs: {e}")

    async def _update_season_highs_from_event(self, event: Dict):
        """Update season highs from a single event."""
        try:
            # This would need to be implemented based on your event data structure
            # Extract player stats and update season highs
            pass
            
        except Exception as e:
            logger.error(f"Error updating season highs from event: {e}")

    def add_notification_channel(self, channel_id: int):
        """Add a channel to receive notifications."""
        if channel_id not in self.notification_channels:
            self.notification_channels.append(channel_id)
            logger.info(f"Added notification channel: {channel_id}")

    def remove_notification_channel(self, channel_id: int):
        """Remove a channel from notifications."""
        if channel_id in self.notification_channels:
            self.notification_channels.remove(channel_id)
            logger.info(f"Removed notification channel: {channel_id}")

    async def send_manual_notification(self, title: str, description: str, 
                                     fields: List[Dict[str, str]] = None):
        """Send a manual notification."""
        colors = get_league_colors()
        emojis = get_league_emojis()
        
        notification = GameNotification(
            type='manual',
            title=title,
            description=description,
            color=colors['info'],
            fields=fields or [],
            footer=create_branded_footer("Real-time updates")
        )
        
        await self._send_notification(notification)
