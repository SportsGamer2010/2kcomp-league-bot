"""League information and branding commands for the Discord bot."""

import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings
from core.utils import get_league_colors, get_league_emojis, create_branded_footer, get_league_branding, get_league_logo_url

logger = logging.getLogger(__name__)


class LeagueCog(commands.Cog):
    """League information and branding commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="league", description="Get information about 2KCompLeague")
    async def league(self, interaction: discord.Interaction):
        """Display comprehensive league information."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"League command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring league command: {e}")
            return
        
        try:
            branding = get_league_branding()
            colors = branding["colors"]
            emojis = branding["emojis"]
            
            embed = discord.Embed(
                title=f"{emojis['shield']} 2KCompLeague Official",
                description=f"**{branding['description']}**\n*{branding['tagline']}*",
                color=colors["primary"],
                url=branding["website"]
            )
            
            # Add logo as thumbnail
            embed.set_thumbnail(url=branding["logo_url"])
            
            # League Overview
            embed.add_field(
                name="🏆 League Overview",
                value=(
                    "**2KCompLeague** is the premier destination for NBA 2K competitive gaming. "
                    "We provide a professional, organized environment for players to showcase their skills, "
                    "compete for championships, and build lasting rivalries.\n\n"
                    "• **Multiple Seasons**: NBA2K24, NBA2K25, and upcoming NBA2K26\n"
                    "• **Professional Structure**: Organized leagues with standings and playoffs\n"
                    "• **Comprehensive Stats**: Track every aspect of player performance\n"
                    "• **Championship History**: Rich legacy of champions and memorable moments"
                ),
                inline=False
            )
            
            # Current Season
            embed.add_field(
                name="🎮 Current Season",
                value=(
                    "**NBA2K26 Season 1** - Coming October 1, 2025\n\n"
                    "• **Registration**: [2kcompleague.com/register](https://2kcompleague.com/register)\n"
                    "• **Season Start**: October 1, 2025\n"
                    "• **Format**: Competitive 5v5 matches\n"
                    "• **Platform**: PlayStation 5\n"
                    "• **Monthly Seasons**: New season each month\n"
                    "• **Playoff Qualification**: 10+ games required"
                ),
                inline=False
            )
            
            # League Rules
            embed.add_field(
                name="📋 League Rules & Structure",
                value=(
                    "**Monthly Season Format:**\n"
                    "• Regular season runs for 3 weeks\n"
                    "• Last week dedicated to playoffs\n"
                    "• **Playoff Qualification**: Teams need 10+ games\n"
                    "• **Playoff Format**: Best of 3 series\n"
                    "• **Seeding**: Based on regular season record\n"
                    "• **Champion**: Crowned each month\n\n"
                    "**Game Requirements:**\n"
                    "• All games tracked via 2kcompleague.com\n"
                    "• Real-time statistics and standings\n"
                    "• Comprehensive player performance tracking"
                ),
                inline=False
            )
            
            # League Features
            embed.add_field(
                name="⭐ League Features",
                value=(
                    f"{emojis['trophy']} **Championship Tournaments**\n"
                    f"{emojis['star']} **Player Statistics Tracking**\n"
                    f"{emojis['fire']} **Record Breaking Moments**\n"
                    f"{emojis['crown']} **Hall of Fame Recognition**\n"
                    f"{emojis['diamond']} **Professional Broadcasting**\n"
                    f"{emojis['target']} **Skill-Based Matchmaking**"
                ),
                inline=True
            )
            
            # Notable Teams
            embed.add_field(
                name="🏆 Notable Teams",
                value=(
                    f"[**Goon Squad**](https://2kcompleague.com/team/goon-squad/) - 2x Champions\n"
                    f"[**Who Run It**](https://2kcompleague.com/team/who-run-it/) - Back-to-Back Champions\n"
                    f"[**No Excuses**](https://2kcompleague.com/team/no-excuses/) - Inaugural Champions\n"
                    f"[**University Of Delaware**](https://2kcompleague.com/team/university-of-delaware/) - Academic Excellence\n"
                    f"[**Bankruptcy**](https://2kcompleague.com/team/bankruptcy/) - Underdog Story\n"
                    f"[**Top Dawgs OF NC**](https://2kcompleague.com/team/top-dawgs-of-nc/) - First NBA2K25 Champions"
                ),
                inline=True
            )
            
            # Quick Links
            embed.add_field(
                name="🔗 Quick Links",
                value=(
                    "• [**Official Website**](https://2kcompleague.com)\n"
                    "• [**Player Registration**](https://2kcompleague.com/register)\n"
                    "• [**Current Standings**](https://2kcompleague.com/table/nba2k26-season-1-standings/)\n"
                    "• [**Season Stats**](https://2kcompleague.com/list/nba2k26-season-1-stats/)\n"
                    "• [**All-Time Records**](https://2kcompleague.com/list/all-time-statistics/)\n"
                    "• [**Championship History**](https://2kcompleague.com)"
                ),
                inline=True
            )
            
            # Championship Leaders
            embed.add_field(
                name="👑 Championship Leaders",
                value=(
                    "**Most Championships:**\n"
                    "🥇 **Goon Squad** - 2 titles\n"
                    "🥇 **Who Run It** - 2 titles\n"
                    "🥉 **No Excuses** - 1 title\n"
                    "🥉 **Top Dawgs OF NC** - 1 title\n"
                    "🥉 **University Of Delaware** - 1 title\n"
                    "🥉 **Bankruptcy** - 1 title"
                ),
                inline=False
            )
            
            embed.set_footer(text=create_branded_footer("Join the competition today!"))
            embed.set_thumbnail(url="https://2kcompleague.com/wp-content/uploads/2024/01/2kcomp-logo.png")
            
            await interaction.followup.send(embed=embed)
            logger.info(f"League command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in league command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching league information. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="commands", description="Get help with bot commands and features")
    async def commands(self, interaction: discord.Interaction):
        """Display comprehensive help information."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Commands command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring commands command: {e}")
            return
        
        try:
            colors = get_league_colors()
            emojis = get_league_emojis()
            
            embed = discord.Embed(
                title=f"{emojis['star']} 2KCompLeague Bot Commands",
                description="**Complete guide to all bot features and commands**",
                color=colors["info"]
            )
            
            # Player Commands
            embed.add_field(
                name="👤 Player Commands",
                value=(
                    "`/player <name>` - View detailed player stats and rankings\n"
                                                "`/milestones` - Top 5 players in each statistical category (all-time)\n"
                    "`/leaders <type> [stat]` - Season and career leaders\n"
                    "`/scorers` - Historical season leading scorers"
                ),
                inline=False
            )
            
            # League Commands
            embed.add_field(
                 name="🏆 League Commands",
                 value=(
                     "`/league` - Comprehensive league information\n"
                     "`/history` - Championship history and hierarchy\n"
                     "`/records` - All-time single-game records\n"
                     "`/doubledoubles` - All double-doubles in league history\n"
                     "`/tripledoubles` - All triple-doubles in league history\n"
                     "`/standings` - Current season standings\n"
                     "`/topteams` - Top 5 teams by most wins\n"
                    "`/recent` - Recent games and standout performances\n"
                    "`/seasonhighs` - Current season high performances\n"
                    "`/playoffrace` - Current playoff race standings\n"
                    "`/spotlight` - Random spotlight player\n"
                    "`/career-leader` - Career leader spotlight\n"
                    "`/record-holder` - Record holder spotlight"
                 ),
                 inline=False
             )
            
            # Community Commands
            embed.add_field(
                 name="🗳️ Community Commands",
                 value=(
                     "`/poll` - Create a custom community poll\n"
                     "`/preseason-poll` - Create preseason tournament poll\n"
                    "`/quick-poll` - Create a quick yes/no poll\n"
                    "`/poll-results` - Get results for a specific poll\n"
                    "`/active-polls` - Show all active polls"
                ),
                inline=False
            )
            
            # Admin Commands
            embed.add_field(
                        name="⚙️ Admin Commands",
                        value=(
                            "`/admin-announce <message>` - Send league announcements\n"
                            "`/admin-sync` - Sync bot commands (Admin only)\n"
                            "`/admin-clear-commands` - Clear all global commands (Admin only)\n"
                            "`/notifications status` - Check notification system\n"
                            "`/notifications test` - Test notification system"
                        ),
                        inline=False
                    )
            
            # Features
            embed.add_field(
                 name="✨ Key Features",
                 value=(
                     f"{emojis['fire']} **Real-time Statistics** - Live data from 2kcompleague.com\n"
                     f"{emojis['target']} **Clickable Links** - Direct access to player profiles\n"
                     f"{emojis['crown']} **Record Tracking** - Monitor record-breaking performances\n"
                     f"{emojis['star']} **Professional Branding** - Official 2KCompLeague experience\n"
                     f"{emojis['diamond']} **Comprehensive Data** - All-time and season statistics\n"
                     f"🗳️ **Community Polls** - Interactive voting and feedback system"
                 ),
                 inline=False
             )
            
            # Tips
            embed.add_field(
                name="💡 Usage Tips",
                value=(
                    "• Use `/player` with exact player names for best results\n"
                    "• Click player names in embeds to view full profiles\n"
                    "• All statistics are updated in real-time\n"
                    "• Use `/league` to learn more about 2KCompLeague\n"
                    "• Check `/records` for the most impressive performances"
                ),
                inline=False
            )
            
            embed.set_footer(text=create_branded_footer("Need more help? Visit 2kcompleague.com"))
            
            await interaction.followup.send(embed=embed)
            logger.info(f"Commands command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in commands command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching commands information. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="standings", description="View current season standings")
    async def standings(self, interaction: discord.Interaction):
        """Display current season standings."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Standings command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring standings command: {e}")
            return
        
        try:
            colors = get_league_colors()
            emojis = get_league_emojis()
            
            embed = discord.Embed(
                title=f"{emojis['trophy']} NBA2K26 Season 1 Standings",
                description="**Current league standings and team performance**",
                color=colors["success"]
            )
            
            # Note about upcoming season
            embed.add_field(
                name="📅 Season Information",
                value=(
                    "**NBA2K26 Season 1** begins **October 1, 2025**\n\n"
                    "• **Registration**: [2kcompleague.com/register](https://2kcompleague.com/register)\n"
                    "• **Standings**: [View Live Standings](https://2kcompleague.com/table/nba2k26-season-1-standings/)\n"
                    "• **Team Stats**: [Season Statistics](https://2kcompleague.com/list/nba2k26-season-1-stats/)\n\n"
                    "*Standings will be updated in real-time once the season begins*"
                ),
                inline=False
            )
            
            # Previous Season Champions with clickable team links
            embed.add_field(
                name="🏆 Previous Season Champions",
                value=(
                    "**NBA2K25 Season 6**: [Who Run It](https://2kcompleague.com/team/who-run-it/) 🥇\n"
                    "**NBA2K25 Season 5**: [Who Run It](https://2kcompleague.com/team/who-run-it/) 🥇\n"
                    "**NBA2K25 Season 4**: [Bankruptcy](https://2kcompleague.com/team/bankruptcy/) 🥇\n"
                    "**NBA2K25 Season 3**: [Goon Squad](https://2kcompleague.com/team/goon-squad/) 🥇\n"
                    "**NBA2K25 Season 2**: [University Of Delaware](https://2kcompleague.com/team/university-of-delaware/) 🥇\n"
                    "**NBA2K25 Season 1**: [Top Dawgs OF NC](https://2kcompleague.com/team/top-dawgs-of-nc/) 🥇"
                ),
                inline=False
            )
            
            embed.set_footer(text=create_branded_footer("Register now for NBA2K26 Season 1!"))
            
            await interaction.followup.send(embed=embed)
            logger.info(f"Standings command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in standings command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching standings. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="topteams", description="View top 5 teams by most wins")
    async def topteams(self, interaction: discord.Interaction):
        """Display top 5 teams by most wins."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Topteams command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring topteams command: {e}")
            return
        
        try:
            from core.http import HTTPClient
            from core.sportspress import fetch_events
            from core.names import get_team_name, get_team_url
            
            colors = get_league_colors()
            emojis = get_league_emojis()
            
            # Create HTTP client
            http_client = HTTPClient()
            
            # Fetch all events to analyze team wins
            events = await fetch_events(http_client)
            
            # Track team wins
            team_wins = {}
            team_losses = {}
            
            # Analyze each event to determine winners
            for event in events:
                try:
                    # Get teams from event
                    teams = event.get("teams", [])
                    if not isinstance(teams, list) or len(teams) < 2:
                        continue
                    
                    team_a_id = teams[0]
                    team_b_id = teams[1]
                    
                    # Get performance data
                    performance_data = event.get("performance", {})
                    if not performance_data:
                        continue
                    
                    # Calculate scores for each team
                    team_a_score = 0
                    team_b_score = 0
                    
                    # Look for team scores in performance data
                    for team_id, team_performance in performance_data.items():
                        if team_id == "0":  # Skip header
                            continue
                        
                        if isinstance(team_performance, dict):
                            # Look for team totals or calculate from player stats
                            team_total = team_performance.get("total", {})
                            if team_total:
                                # Try to get team score from total
                                score = team_total.get("pts", 0)
                                if score:
                                    if team_id == str(team_a_id):
                                        team_a_score = float(score)
                                    elif team_id == str(team_b_id):
                                        team_b_score = float(score)
                    
                    # If we couldn't get scores from team totals, try to calculate from player stats
                    if team_a_score == 0 and team_b_score == 0:
                        for team_id, team_performance in performance_data.items():
                            if team_id == "0":  # Skip header
                                continue
                            
                            if isinstance(team_performance, dict):
                                team_score = 0
                                for player_id, player_stats in team_performance.items():
                                    if player_id == "total":  # Skip team total row
                                        continue
                                    if isinstance(player_stats, dict):
                                        pts = player_stats.get("pts", 0)
                                        if pts:
                                            team_score += float(pts)
                                
                                if team_id == str(team_a_id):
                                    team_a_score = team_score
                                elif team_id == str(team_b_id):
                                    team_b_score = team_score
                    
                    # Determine winner and update records
                    if team_a_score > team_b_score:
                        # Team A wins
                        team_wins[team_a_id] = team_wins.get(team_a_id, 0) + 1
                        team_losses[team_b_id] = team_losses.get(team_b_id, 0) + 1
                    elif team_b_score > team_a_score:
                        # Team B wins
                        team_wins[team_b_id] = team_wins.get(team_b_id, 0) + 1
                        team_losses[team_a_id] = team_losses.get(team_a_id, 0) + 1
                    # Ties are ignored for win/loss calculation
                    
                except Exception as e:
                    logger.warning(f"Error processing event for team wins: {e}")
                    continue
            
            # Sort teams by wins (descending)
            sorted_teams = sorted(team_wins.items(), key=lambda x: x[1], reverse=True)
            
            # Get top 5 teams
            top_teams = sorted_teams[:5]
            
            if not top_teams:
                embed = discord.Embed(
                    title=f"{emojis['trophy']} Top Teams by Wins",
                    description="No team win data available yet.",
                    color=colors["warning"]
                )
                embed.add_field(
                    name="📊 Information",
                    value="Team win data will be available once games are played and recorded.",
                    inline=False
                )
                embed.set_footer(text=create_branded_footer("Check back after games are played!"))
                await interaction.followup.send(embed=embed)
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"{emojis['trophy']} Top 5 Teams by Wins",
                description="**Teams ranked by total wins across all seasons**",
                color=colors["success"]
            )
            
            # Add top teams
            for rank, (team_id, wins) in enumerate(top_teams, 1):
                try:
                    # Get team name and URL
                    team_name = await get_team_name(http_client, team_id)
                    team_url = await get_team_url(http_client, team_id)
                    
                    # Format team display
                    if team_url and team_url != f"https://2kcompleague.com/team/team-{team_id}/":
                        team_display = f"[**{team_name}**]({team_url})"
                    else:
                        team_display = f"**{team_name}**"
                    
                    # Get losses for win percentage
                    losses = team_losses.get(team_id, 0)
                    total_games = wins + losses
                    win_pct = (wins / total_games * 100) if total_games > 0 else 0
                    
                    # Medal emojis
                    if rank == 1:
                        medal = "🥇"
                    elif rank == 2:
                        medal = "🥈"
                    elif rank == 3:
                        medal = "🥉"
                    else:
                        medal = f"**#{rank}**"
                    
                    embed.add_field(
                        name=f"{medal} {team_display}",
                        value=f"**{wins}** wins ({win_pct:.1f}% win rate)\n{total_games} total games",
                        inline=False
                    )
                    
                except Exception as e:
                    logger.warning(f"Error processing team {team_id} for topteams: {e}")
                    embed.add_field(
                        name=f"**#{rank}** Team {team_id}",
                        value=f"**{wins}** wins",
                        inline=False
                    )
            
            # Add summary
            total_teams = len(team_wins)
            total_games = sum(team_wins.values()) + sum(team_losses.values())
            
            embed.add_field(
                name="📊 League Summary",
                value=(
                    f"**Total Teams**: {total_teams}\n"
                    f"**Total Games**: {total_games}\n"
                    f"**Data Source**: All historical games\n"
                    f"**Last Updated**: Real-time from 2kcompleague.com"
                ),
                inline=False
            )
            
            embed.set_footer(text=create_branded_footer("Based on all-time game records"))
            
            await interaction.followup.send(embed=embed)
            logger.info(f"Topteams command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in topteams command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while fetching top teams data. Please try again later.",
                    ephemeral=True
                )
            except:
                pass


async def setup(bot: commands.Bot):
    """Set up the league cog."""
    await bot.add_cog(LeagueCog(bot))
    logger.info("League cog loaded")
