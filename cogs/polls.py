"""Polling system for community engagement and voting."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings
from core.utils import get_league_colors, get_league_emojis, create_branded_footer, get_league_branding, get_league_logo_url

logger = logging.getLogger(__name__)


class PollsCog(commands.Cog):
    """Polling system for community engagement."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_polls: Dict[int, Dict] = {}  # message_id -> poll_data
        self.poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    @app_commands.command(name="poll", description="Create a poll for the community")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)",
        duration="Poll duration in hours (default: 24)"
    )
    async def create_poll(self, interaction: discord.Interaction, 
                         question: str,
                         option1: str,
                         option2: str,
                         option3: str = None,
                         option4: str = None,
                         option5: str = None,
                         duration: int = 24):
        """Create a community poll."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Poll command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring poll command: {e}")
            return
        
        try:
            # Validate inputs
            options = [option1, option2]
            if option3:
                options.append(option3)
            if option4:
                options.append(option4)
            if option5:
                options.append(option5)
            
            if len(options) < 2:
                await interaction.followup.send(
                    "❌ Poll must have at least 2 options.",
                    ephemeral=True
                )
                return
            
            if len(options) > 10:
                await interaction.followup.send(
                    "❌ Poll can have at most 10 options.",
                    ephemeral=True
                )
                return
            
            if duration < 1 or duration > 168:  # Max 1 week
                await interaction.followup.send(
                    "❌ Poll duration must be between 1 and 168 hours (1 week).",
                    ephemeral=True
                )
                return

            # Create poll embed
            branding = get_league_branding()
            colors = branding["colors"]
            emojis = branding["emojis"]
            
            embed = discord.Embed(
                title=f"{emojis['shield']} Community Poll",
                description=f"**{question}**",
                color=colors["primary"],
                url=branding["website"]
            )
            
            # Add logo as thumbnail
            embed.set_thumbnail(url=branding["logo_url"])
            
            # Add options
            options_text = ""
            for i, option in enumerate(options):
                emoji = self.poll_emojis[i]
                options_text += f"{emoji} {option}\n"
            
            embed.add_field(
                name="Options",
                value=options_text,
                inline=False
            )
            
            # Add poll info
            end_time = datetime.now() + timedelta(hours=duration)
            embed.add_field(
                name="Poll Information",
                value=(
                    f"**Created by:** {interaction.user.mention}\n"
                    f"**Duration:** {duration} hours\n"
                    f"**Ends:** <t:{int(end_time.timestamp())}:R>\n"
                    f"**Votes:** 0"
                ),
                inline=False
            )
            
            embed.set_footer(text=create_branded_footer("React to vote • Results update automatically"))
            
            # Send poll message
            poll_message = await interaction.followup.send(embed=embed)
            
            # Add reaction options
            for i in range(len(options)):
                await poll_message.add_reaction(self.poll_emojis[i])
            
            # Store poll data
            poll_data = {
                'question': question,
                'options': options,
                'creator': interaction.user.id,
                'created_at': datetime.now(),
                'end_time': end_time,
                'message_id': poll_message.id,
                'channel_id': interaction.channel.id,
                'votes': {}  # user_id -> option_index
            }
            
            self.active_polls[poll_message.id] = poll_data
            
            # Start poll monitoring
            asyncio.create_task(self._monitor_poll(poll_message.id))
            
            logger.info(f"Poll created by {interaction.user}: {question}")
            
        except Exception as e:
            logger.error(f"Error creating poll: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while creating the poll. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="preseason-poll", description="Create a preseason tournament poll")
    async def preseason_poll(self, interaction: discord.Interaction):
        """Create a preseason tournament poll."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Preseason poll command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring preseason poll command: {e}")
            return
        
        try:
            branding = get_league_branding()
            colors = branding["colors"]
            emojis = branding["emojis"]
            
            embed = discord.Embed(
                title=f"{emojis['shield']} NBA2K26 Season 1 Preseason Tournament",
                description="**Should we host a preseason tournament before the regular season begins?**",
                color=colors["primary"],
                url=branding["website"]
            )
            
            # Add logo as thumbnail
            embed.set_thumbnail(url=branding["logo_url"])
            
            # Add tournament details
            embed.add_field(
                name="Tournament Details",
                value=(
                    "🏆 **Format**: Single elimination bracket\n"
                    "⏰ **Duration**: 1-2 weeks before Season 1\n"
                    "🎮 **Games**: Best of 3 series\n"
                    "🏅 **Prize**: Bragging rights + special recognition\n"
                    "📅 **Start**: TBD (October 1, 2025 Season 1 start)"
                ),
                inline=False
            )
            
            # Add options
            options_text = (
                "1️⃣ **Yes, let's do it!** - I want to participate in a preseason tournament\n"
                "2️⃣ **Maybe** - I'm interested but need more details\n"
                "3️⃣ **No** - I prefer to wait for the regular season\n"
                "4️⃣ **I don't care** - Either way is fine with me"
            )
            
            embed.add_field(
                name="Vote Options",
                value=options_text,
                inline=False
            )
            
            # Add poll info
            end_time = datetime.now() + timedelta(hours=72)  # 3 days
            embed.add_field(
                name="Poll Information",
                value=(
                    f"**Created by:** {interaction.user.mention}\n"
                    f"**Duration:** 72 hours (3 days)\n"
                    f"**Ends:** <t:{int(end_time.timestamp())}:R>\n"
                    f"**Votes:** 0"
                ),
                inline=False
            )
            
            embed.set_footer(text=create_branded_footer("React to vote • Results will determine tournament planning"))
            
            # Send poll message
            poll_message = await interaction.followup.send(embed=embed)
            
            # Add reaction options
            for i in range(4):
                await poll_message.add_reaction(self.poll_emojis[i])
            
            # Store poll data
            poll_data = {
                'question': "Should we host a preseason tournament before the regular season begins?",
                'options': [
                    "Yes, let's do it! - I want to participate in a preseason tournament",
                    "Maybe - I'm interested but need more details",
                    "No - I prefer to wait for the regular season",
                    "I don't care - Either way is fine with me"
                ],
                'creator': interaction.user.id,
                'created_at': datetime.now(),
                'end_time': end_time,
                'message_id': poll_message.id,
                'channel_id': interaction.channel.id,
                'votes': {},
                'type': 'preseason_tournament'
            }
            
            self.active_polls[poll_message.id] = poll_data
            
            # Start poll monitoring
            asyncio.create_task(self._monitor_poll(poll_message.id))
            
            logger.info(f"Preseason tournament poll created by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error creating preseason poll: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while creating the preseason poll. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="quick-poll", description="Create a quick yes/no poll")
    @app_commands.describe(
        question="The yes/no question",
        duration="Poll duration in hours (default: 12)"
    )
    async def quick_poll(self, interaction: discord.Interaction, 
                        question: str,
                        duration: int = 12):
        """Create a quick yes/no poll."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Quick poll command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring quick poll command: {e}")
            return
        
        try:
            if duration < 1 or duration > 72:  # Max 3 days for quick polls
                await interaction.followup.send(
                    "❌ Quick poll duration must be between 1 and 72 hours.",
                    ephemeral=True
                )
                return

            branding = get_league_branding()
            colors = branding["colors"]
            emojis = branding["emojis"]
            
            embed = discord.Embed(
                title=f"{emojis['shield']} Quick Poll",
                description=f"**{question}**",
                color=colors["primary"],
                url=branding["website"]
            )
            
            # Add logo as thumbnail
            embed.set_thumbnail(url=branding["logo_url"])
            
            # Add options
            embed.add_field(
                name="Options",
                value="✅ **Yes**\n❌ **No**",
                inline=False
            )
            
            # Add poll info
            end_time = datetime.now() + timedelta(hours=duration)
            embed.add_field(
                name="Poll Information",
                value=(
                    f"**Created by:** {interaction.user.mention}\n"
                    f"**Duration:** {duration} hours\n"
                    f"**Ends:** <t:{int(end_time.timestamp())}:R>\n"
                    f"**Votes:** 0"
                ),
                inline=False
            )
            
            embed.set_footer(text=create_branded_footer("React to vote • Results update automatically"))
            
            # Send poll message
            poll_message = await interaction.followup.send(embed=embed)
            
            # Add reaction options
            await poll_message.add_reaction("✅")
            await poll_message.add_reaction("❌")
            
            # Store poll data
            poll_data = {
                'question': question,
                'options': ["Yes", "No"],
                'creator': interaction.user.id,
                'created_at': datetime.now(),
                'end_time': end_time,
                'message_id': poll_message.id,
                'channel_id': interaction.channel.id,
                'votes': {},
                'type': 'quick_poll'
            }
            
            self.active_polls[poll_message.id] = poll_data
            
            # Start poll monitoring
            asyncio.create_task(self._monitor_poll(poll_message.id))
            
            logger.info(f"Quick poll created by {interaction.user}: {question}")
            
        except Exception as e:
            logger.error(f"Error creating quick poll: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while creating the quick poll. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="poll-results", description="Get results for a specific poll")
    @app_commands.describe(message_id="The message ID of the poll")
    async def poll_results(self, interaction: discord.Interaction, message_id: str):
        """Get results for a specific poll."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Poll results command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring poll results command: {e}")
            return
        
        try:
            try:
                msg_id = int(message_id)
            except ValueError:
                await interaction.followup.send(
                    "❌ Invalid message ID. Please provide a valid message ID.",
                    ephemeral=True
                )
                return
            
            if msg_id not in self.active_polls:
                await interaction.followup.send(
                    "❌ Poll not found. Make sure the message ID is correct and the poll is still active.",
                    ephemeral=True
                )
                return
            
            poll_data = self.active_polls[msg_id]
            await self._send_poll_results(interaction, poll_data)
            
        except Exception as e:
            logger.error(f"Error getting poll results: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while getting poll results. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="active-polls", description="Show all active polls")
    async def active_polls(self, interaction: discord.Interaction):
        """Show all active polls."""
        try:
            await interaction.response.defer()
        except discord.NotFound:
            logger.warning(f"Active polls command interaction expired for user {interaction.user}")
            return
        except Exception as e:
            logger.error(f"Error deferring active polls command: {e}")
            return
        
        try:
            if not self.active_polls:
                await interaction.followup.send(
                    "📊 No active polls found.",
                    ephemeral=True
                )
                return
            
            colors = get_league_colors()
            emojis = get_league_emojis()
            
            embed = discord.Embed(
                title=f"{emojis['target']} Active Polls",
                description="**Currently running community polls**",
                color=colors["info"]
            )
            
            for msg_id, poll_data in self.active_polls.items():
                time_left = poll_data['end_time'] - datetime.now()
                hours_left = int(time_left.total_seconds() / 3600)
                
                poll_type = poll_data.get('type', 'standard')
                type_emoji = "🏆" if poll_type == 'preseason_tournament' else "⚡" if poll_type == 'quick_poll' else "📊"
                
                embed.add_field(
                    name=f"{type_emoji} {poll_data['question'][:50]}{'...' if len(poll_data['question']) > 50 else ''}",
                    value=(
                        f"**ID:** `{msg_id}`\n"
                        f"**Time Left:** {hours_left} hours\n"
                        f"**Votes:** {len(poll_data['votes'])}\n"
                        f"**Options:** {len(poll_data['options'])}"
                    ),
                    inline=True
                )
            
            embed.set_footer(text=create_branded_footer("Use /poll-results <message_id> to see detailed results"))
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing active polls: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while showing active polls. Please try again later.",
                    ephemeral=True
                )
            except:
                pass

    async def _monitor_poll(self, message_id: int):
        """Monitor a poll and update results."""
        try:
            poll_data = self.active_polls.get(message_id)
            if not poll_data:
                return
            
            # Wait until poll ends
            while datetime.now() < poll_data['end_time']:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Update poll results
                await self._update_poll_results(message_id)
            
            # Poll has ended, send final results
            await self._end_poll(message_id)
            
        except Exception as e:
            logger.error(f"Error monitoring poll {message_id}: {e}")

    async def _update_poll_results(self, message_id: int):
        """Update poll results based on reactions."""
        try:
            poll_data = self.active_polls.get(message_id)
            if not poll_data:
                return
            
            channel = self.bot.get_channel(poll_data['channel_id'])
            if not channel:
                return
            
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                # Message was deleted
                del self.active_polls[message_id]
                return
            
            # Count reactions
            vote_counts = {}
            total_votes = 0
            
            for reaction in message.reactions:
                if reaction.emoji in self.poll_emojis or reaction.emoji in ["✅", "❌"]:
                    # Get the option index
                    if reaction.emoji in self.poll_emojis:
                        option_index = self.poll_emojis.index(reaction.emoji)
                    elif reaction.emoji == "✅":
                        option_index = 0
                    elif reaction.emoji == "❌":
                        option_index = 1
                    else:
                        continue
                    
                    # Count unique users (subtract 1 for bot reaction)
                    unique_users = set()
                    async for user in reaction.users():
                        if not user.bot:
                            unique_users.add(user.id)
                    
                    vote_count = len(unique_users)
                    vote_counts[option_index] = vote_count
                    total_votes += vote_count
            
            # Update poll data
            poll_data['vote_counts'] = vote_counts
            poll_data['total_votes'] = total_votes
            
            # Update embed
            await self._update_poll_embed(message, poll_data)
            
        except Exception as e:
            logger.error(f"Error updating poll results for {message_id}: {e}")

    async def _update_poll_embed(self, message: discord.Message, poll_data: Dict):
        """Update the poll embed with current results."""
        try:
            colors = get_league_colors()
            emojis = get_league_emojis()
            
            # Determine poll type and title
            poll_type = poll_data.get('type', 'standard')
            if poll_type == 'preseason_tournament':
                title = f"{emojis['trophy']} NBA2K26 Season 1 Preseason Tournament"
            elif poll_type == 'quick_poll':
                title = f"{emojis['target']} Quick Poll"
            else:
                title = f"{emojis['target']} Community Poll"
            
            embed = discord.Embed(
                title=title,
                description=f"**{poll_data['question']}**",
                color=colors["info"]
            )
            
            # Add options with vote counts
            options_text = ""
            vote_counts = poll_data.get('vote_counts', {})
            total_votes = poll_data.get('total_votes', 0)
            
            for i, option in enumerate(poll_data['options']):
                if poll_type == 'quick_poll':
                    emoji = "✅" if i == 0 else "❌"
                else:
                    emoji = self.poll_emojis[i]
                
                votes = vote_counts.get(i, 0)
                percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                
                # Create progress bar
                bar_length = 10
                filled_length = int(bar_length * percentage / 100)
                bar = "█" * filled_length + "░" * (bar_length - filled_length)
                
                options_text += f"{emoji} {option}\n"
                options_text += f"`{bar}` {votes} votes ({percentage:.1f}%)\n\n"
            
            embed.add_field(
                name="Results",
                value=options_text,
                inline=False
            )
            
            # Add poll info
            time_left = poll_data['end_time'] - datetime.now()
            hours_left = int(time_left.total_seconds() / 3600)
            
            embed.add_field(
                name="Poll Information",
                value=(
                    f"**Created by:** <@{poll_data['creator']}>\n"
                    f"**Time Left:** {hours_left} hours\n"
                    f"**Total Votes:** {total_votes}\n"
                    f"**Ends:** <t:{int(poll_data['end_time'].timestamp())}:R>"
                ),
                inline=False
            )
            
            embed.set_footer(text=create_branded_footer("React to vote • Results update automatically"))
            
            await message.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Error updating poll embed: {e}")

    async def _end_poll(self, message_id: int):
        """End a poll and send final results."""
        try:
            poll_data = self.active_polls.get(message_id)
            if not poll_data:
                return
            
            channel = self.bot.get_channel(poll_data['channel_id'])
            if not channel:
                return
            
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                # Message was deleted
                del self.active_polls[message_id]
                return
            
            # Send final results
            await self._send_final_results(channel, poll_data)
            
            # Remove from active polls
            del self.active_polls[message_id]
            
            logger.info(f"Poll {message_id} ended")
            
        except Exception as e:
            logger.error(f"Error ending poll {message_id}: {e}")

    async def _send_final_results(self, channel: discord.TextChannel, poll_data: Dict):
        """Send final poll results."""
        try:
            colors = get_league_colors()
            emojis = get_league_emojis()
            
            # Determine poll type and title
            poll_type = poll_data.get('type', 'standard')
            if poll_type == 'preseason_tournament':
                title = f"{emojis['trophy']} Preseason Tournament Poll - FINAL RESULTS"
            elif poll_type == 'quick_poll':
                title = f"{emojis['target']} Quick Poll - FINAL RESULTS"
            else:
                title = f"{emojis['target']} Community Poll - FINAL RESULTS"
            
            embed = discord.Embed(
                title=title,
                description=f"**{poll_data['question']}**",
                color=colors["success"]
            )
            
            # Add final results
            vote_counts = poll_data.get('vote_counts', {})
            total_votes = poll_data.get('total_votes', 0)
            
            if total_votes == 0:
                embed.add_field(
                    name="Results",
                    value="No votes were cast in this poll.",
                    inline=False
                )
            else:
                # Sort options by vote count
                sorted_options = sorted(
                    enumerate(poll_data['options']),
                    key=lambda x: vote_counts.get(x[0], 0),
                    reverse=True
                )
                
                results_text = ""
                for i, (option_index, option) in enumerate(sorted_options):
                    votes = vote_counts.get(option_index, 0)
                    percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                    
                    if poll_type == 'quick_poll':
                        emoji = "✅" if option_index == 0 else "❌"
                    else:
                        emoji = self.poll_emojis[option_index]
                    
                    position = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                    
                    results_text += f"{position} {emoji} **{option}**\n"
                    results_text += f"`{votes} votes ({percentage:.1f}%)`\n\n"
                
                embed.add_field(
                    name="Final Results",
                    value=results_text,
                    inline=False
                )
            
            # Add poll summary
            embed.add_field(
                name="Poll Summary",
                value=(
                    f"**Total Votes:** {total_votes}\n"
                    f"**Duration:** {poll_data['created_at'].strftime('%Y-%m-%d %H:%M')} - {poll_data['end_time'].strftime('%Y-%m-%d %H:%M')}\n"
                    f"**Created by:** <@{poll_data['creator']}>"
                ),
                inline=False
            )
            
            embed.set_footer(text=create_branded_footer("Poll completed • Thank you for voting!"))
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error sending final results: {e}")

    async def _send_poll_results(self, interaction: discord.Interaction, poll_data: Dict):
        """Send poll results to interaction."""
        try:
            colors = get_league_colors()
            emojis = get_league_emojis()
            
            # Determine poll type and title
            poll_type = poll_data.get('type', 'standard')
            if poll_type == 'preseason_tournament':
                title = f"{emojis['trophy']} Preseason Tournament Poll Results"
            elif poll_type == 'quick_poll':
                title = f"{emojis['target']} Quick Poll Results"
            else:
                title = f"{emojis['target']} Poll Results"
            
            embed = discord.Embed(
                title=title,
                description=f"**{poll_data['question']}**",
                color=colors["info"]
            )
            
            # Add current results
            vote_counts = poll_data.get('vote_counts', {})
            total_votes = poll_data.get('total_votes', 0)
            
            if total_votes == 0:
                embed.add_field(
                    name="Current Results",
                    value="No votes have been cast yet.",
                    inline=False
                )
            else:
                results_text = ""
                for i, option in enumerate(poll_data['options']):
                    if poll_type == 'quick_poll':
                        emoji = "✅" if i == 0 else "❌"
                    else:
                        emoji = self.poll_emojis[i]
                    
                    votes = vote_counts.get(i, 0)
                    percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                    
                    results_text += f"{emoji} **{option}**\n"
                    results_text += f"`{votes} votes ({percentage:.1f}%)`\n\n"
                
                embed.add_field(
                    name="Current Results",
                    value=results_text,
                    inline=False
                )
            
            # Add poll info
            time_left = poll_data['end_time'] - datetime.now()
            hours_left = int(time_left.total_seconds() / 3600)
            
            embed.add_field(
                name="Poll Information",
                value=(
                    f"**Total Votes:** {total_votes}\n"
                    f"**Time Left:** {hours_left} hours\n"
                    f"**Ends:** <t:{int(poll_data['end_time'].timestamp())}:R>\n"
                    f"**Created by:** <@{poll_data['creator']}>"
                ),
                inline=False
            )
            
            embed.set_footer(text=create_branded_footer("Results update automatically"))
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error sending poll results: {e}")


async def setup(bot: commands.Bot):
    """Set up the polls cog."""
    await bot.add_cog(PollsCog(bot))
    logger.info("Polls cog loaded")
