"""Comprehensive notification system for stat updates, record breakers, and league events."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field

from .config import settings
from .http import HTTPClient
from .names import get_player_name, get_team_name, get_player_url

logger = logging.getLogger(__name__)


@dataclass
class GameEvent:
    """Represents a game event for tracking."""
    game_id: int
    date: str
    home_team: str
    away_team: str
    players: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StatMilestone:
    """Represents a statistical milestone."""
    player_name: str
    player_id: int
    stat_type: str
    value: float
    game_id: int
    game_date: str
    team_name: str
    is_record: bool = False
    is_season_high: bool = False
    is_career_high: bool = False


@dataclass
class NotificationState:
    """Tracks notification state to avoid duplicates."""
    last_game_id: int = 0
    last_check_time: datetime = field(default_factory=datetime.now)
    processed_games: Set[int] = field(default_factory=set)
    sent_notifications: Set[str] = field(default_factory=set)


class NotificationSystem:
    """Comprehensive notification system for league events."""
    
    def __init__(self, bot, http_client: HTTPClient):
        self.bot = bot
        self.http_client = http_client
        self.state = NotificationState()
        
        # Milestone thresholds
        self.milestone_thresholds = {
            "points": [20, 30, 40, 50, 60, 70],
            "assists": [10, 15, 20, 25],
            "rebounds": [10, 15, 20, 25, 30],
            "steals": [5, 7, 10],
            "blocks": [3, 5, 7, 10],
            "threes_made": [5, 7, 10, 15]
        }
        
        # Record thresholds (single-game records)
        self.record_thresholds = {
            "points": 50,  # Alert for 50+ points
            "assists": 20,  # Alert for 20+ assists
            "rebounds": 20,  # Alert for 20+ rebounds
            "steals": 8,   # Alert for 8+ steals
            "blocks": 5,   # Alert for 5+ blocks
            "threes_made": 10  # Alert for 10+ threes
        }
    
    async def start_monitoring(self):
        """Start the notification monitoring system."""
        logger.info("Starting notification monitoring system...")
        
        while True:
            try:
                await self._check_for_new_events()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in notification monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _check_for_new_events(self):
        """Check for new games and stat events."""
        try:
            # Get recent events
            recent_events = await self._get_recent_events()
            
            if not recent_events:
                return
            
            # Process new games
            new_games = [event for event in recent_events 
                        if event.game_id > self.state.last_game_id]
            
            if new_games:
                logger.info(f"Found {len(new_games)} new games")
                
                for game in new_games:
                    await self._process_game_events(game)
                
                # Update state
                self.state.last_game_id = max(event.game_id for event in new_games)
                self.state.last_check_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error checking for new events: {e}")
    
    async def _get_recent_events(self) -> List[GameEvent]:
        """Get recent game events from the API."""
        try:
            # Get events from the last 24 hours
            url = f"{settings.SPORTSPRESS_BASE}/events?per_page=50"
            events_data = await self.http_client.get_json(url)
            
            if not events_data:
                return []
            
            game_events = []
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for event in events_data:
                try:
                    event_date = event.get("date")
                    if not event_date:
                        continue
                    
                    # Parse date and check if recent
                    event_datetime = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                    if event_datetime < cutoff_time:
                        continue
                    
                    game_id = event.get("id")
                    if not game_id or game_id in self.state.processed_games:
                        continue
                    
                    # Get teams
                    teams = event.get("teams", [])
                    home_team = teams[0] if len(teams) > 0 else "Unknown"
                    away_team = teams[1] if len(teams) > 1 else "Unknown"
                    
                    # Get player data
                    players = await self._get_game_player_stats(event)
                    
                    game_event = GameEvent(
                        game_id=game_id,
                        date=event_date,
                        home_team=home_team,
                        away_team=away_team,
                        players=players
                    )
                    
                    game_events.append(game_event)
                    
                except Exception as e:
                    logger.warning(f"Error processing event {event.get('id', 'unknown')}: {e}")
                    continue
            
            return game_events
            
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            return []
    
    async def _get_game_player_stats(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get player statistics for a specific game."""
        try:
            players = []
            
            # Check for performance data
            performance = event.get("performance", {})
            if performance and isinstance(performance, dict):
                for player_id, player_data in performance.items():
                    if isinstance(player_data, dict):
                        players.append({
                            "player_id": int(player_id),
                            "stats": player_data
                        })
            
            # Fallback to boxscore if no performance data
            if not players:
                boxscore = event.get("boxscore", {})
                if boxscore and isinstance(boxscore, dict):
                    for player_id, player_data in boxscore.items():
                        if isinstance(player_data, dict):
                            players.append({
                                "player_id": int(player_id),
                                "stats": player_data
                            })
            
            return players
            
        except Exception as e:
            logger.error(f"Error getting game player stats: {e}")
            return []
    
    async def _process_game_events(self, game: GameEvent):
        """Process events for a specific game."""
        try:
            logger.info(f"Processing game {game.game_id}: {game.away_team} @ {game.home_team}")
            
            # Check for milestones and records
            milestones = await self._check_milestones(game)
            
            # Send notifications
            for milestone in milestones:
                await self._send_milestone_notification(milestone)
            
            # Mark game as processed
            self.state.processed_games.add(game.game_id)
            
        except Exception as e:
            logger.error(f"Error processing game {game.game_id}: {e}")
    
    async def _check_milestones(self, game: GameEvent) -> List[StatMilestone]:
        """Check for statistical milestones in a game."""
        milestones = []
        
        for player_data in game.players:
            try:
                player_id = player_data["player_id"]
                stats = player_data["stats"]
                
                # Get player and team names
                player_name = await get_player_name(self.http_client, player_id)
                team_name = await get_team_name(self.http_client, stats.get("team", 0))
                
                # Check each stat type
                for stat_type, thresholds in self.milestone_thresholds.items():
                    value = float(stats.get(stat_type, 0))
                    
                    if value > 0:
                        # Check for milestones
                        for threshold in thresholds:
                            if value >= threshold:
                                # Check if this is a record
                                is_record = value >= self.record_thresholds.get(stat_type, float('inf'))
                                
                                milestone = StatMilestone(
                                    player_name=player_name,
                                    player_id=player_id,
                                    stat_type=stat_type,
                                    value=value,
                                    game_id=game.game_id,
                                    game_date=game.date,
                                    team_name=team_name,
                                    is_record=is_record,
                                    is_season_high=False,  # Would need to check against season stats
                                    is_career_high=False   # Would need to check against career stats
                                )
                                
                                milestones.append(milestone)
                
            except Exception as e:
                logger.warning(f"Error checking milestones for player {player_data.get('player_id', 'unknown')}: {e}")
                continue
        
        return milestones
    
    async def _send_milestone_notification(self, milestone: StatMilestone):
        """Send a milestone notification to Discord."""
        try:
            # Create notification key to avoid duplicates
            notification_key = f"{milestone.player_id}_{milestone.stat_type}_{milestone.value}_{milestone.game_id}"
            
            if notification_key in self.state.sent_notifications:
                return
            
            # Get announce channel
            channel = self.bot.get_channel(settings.ANNOUNCE_CHANNEL_ID)
            if not channel:
                logger.warning("Announce channel not found")
                return
            
            # Create embed
            embed = await self._create_milestone_embed(milestone)
            
            # Send notification
            await channel.send(embed=embed)
            
            # Mark as sent
            self.state.sent_notifications.add(notification_key)
            
            logger.info(f"Sent milestone notification: {milestone.player_name} - {milestone.value} {milestone.stat_type}")
            
        except Exception as e:
            logger.error(f"Error sending milestone notification: {e}")
    
    async def _create_milestone_embed(self, milestone: StatMilestone) -> Any:
        """Create a Discord embed for a milestone notification."""
        import discord
        
        # Determine emoji and color based on stat type and value
        stat_emojis = {
            "points": "🏀",
            "assists": "✨", 
            "rebounds": "📊",
            "steals": "🔪",
            "blocks": "🛡️",
            "threes_made": "🎯"
        }
        
        emoji = stat_emojis.get(milestone.stat_type, "📈")
        
        # Determine color based on whether it's a record
        color = 0xFF0000 if milestone.is_record else 0x00FF00  # Red for records, green for milestones
        
        # Create title
        if milestone.is_record:
            title = f"🔥 RECORD ALERT! {emoji}"
        else:
            title = f"🎉 Milestone Alert! {emoji}"
        
        # Create description
        stat_display = milestone.stat_type.replace("_", " ").title()
        if milestone.stat_type == "threes_made":
            stat_display = "3-Pointers Made"
        
        description = f"**{milestone.player_name}** just dropped **{milestone.value:.0f} {stat_display}**!"
        
        if milestone.is_record:
            description += f"\n\n🔥 **NEW SINGLE-GAME RECORD!**"
        
        # Create embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=discord.utils.utcnow()
        )
        
        # Add fields
        embed.add_field(
            name="🏆 Game Details",
            value=f"**Team:** {milestone.team_name}\n**Date:** {milestone.game_date[:10]}",
            inline=True
        )
        
        # Add player profile link
        player_url = await get_player_url(self.http_client, milestone.player_id)
        if player_url:
            embed.add_field(
                name="👤 Player Profile",
                value=f"[View {milestone.player_name}'s Profile]({player_url})",
                inline=True
            )
        
        embed.set_footer(text="2KCompLeague | Live Stat Tracking")
        
        return embed
    
    async def send_weekly_summary(self):
        """Send a weekly summary of league activity."""
        try:
            # Get announce channel
            channel = self.bot.get_channel(settings.ANNOUNCE_CHANNEL_ID)
            if not channel:
                return
            
            # Create weekly summary embed
            embed = await self._create_weekly_summary_embed()
            
            # Send summary
            await channel.send(embed=embed)
            
            logger.info("Sent weekly summary")
            
        except Exception as e:
            logger.error(f"Error sending weekly summary: {e}")
    
    async def _create_weekly_summary_embed(self) -> Any:
        """Create a weekly summary embed."""
        import discord
        
        embed = discord.Embed(
            title="📊 Weekly League Summary",
            description="Here's what happened in 2KCompLeague this week!",
            color=0x0099ff,
            timestamp=discord.utils.utcnow()
        )
        
        # Add summary fields (would be populated with actual data)
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
        
        embed.set_footer(text="2KCompLeague | Powered by SportsPress")
        
        return embed


async def start_notification_system(bot, http_client: HTTPClient):
    """Start the notification system."""
    notification_system = NotificationSystem(bot, http_client)
    
    # Start monitoring in background
    asyncio.create_task(notification_system.start_monitoring())
    
    # Schedule weekly summary (every Sunday at 6 PM)
    async def weekly_summary_scheduler():
        while True:
            now = datetime.now()
            # Calculate next Sunday at 6 PM
            days_ahead = 6 - now.weekday()  # Sunday is 6
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_sunday = now + timedelta(days=days_ahead)
            next_sunday = next_sunday.replace(hour=18, minute=0, second=0, microsecond=0)
            
            # Wait until next Sunday
            wait_seconds = (next_sunday - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Send weekly summary
            await notification_system.send_weekly_summary()
    
    # Start weekly summary scheduler
    asyncio.create_task(weekly_summary_scheduler())
    
    logger.info("Notification system started")
    return notification_system
