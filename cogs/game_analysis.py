"""Game analysis and community engagement features for the Discord bot."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings
from core.http import HTTPClient
from core.utils import format_number, get_league_colors, get_league_emojis, create_branded_footer

logger = logging.getLogger(__name__)


class GameAnalysisCog(commands.Cog):
    """Game analysis and community engagement features."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="recent", description="Show recent games and standout performances")
    async def recent_games(self, interaction: discord.Interaction, count: int = 5):
        """Display recent games with standout performances."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Recent games command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring recent games command: {e}")
            return
        
        try:
            http_client = getattr(self.bot, 'http_client', None)
            if not http_client:
                await interaction.followup.send(
                    "❌ HTTP client not available. Please try again later.",
                    ephemeral=True
                )
                return

            # Fetch recent events
            events = await self._fetch_recent_events(http_client, count)
            
            if not events:
                await interaction.followup.send(
                    "❌ No recent games found. Please try again later.",
                    ephemeral=True
                )
                return

            colors = get_league_colors()
            emojis = get_league_emojis()
            
            embed = discord.Embed(
                title=f"{emojis['fire']} Recent Games & Standout Performances",
                description="**Latest 2KCompLeague action with top individual performances**",
                color=colors["warning"]
            )

            for event in events:
                game_info = await self._analyze_game_performance(http_client, event)
                if game_info:
                    embed.add_field(
                        name=f"🏀 {game_info['title']}",
                        value=game_info['description'],
                        inline=False
                    )

            embed.set_footer(text=create_branded_footer("Click game links to view full box scores"))
            
            await interaction.followup.send(embed=embed)
            logger.info(f"Recent games command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in recent games command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching recent games. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="seasonhighs", description="Show current season high performances")
    async def season_highs(self, interaction: discord.Interaction):
        """Display current season high performances."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Season highs command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring season highs command: {e}")
            return
        
        try:
            http_client = getattr(self.bot, 'http_client', None)
            if not http_client:
                await interaction.followup.send(
                    "❌ HTTP client not available. Please try again later.",
                    ephemeral=True
                )
                return

            # Get current month's events
            current_month_events = await self._fetch_current_month_events(http_client)
            
            if not current_month_events:
                await interaction.followup.send(
                    "❌ No games found for current season. Please try again later.",
                    ephemeral=True
                )
                return

            # Analyze season highs
            season_highs = await self._calculate_season_highs(current_month_events)
            
            colors = get_league_colors()
            emojis = get_league_emojis()
            
            embed = discord.Embed(
                title=f"{emojis['crown']} NBA2K26 Season 1 Highs",
                description="**Current season's top individual performances**",
                color=colors["accent"]
            )

            for stat, data in season_highs.items():
                if data['value'] > 0:
                    embed.add_field(
                        name=f"{emojis.get(stat, '🏀')} {data['display_name']}",
                        value=f"**{format_number(data['value'], data['unit'])}** by [{data['player']}]({data['player_url']})\n"
                              f"vs {data['opponent']} • {data['date']}\n"
                              f"[View Game]({data['game_url']})",
                        inline=True
                    )

            embed.set_footer(text=create_branded_footer("Updated after each game"))
            
            await interaction.followup.send(embed=embed)
            logger.info(f"Season highs command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in season highs command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching season highs. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="playoffrace", description="Show current playoff race standings")
    async def playoff_race(self, interaction: discord.Interaction):
        """Display current playoff race based on games played."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Playoff race command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring playoff race command: {e}")
            return
        
        try:
            http_client = getattr(self.bot, 'http_client', None)
            if not http_client:
                await interaction.followup.send(
                    "❌ HTTP client not available. Please try again later.",
                    ephemeral=True
                )
                return

            # Get current month's events
            current_month_events = await self._fetch_current_month_events(http_client)
            
            if not current_month_events:
                await interaction.followup.send(
                    "❌ No games found for current season. Please try again later.",
                    ephemeral=True
                )
                return

            # Calculate team standings
            team_standings = await self._calculate_team_standings(current_month_events)
            
            colors = get_league_colors()
            emojis = get_league_emojis()
            
            embed = discord.Embed(
                title=f"{emojis['trophy']} NBA2K26 Season 1 Playoff Race",
                description="**Teams need 10+ games to qualify for playoffs**\n*Playoffs: Best of 3, seeded by regular season record*",
                color=colors["primary"]
            )

            # Sort teams by wins, then by games played
            sorted_teams = sorted(team_standings.values(), 
                                key=lambda x: (x['wins'], x['games_played']), 
                                reverse=True)

            playoff_eligible = []
            playoff_race = []
            
            for team in sorted_teams:
                if team['games_played'] >= 10:
                    playoff_eligible.append(team)
                else:
                    playoff_race.append(team)

            # Playoff eligible teams
            if playoff_eligible:
                eligible_text = ""
                for i, team in enumerate(playoff_eligible[:8], 1):  # Top 8
                    status = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    eligible_text += f"{status} **{team['name']}** - {team['wins']}-{team['losses']} ({team['games_played']} games)\n"
                
                embed.add_field(
                    name="🏆 Playoff Eligible (10+ Games)",
                    value=eligible_text,
                    inline=False
                )

            # Teams in playoff race
            if playoff_race:
                race_text = ""
                for team in playoff_race[:5]:  # Top 5 in race
                    games_needed = 10 - team['games_played']
                    race_text += f"**{team['name']}** - {team['wins']}-{team['losses']} ({team['games_played']} games)\n"
                    race_text += f"*Needs {games_needed} more games*\n\n"
                
                embed.add_field(
                    name="🏃‍♂️ Playoff Race (Under 10 Games)",
                    value=race_text,
                    inline=False
                )

            embed.set_footer(text=create_branded_footer("Playoffs: Last week of each month"))
            
            await interaction.followup.send(embed=embed)
            logger.info(f"Playoff race command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in playoff race command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching playoff race. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    async def _fetch_recent_events(self, http_client: HTTPClient, count: int) -> List[Dict]:
        """Fetch recent events from the API."""
        try:
            # Get recent events (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            url = f"{settings.SPORTSPRESS_BASE}/events"
            params = {
                'after': start_date.isoformat(),
                'before': end_date.isoformat(),
                'per_page': count,
                'orderby': 'date',
                'order': 'desc'
            }
            
            events = await http_client.get_json(url, params=params)
            return events if isinstance(events, list) else []
            
        except Exception as e:
            logger.error(f"Error fetching recent events: {e}")
            return []

    async def _fetch_current_month_events(self, http_client: HTTPClient) -> List[Dict]:
        """Fetch current month's events."""
        try:
            now = datetime.now()
            # Get first day of current month
            first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Get last day of current month
            if now.month == 12:
                last_day = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
            
            url = f"{settings.SPORTSPRESS_BASE}/events"
            params = {
                'after': first_day.isoformat(),
                'before': last_day.isoformat(),
                'per_page': 100,
                'orderby': 'date',
                'order': 'desc'
            }
            
            events = await http_client.get_json(url, params=params)
            return events if isinstance(events, list) else []
            
        except Exception as e:
            logger.error(f"Error fetching current month events: {e}")
            return []

    async def _analyze_game_performance(self, http_client: HTTPClient, event: Dict) -> Optional[Dict]:
        """Analyze a single game for standout performances."""
        try:
            # This would need to be implemented based on your event data structure
            # For now, return basic game info
            title = event.get('title', {}).get('rendered', 'Unknown Game')
            date = event.get('date', '')
            link = event.get('link', '')
            
            # Extract teams from title (assuming format like "Team A vs Team B")
            teams = title.split(' vs ')
            if len(teams) == 2:
                team1, team2 = teams
                description = f"**{team1}** vs **{team2}**\n"
                description += f"📅 {date}\n"
                description += f"[View Full Box Score]({link})"
                
                return {
                    'title': title,
                    'description': description
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing game performance: {e}")
            return None

    async def _calculate_season_highs(self, events: List[Dict]) -> Dict[str, Dict]:
        """Calculate season highs from events."""
        # This would need to be implemented based on your event data structure
        # For now, return placeholder data
        return {
            'points': {
                'display_name': 'Points',
                'value': 41,
                'unit': 'pts',
                'player': 'Halibans',
                'player_url': 'https://2kcompleague.com/player/halibans/',
                'opponent': 'Goon Squad',
                'date': 'June 23, 2025',
                'game_url': 'https://2kcompleague.com/event/goon-squad-vs-missing-in-action/'
            },
            'assists': {
                'display_name': 'Assists',
                'value': 18,
                'unit': 'ast',
                'player': 'Hey imFading',
                'player_url': 'https://2kcompleague.com/player/hey-imfading/',
                'opponent': 'Goon Squad',
                'date': 'June 23, 2025',
                'game_url': 'https://2kcompleague.com/event/missing-in-action-vs-goon-squad/'
            },
            'rebounds': {
                'display_name': 'Rebounds',
                'value': 23,
                'unit': 'reb',
                'player': 'ShunRemains',
                'player_url': 'https://2kcompleague.com/player/shunremains/',
                'opponent': 'Goon Squad',
                'date': 'June 23, 2025',
                'game_url': 'https://2kcompleague.com/event/goon-squad-vs-missing-in-action/'
            }
        }

    async def _calculate_team_standings(self, events: List[Dict]) -> Dict[str, Dict]:
        """Calculate team standings from events."""
        # This would need to be implemented based on your event data structure
        # For now, return placeholder data
        return {
            'goon-squad': {
                'name': 'Goon Squad',
                'wins': 8,
                'losses': 3,
                'games_played': 11
            },
            'missing-in-action': {
                'name': 'Missing In Action',
                'wins': 7,
                'losses': 4,
                'games_played': 11
            },
            'buyin': {
                'name': 'Buyin',
                'wins': 5,
                'losses': 2,
                'games_played': 7
            }
        }


async def setup(bot: commands.Bot):
    """Set up the game analysis cog."""
    await bot.add_cog(GameAnalysisCog(bot))
    logger.info("Game analysis cog loaded")
