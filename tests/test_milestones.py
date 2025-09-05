"""Unit tests for milestone detection functionality."""

from unittest.mock import MagicMock, patch

import pytest

from core.http import HTTPClient
from core.milestones import (
    PlayerTotals,
    _format_milestone_message,
    _get_crossed_thresholds,
    detect_milestone_crossings,
    format_milestone_embed,
    get_current_season_totals,
    scan_and_detect_crossings,
    update_milestone_state,
)
from core.types import MilestoneNotification, PlayerStats


class TestPlayerTotals:
    """Test PlayerTotals dataclass."""

    def test_player_totals_creation(self):
        """Test creating a PlayerTotals instance."""
        totals = PlayerTotals(
            player_id=1, name="TestPlayer", points=100.0, assists=25.0, rebounds=50.0
        )

        assert totals.player_id == 1
        assert totals.name == "TestPlayer"
        assert totals.points == 100.0
        assert totals.assists == 25.0
        assert totals.rebounds == 50.0
        assert totals.steals == 0.0  # Default value
        assert totals.blocks == 0.0  # Default value
        assert totals.threes_made == 0.0  # Default value

    def test_player_totals_defaults(self):
        """Test PlayerTotals with default values."""
        totals = PlayerTotals(player_id=1, name="TestPlayer")

        assert totals.points == 0.0
        assert totals.assists == 0.0
        assert totals.rebounds == 0.0
        assert totals.steals == 0.0
        assert totals.blocks == 0.0
        assert totals.threes_made == 0.0


class TestGetCrossedThresholds:
    """Test _get_crossed_thresholds function."""

    def test_get_crossed_thresholds_single_crossing(self):
        """Test detecting a single threshold crossing."""
        thresholds = [100, 250, 500, 1000]
        previous = 95.0
        current = 150.0

        result = _get_crossed_thresholds(previous, current, thresholds)

        assert result == [100]

    def test_get_crossed_thresholds_multiple_crossings(self):
        """Test detecting multiple threshold crossings."""
        thresholds = [100, 250, 500, 1000]
        previous = 95.0
        current = 300.0

        result = _get_crossed_thresholds(previous, current, thresholds)

        assert result == [100, 250]

    def test_get_crossed_thresholds_no_crossings(self):
        """Test when no thresholds are crossed."""
        thresholds = [100, 250, 500, 1000]
        previous = 50.0
        current = 75.0

        result = _get_crossed_thresholds(previous, current, thresholds)

        assert result == []

    def test_get_crossed_thresholds_exact_match(self):
        """Test when current total exactly matches a threshold."""
        thresholds = [100, 250, 500, 1000]
        previous = 95.0
        current = 100.0

        result = _get_crossed_thresholds(previous, current, thresholds)

        assert result == [100]

    def test_get_crossed_thresholds_decreasing_totals(self):
        """Test when totals decrease (should not detect crossings)."""
        thresholds = [100, 250, 500, 1000]
        previous = 300.0
        current = 200.0

        result = _get_crossed_thresholds(previous, current, thresholds)

        assert result == []


class TestFormatMilestoneMessage:
    """Test _format_milestone_message function."""

    def test_format_milestone_message_points(self):
        """Test formatting points milestone message."""
        message = _format_milestone_message("Player1", "points", 1000, 1050.0)

        assert "🏀" in message
        assert "Player1" in message
        assert "1,000" in message  # Message uses comma formatting
        assert "Points" in message
        assert "1050.0" in message

    def test_format_milestone_message_assists(self):
        """Test formatting assists milestone message."""
        message = _format_milestone_message("Player2", "assists", 250, 275.0)

        assert "🎯" in message
        assert "Player2" in message
        assert "250" in message
        assert "Assists" in message
        assert "275.0" in message

    def test_format_milestone_message_unknown_stat(self):
        """Test formatting message for unknown stat."""
        message = _format_milestone_message("Player3", "unknown_stat", 500, 550.0)

        assert "🏆" in message  # Default emoji
        assert "Unknown Stat" in message


