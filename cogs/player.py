"""Player profile commands for the Discord bot."""

import logging
from typing import Optional, List

import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings
from core.http import HTTPClient, create_http_session
from core.names import get_player_name, get_player_url
from core.rankings import get_player_rankings
from core.utils import format_number, format_rank, get_league_colors, create_branded_footer, get_league_branding, get_league_logo_url

logger = logging.getLogger(__name__)


class PlayerCog(commands.Cog):
    """Player profile commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="player", description="Show a player's stats and rankings")
    @app_commands.describe(player_name="The player's name to look up")
    async def player(self, interaction: discord.Interaction, player_name: str):
        """Show a player's comprehensive stats and rankings."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            # Interaction already expired, can't respond
            logger.warning(f"Player command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring player command: {e}")
            return
        
        try:
            # Use the bot's HTTP client
            http_client = getattr(self.bot, 'http_client', None)
            if not http_client:
                await interaction.followup.send(
                    "❌ HTTP client not available. Please try again later.",
                    ephemeral=True
                )
                return
            
            # Find player by name
            player_data = await self._find_player_by_name(http_client, player_name)
            
            if not player_data:
                await interaction.followup.send(
                    f"❌ Player '{player_name}' not found. Please check the spelling and try again.",
                    ephemeral=True
                )
                return
            
            # Get player stats and rankings
            player_stats = await self._get_player_stats(http_client, player_data['id'])
            player_rankings = await self._calculate_player_rankings(http_client, player_data['id'], player_stats)
            
            # Create player card embed
            embed = self._create_player_card(player_data, player_stats, player_rankings)
            
            await interaction.followup.send(embed=embed)
            
            logger.info(f"Player command used by {interaction.user} for player: {player_name}")
            
        except Exception as e:
            logger.error(f"Error in player command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching player data. Please try again later.",
                    ephemeral=True
                )
            except:
                pass  # If we can't send the error message, just log it


    async def _find_player_by_name(self, client: HTTPClient, player_name: str) -> Optional[dict]:
        """Find a player by name in the SportsPress API."""
        try:
            # Search for players with the given name
            url = f"{settings.SPORTSPRESS_BASE}/players?search={player_name}&per_page=50"
            players = await client.get_json(url)
            
            if not players:
                return None
            
            # Find exact match first
            for player in players:
                title = player.get("title", {}).get("rendered", "")
                if title.lower() == player_name.lower():
                    return player
            
            # Find partial match
            for player in players:
                title = player.get("title", {}).get("rendered", "")
                if player_name.lower() in title.lower():
                    return player
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding player by name: {e}")
            return None

    async def _get_player_stats(self, client: HTTPClient, player_id: int) -> dict:
        """Get player statistics from SportsPress API."""
        try:
            # Try to get stats from the all-time statistics list
            all_time_stats = await self._get_all_time_stats(client)
            
            # Find the player in all-time stats
            for player_data in all_time_stats:
                if player_data.get("player_id") == player_id:
                    return player_data.get("stats", {})
            
            # Fallback: try to get individual player data
            url = f"{settings.SPORTSPRESS_BASE}/players/{player_id}"
            player_data = await client.get_json(url)
            
            if not player_data:
                return {}
            
            # Extract statistics from the complex structure
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
                "games_played": 0,
                "ppg": 0.0,
                "apg": 0.0,
                "rpg": 0.0,
                "spg": 0.0,
                "bpg": 0.0,
                "threep_percent": 0.0
            }
            
            # Get statistics dict (keys are season/league IDs)
            statistics = player_data.get("statistics", {})
            if statistics and isinstance(statistics, dict):
                # Aggregate stats across all seasons/leagues
                for season_id, season_stats in statistics.items():
                    if isinstance(season_stats, dict):
                        for stat_name, stat_value in season_stats.items():
                            # Map SportsPress keys to our internal keys
                            if stat_name == "pts": stats["points"] += float(stat_value or 0)
                            elif stat_name == "ast": stats["assists"] += float(stat_value or 0)
                            elif stat_name == "rebtwo": stats["rebounds"] += float(stat_value or 0)
                            elif stat_name == "stl": stats["steals"] += float(stat_value or 0)
                            elif stat_name == "blk": stats["blocks"] += float(stat_value or 0)
                            elif stat_name == "threepm": stats["threes_made"] += float(stat_value or 0)
                            elif stat_name == "gp": stats["games_played"] += float(stat_value or 0)
                            elif stat_name == "fgm": stats["fgm"] += float(stat_value or 0)
                            elif stat_name == "fga": stats["fga"] += float(stat_value or 0)
                            elif stat_name == "threepa": stats["threepa"] += float(stat_value or 0)
            
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
                stats["threep_percent"] = (stats["threes_made"] / stats["threepa"]) * 100
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting player stats: {e}")
            return {}

    async def _get_all_time_stats(self, client: HTTPClient) -> List[dict]:
        """Get all-time statistics from the SportsPress API."""
        try:
            # Get the All Time Statistics list (ID: 2347)
            list_url = f"{settings.SPORTSPRESS_BASE}/lists/2347"
            list_data = await client.get_json(list_url)
            
            if not list_data or "data" not in list_data:
                logger.warning("All-time statistics list not found")
                return []
            
            # We already have the list data from the previous call
            
            data = list_data["data"]
            all_time_stats = []
            
            # Process the data based on its structure
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
            
            logger.info(f"Fetched {len(all_time_stats)} players from all-time statistics")
            return all_time_stats
            
        except Exception as e:
            logger.error(f"Error getting all-time stats: {e}")
            return []

    async def _calculate_player_rankings(self, client: HTTPClient, player_id: int, player_stats: dict) -> dict:
        """Calculate accurate rankings for a player based on all-time statistics."""
        try:
            # Get all-time stats to calculate rankings
            all_time_stats = await self._get_all_time_stats(client)
            if not all_time_stats:
                logger.warning("No all-time stats available for ranking calculation")
                return {}
            
            # Extract all players' stats for ranking
            all_players = []
            for player_data in all_time_stats:
                if isinstance(player_data, dict) and player_data.get("player_id"):
                    all_players.append(player_data)
            
            if not all_players:
                logger.warning("No players found in all-time stats for ranking")
                return {}
            
            # Calculate rankings for each stat category
            rankings = {}
            
            # Define stat fields to rank
            stat_fields = [
                ("points", "points"),
                ("assists", "assists"), 
                ("rebounds", "rebounds"),
                ("steals", "steals"),
                ("blocks", "blocks"),
                ("threes_made", "threes_made"),
                ("ppg", "ppg"),
                ("apg", "apg"),
                ("rpg", "rpg"),
                ("spg", "spg"),
                ("bpg", "bpg"),
                ("threep_percent", "threep_percent")
            ]
            
            for rank_key, stat_key in stat_fields:
                # Sort all players by this stat (descending for most stats)
                reverse = rank_key not in ["bpg"]  # Blocks per game might be better ascending
                
                sorted_players = sorted(
                    all_players,
                    key=lambda p: p.get("stats", {}).get(stat_key, 0),
                    reverse=reverse
                )
                
                # Find the rank of our target player
                target_rank = None
                for rank, player in enumerate(sorted_players, 1):
                    if player.get("player_id") == player_id:
                        target_rank = rank
                        break
                
                rankings[rank_key] = target_rank or 0
            
            logger.info(f"Calculated rankings for player {player_id}: {rankings}")
            return rankings
            
        except Exception as e:
            logger.error(f"Error calculating player rankings: {e}")
            return {}

    def _create_player_card(self, player_data: dict, stats: dict, rankings: dict) -> discord.Embed:
        """Create a player card embed."""
        player_name = player_data.get("title", {}).get("rendered", "Unknown Player")
        player_url = player_data.get("link", "")
        
        # Create embed
        branding = get_league_branding()
        colors = branding["colors"]
        emojis = branding["emojis"]
        
        embed = discord.Embed(
            title=f"{emojis['basketball']} {player_name}",
            description=f"**2KCompLeague Player Profile**\n*Click the title to view the full profile on 2kcompleague.com*",
            color=colors["primary"],  # Use primary red from logo
            url=player_url
        )
        
        # Add logo as thumbnail
        embed.set_thumbnail(url=branding["logo_url"])
        
        # Add stats fields
        games_played = stats.get("games_played", 0)
        
        # Total stats
        embed.add_field(
            name="🏀 Points",
            value=f"{format_number(int(stats.get('points', 0)), 'pts')} (Rank: {format_rank(rankings.get('points', 0))})",
            inline=True
        )
        
        embed.add_field(
            name="✨ Assists",
            value=f"{format_number(int(stats.get('assists', 0)), 'ast')} (Rank: {format_rank(rankings.get('assists', 0))})",
            inline=True
        )
        
        embed.add_field(
            name="📊 Rebounds",
            value=f"{format_number(int(stats.get('rebounds', 0)), 'reb')} (Rank: {format_rank(rankings.get('rebounds', 0))})",
            inline=True
        )
        
        embed.add_field(
            name="🔪 Steals",
            value=f"{format_number(int(stats.get('steals', 0)), 'stl')} (Rank: {format_rank(rankings.get('steals', 0))})",
            inline=True
        )
        
        embed.add_field(
            name="🛡️ Blocks",
            value=f"{format_number(int(stats.get('blocks', 0)), 'blk')} (Rank: {format_rank(rankings.get('blocks', 0))})",
            inline=True
        )
        
        embed.add_field(
            name="🎯 3PM",
            value=f"{format_number(int(stats.get('threes_made', 0)), '3PM')} (Rank: {format_rank(rankings.get('threes_made', 0))})",
            inline=True
        )
        
        # Per-game averages
        if games_played > 0:
            ppg = stats.get('points', 0) / games_played
            apg = stats.get('assists', 0) / games_played
            rpg = stats.get('rebounds', 0) / games_played
            spg = stats.get('steals', 0) / games_played
            bpg = stats.get('blocks', 0) / games_played
            
            embed.add_field(
                name="PPG (Rank)",
                value=f"{ppg:.1f} (Rank: {format_rank(rankings.get('ppg', 0))})",
                inline=True
            )
            
            embed.add_field(
                name="APG (Rank)",
                value=f"{apg:.1f} (Rank: {format_rank(rankings.get('apg', 0))})",
                inline=True
            )
            
            embed.add_field(
                name="RPG (Rank)",
                value=f"{rpg:.1f} (Rank: {format_rank(rankings.get('rpg', 0))})",
                inline=True
            )
            
            embed.add_field(
                name="SPG (Rank)",
                value=f"{spg:.1f} (Rank: {format_rank(rankings.get('spg', 0))})",
                inline=True
            )
            
            embed.add_field(
                name="BPG (Rank)",
                value=f"{bpg:.1f} (Rank: {format_rank(rankings.get('bpg', 0))})",
                inline=True
            )
            
            # 3P%
            threepa = stats.get('threepa', 0)
            if threepa > 0:
                threep_percent = (stats.get('threepm', 0) / threepa) * 100
                embed.add_field(
                    name="3P% (Rank)",
                    value=f"{threep_percent:.1f}% (Rank: {format_rank(rankings.get('threep_percent', 0))})",
                    inline=True
                )
        
        # Games played
        embed.add_field(
            name="Games Played",
            value=format_number(int(games_played), "games"),
            inline=False
        )
        
        # Footer
        embed.set_footer(text=create_branded_footer("View full profile for complete stats"))
        
        return embed


async def setup(bot: commands.Bot):
    """Set up the player cog."""
    await bot.add_cog(PlayerCog(bot))
