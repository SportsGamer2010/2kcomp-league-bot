"""Status commands for viewing leaders and records."""

import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings
from core.leaders import top_n_season_leaders, top_n_career_leaders, top_n_career_leaders_alltime, format_leaders_embed


logger = logging.getLogger(__name__)


class StatusCog(commands.Cog):
    """Status commands for viewing statistics."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors in status commands."""
        logger.error(f"Status command error: {error}")
        await interaction.response.send_message(
            "❌ An error occurred while processing your command.",
            ephemeral=True
        )
    
    @app_commands.command(name="leaders", description="View season or career leaders")
    @app_commands.describe(
        type="Type of leaders to view",
        stat="Specific statistic to view (optional)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Season", value="season"),
        app_commands.Choice(name="Career", value="career")
    ])
    @app_commands.choices(stat=[
        app_commands.Choice(name="Points", value="points"),
        app_commands.Choice(name="Assists", value="assists"),
        app_commands.Choice(name="Rebounds", value="rebounds"),
        app_commands.Choice(name="Steals", value="steals"),
        app_commands.Choice(name="Blocks", value="blocks"),
        app_commands.Choice(name="3-Pointers Made", value="threes_made")
    ])
    async def leaders(
        self,
        interaction: discord.Interaction,
        type: str,
        stat: Optional[str] = None
    ):
        """View season or career leaders."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            # Interaction already expired, can't respond
            logger.warning(f"Leaders command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring leaders command: {e}")
            return
        
        try:
            # Get HTTP client from bot
            http_client = getattr(self.bot, 'http_client', None)
            logger.info(f"HTTP client retrieved: {http_client is not None}")
            if not http_client:
                logger.error("HTTP client not found in bot")
                await interaction.followup.send(
                    "❌ Bot is not properly initialized. Please try again later.",
                    ephemeral=True
                )
                return
            
            # Calculate leaders based on type
            logger.info(f"Calculating {type} leaders...")
            if type == "season":
                leaders_data = await top_n_season_leaders(http_client)
                title = "Season Leaders"
            else:  # career
                # Use All Time Statistics for better performance and accuracy
                leaders_data = await top_n_career_leaders_alltime(http_client)
                title = "Career Leaders (All-Time)"
            
            logger.info(f"Leaders data retrieved: {leaders_data is not None}")
            if not leaders_data:
                logger.warning("No leaders data available")
                await interaction.followup.send(
                    "❌ No leaders data available at the moment.",
                    ephemeral=True
                )
                return
            
            # Format embed
            logger.info("Formatting embed...")
            embed = format_leaders_embed(leaders_data, type)
            logger.info(f"Embed formatted: {embed is not None}")
            
            # Filter by specific stat if requested
            if stat:
                logger.info(f"Filtering by stat: {stat}")
                # Create a new embed with only the requested stat
                filtered_embed = discord.Embed(
                    title=f"{title} - {stat.replace('_', ' ').title()}",
                    color=0x0099ff,
                    timestamp=discord.utils.utcnow()
                )
                
                # Find the field for the requested stat
                for field in embed["fields"]:
                    if field["name"].lower().endswith(stat.replace("_", " ")):
                        filtered_embed.add_field(
                            name=field["name"],
                            value=field["value"],
                            inline=False
                        )
                        break
                
                filtered_embed.set_footer(text="2KCompLeague | Auto-generated")
                await interaction.followup.send(embed=filtered_embed)
            else:
                # Send full embed
                await interaction.followup.send(embed=discord.Embed.from_dict(embed))
            
            logger.info(f"Leaders command used by {interaction.user}: {type} leaders")
            
        except Exception as e:
            logger.error(f"Failed to get leaders: {e}")
            await interaction.followup.send(
                "❌ Failed to retrieve leaders data. Please try again later.",
                ephemeral=True
            )
    

    
    @app_commands.command(name="help", description="Show help information")
    async def help(self, interaction: discord.Interaction):
        """Show help information."""
        embed = discord.Embed(
            title="🤖 2KCompLeague Bot Help",
            description="Welcome to the 2KCompLeague Discord bot! Here are the available commands:",
            color=0x0099ff,
            timestamp=discord.utils.utcnow()
        )
        
        # User commands
        embed.add_field(
            name="📊 User Commands",
            value="**`/leaders`** - View season or career leaders\n"
                  "**`/records`** - View single-game records\n"
                  "**`/milestones`** - View top 5 players in each stat category (all-time)\n"
                  "**`/history`** - View league championship history\n"
                  "**`/scorers`** - View leading scorers for each season\n"
                  "**`/player <name>`** - View player stats and rankings\n"
                  "**`/help`** - Show this help message",
            inline=False
        )
        
        # Admin commands
        embed.add_field(
            name="⚙️ Admin Commands",
            value="**`/announce`** - Send an announcement\n"
                  "**`/status`** - Check bot status\n"
                  "**`/history`** - View championship history",
            inline=False
        )
        
        # Features
        embed.add_field(
            name="🚀 Features",
            value="• **Automatic Leaders Monitoring** - Get notified when leaders change\n"
                  "• **Milestone Tracking** - Celebrate when players reach milestones\n"
                  "• **Record Breaking** - Get notified of new single-game records\n"
                  "• **Real-time Updates** - All data is fetched live from 2KCompLeague.com",
            inline=False
        )
        
        embed.set_footer(text="2KCompLeague | Powered by SportsPress")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Set up the status cog."""
    await bot.add_cog(StatusCog(bot))
    logger.info("Status cog loaded")
