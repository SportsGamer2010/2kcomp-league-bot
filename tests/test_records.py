"""Unit tests for single game records functionality."""

from unittest.mock import MagicMock, patch

import pytest

from core.http import HTTPClient
from core.records import (
    RecordCandidate,
    _try_update_max,
    compute_single_game_records,
    format_records_embed,
    load_records_seed,
    records_changed,
)
from core.types import EventPlayerRow, RecordsData, SingleGameRecord


class TestRecordCandidate:
    """Test RecordCandidate dataclass."""

    def test_record_candidate_creation(self):
        """Test creating a RecordCandidate instance."""
        candidate = RecordCandidate(
            stat="points",
            value=45.0,
            holder="TestPlayer",
            game="Team A vs Team B",
            date="2024-01-15",
        )

        assert candidate.stat == "points"
        assert candidate.value == 45.0
        assert candidate.holder == "TestPlayer"
        assert candidate.game == "Team A vs Team B"
        assert candidate.date == "2024-01-15"


class TestTryUpdateMax:
    """Test _try_update_max function."""

    def test_update_max_with_none_current(self):
        """Test updating when current record is None."""
        candidate = RecordCandidate(
            stat="points", value=30.0, holder="Player1", game="Game1", date="2024-01-01"
        )

        result = _try_update_max(None, candidate)

        assert result is not None
        assert result.stat == "points"
        assert result.value == 30.0
        assert result.holder == "Player1"

    def test_update_max_with_higher_value(self):
        """Test updating when candidate has higher value."""
        current = SingleGameRecord(
            stat="points", value=25.0, holder="Player1", game="Game1", date="2024-01-01"
        )

        candidate = RecordCandidate(
            stat="points", value=35.0, holder="Player2", game="Game2", date="2024-01-02"
        )

        result = _try_update_max(current, candidate)

        assert result is not None
        assert result.value == 35.0
        assert result.holder == "Player2"
        assert result.game == "Game2"

    def test_no_update_with_lower_value(self):
        """Test no update when candidate has lower value."""
        current = SingleGameRecord(
            stat="points", value=40.0, holder="Player1", game="Game1", date="2024-01-01"
        )

        candidate = RecordCandidate(
            stat="points", value=30.0, holder="Player2", game="Game2", date="2024-01-02"
        )

        result = _try_update_max(current, candidate)

        assert result is current  # Should return same object
        assert result.value == 40.0
        assert result.holder == "Player1"

    def test_no_update_with_equal_value(self):
        """Test no update when candidate has equal value."""
        current = SingleGameRecord(
            stat="points", value=30.0, holder="Player1", game="Game1", date="2024-01-01"
        )

        candidate = RecordCandidate(
            stat="points", value=30.0, holder="Player2", game="Game2", date="2024-01-02"
        )

        result = _try_update_max(current, candidate)

        assert result is current  # Should return same object
        assert result.value == 30.0
        assert result.holder == "Player1"


