"""Unit tests for data types and Pydantic models."""

import pytest

from core.types import (
    BotState,
    EventPlayerRow,
    LeaderEntry,
    LeadersData,
    MilestoneNotification,
    PlayerStats,
    RecordsData,
    SingleGameRecord,
)


class TestPlayerStats:
    """Test PlayerStats model."""

    def test_player_stats_creation(self):
        """Test creating a PlayerStats instance."""
        stats = PlayerStats(
            id=1,
            name="TestPlayer",
            points=25.0,
            assists=8.0,
            rebounds=12.0,
            steals=3.0,
            blocks=2.0,
            threes_made=5.0,
        )

        assert stats.id == 1
        assert stats.name == "TestPlayer"
        assert stats.points == 25.0
        assert stats.assists == 8.0
        assert stats.rebounds == 12.0
        assert stats.steals == 3.0
        assert stats.blocks == 2.0
        assert stats.threes_made == 5.0

    def test_player_stats_defaults(self):
        """Test PlayerStats with default values."""
        stats = PlayerStats(id=1, name="TestPlayer")

        assert stats.points == 0.0
        assert stats.assists == 0.0
        assert stats.rebounds == 0.0
        assert stats.steals == 0.0
        assert stats.blocks == 0.0
        assert stats.threes_made == 0.0
        assert stats.fgm == 0.0
        assert stats.fga == 0.0
        assert stats.threepm == 0.0
        assert stats.threepa == 0.0
        assert stats.fg_percent == 0.0
        assert stats.threep_percent == 0.0

    def test_player_stats_validation(self):
        """Test PlayerStats validation."""
        # Should work with valid data
        stats = PlayerStats(id=1, name="TestPlayer", points=25.0)
        assert stats.points == 25.0

        # Should handle float values
        stats = PlayerStats(id=1, name="TestPlayer", points=25, assists=8)
        assert stats.points == 25.0
        assert stats.assists == 8.0


class TestLeaderEntry:
    """Test LeaderEntry model."""

    def test_leader_entry_creation(self):
        """Test creating a LeaderEntry instance."""
        entry = LeaderEntry(name="TestPlayer", value=45.0)

        assert entry.name == "TestPlayer"
        assert entry.value == 45.0

    def test_leader_entry_validation(self):
        """Test LeaderEntry validation."""
        # Should work with valid data
        entry = LeaderEntry(name="TestPlayer", value=45)
        assert entry.value == 45.0

        # Should handle empty string names
        entry = LeaderEntry(name="", value=0.0)
        assert entry.name == ""


class TestLeadersData:
    """Test LeadersData model."""

    def test_leaders_data_creation(self):
        """Test creating a LeadersData instance."""
        leaders = LeadersData(
            points=[
                LeaderEntry(name="Player1", value=45.0),
                LeaderEntry(name="Player2", value=38.0),
            ],
            rebounds=[
                LeaderEntry(name="Player2", value=15.0),
                LeaderEntry(name="Player1", value=12.0),
            ],
        )

        assert len(leaders.points) == 2
        assert len(leaders.rebounds) == 2
        assert leaders.points[0].name == "Player1"
        assert leaders.points[0].value == 45.0
        assert leaders.rebounds[0].name == "Player2"
        assert leaders.rebounds[0].value == 15.0

    def test_leaders_data_defaults(self):
        """Test LeadersData with default values."""
        leaders = LeadersData()

        assert leaders.points == []
        assert leaders.assists == []
        assert leaders.rebounds == []
        assert leaders.steals == []
        assert leaders.blocks == []
        assert leaders.threes_made == []

    def test_leaders_data_empty_lists(self):
        """Test LeadersData with empty lists."""
        leaders = LeadersData(points=[], rebounds=[])

        assert leaders.points == []
        assert leaders.rebounds == []


class TestSingleGameRecord:
    """Test SingleGameRecord model."""

    def test_single_game_record_creation(self):
        """Test creating a SingleGameRecord instance."""
        record = SingleGameRecord(
            stat="points",
            value=45.0,
            holder="TestPlayer",
            game="Team A vs Team B",
            date="2024-01-15",
        )

        assert record.stat == "points"
        assert record.value == 45.0
        assert record.holder == "TestPlayer"
        assert record.game == "Team A vs Team B"
        assert record.date == "2024-01-15"

    def test_single_game_record_validation(self):
        """Test SingleGameRecord validation."""
        # Should work with valid data
        record = SingleGameRecord(
            stat="rebounds",
            value=15,
            holder="TestPlayer",
            game="Game1",
            date="2024-01-15",
        )
        assert record.value == 15.0

        # Should handle empty strings
        record = SingleGameRecord(
            stat="assists", value=0.0, holder="", game="", date="2024-01-15"
        )
        assert record.holder == ""
        assert record.game == ""


