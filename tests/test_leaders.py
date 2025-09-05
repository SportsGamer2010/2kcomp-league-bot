"""Unit tests for leaders functionality."""

from unittest.mock import MagicMock, patch

import pytest

from core.http import HTTPClient
from core.leaders import (
    _stable_sort_leaders,
    format_leaders_embed,
    leaders_changed,
    top_n_career_leaders,
    top_n_season_leaders,
)
from core.types import LeaderEntry, LeadersData, PlayerStats


class TestStableSortLeaders:
    """Test _stable_sort_leaders function."""

    def test_sort_leaders_descending(self):
        """Test sorting leaders in descending order."""

        players = [
            PlayerStats(id=1, name="Player1", points=25.0),
            PlayerStats(id=2, name="Player2", points=30.0),
            PlayerStats(id=3, name="Player3", points=20.0),
        ]

        result = _stable_sort_leaders(players, "points")

        assert len(result) == 3
        assert result[0][0] == "Player2"  # Highest value first
        assert result[0][1] == 30.0
        assert result[1][0] == "Player1"
        assert result[1][1] == 25.0
        assert result[2][0] == "Player3"
        assert result[2][1] == 20.0

    def test_sort_leaders_with_ties(self):
        """Test sorting leaders with tied values (should sort by name)."""

        players = [
            PlayerStats(id=1, name="Charlie", points=25.0),
            PlayerStats(id=2, name="Alice", points=25.0),
            PlayerStats(id=3, name="Bob", points=25.0),
        ]

        result = _stable_sort_leaders(players, "points")

        assert len(result) == 3
        # Should sort by name alphabetically when values are tied
        assert result[0][0] == "Alice"
        assert result[1][0] == "Bob"
        assert result[2][0] == "Charlie"

    def test_sort_leaders_empty_list(self):
        """Test sorting empty list."""
        result = _stable_sort_leaders([], "points")
        assert result == []

    def test_sort_leaders_single_entry(self):
        """Test sorting single entry."""

        players = [PlayerStats(id=1, name="Player1", points=25.0)]
        result = _stable_sort_leaders(players, "points")

        assert len(result) == 1
        assert result[0][0] == "Player1"
        assert result[0][1] == 25.0


class TestTopNSeasonLeaders:
    """Test top_n_season_leaders function."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        client = MagicMock(spec=HTTPClient)
        return client

    @patch("core.leaders.fetch_players_for_season")
    @patch("core.leaders.settings")
    async def test_top_n_season_leaders_success(
        self, mock_settings, mock_fetch_players, mock_http_client
    ):
        """Test successful season leaders computation."""

        mock_settings.SPORTSPRESS_BASE = "https://example.com"
        mock_settings.leaders_endpoint = "/players?league=test"

        # Mock the fetched players
        mock_players = [
            PlayerStats(id=1, name="Player1", points=55.0, rebounds=18.0),
            PlayerStats(id=2, name="Player2", points=20.0, rebounds=12.0),
        ]
        mock_fetch_players.return_value = mock_players

        result = await top_n_season_leaders(mock_http_client, n=2)

        # Verify results
        assert result.points is not None
        assert len(result.points) == 2

        # Player1 should be first (55 points)
        assert result.points[0].name == "Player1"
        assert result.points[0].value == 55.0

        # Player2 should be second (20 points)
        assert result.points[1].name == "Player2"
        assert result.points[1].value == 20.0

        # Check rebounds
        assert result.rebounds is not None
        assert len(result.rebounds) == 2

        # Player1 should be first in rebounds (18 total)
        assert result.rebounds[0].name == "Player1"
        assert result.rebounds[0].value == 18.0

        # Player2 should be second in rebounds (12 total)
        assert result.rebounds[1].name == "Player2"
        assert result.rebounds[1].value == 12.0

    @patch("core.leaders.fetch_players_for_season")
    @patch("core.leaders.settings")
    async def test_top_n_season_leaders_with_fetch_error(
        self, mock_settings, mock_fetch_players, mock_http_client
    ):
        """Test season leaders computation when fetch_players_for_season fails."""
        mock_settings.SPORTSPRESS_BASE = "https://example.com"
        mock_settings.leaders_endpoint = "/players?league=test"
        mock_fetch_players.side_effect = Exception("API Error")

        result = await top_n_season_leaders(mock_http_client, n=2)

        # Should return empty LeadersData on error
        assert isinstance(result, LeadersData)
        assert result.points == []
        assert result.rebounds == []


class TestTopNCareerLeaders:
    """Test top_n_career_leaders function."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        client = MagicMock(spec=HTTPClient)
        return client

    @patch("core.leaders.fetch_all_players_seasons")
    @patch("core.leaders.aggregate_player_stats")
    @patch("core.leaders.settings")
    async def test_top_n_career_leaders_success(
        self, mock_settings, mock_aggregate, mock_fetch_all, mock_http_client
    ):
        """Test successful career leaders computation."""

        mock_settings.SPORTSPRESS_BASE = "https://example.com"

        # Mock the aggregated players data
        mock_aggregated_players = {
            "Player1": PlayerStats(id=1, name="Player1", points=55.0, rebounds=18.0)
        }
        mock_aggregate.return_value = mock_aggregated_players

        # Mock the fetch function
        mock_fetch_all.return_value = {}  # Not used directly in the test

        result = await top_n_career_leaders(
            mock_http_client,
            season_queries=["/players?league=2023", "/players?league=2024"],
            n=1,
        )

        # Verify results - should aggregate across all seasons
        assert result.points is not None
        assert len(result.points) == 1

        # Player1 should have 55 total career points
        assert result.points[0].name == "Player1"
        assert result.points[0].value == 55.0


