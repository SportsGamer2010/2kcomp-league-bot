"""Milestones commands for the Discord bot."""

import logging
from typing import List, Dict, Any, Optional

import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings
from core.http import HTTPClient, create_http_session
from core.names import get_player_name, get_player_url
from core.utils import format_number, get_league_colors, get_league_emojis, create_branded_footer, get_league_branding, get_league_logo_url

logger = logging.getLogger(__name__)


class MilestonesCog(commands.Cog):
    """Milestones commands for viewing top performers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="milestones", description="Show top 5 players in each stat category")
    async def milestones(self, interaction: discord.Interaction):
        """Show top 5 players in each stat category with clickable names."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            # Interaction already expired, can't respond
            logger.warning(f"Milestones command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring milestones command: {e}")
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
            
            # Get milestones data
            milestones_data = await self._get_milestones_data(http_client)
            
            if not milestones_data:
                await interaction.followup.send(
                    "❌ Unable to fetch milestones data. Please try again later.",
                    ephemeral=True
                )
                return
            
            # Create milestones embed
            embed = self._create_milestones_embed(milestones_data)
            
            await interaction.followup.send(embed=embed)
            
            logger.info(f"Milestones command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in milestones command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching milestones data. Please try again later.",
                    ephemeral=True
                )
            except:
                pass  # If we can't send the error message, just log it

    async def _get_milestones_data(self, client: HTTPClient) -> Dict[str, List[Dict[str, Any]]]:
        """Get top 5 players for each stat category using All Time Statistics."""
        try:
            logger.info("Fetching milestones data from All Time Statistics...")
            
            # Get all-time statistics from the dedicated list
            all_time_stats = await self._get_all_time_stats(client)
            
            if not all_time_stats:
                logger.warning("No all-time statistics found")
                return {}
            
            logger.info(f"Fetched {len(all_time_stats)} players from all-time statistics")
            
            # Calculate top 5 for each category
            milestones = self._calculate_top_5_milestones(all_time_stats)
            
            return milestones
            
        except Exception as e:
            logger.error(f"Error getting milestones data: {e}")
            return {}

    async def _get_player_statistics(self, client: HTTPClient, player_id: int) -> Dict[str, float]:
        """Get statistics for a specific player."""
        try:
            url = f"{settings.SPORTSPRESS_BASE}/players/{player_id}"
            player_data = await client.get_json(url)
            
            if not player_data:
                return {}
            
            # Initialize stats
            stats = {
                "points": 0.0,
                "assists": 0.0,
                "rebounds": 0.0,
                "steals": 0.0,
                "blocks": 0.0,
                "threes_made": 0.0,
                "games_played": 0
            }
            
            # Get statistics dict (keys are season/league IDs)
            statistics = player_data.get("statistics", {})
            if statistics and isinstance(statistics, dict):
                # Aggregate stats across all seasons/leagues
                for season_id, season_stats in statistics.items():
                    if isinstance(season_stats, dict):
                        for stat_name, stat_value in season_stats.items():
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
            
            return stats
            
        except Exception as e:
            logger.warning(f"Error getting statistics for player {player_id}: {e}")
            return {}

    def _calculate_top_5_milestones(self, player_stats: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate top 5 players for each stat category."""
        milestones = {}
        
        # Define stat categories to track
        stat_categories = [
            ("points", "Points", "pts"),
            ("assists", "Assists", "ast"),
            ("rebounds", "Rebounds", "reb"),
            ("steals", "Steals", "stl"),
            ("blocks", "Blocks", "blk"),
            ("threes_made", "3-Pointers Made", "3PM"),
            ("ppg", "Points Per Game", "PPG"),
            ("apg", "Assists Per Game", "APG"),
            ("rpg", "Rebounds Per Game", "RPG"),
            ("spg", "Steals Per Game", "SPG"),
            ("bpg", "Blocks Per Game", "BPG")
        ]
        
        for stat_key, display_name, unit in stat_categories:
            # Sort players by this stat (descending)
            sorted_players = sorted(
                player_stats,
                key=lambda p: p["stats"].get(stat_key, 0),
                reverse=True
            )
            
            # Get top 5
            top_5 = []
            for i, player in enumerate(sorted_players[:5]):
                stat_value = player["stats"].get(stat_key, 0)
                if stat_value > 0:  # Only include players with actual stats
                    top_5.append({
                        "rank": i + 1,
                        "player_id": player["player_id"],
                        "player_name": player["player_name"],
                        "value": stat_value,
                        "unit": unit
                    })
            
            milestones[stat_key] = {
                "display_name": display_name,
                "unit": unit,
                "top_5": top_5
            }
        
        return milestones

    def _create_milestones_embed(self, milestones_data: Dict[str, Any]) -> discord.Embed:
        """Create a milestones embed."""
        branding = get_league_branding()
        colors = branding["colors"]
        emojis = branding["emojis"]
        
        embed = discord.Embed(
            title=f"{emojis['shield']} 2KCompLeague Milestones",
            description="**Top 5 players in each statistical category**\n*Click player names to view their full profiles on 2kcompleague.com*",
            color=colors["primary"],  # Use primary red from logo
            url=branding["website"]
        )
        
        # Add logo as thumbnail
        embed.set_thumbnail(url=branding["logo_url"])
        embed.set_footer(text=create_branded_footer("Click names to view profiles"))
        
        # Define stat categories to display
        stat_categories = [
            ("points", "🏀 Points"),
            ("assists", "✨ Assists"),
            ("rebounds", "📊 Rebounds"),
            ("steals", "🔪 Steals"),
            ("blocks", "🛡️ Blocks"),
            ("threes_made", "🎯 3-Pointers Made"),
            ("ppg", "📈 Points Per Game"),
            ("apg", "📈 Assists Per Game"),
            ("rpg", "📈 Rebounds Per Game"),
            ("spg", "📈 Steals Per Game"),
            ("bpg", "📈 Blocks Per Game")
        ]
        
        for stat_key, emoji_name in stat_categories:
            if stat_key in milestones_data:
                stat_info = milestones_data[stat_key]
                display_name = stat_info["display_name"]
                top_5 = stat_info["top_5"]
                unit = stat_info["unit"]
                
                if top_5:
                    # Create field value with clickable player names
                    field_value = ""
                    for player in top_5:
                        rank = player["rank"]
                        player_name = player["player_name"]
                        player_id = player["player_id"]
                        value = player["value"]
                        
                        # Get player URL (we'll need to fetch this)
                        # For now, construct the URL based on player name
                        player_slug = player_name.lower().replace(" ", "-").replace("_", "-")
                        player_url = f"https://2kcompleague.com/player/{player_slug}/"
                        
                        # Create clickable link
                        clickable_name = f"[{player_name}]({player_url})"
                        
                        # Format the value with proper spacing and commas
                        if unit in ["PPG", "APG", "RPG", "SPG", "BPG"]:
                            formatted_value = f"{value:.1f} {unit}"
                        else:
                            formatted_value = format_number(int(value), unit)
                        
                        field_value += f"**{rank}.** {clickable_name} - {formatted_value}\n"
                    
                    embed.add_field(
                        name=f"{emoji_name} {display_name}",
                        value=field_value,
                        inline=False
                    )
        
        return embed

    async def _get_all_time_stats(self, client: HTTPClient) -> List[Dict[str, Any]]:
        """Get all-time statistics from the SportsPress API."""
        try:
            # Get the All Time Statistics list (ID: 2347)
            list_url = f"{settings.SPORTSPRESS_BASE}/lists/2347"
            list_data = await client.get_json(list_url)
            
            if not list_data or "data" not in list_data:
                return []
            
            data = list_data["data"]
            all_time_stats = []
            
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
                        games = int(player_data.get("g", 0))
                        
                        # Only include players with actual stats
                        if points > 0 or assists > 0 or rebounds > 0 or steals > 0 or blocks > 0 or threes > 0:
                            player_stats = {
                                "player_id": int(player_id),
                                "player_name": player_name,
                                "stats": {
                                    "points": points,
                                    "assists": assists,
                                    "rebounds": rebounds,
                                    "steals": steals,
                                    "blocks": blocks,
                                    "threes_made": threes,
                                    "games_played": games,
                                    "ppg": float(player_data.get("ppg", 0)),
                                    "apg": float(player_data.get("apg", 0)),
                                    "rpg": float(player_data.get("rpg", 0)),
                                    "spg": float(player_data.get("spg", 0)),
                                    "bpg": float(player_data.get("bpg", 0)),
                                    "threep_percent": float(player_data.get("threeppercent", 0))
                                }
                            }
                            all_time_stats.append(player_stats)
            
            logger.info(f"Processed {len(all_time_stats)} players from all-time statistics")
            return all_time_stats
            
        except Exception as e:
            logger.error(f"Error getting all-time stats: {e}")
            return []


async def setup(bot: commands.Bot):
    """Set up the milestones cog."""
    await bot.add_cog(MilestonesCog(bot))
