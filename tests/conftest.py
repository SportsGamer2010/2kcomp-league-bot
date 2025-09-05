"""Pytest configuration and shared fixtures."""

import asyncio
import os

import pytest

# Mock settings before importing other modules
os.environ.setdefault("DISCORD_TOKEN", "test_token")
os.environ.setdefault("GUILD_ID", "123456789")
os.environ.setdefault("ANNOUNCE_CHANNEL_ID", "123456789")
os.environ.setdefault("HISTORY_CHANNEL_ID", "123456789")
os.environ.setdefault("SPORTSPRESS_BASE", "https://example.com")
os.environ.setdefault("SPORTSPRESS_USERNAME", "test_user")
os.environ.setdefault("SPORTSPRESS_PASSWORD", "test_pass")
os.environ.setdefault("MIN_FGA_FOR_FG_PERCENT", "10")
os.environ.setdefault("MIN_3PA_FOR_3P_PERCENT", "5")
os.environ.setdefault("RECORDS_SEED_PATH", "data/records_seed.json")
os.environ.setdefault("STATE_PATH", "data/state.json")


# Mock HTTPClient class for testing
class MockHTTPClient:
    """Mock HTTP client for testing."""

    pass


@pytest.fixture
def sample_single_game_record():
    """Sample single game record for testing."""
    from core.types import SingleGameRecord

    return SingleGameRecord(
        stat="points",
        value=45.0,
        holder="TestPlayer",
        game="Team A vs Team B",
        date="2024-01-15",
    )


@pytest.fixture
def sample_records_data():
    """Sample records data for testing."""
    from core.types import RecordsData, SingleGameRecord

    return RecordsData(
        points=SingleGameRecord(
            stat="points", value=45.0, holder="Player1", game="Game1", date="2024-01-15"
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


@pytest.fixture
def sample_event_player_row():
    """Sample event player row for testing."""
    from core.types import EventPlayerRow

    return EventPlayerRow(
        name="TestPlayer",
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
    )


@pytest.fixture
def sample_leader_entry():
    """Sample leader entry for testing."""
    from core.types import LeaderEntry

    return LeaderEntry(name="TestPlayer", value=45.0)


@pytest.fixture
def sample_leaders_data():
    """Sample leaders data for testing."""
    from core.types import LeaderEntry, LeadersData

    return LeadersData(
        points=[
            LeaderEntry(name="Player1", value=45.0),
            LeaderEntry(name="Player2", value=38.0),
            LeaderEntry(name="Player3", value=32.0),
        ],
        rebounds=[
            LeaderEntry(name="Player2", value=15.0),
            LeaderEntry(name="Player1", value=12.0),
            LeaderEntry(name="Player3", value=10.0),
        ],
    )


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing."""
    return MockHTTPClient()


@pytest.fixture
def sample_events_data():
    """Sample events data structure for testing."""
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
        }
    ]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Helper function to create test data
def create_test_records_data(**kwargs):
    """Helper to create test records data with specific values."""
    from core.types import RecordsData, SingleGameRecord

    records = RecordsData()
    for stat, value in kwargs.items():
        if hasattr(records, stat):
            setattr(
                records,
                stat,
                SingleGameRecord(
                    stat=stat,
                    value=value,
                    holder=f"TestPlayer_{stat}",
                    game=f"TestGame_{stat}",
                    date="2024-01-15",
                ),
            )
    return records


def create_test_event_player_row(**kwargs):
    """Helper to create test event player row with specific values."""
    from core.types import EventPlayerRow

    defaults = {
        "name": "TestPlayer",
        "team": "Team A",
        "opp": "Team B",
        "game": "Team A vs Team B",
        "date": "2024-01-15",
        "points": 0.0,
        "rebounds": 0.0,
        "assists": 0.0,
        "steals": 0.0,
        "blocks": 0.0,
        "threes_made": 0.0,
        "fgm": 0.0,
        "fga": 0.0,
        "threepm": 0.0,
        "threepa": 0.0,
        "fg_percent": 0.0,
        "threep_percent": 0.0,
    }
    defaults.update(kwargs)
    return EventPlayerRow(**defaults)