class TestGetCurrentSeasonTotals:
    """Test get_current_season_totals function."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        client = MagicMock(spec=HTTPClient)
        return client

    @patch("core.milestones.settings")
    @patch("core.milestones.fetch_players_for_season")
    async def test_get_current_season_totals_success(
        self, mock_fetch_players, mock_settings, mock_http_client
    ):
        """Test successful fetching of season totals."""
        mock_settings.SPORTSPRESS_BASE = "https://example.com"
        mock_settings.leaders_endpoint = "/players?league=test"

        # Mock the fetched players
        mock_players = [
            PlayerStats(
                id=1, name="Player1", points=150.0, assists=25.0, rebounds=50.0
            ),
            PlayerStats(
                id=2, name="Player2", points=300.0, assists=50.0, rebounds=100.0
            ),
        ]
        mock_fetch_players.return_value = mock_players

        result = await get_current_season_totals(mock_http_client)

        assert len(result) == 2

        # Check Player1
        player1 = result[1]
        assert player1.name == "Player1"
        assert player1.points == 150.0
        assert player1.assists == 25.0
        assert player1.rebounds == 50.0

        # Check Player2
        player2 = result[2]
        assert player2.name == "Player2"
        assert player2.points == 300.0
        assert player2.assists == 50.0
        assert player2.rebounds == 100.0

    @patch("core.milestones.settings")
    @patch("core.milestones.fetch_players_for_season")
    async def test_get_current_season_totals_no_endpoint(
        self, mock_fetch_players, mock_settings, mock_http_client
    ):
        """Test when no leaders endpoint is configured."""
        mock_settings.SPORTSPRESS_BASE = "https://example.com"
        mock_settings.leaders_endpoint = None

        result = await get_current_season_totals(mock_http_client)

        assert result == {}
        mock_fetch_players.assert_not_called()

    @patch("core.milestones.settings")
    @patch("core.milestones.fetch_players_for_season")
    async def test_get_current_season_totals_fetch_error(
        self, mock_fetch_players, mock_settings, mock_http_client
    ):
        """Test when fetch_players_for_season fails."""
        mock_settings.SPORTSPRESS_BASE = "https://example.com"
        mock_settings.leaders_endpoint = "/players?league=test"
        mock_fetch_players.side_effect = Exception("API Error")

        result = await get_current_season_totals(mock_http_client)

        assert result == {}


class TestDetectMilestoneCrossings:
    """Test detect_milestone_crossings function."""

    def test_detect_milestone_crossings_new_crossings(self):
        """Test detecting new milestone crossings."""
        current_totals = {
            1: PlayerTotals(player_id=1, name="Player1", points=150.0, assists=50.0),
            2: PlayerTotals(player_id=2, name="Player2", points=300.0, rebounds=100.0),
        }

        last_totals = {
            "1": {"points": 95.0, "assists": 20.0},
            "2": {"points": 250.0, "rebounds": 75.0},
        }

        milestones_sent = {
            "1": {"points": [100]},  # 100 already sent
            "2": {"points": [250]},  # 250 already sent
        }

        notifications = detect_milestone_crossings(
            current_totals, last_totals, milestones_sent
        )

        assert len(notifications) == 2

        # Player1 should have 150 points crossing (100 already sent, so no notification)
        # Player1 should have 50 assists crossing (new - 50 is in thresholds)
        # Player2 should have 300 points crossing (250 already sent, so no notification)
        # Player2 should have 100 rebounds crossing (new)

        # Check that notifications are for new crossings only
        notification_stats = [n.stat for n in notifications]
        assert "assists" in notification_stats
        assert "rebounds" in notification_stats

    def test_detect_milestone_crossings_no_crossings(self):
        """Test when no milestones are crossed."""
        current_totals = {
            1: PlayerTotals(player_id=1, name="Player1", points=95.0, assists=20.0)
        }

        last_totals = {"1": {"points": 90.0, "assists": 18.0}}

        milestones_sent = {"1": {"points": [100], "assists": [25]}}

        notifications = detect_milestone_crossings(
            current_totals, last_totals, milestones_sent
        )

        assert len(notifications) == 0

    def test_detect_milestone_crossings_first_time_player(self):
        """Test milestone detection for a player with no previous data."""
        current_totals = {
            1: PlayerTotals(player_id=1, name="Player1", points=150.0, assists=50.0)
        }

        last_totals = {}  # No previous data
        milestones_sent = {}  # No previous milestones

        notifications = detect_milestone_crossings(
            current_totals, last_totals, milestones_sent
        )

        assert len(notifications) == 2  # 100 points and 50 assists
        assert any(n.stat == "points" and n.threshold == 100 for n in notifications)
        assert any(n.stat == "assists" and n.threshold == 50 for n in notifications)


class TestUpdateMilestoneState:
    """Test update_milestone_state function."""

    def test_update_milestone_state_new_player(self):
        """Test updating state with a new player."""
        current_totals = {
            1: PlayerTotals(player_id=1, name="Player1", points=150.0, assists=25.0)
        }

        notifications = [
            MilestoneNotification(
                player="Player1",
                stat="points",
                value=150.0,
                threshold=100,
                message="Test message",
            )
        ]

        last_totals = {}
        milestones_sent = {}

        updated_last_totals, updated_milestones_sent = update_milestone_state(
            current_totals, notifications, last_totals, milestones_sent
        )

        # Check that last totals were updated
        assert "1" in updated_last_totals
        assert updated_last_totals["1"]["points"] == 150.0
        assert updated_last_totals["1"]["assists"] == 25.0

        # Check that milestones sent were updated
        assert "Player1" in updated_milestones_sent
        assert updated_milestones_sent["Player1"]["points"] == [100]

    def test_update_milestone_state_existing_player(self):
        """Test updating state for an existing player."""
        current_totals = {
            1: PlayerTotals(player_id=1, name="Player1", points=200.0, assists=30.0)
        }

        notifications = [
            MilestoneNotification(
                player="Player1",
                stat="points",
                value=200.0,
                threshold=200,
                message="Test message",
            )
        ]

        last_totals = {"1": {"points": 150.0, "assists": 25.0}}
        milestones_sent = {"Player1": {"points": [100]}}

        updated_last_totals, updated_milestones_sent = update_milestone_state(
            current_totals, notifications, last_totals, milestones_sent
        )

        # Check that last totals were updated
        assert updated_last_totals["1"]["points"] == 200.0
        assert updated_last_totals["1"]["assists"] == 30.0

        # Check that milestones sent were updated
        assert updated_milestones_sent["Player1"]["points"] == [100, 200]


class TestFormatMilestoneEmbed:
    """Test format_milestone_embed function."""

    def test_format_milestone_embed_with_notifications(self):
        """Test formatting embed with milestone notifications."""
        notifications = [
            MilestoneNotification(
                player="Player1",
                stat="points",
                value=150.0,
                threshold=100,
                message="Test message 1",
            ),
            MilestoneNotification(
                player="Player2",
                stat="assists",
                value=30.0,
                threshold=25,
                message="Test message 2",
            ),
        ]

        embed = format_milestone_embed(notifications)

        assert embed["title"] == "🏆 Milestone Achievements"
        assert embed["color"] == 0xFFD700
        assert (
            "Players have reached new statistical milestones!" in embed["description"]
        )
        assert len(embed["fields"]) == 2

        # Check points field
        points_field = next(f for f in embed["fields"] if "Points" in f["name"])
        assert "🏀" in points_field["name"]
        assert "Player1" in points_field["value"]
        assert "100" in points_field["value"]

        # Check assists field
        assists_field = next(f for f in embed["fields"] if "Assists" in f["name"])
        assert "🎯" in assists_field["name"]
        assert "Player2" in assists_field["value"]
        assert "25" in assists_field["value"]

    def test_format_milestone_embed_no_notifications(self):
        """Test formatting embed with no notifications."""
        embed = format_milestone_embed([])

        assert embed is None


class TestScanAndDetectCrossings:
    """Test scan_and_detect_crossings function."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        client = MagicMock(spec=HTTPClient)
        return client

    @patch("core.milestones.get_current_season_totals")
    @patch("core.milestones.detect_milestone_crossings")
    @patch("core.milestones.update_milestone_state")
    async def test_scan_and_detect_crossings_success(
        self,
        mock_update_state,
        mock_detect_crossings,
        mock_get_totals,
        mock_http_client,
    ):
        """Test successful milestone scanning."""
        # Mock current totals
        mock_totals = {1: PlayerTotals(player_id=1, name="Player1", points=150.0)}
        mock_get_totals.return_value = mock_totals

        # Mock milestone detection
        mock_notifications = [
            MilestoneNotification(
                player="Player1",
                stat="points",
                value=150.0,
                threshold=100,
                message="Test message",
            )
        ]
        mock_detect_crossings.return_value = mock_notifications

        # Mock state update
        mock_updated_totals = {"1": {"points": 150.0}}
        mock_updated_milestones = {"Player1": {"points": [100]}}
        mock_update_state.return_value = (mock_updated_totals, mock_updated_milestones)

        last_totals = {"1": {"points": 95.0}}
        milestones_sent = {}

        notifications, updated_totals, updated_milestones = (
            await scan_and_detect_crossings(
                mock_http_client, last_totals, milestones_sent
            )
        )

        assert len(notifications) == 1
        assert notifications[0].player == "Player1"
        assert notifications[0].threshold == 100

        assert updated_totals == mock_updated_totals
        assert updated_milestones == mock_updated_milestones

    @patch("core.milestones.get_current_season_totals")
    async def test_scan_and_detect_crossings_no_totals(
        self, mock_get_totals, mock_http_client
    ):
        """Test milestone scanning when no totals are found."""
        mock_get_totals.return_value = {}

        last_totals = {"1": {"points": 95.0}}
        milestones_sent = {}

        notifications, updated_totals, updated_milestones = (
            await scan_and_detect_crossings(
                mock_http_client, last_totals, milestones_sent
            )
        )

        assert len(notifications) == 0
        assert updated_totals == last_totals
        assert updated_milestones == milestones_sent

    @patch("core.milestones.get_current_season_totals")
    async def test_scan_and_detect_crossings_error(
        self, mock_get_totals, mock_http_client
    ):
        """Test milestone scanning when an error occurs."""
        mock_get_totals.side_effect = Exception("API Error")

        last_totals = {"1": {"points": 95.0}}
        milestones_sent = {}

        notifications, updated_totals, updated_milestones = (
            await scan_and_detect_crossings(
                mock_http_client, last_totals, milestones_sent
            )
        )

        assert len(notifications) == 0
        assert updated_totals == last_totals
        assert updated_milestones == milestones_sent


if __name__ == "__main__":
    pytest.main([__file__])
