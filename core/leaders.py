"""Leaders calculation for season and career statistics."""

import logging
from typing import Dict, List, Tuple

from .config import settings
from .http import HTTPClient
from .sportspress import (
    aggregate_player_stats,
    fetch_all_players_seasons,
    fetch_players_for_season,
)
from .types import LeaderEntry, LeadersData, PlayerStats

logger = logging.getLogger(__name__)


async def top_n_career_leaders_alltime(client: HTTPClient, n: int = 3) -> LeadersData:
    """
    Get top N career leaders from All Time Statistics list.
    
    Args:
        client: HTTP client instance
        n: Number of leaders to return per stat
        
    Returns:
        LeadersData with career leaders from all-time statistics
    """
    try:
        logger.info(f"Calculating top {n} career leaders from All Time Statistics")
        
        # Get the All Time Statistics list (ID: 2347)
        list_url = f"{settings.SPORTSPRESS_BASE}/lists/2347"
        list_data = await client.get_json(list_url)
        
        if not list_data or "data" not in list_data:
            logger.warning("No all-time statistics data found")
            return LeadersData()
        
        data = list_data["data"]
        players = []
        
        # Process the data (dict format with player IDs as keys)
        if isinstance(data, dict):
            for player_id, player_data in data.items():
                if player_id == "0":  # Skip header
                    continue
                
                if isinstance(player_data, dict):
                    # Extract player stats
                    player_name = player_data.get("name", f"Player {player_id}")
                    points = float(player_data.get("pts", 0))
                    assists = float(player_data.get("ast", 0))
                    rebounds = float(player_data.get("rebtwo", 0))
                    steals = float(player_data.get("stl", 0))
                    blocks = float(player_data.get("blk", 0))
                    threes = float(player_data.get("threepm", 0))
                    
                    # Only include players with actual stats
                    if points > 0 or assists > 0 or rebounds > 0 or steals > 0 or blocks > 0 or threes > 0:
                        player = PlayerStats(
                            id=int(player_id),
                            name=player_name,
                            points=points,
                            assists=assists,
                            rebounds=rebounds,
                            steals=steals,
                            blocks=blocks,
                            threes_made=threes
                        )
                        players.append(player)
        
        logger.info(f"Processed {len(players)} players from all-time statistics")
        
        # Calculate leaders for each stat
        leaders_data = LeadersData()
        
        # Points leaders
        points_leaders = _stable_sort_leaders(players, "points")
        leaders_data.points = [
            LeaderEntry(name=name, value=value) 
            for name, value in points_leaders[:n]
        ]
        
        # Assists leaders
        assists_leaders = _stable_sort_leaders(players, "assists")
        leaders_data.assists = [
            LeaderEntry(name=name, value=value) 
            for name, value in assists_leaders[:n]
        ]
        
        # Rebounds leaders
        rebounds_leaders = _stable_sort_leaders(players, "rebounds")
        leaders_data.rebounds = [
            LeaderEntry(name=name, value=value) 
            for name, value in rebounds_leaders[:n]
        ]
        
        # Steals leaders
        steals_leaders = _stable_sort_leaders(players, "steals")
        leaders_data.steals = [
            LeaderEntry(name=name, value=value) 
            for name, value in steals_leaders[:n]
        ]
        
        # Blocks leaders
        blocks_leaders = _stable_sort_leaders(players, "blocks")
        leaders_data.blocks = [
            LeaderEntry(name=name, value=value) 
            for name, value in blocks_leaders[:n]
        ]
        
        # 3-Pointers Made leaders
        threes_leaders = _stable_sort_leaders(players, "threes_made")
        leaders_data.threes_made = [
            LeaderEntry(name=name, value=value) 
            for name, value in threes_leaders[:n]
        ]
        
        logger.info(f"Calculated career leaders for {len(players)} players")
        return leaders_data
        
    except Exception as e:
        logger.error(f"Failed to calculate career leaders from all-time stats: {e}")
        return LeadersData()


def _stable_sort_leaders(
    players: List[PlayerStats], stat: str
) -> List[Tuple[str, float]]:
    """
    Sort players by a specific stat with stable sorting (value desc, then name).

    Args:
        players: List of players to sort
        stat: Stat name to sort by

    Returns:
        List of (name, value) tuples sorted by value descending, then name
    """
    # Extract stat values
    stat_values = []
    for player in players:
        value = getattr(player, stat, 0.0)
        if value > 0:  # Only include players with positive values
            stat_values.append((player.name, value))

    # Sort by value descending, then by name ascending for stability
    stat_values.sort(key=lambda x: (-x[1], x[0].lower()))

    return stat_values


