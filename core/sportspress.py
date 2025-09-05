"""SportsPress API integration for player and event data."""

import logging
from typing import Any, Dict, List
from urllib.parse import urljoin

from .http import HTTPClient
from .types import EventPlayerRow, PlayerStats

logger = logging.getLogger(__name__)


# Mapping from canonical stat names to SportsPress API field names
STAT_MAP = {
    "points": "points",
    "assists": "assists",
    "rebounds": "rebounds",
    "steals": "steals",
    "blocks": "blocks",
    "threes_made": "threes_made",
}

# Mapping from canonical stat names to event API field names
EVENT_KEY_MAP = {
    "points": "pts",
    "rebounds": "rebtwo",
    "assists": "ast",
    "steals": "stl",
    "blocks": "blk",
    "turnovers": "to",
    "fgm": "fgm",
    "fga": "fga",
    "threes_made": "threepm",
    "threes_att": "threepa",
    "fg_percent": "fgpercent",
    "threep_percent": "threeppercent",
}


def _safe_extract_float(data: Dict[str, Any], key: str, default: float = 0.0) -> float:
    """Safely extract a float value from data."""
    try:
        value = data.get(key, default)
        if value in (None, "", "null"):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def _extract_player_name(data: Dict[str, Any]) -> str:
    """Extract player name from SportsPress data."""
    # Try different possible name fields
    name_fields = ["name", "title", "post_title", "player_name"]
    for field in name_fields:
        if field in data and data[field]:
            return str(data[field]).strip()

    # Fallback to ID if no name found
    return f"Player_{data.get('id', 'Unknown')}"


def _extract_player_id(data: Dict[str, Any]) -> int:
    """Extract player ID from SportsPress data."""
    return int(data.get("id", 0))


def _extract_player_meta(data: Dict[str, Any]) -> Dict[str, float]:
    """Extract player statistics from meta field."""
    meta = data.get("meta", {})
    stats = {}

    for canon_name, api_name in STAT_MAP.items():
        stats[canon_name] = _safe_extract_float(meta, api_name)

    return stats


async def fetch_players_for_season(
    client: HTTPClient, base_url: str, season_query: str
) -> List[PlayerStats]:
    """
    Fetch all players for a specific season.

    Args:
        client: HTTP client instance
        base_url: SportsPress API base URL
        season_query: Season query string (e.g., "?league=nba2k25s1")

    Returns:
        List of player statistics
    """
    url = urljoin(base_url, f"/players{season_query}")
    logger.info(f"Fetching players for season: {season_query}")

    players = []
    async for player_data in client.paginate(url):
        try:
            player_id = _extract_player_id(player_data)
            name = _extract_player_name(player_data)
            meta_stats = _extract_player_meta(player_data)

            player = PlayerStats(id=player_id, name=name, **meta_stats)
            players.append(player)

        except Exception as e:
            logger.warning(f"Failed to parse player data: {e}, data: {player_data}")
            continue

    logger.info(f"Fetched {len(players)} players for season {season_query}")
    return players


async def fetch_all_players_seasons(
    client: HTTPClient, base_url: str, season_queries: List[str]
) -> List[List[PlayerStats]]:
    """
    Fetch players for all seasons.

    Args:
        client: HTTP client instance
        base_url: SportsPress API base URL
        season_queries: List of season query strings

    Returns:
        List of player lists, one per season
    """
    logger.info(f"Fetching players for {len(season_queries)} seasons")

    season_players = []
    for season_query in season_queries:
        try:
            players = await fetch_players_for_season(client, base_url, season_query)
            season_players.append(players)
        except Exception as e:
            logger.error(f"Failed to fetch players for season {season_query}: {e}")
            season_players.append([])  # Empty list for failed season

    return season_players


