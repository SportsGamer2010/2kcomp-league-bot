"""History commands for the Discord bot."""

import logging
from typing import List, Dict, Any

import discord
from discord.ext import commands
from discord import app_commands

from core.utils import create_branded_footer, get_league_branding

logger = logging.getLogger(__name__)


class HistoryCog(commands.Cog):
    """History commands for viewing league championships."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.branding = get_league_branding()
        
        # Team name to URL mapping for championship teams
        self.team_urls = {
            "Goon Squad": "https://2kcompleague.com/team/goon-squad/",
            "Who Run It": "https://2kcompleague.com/team/who-run-it/",
            "No Excuses": "https://2kcompleague.com/team/no-excuses/",
            "Top Dawgs OF NC": "https://2kcompleague.com/team/top-dawgs-of-nc/",
            "University Of Delaware": "https://2kcompleague.com/team/university-of-delaware/",
            "Bankruptcy": "https://2kcompleague.com/team/bankruptcy/",
            "Coming October 1, 2025": "https://2kcompleague.com/register/"
        }

    @app_commands.command(name="history", description="Show league championship history")
    async def history(self, interaction: discord.Interaction):
        """Show league championship history with hierarchy and season breakdown."""
        await interaction.response.defer()
        
        try:
            # Create history embed
            embed = self._create_history_embed()
            
            await interaction.followup.send(embed=embed)
            
            logger.info(f"History command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in history command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while displaying history. Please try again later.",
                    ephemeral=True
                )
            except:
                pass  # If we can't send the error message, just log it

    @app_commands.command(name="scorers", description="Show leading scorers for each season")
    async def scorers(self, interaction: discord.Interaction):
        """Show leading scorers for each season with team names and stat links."""
        await interaction.response.defer()
        
        try:
            # Create scorers embed
            embed = self._create_scorers_embed()
            
            await interaction.followup.send(embed=embed)
            
            logger.info(f"Scorers command used by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in scorers command: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while displaying leading scorers. Please try again later.",
                    ephemeral=True
                )
            except:
                pass  # If we can't send the error message, just log it

    def _create_history_embed(self) -> discord.Embed:
        """Create a history embed with championship hierarchy."""
        embed = discord.Embed(
            title="🏆 2KCompLeague Championship History",
            description="**CHAMPIONSHIP HIERARCHY - SORTED BY TITLES**\n*(Teams are ranked by their championship count - challenge the elite!)*",
            color=self.branding["colors"]["primary"]  # Use league branding
        )
        embed.set_footer(text=create_branded_footer())
        
        # Championship hierarchy data
        championship_data = [
            {
                "rank": 1,
                "team": "Goon Squad",
                "titles": 2,
                "championships": [
                    {"season": "NBA2K24 Season 2", "subtitle": "Back-to-Back Contenders"},
                    {"season": "NBA2K25 Season 3", "subtitle": "Return to Glory"}
                ]
            },
            {
                "rank": 2,
                "team": "Who Run It",
                "titles": 2,
                "championships": [
                    {"season": "NBA2K25 Season 5", "subtitle": "Prize Pool Champions ($250)"},
                    {"season": "NBA2K25 Season 6", "subtitle": "Back-to-Back Champions"}
                ]
            },
            {
                "rank": 3,
                "team": "No Excuses",
                "titles": 1,
                "championships": [
                    {"season": "NBA2K24 Season 1", "subtitle": "Inaugural Season Champions"}
                ]
            },
            {
                "rank": 4,
                "team": "Top Dawgs OF NC",
                "titles": 1,
                "championships": [
                    {"season": "NBA2K25 Season 1", "subtitle": "First NBA2K25 Champions"}
                ]
            },
            {
                "rank": 5,
                "team": "University Of Delaware",
                "titles": 1,
                "championships": [
                    {"season": "NBA2K25 Season 2", "subtitle": "Academic Excellence"}
                ]
            },
            {
                "rank": 6,
                "team": "Bankruptcy",
                "titles": 1,
                "championships": [
                    {"season": "NBA2K25 Season 4", "subtitle": "Underdog Story"}
                ]
            },
            {
                "rank": 7,
                "team": "Coming October 1, 2025",
                "titles": 1,
                "championships": [
                    {"season": "NBA2K26 Season 1", "subtitle": "Registration Opening Soon!"}
                ]
            }
        ]
        
        # Create championship hierarchy fields
        current_field = ""
        field_count = 0
        max_field_length = 1000  # Discord field limit
        
        for team_data in championship_data:
            rank = team_data["rank"]
            team = team_data["team"]
            titles = team_data["titles"]
            championships = team_data["championships"]
            
            # Create team entry with clickable team name
            team_url = self.team_urls.get(team, "")
            if team_url:
                team_link = f"[{team}]({team_url})"
            else:
                team_link = team
            
            team_entry = f"**#{rank} - {team_link}: {titles} title{'s' if titles > 1 else ''}**\n"
            
            for champ in championships:
                season = champ["season"]
                subtitle = champ["subtitle"]
                team_entry += f"{season} - {subtitle}\n"
            
            team_entry += "\n"
            
            # Check if adding this entry would exceed field limit
            if len(current_field) + len(team_entry) > max_field_length and current_field:
                # Add current field and start new one
                field_count += 1
                embed.add_field(
                    name=f"CHAMPIONSHIP HIERARCHY (Part {field_count})",
                    value=current_field,
                    inline=False
                )
                current_field = team_entry
            else:
                current_field += team_entry
        
        # Add remaining content
        if current_field:
            field_count += 1
            embed.add_field(
                name=f"CHAMPIONSHIP HIERARCHY (Part {field_count})",
                value=current_field,
                inline=False
            )
        
        # Add season-by-season breakdown
        self._add_season_breakdown(embed)
        
        return embed

    def _add_season_breakdown(self, embed: discord.Embed):
        """Add season-by-season breakdown to the embed."""
        # NBA2K24 seasons
        nba2k24_field = "**NBA2K24**\n"
        
        # Season 1: No Excuses
        no_excuses_url = self.team_urls.get("No Excuses", "")
        no_excuses_link = f"[No Excuses]({no_excuses_url})" if no_excuses_url else "No Excuses"
        nba2k24_field += f"**Season 1: {no_excuses_link}**\n"
        nba2k24_field += "└ Inaugural Season Champions\n\n"
        
        # Season 2: Goon Squad
        goon_squad_url = self.team_urls.get("Goon Squad", "")
        goon_squad_link = f"[Goon Squad]({goon_squad_url})" if goon_squad_url else "Goon Squad"
        nba2k24_field += f"**Season 2: {goon_squad_link}**\n"
        nba2k24_field += "└ Back-to-Back Contenders\n"
        
        embed.add_field(
            name="📅 NBA2K24 Seasons",
            value=nba2k24_field,
            inline=False
        )
        
        # NBA2K25 seasons
        nba2k25_field = "**NBA2K25**\n"
        
        # Season 1: Top Dawgs OF NC
        top_dawgs_url = self.team_urls.get("Top Dawgs OF NC", "")
        top_dawgs_link = f"[Top Dawgs OF NC]({top_dawgs_url})" if top_dawgs_url else "Top Dawgs OF NC"
        nba2k25_field += f"**Season 1: {top_dawgs_link}**\n"
        nba2k25_field += "└ First NBA2K25 Champions\n\n"
        
        # Season 2: University Of Delaware
        delaware_url = self.team_urls.get("University Of Delaware", "")
        delaware_link = f"[University Of Delaware]({delaware_url})" if delaware_url else "University Of Delaware"
        nba2k25_field += f"**Season 2: {delaware_link}**\n"
        nba2k25_field += "└ Academic Excellence\n\n"
        
        # Season 3: Goon Squad
        nba2k25_field += f"**Season 3: {goon_squad_link}**\n"
        nba2k25_field += "└ Return to Glory\n\n"
        
        # Season 4: Bankruptcy
        bankruptcy_url = self.team_urls.get("Bankruptcy", "")
        bankruptcy_link = f"[Bankruptcy]({bankruptcy_url})" if bankruptcy_url else "Bankruptcy"
        nba2k25_field += f"**Season 4: {bankruptcy_link}**\n"
        nba2k25_field += "└ Underdog Story\n\n"
        
        # Season 5: Who Run It
        who_run_it_url = self.team_urls.get("Who Run It", "")
        who_run_it_link = f"[Who Run It]({who_run_it_url})" if who_run_it_url else "Who Run It"
        nba2k25_field += f"**Season 5: {who_run_it_link}**\n"
        nba2k25_field += "└ Prize Pool Champions ($250)\n\n"
        
        # Season 6: Who Run It
        nba2k25_field += f"**Season 6: {who_run_it_link}**\n"
        nba2k25_field += "└ Back-to-Back Champions\n"
        
        embed.add_field(
            name="📅 NBA2K25 Seasons",
            value=nba2k25_field,
            inline=False
        )

    def _create_scorers_embed(self) -> discord.Embed:
        """Create a scorers embed with leading scorers for each season."""
        embed = discord.Embed(
            title="🏀 2KCompLeague Leading Scorers",
            description="**Season Leading Scorers - Ranked by Total Points**\n*(Click names for player profiles, click season stats for full leaderboards)*",
            color=self.branding["colors"]["secondary"]  # Use league branding
        )
        embed.set_footer(text=create_branded_footer())
        
        # Leading scorers data (sorted by points, highest first)
        leading_scorers = [
            {
                "season": "NBA2k25 Season 5",
                "name": "||GREEN-ME||",
                "team": "Mandalo Mafia",
                "points": 424.0,
                "player_url": "https://2kcompleague.com/player/green-me/",
                "stats_url": "https://2kcompleague.com/list/nba2k25-season-5-stats/"
            },
            {
                "season": "NBA2k25 Season 1",
                "name": "ComeUpZan",
                "team": "Goon Squad",
                "points": 389.0,
                "player_url": "https://2kcompleague.com/player/comeupzan/",
                "stats_url": "https://2kcompleague.com/list/nba2k25-season-1-stats/"
            },
            {
                "season": "NBA2k25 Season 4",
                "name": "Swvdez",
                "team": "Bankruptcy",
                "points": 367.0,
                "player_url": "https://2kcompleague.com/player/swvdez/",
                "stats_url": "https://2kcompleague.com/list/nba2k25-season-4-player-statistics/"
            },
            {
                "season": "NBA2k25 Season 3",
                "name": "JT5_Era",
                "team": "Goon Squad",
                "points": 337.0,
                "player_url": "https://2kcompleague.com/player/jt5-era/",
                "stats_url": "https://2kcompleague.com/list/nba2k25-season-3-player-stats/"
            },
            {
                "season": "NBA2k25 Season 2",
                "name": "||TurnupTyTy||",
                "team": "Dream Chasers",
                "points": 307.0,
                "player_url": "https://2kcompleague.com/player/turnuptyty/",
                "stats_url": "https://2kcompleague.com/list/nba2k25-season-2-player-statistics/"
            },
            {
                "season": "NBA2k25 Season 6",
                "name": "Halibans",
                "team": "Missing In Action",
                "points": 279.0,
                "player_url": "https://2kcompleague.com/player/halibans/",
                "stats_url": "https://2kcompleague.com/list/nba2k25-season-6-stats/"
            },
            {
                "season": "NBA2k24 Season 2",
                "name": "Kjfrmdastu",
                "team": "FrmDaStu",
                "points": 183.0,
                "player_url": "https://2kcompleague.com/player/kjfrmdastu/",
                "stats_url": "https://2kcompleague.com/list/nba2k24-season-2-stat-leaders/"
            },
            {
                "season": "2k24 Season 1",
                "name": "Pay-Master-Goat",
                "team": "Street Junkies",
                "points": 148.0,
                "player_url": "https://2kcompleague.com/player/pay-master-goat/",
                "stats_url": "https://2kcompleague.com/list/2k24-season-1-stats/"
            }
        ]
        
        # Create fields for each season (split into multiple fields due to Discord limits)
        current_field = ""
        field_count = 0
        max_field_length = 1000
        
        for i, scorer in enumerate(leading_scorers):
            # Create clickable player name and season stats link
            player_link = f"[{scorer['name']}]({scorer['player_url']})"
            stats_link = f"[Season Stats]({scorer['stats_url']})"
            
            # Create season entry
            season_entry = f"**#{i+1} {scorer['season']}**\n"
            season_entry += f"🏆 {player_link} ({scorer['team']})\n"
            season_entry += f"📊 {scorer['points']} points\n"
            season_entry += f"📋 {stats_link}\n\n"
            
            # Check if adding this entry would exceed field limit
            if len(current_field) + len(season_entry) > max_field_length and current_field:
                # Add current field and start new one
                field_count += 1
                embed.add_field(
                    name=f"Leading Scorers (Part {field_count})",
                    value=current_field,
                    inline=False
                )
                current_field = season_entry
            else:
                current_field += season_entry
        
        # Add remaining content
        if current_field:
            field_count += 1
            embed.add_field(
                name=f"Leading Scorers (Part {field_count})",
                value=current_field,
                inline=False
            )
        
        # Add summary statistics
        total_seasons = len(leading_scorers)
        highest_scorer = leading_scorers[0]  # Already sorted by points
        lowest_scorer = leading_scorers[-1]
        avg_points = sum(scorer["points"] for scorer in leading_scorers) / total_seasons
        
        summary_field = f"**📈 Summary Statistics**\n"
        summary_field += f"🏆 Highest: {highest_scorer['name']} - {highest_scorer['points']} points\n"
        summary_field += f"📉 Lowest: {lowest_scorer['name']} - {lowest_scorer['points']} points\n"
        summary_field += f"📊 Average: {avg_points:.1f} points\n"
        summary_field += f"📋 Total Seasons: {total_seasons}"
        
        embed.add_field(
            name="📊 Statistics",
            value=summary_field,
            inline=False
        )
        
        return embed


async def setup(bot: commands.Bot):
    """Set up the history cog."""
    await bot.add_cog(HistoryCog(bot))