"""Record monitoring system for Discord notifications."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import discord

from .config import settings
from .records import RecordsData, SingleGameRecord
from .http import HTTPClient

logger = logging.getLogger(__name__)

# File to store previous records for comparison
RECORDS_FILE = Path("data/previous_records.json")


class RecordMonitor:
    """Monitors for new records and sends Discord notifications."""
    
    def __init__(self, bot: discord.ext.commands.Bot, http_client: HTTPClient):
        self.bot = bot
        self.http_client = http_client
        self.previous_records: Optional[RecordsData] = None
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        RECORDS_FILE.parent.mkdir(exist_ok=True)
    
    async def load_previous_records(self) -> Optional[RecordsData]:
        """Load previous records from file."""
        try:
            if RECORDS_FILE.exists():
                with open(RECORDS_FILE, 'r') as f:
                    data = json.load(f)
                    return RecordsData(**data)
        except Exception as e:
            logger.warning(f"Failed to load previous records: {e}")
        return None
    
    async def save_current_records(self, records: RecordsData):
        """Save current records to file."""
        try:
            with open(RECORDS_FILE, 'w') as f:
                json.dump(records.dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save current records: {e}")
    
    def _compare_records(self, old_record: Optional[SingleGameRecord], 
                        new_record: Optional[SingleGameRecord]) -> bool:
        """Compare two records to see if a new record was set."""
        if not old_record and new_record:
            return True  # New record set
        if old_record and new_record:
            return new_record.value > old_record.value
        return False
    
    async def check_for_new_records(self, current_records: RecordsData) -> list:
        """Check for new records and return list of new records."""
        new_records = []
        
        if not self.previous_records:
            logger.info("No previous records to compare against")
            return new_records
        
        # List of record types to check
        record_types = ['points', 'rebounds', 'assists', 'steals', 'blocks', 
                       'threes_made', 'threep_percent']
        
        for record_type in record_types:
            old_record = getattr(self.previous_records, record_type, None)
            new_record = getattr(current_records, record_type, None)
            
            if self._compare_records(old_record, new_record):
                new_records.append({
                    'type': record_type,
                    'old_record': old_record,
                    'new_record': new_record
                })
                logger.info(f"New {record_type} record: {new_record.holder} - {new_record.value}")
        
        return new_records
    
    async def send_record_notification(self, new_records: list):
        """Send Discord notification for new records."""
        if not new_records:
            return
        
        # Get the announce channel
        try:
            channel = self.bot.get_channel(settings.ANNOUNCE_CHANNEL_ID)
            if not channel:
                logger.error(f"Could not find announce channel {settings.ANNOUNCE_CHANNEL_ID}")
                return
            
            for record_info in new_records:
                record_type = record_info['type']
                new_record = record_info['new_record']
                old_record = record_info['old_record']
                
                # Create embed for the new record
                embed = discord.Embed(
                    title="🏆 NEW RECORD BROKEN!",
                    color=0xFFD700,  # Gold
                    timestamp=datetime.now()
                )
                
                # Add record details
                stat_emojis = {
                    'points': '🏀',
                    'rebounds': '📊', 
                    'assists': '🎯',
                    'steals': '🦹',
                    'blocks': '🛡️',
                    'threes_made': '🎯',
                    'fg_percent': '🎯',
                    'threep_percent': '🎯'
                }
                
                stat_units = {
                    'points': 'pts',
                    'rebounds': 'reb',
                    'assists': 'ast', 
                    'steals': 'stl',
                    'blocks': 'blk',
                    'threes_made': '3PM',
                    'fg_percent': '%',
                    'threep_percent': '%'
                }
                
                emoji = stat_emojis.get(record_type, '🏆')
                unit = stat_units.get(record_type, '')
                
                embed.add_field(
                    name=f"{emoji} {record_type.title()} Record",
                    value=f"**{new_record.value:.1f}{unit}** by **{new_record.holder}**\n"
                          f"Game: {new_record.game}\n"
                          f"Date: {new_record.date}\n"
                          + (f"[View Game]({new_record.game_url})" if hasattr(new_record, 'game_url') and new_record.game_url else ""),
                    inline=False
                )
                
                # Add previous record if it exists
                if old_record:
                    embed.add_field(
                        name="Previous Record",
                        value=f"**{old_record.value:.1f}{unit}** by **{old_record.holder}**\n"
                              f"Game: {old_record.game}\n"
                              f"Date: {old_record.date}",
                        inline=True
                    )
                
                embed.set_footer(text="2KCompLeague | Record Monitor")
                
                await channel.send(embed=embed)
                logger.info(f"Sent notification for new {record_type} record")
                
        except Exception as e:
            logger.error(f"Failed to send record notification: {e}")
    
    async def monitor_records(self):
        """Main monitoring loop."""
        logger.info("Starting record monitoring...")
        
        # Load previous records
        self.previous_records = await self.load_previous_records()
        
        while True:
            try:
                # Import here to avoid circular imports
                from .records import compute_single_game_records, resolve_record_names
                
                # Compute current records
                current_records = await compute_single_game_records(self.http_client)
                if current_records:
                    # Resolve names
                    current_records = await resolve_record_names(self.http_client, current_records)
                    
                    # Check for new records
                    new_records = await self.check_for_new_records(current_records)
                    
                    # Send notifications if there are new records
                    if new_records:
                        await self.send_record_notification(new_records)
                    
                    # Save current records as previous for next check
                    await self.save_current_records(current_records)
                    self.previous_records = current_records
                
                # Wait before next check (check every 30 minutes)
                await asyncio.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logger.error(f"Error in record monitoring: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying


async def start_record_monitor(bot: discord.ext.commands.Bot, http_client: HTTPClient):
    """Start the record monitoring system."""
    monitor = RecordMonitor(bot, http_client)
    asyncio.create_task(monitor.monitor_records())
    logger.info("Record monitor started")
