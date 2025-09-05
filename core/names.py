"""Name resolution for players and teams from SportsPress API."""

import logging
from typing import Dict, Optional

from .config import settings
from .http import HTTPClient

logger = logging.getLogger(__name__)

# Cache for player and team names
_player_names: Dict[int, str] = {}
_team_names: Dict[int, str] = {}
_player_urls: Dict[int, str] = {}
_team_urls: Dict[int, str] = {}


async def get_player_name(client: HTTPClient, player_id: int) -> str:
    """
    Get player name by ID, with caching.
    
    Args:
        client: HTTP client instance
        player_id: Player ID
        
    Returns:
        Player name or "Player {id}" if not found
    """
    if player_id is None:
        return "Player None"
    
    if player_id in _player_names:
        return _player_names[player_id]
    
    try:
        player_data = await client.get_json(f"{settings.SPORTSPRESS_BASE}/players/{player_id}")
        name = player_data.get("title", {}).get("rendered", f"Player {player_id}")
        _player_names[player_id] = name
        return name
    except Exception as e:
        logger.warning(f"Failed to fetch player name for ID {player_id}: {e}")
        name = f"Player {player_id}"
        _player_names[player_id] = name
        return name


async def get_team_name(client: HTTPClient, team_id: int) -> str:
    """
    Get team name by ID, with caching.
    
    Args:
        client: HTTP client instance
        team_id: Team ID
        
    Returns:
        Team name or "Team {id}" if not found
    """
    if team_id is None:
        return "Team None"
    
    if team_id in _team_names:
        return _team_names[team_id]
    
    try:
        team_data = await client.get_json(f"{settings.SPORTSPRESS_BASE}/teams/{team_id}")
        name = team_data.get("title", {}).get("rendered", f"Team {team_id}")
        _team_names[team_id] = name
        return name
    except Exception as e:
        # Cache the failure to avoid repeated API calls for missing teams
        name = f"Team {team_id}"
        _team_names[team_id] = name
        # Only log warning for first attempt to avoid spam
        if "Failed to fetch team name" not in str(e):
            logger.warning(f"Failed to fetch team name for ID {team_id}: {e}")
        return name


async def get_player_url(client: HTTPClient, player_id: int) -> str:
    """
    Get player profile URL by ID, with caching.
    
    Args:
        client: HTTP client instance
        player_id: Player ID
        
    Returns:
        Player profile URL
    """
    if player_id is None:
        return ""
    
    # Check cache first
    if player_id in _player_urls:
        return _player_urls[player_id]
    
    try:
        # Fetch player data from SportsPress API
        url = f"{settings.SPORTSPRESS_BASE}/players/{player_id}"
        data = await client.get_json(url)
        
        if data and isinstance(data, dict):
            player_url = data.get("link", "")
            if player_url:
                _player_urls[player_id] = player_url
                return player_url
        
        # Fallback: construct URL from player name if we have it
        if player_id in _player_names:
            player_name = _player_names[player_id]
            # Convert name to slug format
            slug = player_name.lower().replace(" ", "-").replace("_", "-")
            fallback_url = f"https://2kcompleague.com/player/{slug}/"
            _player_urls[player_id] = fallback_url
            return fallback_url
        
        # Final fallback: use ID-based URL
        fallback_url = f"https://2kcompleague.com/player/{player_id}/"
        _player_urls[player_id] = fallback_url
        return fallback_url
        
    except Exception as e:
        logger.warning(f"Failed to fetch player URL for ID {player_id}: {e}")
        # Fallback: use ID-based URL
        fallback_url = f"https://2kcompleague.com/player/{player_id}/"
        _player_urls[player_id] = fallback_url
        return fallback_url


async def get_team_url(client: HTTPClient, team_id: int) -> str:
    """
    Get team profile URL by ID, with caching.
    
    Args:
        client: HTTP client instance
        team_id: Team ID
        
    Returns:
        Team profile URL
    """
    if team_id is None:
        return ""
    
    # Check cache first
    if team_id in _team_urls:
        return _team_urls[team_id]
    
    try:
        # Fetch team data from SportsPress API
        url = f"{settings.SPORTSPRESS_BASE}/teams/{team_id}"
        data = await client.get_json(url)
        
        if data and isinstance(data, dict):
            team_url = data.get("link", "")
            if team_url:
                _team_urls[team_id] = team_url
                return team_url
        
        # Fallback: construct URL from team name if we have it
        if team_id in _team_names:
            team_name = _team_names[team_id]
            # Convert name to slug format
            slug = team_name.lower().replace(" ", "-").replace("_", "-")
            fallback_url = f"https://2kcompleague.com/team/{slug}/"
            _team_urls[team_id] = fallback_url
            return fallback_url
        
        # Final fallback: use ID-based URL
        fallback_url = f"https://2kcompleague.com/team/{team_id}/"
        _team_urls[team_id] = fallback_url
        return fallback_url
        
    except Exception as e:
        logger.warning(f"Failed to fetch team URL for ID {team_id}: {e}")
        # Fallback: use ID-based URL
        fallback_url = f"https://2kcompleague.com/team/{team_id}/"
        _team_urls[team_id] = fallback_url
        return fallback_url


def clear_name_cache():
    """Clear the name caches."""
    global _player_names, _team_names, _player_urls, _team_urls
    _player_names.clear()
    _team_names.clear()
    _player_urls.clear()
    _team_urls.clear()