def _extract_rows_from_event(event: Dict[str, Any]) -> List[EventPlayerRow]:
    """
    Extract player rows from event box score.

    Args:
        event: Event data from SportsPress API

    Returns:
        List of player rows with game context
    """
    rows = []

    # Extract date
    date = ""
    for date_field in ["date", "date_gmt"]:
        if event.get(date_field):
            try:
                date = str(event[date_field])[:10]  # YYYY-MM-DD
                break
            except Exception:
                pass

    # Extract game URL
    game_url = event.get("link", "")

    # Extract team names
    teams = event.get("teams", [])
    team_a = ""
    team_b = ""

    if isinstance(teams, list) and len(teams) >= 2:
        # Teams are IDs, we'll use them as team names for now
        team_a = f"Team {teams[0]}"
        team_b = f"Team {teams[1]}"
    else:
        team_a = str(event.get("team_a", "Team A"))
        team_b = str(event.get("team_b", "Team B"))

    # Try to find performance data (SportsPress format)
    performance_data = event.get("performance")
    if performance_data and isinstance(performance_data, dict):
        # Handle SportsPress performance format
        for team_id, team_performance in performance_data.items():
            if team_id == "0":  # Skip header row
                continue
                
            if isinstance(team_performance, dict):
                for player_id, player_stats in team_performance.items():
                    if player_id == "0":  # Skip header row
                        continue
                        
                    if isinstance(player_stats, dict) and any(player_stats.get(stat) for stat in ["pts", "rebtwo", "ast", "stl", "blk", "fgm", "fga", "threepm", "threepa"]):
                        # Create a row with the performance data
                        row_data = {
                            "name": f"Player {player_id}",  # Will be resolved later
                            "player_id": int(player_id),  # Store player ID for name resolution
                            "team_id": int(team_id),  # Store team ID for name resolution
                            "pts": player_stats.get("pts", "0"),
                            "rebtwo": player_stats.get("rebtwo", "0"),
                            "ast": player_stats.get("ast", "0"),
                            "stl": player_stats.get("stl", "0"),
                            "blk": player_stats.get("blk", "0"),
                            "fgm": player_stats.get("fgm", "0"),
                            "fga": player_stats.get("fga", "0"),
                            "threepm": player_stats.get("threepm", "0"),
                            "threepa": player_stats.get("threepa", "0"),
                            "fgpercent": player_stats.get("fgpercent", "0"),
                            "threeppercent": player_stats.get("threeppercent", "0"),
                        }
                        
                        # Determine team based on team_id and extract opponent team
                        if team_id == str(teams[0]):
                            side = "home"
                            opp_team_id = teams[1]
                        else:
                            side = "away" 
                            opp_team_id = teams[0]
                        
                        # Add opponent team ID to row data
                        row_data["opp_team_id"] = int(opp_team_id)
                        
                        rows.append(_create_player_row(row_data, side, team_a, team_b, date, game_url))

    # Fallback: Try to find box score data
    boxscore_candidates = [
        event.get("meta", {}).get("boxscore"),
        event.get("boxscore"),
        event.get("results", {}).get("boxscore"),
    ]

    if not rows:  # Only try boxscore if no performance data found
        for boxscore in boxscore_candidates:
            if not boxscore:
                continue

            if isinstance(boxscore, dict):
                # Handle {"home": [...], "away": [...]} format
                for side, player_rows in boxscore.items():
                    if isinstance(player_rows, list):
                        for row in player_rows:
                            if isinstance(row, dict):
                                # Try to extract player ID from row data
                                player_id = row.get("id") or row.get("player_id") or row.get("player")
                                if player_id:
                                    row["player_id"] = int(player_id) if str(player_id).isdigit() else None
                                
                                # Try to determine team ID based on side
                                if side.lower() in ["home", "a"]:
                                    row["team_id"] = teams[0] if teams else None
                                    row["opp_team_id"] = teams[1] if len(teams) > 1 else None
                                else:
                                    row["team_id"] = teams[1] if len(teams) > 1 else None
                                    row["opp_team_id"] = teams[0] if teams else None
                                
                                rows.append(
                                    _create_player_row(row, side, team_a, team_b, date, game_url)
                                )
            elif isinstance(boxscore, list):
                # Handle list format with team field
                for row in boxscore:
                    if isinstance(row, dict):
                        team = str(row.get("team", ""))
                        side = "home" if team == team_a else "away"
                        
                        # Try to extract player ID from row data
                        player_id = row.get("id") or row.get("player_id") or row.get("player")
                        if player_id:
                            row["player_id"] = int(player_id) if str(player_id).isdigit() else None
                        
                        # Try to determine team ID based on side
                        if side.lower() in ["home", "a"]:
                            row["team_id"] = teams[0] if teams else None
                            row["opp_team_id"] = teams[1] if len(teams) > 1 else None
                        else:
                            row["team_id"] = teams[1] if len(teams) > 1 else None
                            row["opp_team_id"] = teams[0] if teams else None
                        
                        rows.append(_create_player_row(row, side, team_a, team_b, date, game_url))

            break  # Use first valid boxscore

    # Return all rows - let the records computation handle filtering
    # This ensures we don't lose records that might have incomplete data
    return rows


def _create_player_row(
    row: Dict[str, Any], side: str, team_a: str, team_b: str, date: str, game_url: str = ""
) -> EventPlayerRow:
    """Create an EventPlayerRow from raw data."""
    name = str(row.get("name") or row.get("player") or row.get("title") or "Unknown")

    # Determine team and opponent
    if side.lower().startswith(("home", "a", "team_a")):
        team = team_a
        opp = team_b
    else:
        team = team_b
        opp = team_a

    game = f"{team} vs {opp}".strip() if team and opp else "Unknown vs Unknown"

    # Extract stats using event key mapping
    stats = {}
    for canon_name, event_key in EVENT_KEY_MAP.items():
        stats[canon_name] = _safe_extract_float(row, event_key)

    # Store player_id and team_id for later name resolution
    player_row = EventPlayerRow(
        name=name, 
        team=team, 
        opp=opp, 
        game=game, 
        date=date, 
        player_id=row.get("player_id"),
        team_id=row.get("team_id"),
        opp_team_id=row.get("opp_team_id"),
        **stats
    )
    
    # Add game URL for clickable links
    if game_url:
        player_row.game_url = game_url
    
    return player_row


async def fetch_events(
    client: HTTPClient, base_url: str, *, per_page: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch all events from SportsPress API.

    Args:
        client: HTTP client instance
        base_url: SportsPress API base URL
        per_page: Items per page for pagination

    Returns:
        List of event data
    """
    url = base_url + "/events"
    logger.info("Fetching events from SportsPress API")

    events = []
    async for event in client.paginate(url, per_page=per_page):
        events.append(event)

    logger.info(f"Fetched {len(events)} events")
    return events


def aggregate_player_stats(
    season_players: List[List[PlayerStats]],
) -> Dict[int, PlayerStats]:
    """
    Aggregate player stats across all seasons.

    Args:
        season_players: List of player lists, one per season

    Returns:
        Dictionary mapping player ID to aggregated stats
    """
    aggregated = {}

    for season in season_players:
        for player in season:
            if player.id in aggregated:
                # Add stats to existing player
                existing = aggregated[player.id]
                existing.points += player.points
                existing.assists += player.assists
                existing.rebounds += player.rebounds
                existing.steals += player.steals
                existing.blocks += player.blocks
                existing.threes_made += player.threes_made
                # Use most recent name
                existing.name = player.name
            else:
                # New player
                aggregated[player.id] = player

    logger.info(f"Aggregated stats for {len(aggregated)} unique players")
    return aggregated
