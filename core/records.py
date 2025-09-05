"""Single-game records computation from SportsPress events."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .config import settings
from .http import HTTPClient
from .sportspress import _extract_rows_from_event, fetch_events
from .types import RecordsData, SingleGameRecord, DoubleDouble, TripleDouble
from .names import get_player_name, get_team_name, get_player_url
from .utils import format_number, get_league_colors, create_branded_footer

logger = logging.getLogger(__name__)


@dataclass
class RecordCandidate:
    """Candidate for a single-game record."""

    stat: str
    value: float
    holder: str
    game: str
    date: str
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    opp_team_id: Optional[int] = None
    game_url: Optional[str] = None
    player_url: Optional[str] = None


def _try_update_max(
    current: Optional[SingleGameRecord], candidate: RecordCandidate
) -> Optional[SingleGameRecord]:
    """
    Try to update a record with a new candidate.

    Args:
        current: Current record (can be None)
        candidate: New candidate record

    Returns:
        Updated record if candidate is better, otherwise current
    """
    if current is None or candidate.value > current.value:
        record = SingleGameRecord(
            stat=candidate.stat,
            value=candidate.value,
            holder=candidate.holder,
            game=candidate.game,
            date=candidate.date,
        )
        # Add team information for name resolution
        if candidate.player_id:
            record.player_id = candidate.player_id
        if candidate.team_id:
            record.team_id = candidate.team_id
        if candidate.opp_team_id:
            record.opp_team_id = candidate.opp_team_id
        if candidate.game_url:
            record.game_url = candidate.game_url
        if candidate.player_url:
            record.player_url = candidate.player_url
        return record
    return current


def _check_double_triple_doubles(
    records: RecordsData, 
    row: Any, 
    player_id: Optional[int], 
    team_id: Optional[int], 
    opp_team_id: Optional[int], 
    game_url: Optional[str]
) -> None:
    """
    Check if a player achieved a double-double or triple-double in a game.
    
    Args:
        records: Records data to update
        row: Player row data from event
        player_id: Player ID
        team_id: Team ID
        opp_team_id: Opponent team ID
        game_url: Game URL
    """
    # Define the stats to check for double-doubles/triple-doubles
    stats_to_check = {
        "points": row.points,
        "rebounds": row.rebounds,
        "assists": row.assists,
        "steals": row.steals,
        "blocks": row.blocks
    }
    
    # Find categories where player achieved 10+
    double_digit_categories = []
    values = {}
    
    for stat, value in stats_to_check.items():
        if value >= 10:
            double_digit_categories.append(stat)
            values[stat] = value
    
    # Check for triple-double (3+ categories with 10+)
    if len(double_digit_categories) >= 3:
        triple_double = TripleDouble(
            player=row.name,
            game=row.game,
            date=row.date,
            categories=double_digit_categories,
            values=values,
            player_id=player_id,
            team_id=team_id,
            opp_team_id=opp_team_id,
            game_url=game_url
        )
        records.triple_doubles.append(triple_double)
        logger.debug(f"Triple-double detected: {row.name} - {double_digit_categories}")
    
    # Check for double-double (2+ categories with 10+)
    elif len(double_digit_categories) >= 2:
        double_double = DoubleDouble(
            player=row.name,
            game=row.game,
            date=row.date,
            categories=double_digit_categories,
            values=values,
            player_id=player_id,
            team_id=team_id,
            opp_team_id=opp_team_id,
            game_url=game_url
        )
        records.double_doubles.append(double_double)
        logger.debug(f"Double-double detected: {row.name} - {double_digit_categories}")


async def compute_single_game_records(client: HTTPClient) -> RecordsData:
    """
    Compute single-game records by scanning all events.

    Args:
        client: HTTP client instance

    Returns:
        RecordsData with all single-game records
    """
    logger.info("Computing single-game records from events")

    records = RecordsData()

    try:
        # Search ALL historical events for records
        # This ensures we find all-time records, not just recent ones
        events = []
        try:
            # Use direct API calls to fetch all events (more reliable than pagination)
            import aiohttp
            base_url = settings.SPORTSPRESS_BASE
            page = 1
            max_pages = 50  # Reasonable limit
            
            while page <= max_pages:
                url = f"{base_url}/events?per_page=100&page={page}"
                try:
                    async with client.session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, list) and len(data) > 0:
                                # Process all events that have any performance or boxscore data
                                for event in data:
                                    if event.get("performance") or event.get("boxscore"):
                                        events.append(event)
                                logger.info(f"Page {page}: {len(data)} events, {len([e for e in data if e.get('performance') or e.get('boxscore')])} with data")
                                page += 1
                            else:
                                logger.info(f"Page {page}: No more events")
                                break
                        elif response.status == 400:
                            logger.info(f"Page {page}: HTTP 400 - no more pages")
                            break
                        else:
                            logger.warning(f"Page {page}: HTTP {response.status}")
                            break
                except Exception as e:
                    logger.warning(f"Page {page}: Error - {e}")
                    break
            
            logger.info(f"Fetched {len(events)} total historical events for record search")
        except Exception as e:
            logger.warning(f"Failed to fetch all events, trying fallback: {e}")
            # Fallback: try to get events with smaller page size
            try:
                events = await fetch_events(client, settings.SPORTSPRESS_BASE, per_page=50)
                logger.info(f"Fetched {len(events)} events via fallback")
            except Exception as fallback_error:
                logger.error(f"All event fetching methods failed: {fallback_error}")
                return RecordsData()

        for event in events:
            try:
                # Extract player rows from this event
                player_rows = _extract_rows_from_event(event)

                for row in player_rows:
                    # Get common data for all records
                    player_id = getattr(row, 'player_id', None)
                    team_id = getattr(row, 'team_id', None)
                    opp_team_id = getattr(row, 'opp_team_id', None)
                    game_url = getattr(row, 'game_url', None)
                    
                    # Skip records without proper player/team IDs (from fallback data)
                    # But allow some records through for stats that might not have complete data
                    if not player_id or not team_id or not opp_team_id:
                        # For now, let's allow records through but mark them as incomplete
                        # This ensures we show all record types even if some have missing data
                        pass
                    
                    # Check hard max records (no minimum requirements)
                    records.points = _try_update_max(
                        records.points,
                        RecordCandidate(
                            stat="points",
                            value=row.points,
                            holder=row.name,
                            game=row.game,
                            date=row.date,
                            player_id=player_id,
                            team_id=team_id,
                            opp_team_id=opp_team_id,
                            game_url=game_url,
                        ),
                    )

                    records.rebounds = _try_update_max(
                        records.rebounds,
                        RecordCandidate(
                            stat="rebounds",
                            value=row.rebounds,
                            holder=row.name,
                            game=row.game,
                            date=row.date,
                            player_id=player_id,
                            team_id=team_id,
                            opp_team_id=opp_team_id,
                            game_url=game_url,
                        ),
                    )

                    records.assists = _try_update_max(
                        records.assists,
                        RecordCandidate(
                            stat="assists",
                            value=row.assists,
                            holder=row.name,
                            game=row.game,
                            date=row.date,
                            player_id=player_id,
                            team_id=team_id,
                            opp_team_id=opp_team_id,
                            game_url=game_url,
                        ),
                    )

                    records.steals = _try_update_max(
                        records.steals,
                        RecordCandidate(
                            stat="steals",
                            value=row.steals,
                            holder=row.name,
                            game=row.game,
                            date=row.date,
                            player_id=player_id,
                            team_id=team_id,
                            opp_team_id=opp_team_id,
                            game_url=game_url,
                        ),
                    )

                    records.blocks = _try_update_max(
                        records.blocks,
                        RecordCandidate(
                            stat="blocks",
                            value=row.blocks,
                            holder=row.name,
                            game=row.game,
                            date=row.date,
                            player_id=player_id,
                            team_id=team_id,
                            opp_team_id=opp_team_id,
                            game_url=game_url,
                        ),
                    )

                    records.threes_made = _try_update_max(
                        records.threes_made,
                        RecordCandidate(
                            stat="threes_made",
                            value=row.threes_made,
                            holder=row.name,
                            game=row.game,
                            date=row.date,
                            player_id=player_id,
                            team_id=team_id,
                            opp_team_id=opp_team_id,
                            game_url=game_url,
                        ),
                    )

                    # Check percentage records with minimum attempt requirements
                    if row.fga >= settings.MIN_FGA_FOR_FG_PERCENT:
                        records.fg_percent = _try_update_max(
                            records.fg_percent,
                            RecordCandidate(
                                stat="fg_percent",
                                value=row.fg_percent,
                                holder=row.name,
                                game=row.game,
                                date=row.date,
                                player_id=player_id,
                                team_id=team_id,
                                opp_team_id=opp_team_id,
                                game_url=game_url,
                            ),
                        )

                    if row.threepa >= settings.MIN_3PA_FOR_3P_PERCENT:
                        records.threep_percent = _try_update_max(
                            records.threep_percent,
                            RecordCandidate(
                                stat="threep_percent",
                                value=row.threep_percent,
                                holder=row.name,
                                game=row.game,
                                date=row.date,
                                player_id=player_id,
                                team_id=team_id,
                                opp_team_id=opp_team_id,
                                game_url=game_url,
                            ),
                        )

                    # Check for double-doubles and triple-doubles
                    _check_double_triple_doubles(records, row, player_id, team_id, opp_team_id, game_url)

            except Exception as e:
                logger.warning(f"Failed to process event: {e}")
                continue

        logger.info("Single-game records computation completed")
        return records

    except Exception as e:
        logger.error(f"Failed to compute single-game records: {e}")
        return RecordsData()


async def resolve_record_names(client: HTTPClient, records: RecordsData) -> RecordsData:
    """
    Resolve player and team names in records.
    
    Args:
        client: HTTP client instance
        records: Records data with player/team IDs
        
    Returns:
        Records data with resolved names
    """
    # List of record attributes to resolve
    record_attrs = ['points', 'rebounds', 'assists', 'steals', 'blocks', 'threes_made', 'threep_percent']
    
    for attr in record_attrs:
        record = getattr(records, attr, None)
        if record and hasattr(record, 'player_id'):
            # Only resolve names if we have proper IDs
            if record.player_id is not None:
                # Resolve player name
                player_name = await get_player_name(client, record.player_id)
                record.holder = player_name
                
                # Resolve player URL
                player_url = await get_player_url(client, record.player_id)
                record.player_url = player_url
                
                # Resolve team names in game string
                if hasattr(record, 'team_id') and hasattr(record, 'opp_team_id') and record.team_id is not None and record.opp_team_id is not None:
                    team_name = await get_team_name(client, record.team_id)
                    opp_team_name = await get_team_name(client, record.opp_team_id)
                    record.game = f"{team_name} vs {opp_team_name}"
            else:
                # Try to extract ID from player name if it's in format "Player 4222"
                if record.holder and record.holder.startswith("Player "):
                    try:
                        player_id = int(record.holder.split(" ")[1])
                        player_name = await get_player_name(client, player_id)
                        record.holder = player_name
                        
                        # Also resolve player URL
                        player_url = await get_player_url(client, player_id)
                        record.player_url = player_url
                    except (ValueError, IndexError):
                        pass  # Keep original name if extraction fails
                
                # Try to extract team IDs from game string if it's in format "Team 4217 vs Team 4306"
                if record.game and "Team " in record.game:
                    try:
                        parts = record.game.split(" vs ")
                        if len(parts) == 2:
                            team1_id = int(parts[0].split(" ")[1])
                            team2_id = int(parts[1].split(" ")[1])
                            team1_name = await get_team_name(client, team1_id)
                            team2_name = await get_team_name(client, team2_id)
                            record.game = f"{team1_name} vs {team2_name}"
                    except (ValueError, IndexError):
                        pass  # Keep original game string if extraction fails
    
    # Resolve names for double-doubles and triple-doubles
    for dd in records.double_doubles:
        if dd.player_id is not None:
            player_name = await get_player_name(client, dd.player_id)
            dd.player = player_name
            
            player_url = await get_player_url(client, dd.player_id)
            dd.player_url = player_url
            
            if dd.team_id is not None and dd.opp_team_id is not None:
                team_name = await get_team_name(client, dd.team_id)
                opp_team_name = await get_team_name(client, dd.opp_team_id)
                dd.game = f"{team_name} vs {opp_team_name}"
        else:
            # Try to extract ID from player name if it's in format "Player 4222"
            if dd.player and dd.player.startswith("Player "):
                try:
                    player_id = int(dd.player.split(" ")[1])
                    player_name = await get_player_name(client, player_id)
                    dd.player = player_name
                    
                    player_url = await get_player_url(client, player_id)
                    dd.player_url = player_url
                except (ValueError, IndexError):
                    pass
    
    for td in records.triple_doubles:
        if td.player_id is not None:
            player_name = await get_player_name(client, td.player_id)
            td.player = player_name
            
            player_url = await get_player_url(client, td.player_id)
            td.player_url = player_url
            
            if td.team_id is not None and td.opp_team_id is not None:
                team_name = await get_team_name(client, td.team_id)
                opp_team_name = await get_team_name(client, td.opp_team_id)
                td.game = f"{team_name} vs {opp_team_name}"
        else:
            # Try to extract ID from player name if it's in format "Player 4222"
            if td.player and td.player.startswith("Player "):
                try:
                    player_id = int(td.player.split(" ")[1])
                    player_name = await get_player_name(client, player_id)
                    td.player = player_name
                    
                    player_url = await get_player_url(client, player_id)
                    td.player_url = player_url
                except (ValueError, IndexError):
                    pass
    
    return records


def format_records_embed(records: RecordsData) -> Dict[str, Any]:
    """
    Format records data into a Discord embed.

    Args:
        records: Records data to format

    Returns:
        Discord embed dictionary
    """
    colors = get_league_colors()
    embed = {
        "title": "🏆 2KCompLeague Single-Game Records",
        "color": colors["accent"],  # Gold
        "description": "**All-time single-game records in 2KCompLeague**\n*Click game links to view full match details on 2kcompleague.com*",
        "fields": [],
    }

    stat_configs = [
        ("points", "🏀 Points", "pts"),
        ("rebounds", "📊 Rebounds", "reb"),
        ("assists", "🎯 Assists", "ast"),
        ("steals", "🦹 Steals", "stl"),
        ("blocks", "🛡️ Blocks", "blk"),
        ("threes_made", "🎯 3-Pointers Made", "3PM"),
        ("threep_percent", "🎯 3P%", "%"),
    ]

    for stat, display_name, unit in stat_configs:
        record = getattr(records, stat, None)
        if record:
            # Show all records with game links
            if record.holder and not record.holder.startswith("Player ") and not record.holder.startswith("Player None"):
                # Complete record with real names
                # Make player name clickable if we have a player URL
                if hasattr(record, 'player_url') and record.player_url:
                    player_display = f"[**{record.holder}**]({record.player_url})"
                else:
                    player_display = f"**{record.holder}**"
                
                value = f"**{format_number(record.value, unit)}** by {player_display}\n"
                value += f"Game: {record.game}\n"
                value += f"Date: {record.date}\n"
            else:
                # Incomplete record - show but mark as incomplete
                value = f"**{format_number(record.value, unit)}** by {record.holder}\n"
                value += f"Game: {record.game}\n"
                value += f"Date: {record.date}\n"
                value += "⚠️ *Data incomplete*\n"
            
            # Add game link for ALL records if available
            if hasattr(record, 'game_url') and record.game_url:
                value += f"[View Game]({record.game_url})"
            
            embed["fields"].append(
                {
                    "name": display_name,
                    "value": value,
                    "inline": True,
                }
            )

    # Add double-doubles section
    if records.double_doubles:
        # Sort by date (most recent first) and limit to top 5 to keep field length manageable
        sorted_dds = sorted(records.double_doubles, key=lambda x: x.date, reverse=True)[:5]
        
        dd_value = ""
        for dd in sorted_dds:
            # Make player name clickable if we have a player URL
            if hasattr(dd, 'player_url') and dd.player_url:
                player_display = f"[**{dd.player}**]({dd.player_url})"
            else:
                player_display = f"**{dd.player}**"
            
            # Format the categories and values (shortened)
            category_display = []
            for cat in dd.categories:
                if cat in dd.values:
                    category_display.append(f"{cat.title()}: {int(dd.values[cat])}")
            
            dd_value += f"{player_display} - {', '.join(category_display)}\n"
            dd_value += f"{dd.date}"
            if hasattr(dd, 'game_url') and dd.game_url:
                dd_value += f" • [View Game]({dd.game_url})"
            dd_value += "\n\n"
            
            # Check if we're approaching the 1024 character limit
            if len(dd_value) > 800:  # Leave some buffer
                break
        
        embed["fields"].append(
            {
                "name": "🔥 Double-Doubles (Recent)",
                "value": dd_value.strip(),
                "inline": False,
            }
        )

    # Add triple-doubles section
    if records.triple_doubles:
        # Sort by date (most recent first) and limit to top 5 to keep field length manageable
        sorted_tds = sorted(records.triple_doubles, key=lambda x: x.date, reverse=True)[:5]
        
        td_value = ""
        for td in sorted_tds:
            # Make player name clickable if we have a player URL
            if hasattr(td, 'player_url') and td.player_url:
                player_display = f"[**{td.player}**]({td.player_url})"
            else:
                player_display = f"**{td.player}**"
            
            # Format the categories and values (shortened)
            category_display = []
            for cat in td.categories:
                if cat in td.values:
                    category_display.append(f"{cat.title()}: {int(td.values[cat])}")
            
            td_value += f"{player_display} - {', '.join(category_display)}\n"
            td_value += f"{td.date}"
            if hasattr(td, 'game_url') and td.game_url:
                td_value += f" • [View Game]({td.game_url})"
            td_value += "\n\n"
            
            # Check if we're approaching the 1024 character limit
            if len(td_value) > 800:  # Leave some buffer
                break
        
        embed["fields"].append(
            {
                "name": "👑 Triple-Doubles (Recent)",
                "value": td_value.strip(),
                "inline": False,
            }
        )

    return embed


def records_changed(
    current: RecordsData, previous: RecordsData
) -> List[SingleGameRecord]:
    """
    Check if any records have been broken.

    Args:
        current: Current records
        previous: Previous records

    Returns:
        List of newly broken records
    """
    new_records = []

    for stat in [
        "points",
        "rebounds",
        "assists",
        "steals",
        "blocks",
        "threes_made",
        "fg_percent",
        "threep_percent",
    ]:
        current_record = getattr(current, stat, None)
        previous_record = getattr(previous, stat, None)

        if current_record and (
            not previous_record or current_record.value > previous_record.value
        ):
            new_records.append(current_record)

    return new_records


def load_records_seed() -> RecordsData:
    """
    Load initial records from seed file.

    Returns:
        RecordsData with seed records
    """
    import json
    from pathlib import Path

    seed_path = Path(settings.RECORDS_SEED_PATH)
    if not seed_path.exists():
        logger.warning(f"Records seed file not found: {seed_path}")
        return RecordsData()

    try:
        with open(seed_path) as f:
            seed_data = json.load(f)

        records = RecordsData()

        for stat, record_data in seed_data.items():
            if hasattr(records, stat):
                setattr(
                    records,
                    stat,
                    SingleGameRecord(
                        stat=stat,
                        value=record_data["value"],
                        holder=record_data["holder"],
                        game=record_data["game"],
                        date=record_data["date"],
                    ),
                )

        logger.info(f"Loaded {len(seed_data)} records from seed file")
        return records

    except Exception as e:
        logger.error(f"Failed to load records seed: {e}")
        return RecordsData()
