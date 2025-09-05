"""State persistence and management for the Discord bot."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .config import settings
from .types import BotState, LeadersData

logger = logging.getLogger(__name__)


class StateManager:
    """Manages persistent bot state with atomic file operations."""

    def __init__(self, state_path: Optional[str] = None):
        self.state_path = Path(state_path or settings.STATE_PATH)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> BotState:
        """
        Load bot state from file.

        Returns:
            BotState instance, or default if file doesn't exist
        """
        try:
            if not self.state_path.exists():
                logger.info("No existing state file found, creating default state")
                return BotState()

            with open(self.state_path, encoding="utf-8") as f:
                data = json.load(f)

            # Convert to BotState
            state = BotState(**data)
            logger.info(f"Loaded state from {self.state_path}")
            return state

        except Exception as e:
            logger.error(f"Failed to load state from {self.state_path}: {e}")
            logger.info("Creating default state due to load failure")
            return BotState()

    def save_state(self, state: BotState) -> bool:
        """
        Save bot state to file with atomic write.

        Args:
            state: BotState instance to save

        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Convert to dict for JSON serialization
            state_dict = state.dict()

            # Add metadata
            state_dict["_metadata"] = {
                "last_updated": datetime.utcnow().isoformat(),
                "version": "1.0",
            }

            # Write to temporary file first
            temp_path = self.state_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)

            # Atomic move
            temp_path.replace(self.state_path)

            logger.info(f"State saved to {self.state_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save state to {self.state_path}: {e}")
            return False

    def update_leaders(self, leaders: LeadersData) -> bool:
        """
        Update the last leaders in state.

        Args:
            leaders: New leaders data

        Returns:
            True if update was successful
        """
        try:
            state = self.load_state()
            state.last_leaders = leaders
            return self.save_state(state)
        except Exception as e:
            logger.error(f"Failed to update leaders in state: {e}")
            return False

    def update_milestones(
        self,
        last_totals: Dict[str, Dict[str, float]],
        milestones_sent: Dict[str, Dict[str, list]],
    ) -> bool:
        """
        Update milestone tracking in state.

        Args:
            last_totals: Updated player totals
            milestones_sent: Updated sent milestones tracking

        Returns:
            True if update was successful
        """
        try:
            state = self.load_state()
            state.last_totals = last_totals
            state.milestones_sent = milestones_sent
            return self.save_state(state)
        except Exception as e:
            logger.error(f"Failed to update milestones in state: {e}")
            return False

    def get_last_leaders(self) -> LeadersData:
        """
        Get the last known leaders from state.

        Returns:
            LeadersData instance
        """
        state = self.load_state()
        return state.last_leaders

    def get_milestone_state(
        self,
    ) -> tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, list]]]:
        """
        Get milestone tracking state.

        Returns:
            Tuple of (last_totals, milestones_sent)
        """
        state = self.load_state()
        return state.last_totals, state.milestones_sent

    def backup_state(self, backup_dir: Optional[str] = None) -> bool:
        """
        Create a backup of the current state file.

        Args:
            backup_dir: Directory for backup (defaults to state file directory)

        Returns:
            True if backup was successful
        """
        try:
            if not self.state_path.exists():
                logger.warning("No state file to backup")
                return False

            backup_dir = Path(backup_dir or self.state_path.parent)
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"state_backup_{timestamp}.json"

            # Copy current state to backup
            with open(self.state_path, encoding="utf-8") as src:
                with open(backup_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())

            logger.info(f"State backed up to {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to backup state: {e}")
            return False

    def cleanup_old_backups(
        self, backup_dir: Optional[str] = None, keep_count: int = 5
    ) -> bool:
        """
        Clean up old backup files, keeping only the most recent ones.

        Args:
            backup_dir: Directory containing backups
            keep_count: Number of recent backups to keep

        Returns:
            True if cleanup was successful
        """
        try:
            backup_dir = Path(backup_dir or self.state_path.parent)
            if not backup_dir.exists():
                return True

            # Find all backup files
            backup_files = list(backup_dir.glob("state_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove old backups
            for backup_file in backup_files[keep_count:]:
                backup_file.unlink()
                logger.debug(f"Removed old backup: {backup_file}")

            logger.info(
                f"Cleaned up old backups, keeping {min(keep_count, len(backup_files))} recent ones"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return False


# Global state manager instance
state_manager = StateManager()


def load_bot_state() -> BotState:
    """
    Load the bot state using the global state manager.

    Returns:
        BotState instance
    """
    return state_manager.load_state()


def save_bot_state(state: BotState) -> bool:
    """
    Save the bot state using the global state manager.

    Args:
        state: BotState instance to save

    Returns:
        True if save was successful
    """
    return state_manager.save_state(state)


def update_leaders_in_state(leaders: LeadersData) -> bool:
    """
    Update leaders in the persistent state.

    Args:
        leaders: New leaders data

    Returns:
        True if update was successful
    """
    return state_manager.update_leaders(leaders)


def update_milestones_in_state(
    last_totals: Dict[str, Dict[str, float]],
    milestones_sent: Dict[str, Dict[str, list]],
) -> bool:
    """
    Update milestone tracking in the persistent state.

    Args:
        last_totals: Updated player totals
        milestones_sent: Updated sent milestones tracking

    Returns:
        True if update was successful
    """
    return state_manager.update_milestones(last_totals, milestones_sent)


def get_last_leaders_from_state() -> LeadersData:
    """
    Get the last known leaders from persistent state.

    Returns:
        LeadersData instance
    """
    return state_manager.get_last_leaders()


def get_milestone_state_from_persistence() -> (
    tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, list]]]
):
    """
    Get milestone tracking state from persistence.

    Returns:
        Tuple of (last_totals, milestones_sent)
    """
    return state_manager.get_milestone_state()


def create_state_backup() -> bool:
    """
    Create a backup of the current state.

    Returns:
        True if backup was successful
    """
    return state_manager.backup_state()


def cleanup_state_backups() -> bool:
    """
    Clean up old state backups.

    Returns:
        True if cleanup was successful
    """
    return state_manager.cleanup_old_backups()