async def top_n_season_leaders(client: HTTPClient, n: int = 3) -> LeadersData:
    """
    Get top N season leaders for the current/active season.

    Args:
        client: HTTP client instance
        n: Number of leaders to return per stat

    Returns:
        LeadersData with top N players for each stat
    """
    logger.info(f"Calculating top {n} season leaders")

    # Use the leaders endpoint or first season endpoint
    endpoint = settings.leaders_endpoint
    if not endpoint:
        # Use the first season endpoint (NBA2K26 Season 1) as default
        season_endpoints = settings.season_endpoints.split(',')
        if season_endpoints:
            endpoint = season_endpoints[0].strip()
            logger.info(f"No leaders endpoint configured, using first season: {endpoint}")
        else:
            logger.error("No season endpoints configured")
            return LeadersData()

    try:
        players = await fetch_players_for_season(
            client, settings.SPORTSPRESS_BASE, endpoint
        )

        leaders = LeadersData()

        # Calculate leaders for each stat
        for stat in [
            "points",
            "assists",
            "rebounds",
            "steals",
            "blocks",
            "threes_made",
        ]:
            sorted_players = _stable_sort_leaders(players, stat)
            leaders.__dict__[stat] = [
                LeaderEntry(name=name, value=value)
                for name, value in sorted_players[:n]
            ]

        logger.info(f"Calculated season leaders for {len(players)} players")
        return leaders

    except Exception as e:
        logger.error(f"Failed to calculate season leaders: {e}")
        return LeadersData()


async def top_n_career_leaders(
    client: HTTPClient, season_queries: List[str], n: int = 3
) -> LeadersData:
    """
    Get top N career leaders across all seasons.

    Args:
        client: HTTP client instance
        season_queries: List of season query strings
        n: Number of leaders to return per stat

    Returns:
        LeadersData with top N players for each stat
    """
    logger.info(
        f"Calculating top {n} career leaders across {len(season_queries)} seasons"
    )

    try:
        # Fetch players for all seasons
        season_players = await fetch_all_players_seasons(
            client, settings.SPORTSPRESS_BASE, season_queries
        )

        # Aggregate stats across all seasons
        aggregated_players = aggregate_player_stats(season_players)
        players_list = list(aggregated_players.values())

        leaders = LeadersData()

        # Calculate leaders for each stat
        for stat in [
            "points",
            "assists",
            "rebounds",
            "steals",
            "blocks",
            "threes_made",
        ]:
            sorted_players = _stable_sort_leaders(players_list, stat)
            leaders.__dict__[stat] = [
                LeaderEntry(name=name, value=value)
                for name, value in sorted_players[:n]
            ]

        logger.info(f"Calculated career leaders for {len(players_list)} unique players")
        return leaders

    except Exception as e:
        logger.error(f"Failed to calculate career leaders: {e}")
        return LeadersData()


def format_leaders_embed(
    leaders: LeadersData, scope: str = "season", stat_filter: str = "all"
) -> Dict[str, any]:
    """
    Format leaders data into a Discord embed.

    Args:
        leaders: Leaders data to format
        scope: "season" or "career"
        stat_filter: Specific stat to show, or "all" for all stats

    Returns:
        Discord embed dictionary
    """
    scope_title = "Season" if scope == "season" else "Career"

    if stat_filter == "all":
        # Create embed with all stats
        embed = {
            "title": f"🏆 {scope_title} Leaders",
            "color": 0x00FF00,  # Green
            "fields": [],
        }

        stat_emojis = {
            "points": "🏀",
            "assists": "🎯",
            "rebounds": "📊",
            "steals": "🦹",
            "blocks": "🛡️",
            "threes_made": "🎯",
        }

        for stat, emoji in stat_emojis.items():
            stat_leaders = getattr(leaders, stat, [])
            if stat_leaders:
                value_lines = []
                for i, leader in enumerate(stat_leaders[:3], 1):
                    value_lines.append(f"{i}. **{leader.name}** — {leader.value:.1f}")

                embed["fields"].append(
                    {
                        "name": f"{emoji} {stat.title()}",
                        "value": "\n".join(value_lines) if value_lines else "No data",
                        "inline": True,
                    }
                )
    else:
        # Create embed for specific stat
        stat_leaders = getattr(leaders, stat_filter, [])
        stat_emoji = {
            "points": "🏀",
            "assists": "🎯",
            "rebounds": "📊",
            "steals": "🦹",
            "blocks": "🛡️",
            "threes_made": "🎯",
        }.get(stat_filter, "📈")

        embed = {
            "title": f"{stat_emoji} {scope_title} {stat_filter.title()} Leaders",
            "color": 0x00FF00,
            "fields": [],
        }

        if stat_leaders:
            value_lines = []
            for i, leader in enumerate(
                stat_leaders[:5], 1
            ):  # Show top 5 for specific stat
                value_lines.append(f"{i}. **{leader.name}** — {leader.value:.1f}")

            embed["description"] = "\n".join(value_lines)
        else:
            embed["description"] = "No data available"

    return embed


def leaders_changed(current: LeadersData, previous: LeadersData) -> Dict[str, bool]:
    """
    Check if leaders have changed for any stat.

    Args:
        current: Current leaders data
        previous: Previous leaders data

    Returns:
        Dictionary mapping stat names to whether they changed
    """
    changes = {}

    for stat in ["points", "assists", "rebounds", "steals", "blocks", "threes_made"]:
        current_leaders = getattr(current, stat, [])
        previous_leaders = getattr(previous, stat, [])

        # Compare top 3 leaders
        current_top3 = [(leader.name, leader.value) for leader in current_leaders[:3]]
        previous_top3 = [(leader.name, leader.value) for leader in previous_leaders[:3]]

        changes[stat] = current_top3 != previous_top3

    return changes
