"""Spotlight player notification system."""

import logging
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from core.config import settings
from core.http import HTTPClient
from core.names import get_player_name, get_player_url
from core.utils import get_league_branding, format_number, create_branded_footer

logger = logging.getLogger(__name__)


class SpotlightSystem:
    """System for generating spotlight player notifications."""
    
    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client
        self.branding = get_league_branding()
        
    async def get_spotlight_player(self) -> Optional[Dict]:
        """Get a random spotlight player with their highlight information."""
        try:
            # Get all-time stats for career leaders
            all_time_stats = await self._get_all_time_stats()
            if not all_time_stats:
                logger.warning("No all-time stats available for spotlight")
                return None
                
            # Get single-game records for record holders
            records = await self._get_single_game_records()
            
            # Get recent games for current season highlights
            recent_games = await self._get_recent_games()
            
            # Choose spotlight type
            spotlight_types = [
                "career_leader",
                "blocks_leader",
                "record_holder", 
                "season_standout",
                "veteran_player",
                "championship_winner"
            ]
            
            spotlight_type = random.choice(spotlight_types)
            logger.info(f"Selected spotlight type: {spotlight_type}")
            
            if spotlight_type == "career_leader":
                return await self._get_career_leader_spotlight(all_time_stats)
            elif spotlight_type == "blocks_leader":
                return await self._get_blocks_leader_spotlight(all_time_stats)
            elif spotlight_type == "record_holder":
                return await self._get_record_holder_spotlight(records)
            elif spotlight_type == "season_standout":
                return await self._get_season_standout_spotlight(recent_games)
            elif spotlight_type == "veteran_player":
                return await self._get_veteran_spotlight(all_time_stats)
            elif spotlight_type == "championship_winner":
                return await self._get_championship_winner_spotlight()
                
        except Exception as e:
            logger.error(f"Error getting spotlight player: {e}")
            return None
            
    async def _get_all_time_stats(self) -> Optional[List]:
        """Get all-time statistics from the comprehensive list."""
        try:
            # Use the known all-time statistics list ID
            url = f"{settings.SPORTSPRESS_BASE}/lists/2347"
            response = await self.http_client.get_json(url)
            
            if not response or "data" not in response:
                logger.warning("All-time statistics list not found")
                return None
            
            data = response["data"]
            all_time_stats = []
            
            # Process the data based on its structure (same as player command)
            if isinstance(data, list):
                # List format - each item is a player
                for player in data:
                    if isinstance(player, dict):
                        # Skip header rows
                        if (player.get("name") in ["Player", "Name"] or 
                            player.get("pts") in ["PTS", "Points"] or
                            player.get("number") == "Number"):
                            continue
                        
                        # Extract player stats
                        player_stats = {
                            "player_id": player.get("id"),
                            "player_name": player.get("name", "Unknown"),
                            "stats": {
                                "points": float(player.get("pts", 0)),
                                "assists": float(player.get("ast", 0)),
                                "rebounds": float(player.get("rebtwo", 0)),
                                "steals": float(player.get("stl", 0)),
                                "blocks": float(player.get("blk", 0)),
                                "threes_made": float(player.get("threepm", 0)),
                                "fgm": float(player.get("fgm", 0)),
                                "fga": float(player.get("fga", 0)),
                                "threepm": float(player.get("threepm", 0)),
                                "threepa": float(player.get("threepa", 0)),
                                "games_played": int(player.get("g", 0)),
                                "ppg": float(player.get("ppg", 0)),
                                "apg": float(player.get("apg", 0)),
                                "rpg": float(player.get("rpg", 0)),
                                "spg": float(player.get("spg", 0)),
                                "bpg": float(player.get("bpg", 0)),
                                "threep_percent": float(player.get("threeppercent", 0))
                            }
                        }
                        all_time_stats.append(player_stats)
            
            elif isinstance(data, dict):
                # Dict format - player IDs as keys
                for player_id, player_data in data.items():
                    if player_id == "0":  # Skip header
                        continue
                    
                    if isinstance(player_data, dict):
                        # Extract player stats
                        player_stats = {
                            "player_id": int(player_id),
                            "player_name": str(player_data.get("name", f"Player {player_id}")),
                            "stats": {
                                "points": float(player_data.get("pts", 0)),
                                "assists": float(player_data.get("ast", 0)),
                                "rebounds": float(player_data.get("rebtwo", 0)),
                                "steals": float(player_data.get("stl", 0)),
                                "blocks": float(player_data.get("blk", 0)),
                                "threes_made": float(player_data.get("threepm", 0)),
                                "fgm": float(player_data.get("fgm", 0)),
                                "fga": float(player_data.get("fga", 0)),
                                "threepm": float(player_data.get("threepm", 0)),
                                "threepa": float(player_data.get("threepa", 0)),
                                "games_played": int(player_data.get("g", 0)),
                                "ppg": float(player_data.get("ppg", 0)),
                                "apg": float(player_data.get("apg", 0)),
                                "rpg": float(player_data.get("rpg", 0)),
                                "spg": float(player_data.get("spg", 0)),
                                "bpg": float(player_data.get("bpg", 0)),
                                "threep_percent": float(player_data.get("threeppercent", 0))
                            }
                        }
                        all_time_stats.append(player_stats)
            
            logger.info(f"Fetched {len(all_time_stats)} players from all-time statistics for spotlight")
            return all_time_stats
            
        except Exception as e:
            logger.error(f"Error fetching all-time stats: {e}")
            return None
            
    async def _get_single_game_records(self) -> Optional[Dict]:
        """Get single-game records."""
        try:
            from core.records import compute_single_game_records
            records_data = await compute_single_game_records(self.http_client)
            # Convert RecordsData to dict format for spotlight system
            return {
                "points": records_data.points,
                "rebounds": records_data.rebounds,
                "assists": records_data.assists,
                "steals": records_data.steals,
                "blocks": records_data.blocks,
                "threes_made": records_data.threes_made,
                "double_doubles": records_data.double_doubles,
                "triple_doubles": records_data.triple_doubles
            }
        except Exception as e:
            logger.error(f"Error fetching records: {e}")
            return None
            
    async def _get_recent_games(self) -> Optional[List]:
        """Get recent games for season highlights."""
        try:
            url = f"{settings.SPORTSPRESS_BASE}/wp-json/sportspress/v2/events"
            params = {"per_page": 20, "orderby": "date", "order": "desc"}
            response = await self.http_client.get_json(url, params=params)
            
            if response:
                return response
            return None
            
        except Exception as e:
            logger.error(f"Error fetching recent games: {e}")
            return None
            
    async def _get_career_leader_spotlight(self, all_time_stats: List) -> Optional[Dict]:
        """Get a career leader spotlight."""
        try:
            if not all_time_stats:
                return None
                
            # Find top players in various categories
            career_leaders = []
            
            for player_data in all_time_stats:
                if not isinstance(player_data, dict):
                    continue
                    
                stats = player_data.get("stats", {})
                if not stats:
                    continue
                    
                # Calculate total points
                points = stats.get("points", 0)
                assists = stats.get("assists", 0)
                rebounds = stats.get("rebounds", 0)
                blocks = stats.get("blocks", 0)
                games = stats.get("games_played", 0)
                
                if games > 0:  # Only consider players with games played
                    career_leaders.append({
                        "player_id": player_data.get("player_id"),
                        "player_name": player_data.get("player_name", "Unknown"),
                        "points": points,
                        "assists": assists,
                        "rebounds": rebounds,
                        "blocks": blocks,
                        "games": games,
                        "ppg": points / games if games > 0 else 0
                    })
                    
            if not career_leaders:
                return None
                
            # Sort by total points and pick a top player
            career_leaders.sort(key=lambda x: x["points"], reverse=True)
            spotlight_player = career_leaders[0]
            
            # Get player name and URL
            player_name = spotlight_player["player_name"]
            player_url = await get_player_url(self.http_client, spotlight_player["player_id"])
            
            return {
                "type": "career_leader",
                "title": "🏆 Career Leader Spotlight",
                "player_name": player_name or f"Player {spotlight_player['player_id']}",
                "player_url": player_url or f"{self.branding['website']}/player/{spotlight_player['player_id']}",
                "highlight": f"**{format_number(spotlight_player['points'], 'career points')}** in {spotlight_player['games']} games",
                "description": f"Leading scorer with {format_number(spotlight_player['ppg'], 'PPG')} and {format_number(spotlight_player['assists'], 'career assists')}",
                "color": self.branding["colors"]["accent"]  # Gold for career leaders
            }
            
        except Exception as e:
            logger.error(f"Error creating career leader spotlight: {e}")
            return None

    async def _get_blocks_leader_spotlight(self, all_time_stats: List) -> Optional[Dict]:
        """Get a blocks leader spotlight."""
        try:
            if not all_time_stats:
                return None
                
            # Find top blocks leaders
            blocks_leaders = []
            
            for player_data in all_time_stats:
                if not isinstance(player_data, dict):
                    continue
                    
                stats = player_data.get("stats", {})
                if not stats:
                    continue
                    
                blocks = stats.get("blocks", 0)
                games = stats.get("games_played", 0)
                
                if blocks > 0 and games > 0:  # Only consider players with blocks
                    blocks_leaders.append({
                        "player_id": player_data.get("player_id"),
                        "player_name": player_data.get("player_name", "Unknown"),
                        "blocks": blocks,
                        "games": games,
                        "bpg": blocks / games if games > 0 else 0
                    })
                    
            if not blocks_leaders:
                return None
                
            # Sort by total blocks
            blocks_leaders.sort(key=lambda x: x["blocks"], reverse=True)
            blocks_leader = blocks_leaders[0]
            
            # Get player name and URL
            player_name = blocks_leader["player_name"]
            player_url = await get_player_url(self.http_client, blocks_leader["player_id"])
            
            return {
                "type": "blocks_leader",
                "title": "🛡️ Blocks Leader Spotlight",
                "player_name": player_name or f"Player {blocks_leader['player_id']}",
                "player_url": player_url or f"{self.branding['website']}/player/{blocks_leader['player_id']}",
                "highlight": f"**{format_number(blocks_leader['blocks'], 'blocks')}** in {blocks_leader['games']} games",
                "description": f"Leading shot blocker with {format_number(blocks_leader['bpg'], 'BPG')}",
                "color": self.branding["colors"]["primary"]  # Red for blocks leaders
            }
            
        except Exception as e:
            logger.error(f"Error creating blocks leader spotlight: {e}")
            return None
            
    async def _get_record_holder_spotlight(self, records: Dict) -> Optional[Dict]:
        """Get a record holder spotlight."""
        try:
            if not records or "records" not in records:
                return None
                
            record_list = records["records"]
            if not record_list:
                return None
                
            # Pick a random record
            record = random.choice(record_list)
            
            # Extract player info
            player_name = record.get("player_name", "Unknown Player")
            player_url = record.get("player_url", "")
            stat_value = record.get("value", 0)
            stat_name = record.get("stat_name", "Unknown Stat")
            game_url = record.get("game_url", "")
            
            return {
                "type": "record_holder",
                "title": "⚡ Record Holder Spotlight",
                "player_name": player_name,
                "player_url": player_url,
                "highlight": f"**{format_number(stat_value, stat_name)}** - Single-game record!",
                "description": f"All-time {stat_name} record holder",
                "game_url": game_url,
                "color": self.branding["colors"]["primary"]  # Red for record holders
            }
            
        except Exception as e:
            logger.error(f"Error creating record holder spotlight: {e}")
            return None
            
    async def _get_season_standout_spotlight(self, recent_games: List) -> Optional[Dict]:
        """Get a season standout spotlight."""
        try:
            if not recent_games:
                return None
                
            # Find a recent high-scoring performance
            standout_performance = None
            max_points = 0
            
            for game in recent_games[:10]:  # Check last 10 games
                if not isinstance(game, dict):
                    continue
                    
                # Look for high-scoring performances
                # This would need to be adapted based on your game data structure
                # For now, we'll create a placeholder
                pass
                
            # If no standout found, create a general season highlight
            return {
                "type": "season_standout",
                "title": "🔥 Season Standout",
                "player_name": "League Star",
                "player_url": self.branding["website"],
                "highlight": "**Outstanding Performance** this season!",
                "description": "Making waves in NBA2K26 Season 1",
                "color": self.branding["colors"]["secondary"]  # Blue for season highlights
            }
            
        except Exception as e:
            logger.error(f"Error creating season standout spotlight: {e}")
            return None
            
    async def _get_veteran_spotlight(self, all_time_stats: List) -> Optional[Dict]:
        """Get a veteran player spotlight."""
        try:
            if not all_time_stats:
                return None
                
            # Find players with most games played
            veterans = []
            
            for player_data in all_time_stats:
                if not isinstance(player_data, dict):
                    continue
                    
                stats = player_data.get("stats", {})
                if not stats:
                    continue
                    
                games = stats.get("games_played", 0)
                if games >= 5:  # Consider veterans with 5+ games (lowered threshold)
                    veterans.append({
                        "player_id": player_data.get("player_id"),
                        "player_name": player_data.get("player_name", "Unknown"),
                        "games": games,
                        "stats": stats
                    })
                    
            if not veterans:
                return None
                
            # Sort by games played
            veterans.sort(key=lambda x: x["games"], reverse=True)
            veteran = veterans[0]
            
            # Get player name and URL
            player_name = veteran["player_name"]
            player_url = await get_player_url(self.http_client, veteran["player_id"])
            
            return {
                "type": "veteran",
                "title": "👑 Veteran Spotlight",
                "player_name": player_name or f"Player {veteran['player_id']}",
                "player_url": player_url or f"{self.branding['website']}/player/{veteran['player_id']}",
                "highlight": f"**{veteran['games']} games played** - League veteran!",
                "description": f"Experienced player with {format_number(veteran['stats'].get('points', 0), 'career points')}",
                "color": self.branding["colors"]["shield"]  # Dark red for veterans
            }
            
        except Exception as e:
            logger.error(f"Error creating veteran spotlight: {e}")
            return None
            
    async def _get_championship_winner_spotlight(self) -> Optional[Dict]:
        """Get a championship winner spotlight."""
        try:
            # This would integrate with your championship history
            # For now, create a placeholder
            return {
                "type": "champion",
                "title": "🏆 Champion Spotlight",
                "player_name": "Champion Player",
                "player_url": self.branding["website"],
                "highlight": "**Championship Winner** - Elite status!",
                "description": "Proven winner in 2KCompLeague",
                "color": self.branding["colors"]["accent"]  # Gold for champions
            }
            
        except Exception as e:
            logger.error(f"Error creating championship winner spotlight: {e}")
            return None


def create_spotlight_embed(spotlight_data: Dict) -> str:
    """Create a formatted spotlight message."""
    if not spotlight_data:
        return "🌟 **2KCompLeague Spotlight**\n*No spotlight available at this time.*"
        
    title = spotlight_data["title"]
    player_name = spotlight_data["player_name"]
    player_url = spotlight_data["player_url"]
    highlight = spotlight_data["highlight"]
    description = spotlight_data["description"]
    
    # Create clickable player link
    if player_url and player_url != "Unknown":
        player_link = f"[{player_name}]({player_url})"
    else:
        player_link = player_name
        
    message = f"🌟 **{title}**\n\n"
    message += f"**{player_link}**\n"
    message += f"{highlight}\n"
    message += f"*{description}*\n\n"
    message += f"🛡️ *2KCompLeague | Powered by 2kcompleague.com*"
    
    return message
