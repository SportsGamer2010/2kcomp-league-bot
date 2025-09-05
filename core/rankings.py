"""Player ranking system for calculating league-wide rankings."""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .config import settings
from .http import HTTPClient

logger = logging.getLogger(__name__)


@dataclass
class PlayerRanking:
    """Player ranking data."""
    player_id: int
    player_name: str
    points: float = 0.0
    assists: float = 0.0
    rebounds: float = 0.0
    steals: float = 0.0
    blocks: float = 0.0
    threes_made: float = 0.0
    fgm: float = 0.0
    fga: float = 0.0
    threepm: float = 0.0
    threepa: float = 0.0
    games_played: int = 0
    ppg: float = 0.0
    apg: float = 0.0
    rpg: float = 0.0
    spg: float = 0.0
    bpg: float = 0.0
    threep_percent: float = 0.0


async def get_all_player_rankings(client: HTTPClient) -> List[PlayerRanking]:
    """
    Get rankings for all players in the league.
    
    Args:
        client: HTTP client instance
        
    Returns:
        List of player rankings sorted by various stats
    """
    try:
        logger.info("Fetching all player rankings...")
        
        # Get all players
        players = []
        page = 1
        max_pages = 20  # Reasonable limit
        
        while page <= max_pages:
            url = f"{settings.SPORTSPRESS_BASE}/players?per_page=100&page={page}"
            try:
                data = await client.get_json(url)
                if isinstance(data, list) and len(data) > 0:
                    players.extend(data)
                    logger.info(f"Fetched page {page}: {len(data)} players")
                    page += 1
                else:
                    break
            except Exception as e:
                logger.warning(f"Error fetching players page {page}: {e}")
                break
        
        logger.info(f"Total players fetched: {len(players)}")
        
        # Process each player's statistics
        player_rankings = []
        
        for player in players:
            try:
                player_id = player.get("id")
                player_name = player.get("title", {}).get("rendered", "Unknown")
                
                if not player_id:
                    continue
                
                # Get player statistics
                player_stats = await _get_player_statistics(client, player_id)
                
                if player_stats:
                    ranking = PlayerRanking(
                        player_id=player_id,
                        player_name=player_name,
                        **player_stats
                    )
                    player_rankings.append(ranking)
                    
            except Exception as e:
                logger.warning(f"Error processing player {player.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Processed {len(player_rankings)} player rankings")
        return player_rankings
        
    except Exception as e:
        logger.error(f"Error getting player rankings: {e}")
        return []


async def _get_player_statistics(client: HTTPClient, player_id: int) -> Optional[Dict]:
    """Get statistics for a specific player."""
    try:
        url = f"{settings.SPORTSPRESS_BASE}/players/{player_id}"
        player_data = await client.get_json(url)
        
        if not player_data:
            return None
        
        # Initialize stats
        stats = {
            "points": 0.0,
            "assists": 0.0,
            "rebounds": 0.0,
            "steals": 0.0,
            "blocks": 0.0,
            "threes_made": 0.0,
            "fgm": 0.0,
            "fga": 0.0,
            "threepm": 0.0,
            "threepa": 0.0,
            "games_played": 0
        }
        
        # Extract statistics from the player data
        statistics = player_data.get("statistics", [])
        if statistics:
            for stat_group in statistics:
                if isinstance(stat_group, dict):
                    for stat_name, stat_value in stat_group.items():
                        if stat_name in stats:
                            try:
                                stats[stat_name] += float(stat_value or 0)
                            except (ValueError, TypeError):
                                pass
        
        # Calculate per-game averages
        games_played = stats["games_played"]
        if games_played > 0:
            stats["ppg"] = stats["points"] / games_played
            stats["apg"] = stats["assists"] / games_played
            stats["rpg"] = stats["rebounds"] / games_played
            stats["spg"] = stats["steals"] / games_played
            stats["bpg"] = stats["blocks"] / games_played
            
            # Calculate 3P%
            if stats["threepa"] > 0:
                stats["threep_percent"] = (stats["threepm"] / stats["threepa"]) * 100
        
        return stats
        
    except Exception as e:
        logger.warning(f"Error getting statistics for player {player_id}: {e}")
        return None


def calculate_rankings(player_rankings: List[PlayerRanking]) -> Dict[int, Dict[str, int]]:
    """
    Calculate rankings for all players.
    
    Args:
        player_rankings: List of player ranking data
        
    Returns:
        Dictionary mapping player_id to their rankings for each stat
    """
    rankings = {}
    
    # Define stat fields to rank
    stat_fields = [
        "points", "assists", "rebounds", "steals", "blocks", "threes_made",
        "ppg", "apg", "rpg", "spg", "bpg", "threep_percent"
    ]
    
    for field in stat_fields:
        # Sort players by this stat (descending for most stats, ascending for some)
        reverse = field not in ["bpg"]  # Blocks per game might be better ascending
        
        sorted_players = sorted(
            player_rankings,
            key=lambda p: getattr(p, field, 0),
            reverse=reverse
        )
        
        # Assign rankings
        for rank, player in enumerate(sorted_players, 1):
            if player.player_id not in rankings:
                rankings[player.player_id] = {}
            rankings[player.player_id][field] = rank
    
    return rankings


async def get_player_rankings(client: HTTPClient, player_id: int) -> Dict[str, int]:
    """
    Get rankings for a specific player.
    
    Args:
        client: HTTP client instance
        player_id: Player ID to get rankings for
        
    Returns:
        Dictionary of stat rankings for the player
    """
    try:
        # Get all player rankings
        all_rankings = await get_all_player_rankings(client)
        
        if not all_rankings:
            return {}
        
        # Calculate rankings
        rankings_dict = calculate_rankings(all_rankings)
        
        # Return rankings for the specific player
        return rankings_dict.get(player_id, {})
        
    except Exception as e:
        logger.error(f"Error getting player rankings: {e}")
        return {}
