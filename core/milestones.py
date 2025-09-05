"""Milestone detection and notification system."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .config import settings
from .http import HTTPClient
from .sportspress import (
    fetch_players_for_season,
)
from .types import MilestoneNotification

logger = logging.getLogger(__name__)


# Milestone thresholds for each stat
MILESTONES = {
    "points": [100, 250, 500, 750, 1000, 1500, 2000],
    "assists": [50, 100, 250, 500, 750, 1000],
    "rebounds": [50, 100, 250, 500, 750, 1000],
    "steals": [25, 50, 100, 200, 300],
    "blocks": [25, 50, 100, 200, 300],
    "threes_made": [25, 50, 100, 200, 300],
}


@dataclass
class PlayerTotals:
    """Current season totals for a player."""

    player_id: int
    name: str
    points: float = 0.0
    assists: float = 0.0
    rebounds: float = 0.0
    steals: float = 0.0
    blocks: float = 0.0
    threes_made: float = 0.0


def _get_crossed_thresholds(
    previous_total: float, current_total: float, thresholds: List[int]
) -> List[int]:
    """
    Find thresholds that were crossed between previous and current totals.

    Args:
        previous_total: Previous stat total
        current_total: Current stat total
        thresholds: List of milestone thresholds

    Returns:
        List of thresholds that were crossed
    """
    crossed = []

    for threshold in thresholds:
        if previous_total < threshold <= current_total:
            crossed.append(threshold)

    return crossed


def _format_milestone_message(
    player_name: str, stat: str, threshold: int, current_total: float
) -> str:
    """
    Format a milestone notification message.

    Args:
        player_name: Name of the player
        stat: Statistic name
        threshold: Threshold that was crossed
        current_total: Current total for the stat

    Returns:
        Formatted milestone message
    """
    stat_emojis = {
        "points": "🏀",
        "assists": "🎯",
        "rebounds": "📊",
        "steals": "🦹",
        "blocks": "🛡️",
        "threes_made": "🎯",
    }

    emoji = stat_emojis.get(stat, "🏆")
    stat_display = stat.replace("_", " ").title()

    return f"{emoji} **Milestone Unlocked**: {player_name} reached {threshold:,} {stat_display} (Total: {current_total:.1f})"


async def get_current_season_totals(client: HTTPClient) -> Dict[int, PlayerTotals]:
    """
    Get current season totals for all players.

    Args:
        client: HTTP client instance

    Returns:
        Dictionary mapping player ID to current totals
    """
    logger.info("Fetching current season totals for milestone detection")

    # Use the leaders endpoint or first season endpoint
    endpoint = settings.leaders_endpoint
    if not endpoint:
        logger.error("No leaders endpoint configured for milestone detection")
        return {}

    try:
        players = await fetch_players_for_season(
            client, settings.SPORTSPRESS_BASE, endpoint
        )

        totals = {}
        for player in players:
            totals[player.id] = PlayerTotals(
                player_id=player.id,
                name=player.name,
                points=player.points,
                assists=player.assists,
                rebounds=player.rebounds,
                steals=player.steals,
                blocks=player.blocks,
                threes_made=player.threes_made,
            )

        logger.info(f"Fetched season totals for {len(totals)} players")
        return totals

    except Exception as e:
        logger.error(f"Failed to fetch season totals: {e}")
        return {}


def detect_milestone_crossings(
    current_totals: Dict[int, PlayerTotals],
    last_totals: Dict[str, Dict[str, float]],
    milestones_sent: Dict[str, Dict[str, List[int]]],
) -> List[MilestoneNotification]:
    """
    Detect milestone crossings and generate notifications.

    Args:
        current_totals: Current season totals for all players
        last_totals: Previous totals from state
        milestones_sent: Previously sent milestones from state

    Returns:
        List of milestone notifications
    """
    notifications = []

    for player_id, player_totals in current_totals.items():
        player_id_str = str(player_id)

        # Get previous totals for this player
        previous_totals = last_totals.get(player_id_str, {})

        # Get previously sent milestones for this player
        player_milestones_sent = milestones_sent.get(player_id_str, {})

        # Check each stat for milestone crossings
        for stat in MILESTONES.keys():
            current_value = getattr(player_totals, stat, 0.0)
            previous_value = previous_totals.get(stat, 0.0)

            # Find thresholds that were crossed
            crossed_thresholds = _get_crossed_thresholds(
                previous_value, current_value, MILESTONES[stat]
            )

            # Filter out thresholds that were already announced
            sent_thresholds = set(player_milestones_sent.get(stat, []))
            new_thresholds = [t for t in crossed_thresholds if t not in sent_thresholds]

            # Generate notifications for new crossings
            for threshold in new_thresholds:
                message = _format_milestone_message(
                    player_totals.name, stat, threshold, current_value
                )

                notification = MilestoneNotification(
                    player=player_totals.name,
                    stat=stat,
                    value=current_value,
                    threshold=threshold,
                    message=message,
                )

                notifications.append(notification)

    logger.info(f"Detected {len(notifications)} new milestone crossings")
    return notifications


def update_milestone_state(
    current_totals: Dict[int, PlayerTotals],
    notifications: List[MilestoneNotification],
    last_totals: Dict[str, Dict[str, float]],
    milestones_sent: Dict[str, Dict[str, List[int]]],
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, List[int]]]]:
    """
    Update the milestone state with new totals and sent milestones.

    Args:
        current_totals: Current season totals
        notifications: Milestone notifications that were sent
        last_totals: Previous totals state
        milestones_sent: Previous sent milestones state

    Returns:
        Updated (last_totals, milestones_sent) tuple
    """
    # Update last totals
    updated_last_totals = last_totals.copy()
    for player_id, player_totals in current_totals.items():
        player_id_str = str(player_id)
        updated_last_totals[player_id_str] = {
            "points": player_totals.points,
            "assists": player_totals.assists,
            "rebounds": player_totals.rebounds,
            "steals": player_totals.steals,
            "blocks": player_totals.blocks,
            "threes_made": player_totals.threes_made,
        }

    # Update sent milestones
    updated_milestones_sent = milestones_sent.copy()
    for notification in notifications:
        player_id_str = str(notification.player)  # Using name as ID for now
        if player_id_str not in updated_milestones_sent:
            updated_milestones_sent[player_id_str] = {}

        if notification.stat not in updated_milestones_sent[player_id_str]:
            updated_milestones_sent[player_id_str][notification.stat] = []

        updated_milestones_sent[player_id_str][notification.stat].append(
            notification.threshold
        )

    return updated_last_totals, updated_milestones_sent


def format_milestone_embed(
    notifications: List[MilestoneNotification],
) -> Dict[str, any]:
    """
    Format milestone notifications into a Discord embed.

    Args:
        notifications: List of milestone notifications

    Returns:
        Discord embed dictionary
    """
    if not notifications:
        return None

    embed = {
        "title": "🏆 Milestone Achievements",
        "color": 0xFFD700,  # Gold
        "description": "Players have reached new statistical milestones!",
        "fields": [],
    }

    # Group notifications by stat
    by_stat = {}
    for notification in notifications:
        if notification.stat not in by_stat:
            by_stat[notification.stat] = []
        by_stat[notification.stat].append(notification)

    # Create fields for each stat
    stat_emojis = {
        "points": "🏀",
        "assists": "🎯",
        "rebounds": "📊",
        "steals": "🦹",
        "blocks": "🛡️",
        "threes_made": "🎯",
    }

    for stat, stat_notifications in by_stat.items():
        emoji = stat_emojis.get(stat, "🏆")
        stat_display = stat.replace("_", " ").title()

        # Create value lines for this stat
        value_lines = []
        for notification in stat_notifications:
            value_lines.append(
                f"• **{notification.player}** - {notification.threshold:,} {stat_display}"
            )

        embed["fields"].append(
            {
                "name": f"{emoji} {stat_display}",
                "value": "\n".join(value_lines),
                "inline": True,
            }
        )

    return embed


async def scan_and_detect_crossings(
    client: HTTPClient,
    last_totals: Dict[str, Dict[str, float]],
    milestones_sent: Dict[str, Dict[str, List[int]]],
) -> Tuple[
    List[MilestoneNotification],
    Dict[str, Dict[str, float]],
    Dict[str, Dict[str, List[int]]],
]:
    """
    Scan current season totals and detect milestone crossings.

    Args:
        client: HTTP client instance
        last_totals: Previous totals from state
        milestones_sent: Previously sent milestones from state

    Returns:
        Tuple of (notifications, updated_last_totals, updated_milestones_sent)
    """
    logger.info("Scanning for milestone crossings")

    try:
        # Get current season totals
        current_totals = await get_current_season_totals(client)

        if not current_totals:
            logger.warning("No current totals found for milestone detection")
            return [], last_totals, milestones_sent

        # Detect crossings
        notifications = detect_milestone_crossings(
            current_totals, last_totals, milestones_sent
        )

        # Update state
        updated_last_totals, updated_milestones_sent = update_milestone_state(
            current_totals, notifications, last_totals, milestones_sent
        )

        logger.info(
            f"Milestone scan completed: {len(notifications)} new crossings detected"
        )
        return notifications, updated_last_totals, updated_milestones_sent

    except Exception as e:
        logger.error(f"Failed to scan for milestone crossings: {e}")
        return [], last_totals, milestones_sent