class TestRecordsData:
    """Test RecordsData model."""

    def test_records_data_creation(self):
        """Test creating a RecordsData instance."""
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
        )

        assert records.points is not None
        assert records.points.value == 45.0
        assert records.points.holder == "Player1"

        assert records.rebounds is not None
        assert records.rebounds.value == 15.0
        assert records.rebounds.holder == "Player2"

        # Other stats should be None
        assert records.assists is None
        assert records.steals is None
        assert records.blocks is None
        assert records.threes_made is None
        assert records.fg_percent is None
        assert records.threep_percent is None

    def test_records_data_defaults(self):
        """Test RecordsData with default values."""
        records = RecordsData()

        assert records.points is None
        assert records.rebounds is None
        assert records.assists is None
        assert records.steals is None
        assert records.blocks is None
        assert records.threes_made is None
        assert records.fg_percent is None
        assert records.threep_percent is None


class TestEventPlayerRow:
    """Test EventPlayerRow model."""

    def test_event_player_row_creation(self):
        """Test creating an EventPlayerRow instance."""
        row = EventPlayerRow(
            name="TestPlayer",
            team="Team A",
            opp="Team B",
            game="Team A vs Team B",
            date="2024-01-15",
            points=25.0,
            rebounds=8.0,
            assists=5.0,
            steals=2.0,
            blocks=1.0,
            threes_made=3.0,
            fgm=10.0,
            fga=20.0,
            threepm=3.0,
            threepa=8.0,
            fg_percent=50.0,
            threep_percent=37.5,
        )

        assert row.name == "TestPlayer"
        assert row.team == "Team A"
        assert row.opp == "Team B"
        assert row.game == "Team A vs Team B"
        assert row.date == "2024-01-15"
        assert row.points == 25.0
        assert row.rebounds == 8.0
        assert row.assists == 5.0
        assert row.steals == 2.0
        assert row.blocks == 1.0
        assert row.threes_made == 3.0
        assert row.fgm == 10.0
        assert row.fga == 20.0
        assert row.threepm == 3.0
        assert row.threepa == 8.0
        assert row.fg_percent == 50.0
        assert row.threep_percent == 37.5

    def test_event_player_row_defaults(self):
        """Test EventPlayerRow with default values."""
        row = EventPlayerRow(
            name="TestPlayer",
            team="Team A",
            opp="Team B",
            game="Game1",
            date="2024-01-15",
        )

        assert row.points == 0.0
        assert row.rebounds == 0.0
        assert row.assists == 0.0
        assert row.steals == 0.0
        assert row.blocks == 0.0
        assert row.threes_made == 0.0
        assert row.fgm == 0.0
        assert row.fga == 0.0
        assert row.threepm == 0.0
        assert row.threepa == 0.0
        assert row.fg_percent == 0.0
        assert row.threep_percent == 0.0


class TestBotState:
    """Test BotState model."""

    def test_bot_state_creation(self):
        """Test creating a BotState instance."""
        state = BotState(
            last_leaders=LeadersData(points=[LeaderEntry(name="Player1", value=45.0)]),
            milestones_sent={"points": {"100": [1, 2, 3]}},
            last_totals={"points": {"Player1": 45.0}},
        )

        assert len(state.last_leaders.points) == 1
        assert state.last_leaders.points[0].name == "Player1"
        assert state.milestones_sent["points"]["100"] == [1, 2, 3]
        assert state.last_totals["points"]["Player1"] == 45.0

    def test_bot_state_defaults(self):
        """Test BotState with default values."""
        state = BotState()

        assert isinstance(state.last_leaders, LeadersData)
        assert state.milestones_sent == {}
        assert state.last_totals == {}


class TestMilestoneNotification:
    """Test MilestoneNotification model."""

    def test_milestone_notification_creation(self):
        """Test creating a MilestoneNotification instance."""
        notification = MilestoneNotification(
            player="TestPlayer",
            stat="points",
            value=100.0,
            threshold=100,
            message="TestPlayer has reached 100 points!",
        )

        assert notification.player == "TestPlayer"
        assert notification.stat == "points"
        assert notification.value == 100.0
        assert notification.threshold == 100
        assert notification.message == "TestPlayer has reached 100 points!"


class TestDataValidation:
    """Test data validation edge cases."""

    def test_float_conversion(self):
        """Test that integer values are converted to floats."""
        stats = PlayerStats(
            id=1,
            name="TestPlayer",
            points=25,  # Integer
            rebounds=12,  # Integer
            assists=8,  # Integer
        )

        assert isinstance(stats.points, float)
        assert isinstance(stats.rebounds, float)
        assert isinstance(stats.assists, float)
        assert stats.points == 25.0
        assert stats.rebounds == 12.0
        assert stats.assists == 8.0

    def test_empty_strings_allowed(self):
        """Test that empty strings are allowed for string fields."""
        record = SingleGameRecord(
            stat="points",
            value=0.0,
            holder="",  # Empty string
            game="",  # Empty string
            date="2024-01-15",
        )

        assert record.holder == ""
        assert record.game == ""

    def test_zero_values_allowed(self):
        """Test that zero values are allowed for numeric fields."""
        stats = PlayerStats(
            id=1, name="TestPlayer", points=0.0, rebounds=0.0, assists=0.0
        )

        assert stats.points == 0.0
        assert stats.rebounds == 0.0
        assert stats.assists == 0.0


if __name__ == "__main__":
    pytest.main([__file__])