class TestComputeSingleGameRecords:
    """Test compute_single_game_records function."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        client = MagicMock(spec=HTTPClient)
        return client

    @pytest.fixture
    def sample_events(self):
        """Sample events data for testing."""
        return [
            {
                "id": 1,
                "date": "2024-01-15",
                "title": "Team A vs Team B",
                "results": {
                    "boxscore": [
                        {
                            "name": "Player1",
                            "team": "Team A",
                            "opp": "Team B",
                            "game": "Team A vs Team B",
                            "date": "2024-01-15",
                            "pts": 45.0,
                            "rebtwo": 12.0,
                            "ast": 8.0,
                            "stl": 3.0,
                            "blk": 2.0,
                            "threepm": 7.0,
                            "fgm": 18.0,
                            "fga": 25.0,
                            "threepa": 12.0,
                            "fg_percent": 72.0,
                            "threep_percent": 58.3,
                        },
                        {
                            "name": "Player2",
                            "team": "Team B",
                            "opp": "Team A",
                            "game": "Team A vs Team B",
                            "date": "2024-01-15",
                            "pts": 38.0,
                            "rebtwo": 15.0,
                            "ast": 12.0,
                            "stl": 5.0,
                            "blk": 1.0,
                            "threepm": 6.0,
                            "fgm": 15.0,
                            "fga": 28.0,
                            "threepa": 10.0,
                            "fg_percent": 53.6,
                            "threep_percent": 60.0,
                        },
                    ]
                },
            },
            {
                "id": 2,
                "date": "2024-01-16",
                "title": "Team C vs Team D",
                "results": {
                    "boxscore": [
                        {
                            "name": "Player3",
                            "team": "Team C",
                            "opp": "Team D",
                            "game": "Team C vs Team D",
                            "date": "2024-01-16",
                            "pts": 42.0,
                            "rebtwo": 10.0,
                            "ast": 6.0,
                            "stl": 2.0,
                            "blk": 1.0,
                            "threepm": 5.0,
                            "fgm": 16.0,
                            "fga": 22.0,
                            "threepa": 8.0,
                            "fg_percent": 72.7,
                            "threep_percent": 62.5,
                        }
                    ]
                },
            },
        ]

    @patch("core.records.fetch_events")
    @patch("core.records._extract_rows_from_event")
    @patch("core.records.settings")
    async def test_compute_records_success(
        self,
        mock_settings,
        mock_extract_rows,
        mock_fetch_events,
        mock_http_client,
        sample_events,
    ):
        """Test successful records computation."""
        # Setup mocks
        mock_settings.SPORTSPRESS_BASE = "https://example.com"
        mock_settings.MIN_FGA_FOR_FG_PERCENT = 10
        mock_settings.MIN_3PA_FOR_3P_PERCENT = 5

        mock_fetch_events.return_value = sample_events

        # Mock the extracted rows
        mock_rows = [
            EventPlayerRow(
                name="Player1",
                team="Team A",
                opp="Team B",
                game="Team A vs Team B",
                date="2024-01-15",
                points=45.0,
                rebounds=12.0,
                assists=8.0,
                steals=3.0,
                blocks=2.0,
                threes_made=7.0,
                fgm=18.0,
                fga=25.0,
                threepm=7.0,
                threepa=12.0,
                fg_percent=72.0,
                threep_percent=58.3,
            ),
            EventPlayerRow(
                name="Player2",
                team="Team B",
                opp="Team A",
                game="Team A vs Team B",
                date="2024-01-15",
                points=38.0,
                rebounds=15.0,
                assists=12.0,
                steals=5.0,
                blocks=1.0,
                threes_made=6.0,
                fgm=15.0,
                fga=28.0,
                threepm=6.0,
                threepa=10.0,
                fg_percent=53.6,
                threep_percent=60.0,
            ),
        ]

        mock_extract_rows.side_effect = [mock_rows]

        # Execute function
        result = await compute_single_game_records(mock_http_client)

        # Verify results
        assert result.points is not None
        assert result.points.value == 45.0
        assert result.points.holder == "Player1"

        assert result.rebounds is not None
        assert result.rebounds.value == 15.0
        assert result.rebounds.holder == "Player2"

        assert result.assists is not None
        assert result.assists.value == 12.0
        assert result.assists.holder == "Player2"

        assert result.steals is not None
        assert result.steals.value == 5.0
        assert result.steals.holder == "Player2"

        assert result.blocks is not None
        assert result.blocks.value == 2.0
        assert result.blocks.holder == "Player1"

        assert result.threes_made is not None
        assert result.threes_made.value == 7.0
        assert result.threes_made.holder == "Player1"

        # Percentage records should be set due to minimum attempts
        assert result.fg_percent is not None
        assert result.fg_percent.value == 72.0
        assert result.fg_percent.holder == "Player1"

        assert result.threep_percent is not None
        assert result.threep_percent.value == 60.0
        assert result.threep_percent.holder == "Player2"

    @patch("core.records.fetch_events")
    @patch("core.records.settings")
    async def test_compute_records_with_fetch_error(
        self, mock_settings, mock_fetch_events, mock_http_client
    ):
        """Test records computation when fetch_events fails."""
        mock_settings.SPORTSPRESS_BASE = "https://example.com"
        mock_fetch_events.side_effect = Exception("API Error")

        result = await compute_single_game_records(mock_http_client)

        # Should return empty RecordsData on error
        assert isinstance(result, RecordsData)
        assert result.points is None
        assert result.rebounds is None

    @patch("core.records.fetch_events")
    @patch("core.records._extract_rows_from_event")
    @patch("core.records.settings")
    async def test_compute_records_with_event_processing_error(
        self,
        mock_settings,
        mock_extract_rows,
        mock_fetch_events,
        mock_http_client,
        sample_events,
    ):
        """Test records computation when individual event processing fails."""
        mock_settings.SPORTSPRESS_BASE = "https://example.com"
        mock_settings.MIN_FGA_FOR_FG_PERCENT = 10
        mock_settings.MIN_3PA_FOR_3P_PERCENT = 5

        mock_fetch_events.return_value = sample_events

        # First event fails, second succeeds
        mock_extract_rows.side_effect = [
            Exception("Event processing error"),
            [
                EventPlayerRow(
                    name="Player2",
                    team="Team B",
                    opp="Team A",
                    game="Team A vs Team B",
                    date="2024-01-15",
                    points=38.0,
                    rebounds=15.0,
                    assists=12.0,
                    steals=5.0,
                    blocks=1.0,
                    threes_made=6.0,
                    fgm=15.0,
                    fga=28.0,
                    threepm=6.0,
                    threepa=10.0,
                    fg_percent=53.6,
                    threep_percent=60.0,
                )
            ],
        ]

        result = await compute_single_game_records(mock_http_client)

        # Should still process successful events
        assert result.points is not None
        assert result.points.value == 38.0
        assert result.points.holder == "Player2"

    @patch("core.records.fetch_events")
    @patch("core.records._extract_rows_from_event")
    @patch("core.records.settings")
    async def test_compute_records_percentage_minimums(
        self, mock_settings, mock_extract_rows, mock_fetch_events, mock_http_client
    ):
        """Test percentage records respect minimum attempt requirements."""
        mock_settings.SPORTSPRESS_BASE = "https://example.com"
        mock_settings.MIN_FGA_FOR_FG_PERCENT = 10
        mock_settings.MIN_3PA_FOR_3P_PERCENT = 5

        mock_fetch_events.return_value = [{"id": 1, "results": {"boxscore": []}}]

        # Player with insufficient attempts
        mock_rows = [
            EventPlayerRow(
                name="Player1",
                team="Team A",
                opp="Team B",
                game="Game1",
                date="2024-01-15",
                points=20.0,
                fgm=4.0,
                fga=8.0,  # Below 10 minimum
                threepm=1.0,
                threepa=2.0,  # Below 5 minimum
                fg_percent=50.0,
                threep_percent=50.0,
            )
        ]

        mock_extract_rows.return_value = mock_rows

        result = await compute_single_game_records(mock_http_client)

        # Percentage records should not be set due to insufficient attempts
        assert result.fg_percent is None
        assert result.threep_percent is None

        # Other records should still be set
        assert result.points is not None
        assert result.points.value == 20.0


class TestFormatRecordsEmbed:
    """Test format_records_embed function."""

    def test_format_records_embed_with_all_records(self):
        """Test formatting embed with all records present."""
        records = RecordsData(
            points=SingleGameRecord(
                stat="points",
                value=45.0,
                holder="Player1",
                game="Game1",
                date="2024-01-15",
            ),
            rebounds=SingleGameRecord(
                stat="rebounds",
                value=15.0,
                holder="Player2",
                game="Game2",
                date="2024-01-16",
            ),
            assists=SingleGameRecord(
                stat="assists",
                value=12.0,
                holder="Player3",
                game="Game3",
                date="2024-01-17",
            ),
        )

        embed = format_records_embed(records)

        assert embed["title"] == "🏆 Single-Game Records"
        assert embed["color"] == 0xFFD700
        assert embed["description"] == "All-time single-game records in 2KCompLeague"
        assert embed["footer"]["text"] == "2KCompLeague | Auto-updated"

        # Check fields
        assert len(embed["fields"]) == 3

        # Points field
        points_field = next(f for f in embed["fields"] if f["name"] == "🏀 Points")
        assert "45.0pts" in points_field["value"]
        assert "Player1" in points_field["value"]
        assert "Game1" in points_field["value"]
        assert "2024-01-15" in points_field["value"]

        # Rebounds field
        rebounds_field = next(f for f in embed["fields"] if f["name"] == "📊 Rebounds")
        assert "15.0reb" in rebounds_field["value"]
        assert "Player2" in rebounds_field["value"]

    def test_format_records_embed_with_no_records(self):
        """Test formatting embed with no records."""
        records = RecordsData()

        embed = format_records_embed(records)

        assert embed["title"] == "🏆 Single-Game Records"
        assert len(embed["fields"]) == 0

    def test_format_records_embed_with_partial_records(self):
        """Test formatting embed with only some records."""
        records = RecordsData(
            points=SingleGameRecord(
                stat="points",
                value=45.0,
                holder="Player1",
                game="Game1",
                date="2024-01-15",
            )
        )

        embed = format_records_embed(records)

        assert len(embed["fields"]) == 1
        assert embed["fields"][0]["name"] == "🏀 Points"


class TestRecordsChanged:
    """Test records_changed function."""

    def test_records_changed_with_new_records(self):
        """Test detecting new records."""
        current = RecordsData(
            points=SingleGameRecord(
                stat="points",
                value=50.0,
                holder="Player2",
                game="Game2",
                date="2024-01-16",
            ),
            rebounds=SingleGameRecord(
                stat="rebounds",
                value=20.0,
                holder="Player3",
                game="Game3",
                date="2024-01-17",
            ),
        )

        previous = RecordsData(
            points=SingleGameRecord(
                stat="points",
                value=45.0,
                holder="Player1",
                game="Game1",
                date="2024-01-15",
            ),
            rebounds=SingleGameRecord(
                stat="rebounds",
                value=15.0,
                holder="Player2",
                game="Game2",
                date="2024-01-16",
            ),
        )

        new_records = records_changed(current, previous)

        assert len(new_records) == 2

        # Points record broken
        points_record = next(r for r in new_records if r.stat == "points")
        assert points_record.value == 50.0
        assert points_record.holder == "Player2"

        # Rebounds record broken
        rebounds_record = next(r for r in new_records if r.stat == "rebounds")
        assert rebounds_record.value == 20.0
        assert rebounds_record.holder == "Player3"

    def test_records_changed_with_no_changes(self):
        """Test when no records have changed."""
        current = RecordsData(
            points=SingleGameRecord(
                stat="points",
                value=45.0,
                holder="Player1",
                game="Game1",
                date="2024-01-15",
            )
        )

        previous = RecordsData(
            points=SingleGameRecord(
                stat="points",
                value=45.0,
                holder="Player1",
                game="Game1",
                date="2024-01-15",
            )
        )

        new_records = records_changed(current, previous)

        assert len(new_records) == 0

    def test_records_changed_with_first_time_records(self):
        """Test when records are set for the first time."""
        current = RecordsData(
            points=SingleGameRecord(
                stat="points",
                value=45.0,
                holder="Player1",
                game="Game1",
                date="2024-01-15",
            )
        )

        previous = RecordsData()  # No previous records

        new_records = records_changed(current, previous)

        assert len(new_records) == 1
        assert new_records[0].stat == "points"
        assert new_records[0].value == 45.0
        assert new_records[0].holder == "Player1"


class TestLoadRecordsSeed:
    """Test load_records_seed function."""

    @patch("core.records.settings")
    @patch("builtins.open")
    @patch("json.load")
    def test_load_records_seed_success(self, mock_json_load, mock_open, mock_settings):
        """Test successful loading of seed records."""
        mock_settings.RECORDS_SEED_PATH = "data/records_seed.json"

        seed_data = {
            "points": {
                "stat": "points",
                "value": 50.0,
                "holder": "SeedPlayer",
                "game": "SeedGame",
                "date": "2024-01-01",
            },
            "rebounds": {
                "stat": "rebounds",
                "value": 20.0,
                "holder": "SeedPlayer2",
                "game": "SeedGame2",
                "date": "2024-01-02",
            },
        }

        mock_json_load.return_value = seed_data
        mock_open.return_value.__enter__.return_value = MagicMock()

        result = load_records_seed()

        assert result.points is not None
        assert result.points.value == 50.0
        assert result.points.holder == "SeedPlayer"

        assert result.rebounds is not None
        assert result.rebounds.value == 20.0
        assert result.rebounds.holder == "SeedPlayer2"

    @patch("core.records.settings")
    @patch("pathlib.Path.exists")
    def test_load_records_seed_file_not_found(self, mock_exists, mock_settings):
        """Test loading when seed file doesn't exist."""
        mock_settings.RECORDS_SEED_PATH = "data/records_seed.json"
        mock_exists.return_value = False

        result = load_records_seed()

        assert isinstance(result, RecordsData)
        assert result.points is None
        assert result.rebounds is None

    @patch("core.records.settings")
    @patch("builtins.open")
    def test_load_records_seed_json_error(self, mock_open, mock_settings):
        """Test loading when JSON parsing fails."""
        mock_settings.RECORDS_SEED_PATH = "data/records_seed.json"
        mock_open.side_effect = Exception("File read error")

        result = load_records_seed()

        assert isinstance(result, RecordsData)
        assert result.points is None
        assert result.rebounds is None


if __name__ == "__main__":
    pytest.main([__file__])