class TestLeadersChanged:
    """Test leaders_changed function."""

    def test_leaders_changed_with_changes(self):
        """Test detecting when leaders have changed."""
        current = LeadersData(
            points=[
                LeaderEntry(name="Player1", value=55.0),
                LeaderEntry(name="Player2", value=20.0),
            ],
            rebounds=[
                LeaderEntry(name="Player2", value=12.0),
                LeaderEntry(name="Player1", value=18.0),
            ],
        )

        previous = LeadersData(
            points=[
                LeaderEntry(name="Player1", value=45.0),
                LeaderEntry(name="Player2", value=20.0),
            ],
            rebounds=[
                LeaderEntry(name="Player1", value=15.0),
                LeaderEntry(name="Player2", value=12.0),
            ],
        )

        changes = leaders_changed(current, previous)

        assert changes["points"] is True  # Player1's points changed from 45 to 55
        assert changes["rebounds"] is True  # Player1's rebounds changed from 15 to 18
        assert changes["assists"] is False  # No assists data in either
        assert changes["steals"] is False  # No steals data in either
        assert changes["blocks"] is False  # No blocks data in either
        assert changes["threes_made"] is False  # No threes data in either

    def test_leaders_changed_with_no_changes(self):
        """Test when no leaders have changed."""
        current = LeadersData(
            points=[
                LeaderEntry(name="Player1", value=45.0),
                LeaderEntry(name="Player2", value=20.0),
            ]
        )

        previous = LeadersData(
            points=[
                LeaderEntry(name="Player1", value=45.0),
                LeaderEntry(name="Player2", value=20.0),
            ]
        )

        changes = leaders_changed(current, previous)

        assert changes["points"] is False  # No changes
        assert changes["assists"] is False  # No assists data in either
        assert changes["rebounds"] is False  # No rebounds data in either


class TestFormatLeadersEmbed:
    """Test format_leaders_embed function."""

    def test_format_leaders_embed_with_data(self):
        """Test formatting leaders embed with data."""
        leaders = LeadersData(
            points=[
                LeaderEntry(name="Player1", value=55.0),
                LeaderEntry(name="Player2", value=20.0),
            ],
            rebounds=[
                LeaderEntry(name="Player2", value=12.0),
                LeaderEntry(name="Player1", value=18.0),
            ],
        )

        embed = format_leaders_embed(leaders, "season")

        assert embed["title"] == "🏆 Season Leaders"
        assert embed["color"] == 0x00FF00  # Green

        # Check fields
        assert len(embed["fields"]) == 2

        # Points field
        points_field = next(f for f in embed["fields"] if f["name"] == "🏀 Points")
        assert "Player1" in points_field["value"]
        assert "55.0" in points_field["value"]
        assert "Player2" in points_field["value"]
        assert "20.0" in points_field["value"]

        # Rebounds field
        rebounds_field = next(f for f in embed["fields"] if f["name"] == "📊 Rebounds")
        assert "Player2" in rebounds_field["value"]
        assert "12.0" in rebounds_field["value"]

    def test_format_leaders_embed_career(self):
        """Test formatting leaders embed for career stats."""
        leaders = LeadersData(
            points=[
                LeaderEntry(name="Player1", value=100.0),
                LeaderEntry(name="Player2", value=75.0),
            ]
        )

        embed = format_leaders_embed(leaders, "career", "points")

        assert embed["title"] == "🏀 Career Points Leaders"
        assert "Player1" in embed["description"]
        assert "100.0" in embed["description"]
        assert "Player2" in embed["description"]
        assert "75.0" in embed["description"]

    def test_format_leaders_embed_empty_data(self):
        """Test formatting leaders embed with empty data."""
        leaders = LeadersData()

        embed = format_leaders_embed(leaders, "season")

        assert embed["title"] == "🏆 Season Leaders"
        assert len(embed["fields"]) == 0


if __name__ == "__main__":
    pytest.main([__file__])
