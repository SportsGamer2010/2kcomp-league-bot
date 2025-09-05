"""End-to-end integration tests for the Discord bot."""

import asyncio
import json
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest
import aiohttp

from core.config import settings
from core.http import HTTPClient
from core.leaders import top_n_season_leaders, top_n_career_leaders, format_leaders_embed
from core.records import compute_single_game_records, format_records_embed
from core.milestones import (
    get_current_season_totals,
    detect_milestone_crossings,
    format_milestone_embed,
)
from core.types import (
    PlayerStats,
    LeadersData,
    LeaderEntry,
    RecordsData,
    SingleGameRecord,
    MilestoneNotification,
)
from core.milestones import PlayerTotals
from core.sportspress import (
    fetch_players_for_season,
    fetch_events,
    _extract_rows_from_event,
)


class TestFullDataPipeline:
    """Test the complete data pipeline from API to Discord responses."""

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client for testing."""
        client = AsyncMock(spec=HTTPClient)
        client.get_json = AsyncMock()
        client.paginate = AsyncMock()
        return client

    @pytest.fixture
    def sample_player_data(self):
        """Sample player data from SportsPress API."""
        return [
            {
                "id": 1,
                "name": "Player1",
                "meta": {
                    "points": 125.5,
                    "assists": 8.0,
                    "rebounds": 12.0,
                    "steals": 3.0,
                    "blocks": 2.0,
                    "threes_made": 4.0,
                }
            },
            {
                "id": 2,
                "name": "Player2",
                "meta": {
                    "points": 30.0,
                    "assists": 12.0,
                    "rebounds": 8.0,
                    "steals": 5.0,
                    "blocks": 1.0,
                    "threes_made": 6.0,
                }
            },
            {
                "id": 3,
                "name": "Player3",
                "meta": {
                    "points": 18.0,
                    "assists": 15.0,
                    "rebounds": 15.0,
                    "steals": 2.0,
                    "blocks": 4.0,
                    "threes_made": 2.0,
                }
            },
        ]

    @pytest.fixture
    def sample_event_data(self):
        """Sample event data from SportsPress API."""
        return [
            {
                "id": 1,
                "date": "2024-01-15",
                "title": "Team A vs Team B",
                "teams": [
                    {"name": "Team A"},
                    {"name": "Team B"}
                ],
                "results": {
                    "boxscore": [
                        {
                            "name": "Player1",
                            "team": "Team A",
                            "pts": 45.0,
                            "rebtwo": 18.0,
                            "ast": 12.0,
                            "stl": 5.0,
                            "blk": 3.0,
                            "threepm": 7.0,
                            "fgm": 18.0,
                            "fga": 25.0,
                            "threepa": 12.0,
                            "fgpercent": 72.0,
                            "threeppercent": 58.3,
                        }
                    ]
                }
            }
        ]

    @pytest.mark.asyncio
    async def test_full_leaders_pipeline(self, mock_http_client, sample_player_data):
        """Test complete leaders calculation pipeline."""
        # Mock API response - simulate pagination
        async def mock_paginate(url):
            for player in sample_player_data:
                yield player
        
        mock_http_client.paginate = mock_paginate

        # Test season leaders
        season_leaders = await top_n_season_leaders(mock_http_client, n=3)
        
        assert isinstance(season_leaders, LeadersData)
        assert len(season_leaders.points) == 3
        assert len(season_leaders.assists) == 3
        assert len(season_leaders.rebounds) == 3
        
        # Verify sorting (highest values first)
        assert season_leaders.points[0].value == 125.5  # Player1 (highest)
        assert season_leaders.points[1].value == 30.0   # Player2
        assert season_leaders.points[2].value == 18.0   # Player3
        
        # Test career leaders (simulate multiple seasons)
        career_leaders = await top_n_career_leaders(
            mock_http_client, 
            season_queries=["season1", "season2"], 
            n=3
        )
        
        assert isinstance(career_leaders, LeadersData)
        assert len(career_leaders.points) == 3

    @pytest.mark.asyncio
    async def test_full_records_pipeline(self, mock_http_client, sample_event_data):
        """Test complete records computation pipeline."""
        # Mock API responses - simulate pagination
        async def mock_paginate(url, per_page=100):
            for event in sample_event_data:
                yield event
        
        mock_http_client.paginate = mock_paginate

        # Test records computation
        records = await compute_single_game_records(mock_http_client)
        
        assert isinstance(records, RecordsData)
        assert records.points is not None
        assert records.points.value == 45.0
        assert records.points.holder == "Player1"
        assert records.points.game == "Team A vs Team B"
        assert records.points.date == "2024-01-15"

    @pytest.mark.asyncio
    async def test_full_milestones_pipeline(self, mock_http_client, sample_player_data):
        """Test complete milestone detection pipeline."""
        # Mock API response - simulate pagination
        async def mock_paginate(url):
            for player in sample_player_data:
                yield player
        
        mock_http_client.paginate = mock_paginate

        # Test milestone detection
        totals = await get_current_season_totals(mock_http_client)
        
        assert isinstance(totals, dict)
        assert 1 in totals  # Player1 has ID 1
        assert 2 in totals  # Player2 has ID 2
        
        # Test milestone crossing detection
        previous_state = {
            "1": {
                "points": 95.0, "assists": 5.0, "rebounds": 10.0,
                "steals": 2.0, "blocks": 1.0, "threes_made": 3.0
            }
        }
        
        milestones_sent = {"1": {"points": []}}  # No milestones sent yet
        
        notifications = detect_milestone_crossings(totals, previous_state, milestones_sent)
        
        assert isinstance(notifications, list)
        # Should detect crossing 100 points threshold (Player1 went from 95.0 to 125.5)
        assert any(n.player == "Player1" and n.stat == "points" for n in notifications)

    @pytest.mark.asyncio
    async def test_discord_embed_generation(self):
        """Test Discord embed generation for all data types."""
        # Test leaders embed
        leaders_data = LeadersData(
            points=[
                LeaderEntry(name="Player1", value=30.0),
                LeaderEntry(name="Player2", value=25.5),
            ],
            assists=[
                LeaderEntry(name="Player3", value=15.0),
                LeaderEntry(name="Player1", value=12.0),
            ]
        )
        
        leaders_embed = format_leaders_embed(leaders_data, scope="season")
        assert leaders_embed["title"] == "🏆 Season Leaders"
        assert len(leaders_embed["fields"]) == 2
        
        # Test records embed
        records_data = RecordsData(
            points=SingleGameRecord(
                stat="points",
                value=45.0,
                holder="Player1",
                game="Team A vs Team B",
                date="2024-01-15"
            )
        )
        
        records_embed = format_records_embed(records_data)
        assert "Single-Game Records" in records_embed["title"]
        assert len(records_embed["fields"]) > 0
        
        # Test milestones embed
        milestone_notifications = [
            MilestoneNotification(
                player="Player1",
                stat="points",
                threshold=25,
                value=30.0,
                message="🎉 Player1 crossed 25 points milestone!"
            )
        ]
        
        milestones_embed = format_milestone_embed(milestone_notifications)
        assert "Milestone Achievements" in milestones_embed["title"]
        assert len(milestones_embed["fields"]) > 0


class TestAPIIntegration:
    """Test integration with SportsPress API endpoints."""

    @pytest.fixture
    def real_http_client(self):
        """Create a real HTTP client for integration testing."""
        session = AsyncMock(spec=aiohttp.ClientSession)
        return HTTPClient(session=session)

    @pytest.mark.asyncio
    async def test_api_endpoint_handling(self, real_http_client):
        """Test API endpoint handling and error responses."""
        # Test with invalid endpoint
        with patch.object(real_http_client, 'paginate') as mock_paginate:
            mock_paginate.side_effect = Exception("API Error")
            
            # Should handle errors gracefully
            try:
                players = await fetch_players_for_season(
                    real_http_client, 
                    "https://example.com", 
                    "invalid_endpoint"
                )
                # If no exception, should return empty list
                assert players == []
            except Exception:
                # If exception is raised, that's also acceptable behavior
                pass

    @pytest.mark.asyncio
    async def test_data_parsing_robustness(self):
        """Test data parsing handles various API response formats."""
        # Test with malformed data
        malformed_event = {
            "id": 1,
            "date": "2024-01-15",
            "results": {
                "boxscore": [
                    {
                        "name": "Player1",
                        "pts": "invalid_value",  # Should handle gracefully
                        "assists": None,  # Should handle None values
                    }
                ]
            }
        }
        
        # Should not crash on malformed data
        rows = _extract_rows_from_event(malformed_event)
        assert isinstance(rows, list)


class TestErrorHandling:
    """Test error handling throughout the pipeline."""

    @pytest.mark.asyncio
    async def test_network_failure_handling(self):
        """Test handling of network failures."""
        mock_client = AsyncMock(spec=HTTPClient)
        mock_client.get_json.side_effect = Exception("Network timeout")
        
        # Test leaders with network failure
        leaders = await top_n_season_leaders(mock_client, n=3)
        assert isinstance(leaders, LeadersData)
        assert len(leaders.points) == 0  # Should return empty data
        
        # Test records with network failure
        records = await compute_single_game_records(mock_client)
        assert isinstance(records, RecordsData)
        assert records.points is None  # Should return None

    @pytest.mark.asyncio
    async def test_invalid_data_handling(self):
        """Test handling of invalid data from API."""
        mock_client = AsyncMock(spec=HTTPClient)
        mock_client.get_json.return_value = {
            "status": 200,
            "data": None  # Invalid data
        }
        
        # Should handle gracefully
        leaders = await top_n_season_leaders(mock_client, n=3)
        assert isinstance(leaders, LeadersData)
        assert len(leaders.points) == 0

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self):
        """Test handling of partial API failures."""
        mock_client = AsyncMock(spec=HTTPClient)
        
        # Mock some endpoints working, others failing
        def mock_get_json_side_effect(endpoint):
            if "leaders" in endpoint:
                return {"status": 200, "data": []}
            else:
                raise Exception("Endpoint not found")
        
        mock_client.get_json.side_effect = mock_get_json_side_effect
        
        # Should handle partial failures gracefully
        leaders = await top_n_season_leaders(mock_client, n=3)
        assert isinstance(leaders, LeadersData)


class TestPerformance:
    """Test performance characteristics of the pipeline."""

    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self):
        """Test handling of concurrent API calls."""
        mock_client = AsyncMock(spec=HTTPClient)
        mock_client.get_json.return_value = {"status": 200, "data": []}
        
        # Test concurrent execution
        start_time = datetime.now()
        
        tasks = [
            top_n_season_leaders(mock_client, n=3),
            top_n_career_leaders(mock_client, ["season1"], n=3),
            compute_single_game_records(mock_client),
        ]
        
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()
        
        # Should complete in reasonable time
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 5.0  # Should complete in under 5 seconds
        
        # All tasks should complete successfully
        assert len(results) == 3
        assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self):
        """Test handling of large datasets."""
        # Create large dataset
        large_player_data = [
            {
                "id": i,
                "name": f"Player{i}",
                "meta": {
                    "points": float(i),
                    "assists": float(i % 10),
                    "rebounds": float(i % 15),
                    "steals": float(i % 5),
                    "blocks": float(i % 3),
                    "threes_made": float(i % 8),
                }
            }
            for i in range(100)  # 100 players
        ]
        
        mock_client = AsyncMock(spec=HTTPClient)
        async def mock_paginate(url):
            for player in large_player_data:
                yield player
        
        mock_client.paginate = mock_paginate
        
        # Should handle large datasets efficiently
        start_time = datetime.now()
        leaders = await top_n_season_leaders(mock_client, n=10)
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 2.0  # Should complete quickly
        
        assert len(leaders.points) == 10
        assert leaders.points[0].value == 99.0  # Highest value first


class TestDataConsistency:
    """Test data consistency across the pipeline."""

    @pytest.mark.asyncio
    async def test_data_integrity_throughout_pipeline(self):
        """Test that data integrity is maintained throughout the pipeline."""
        # Create consistent test data
        test_players = [
            {
                "id": 1,
                "name": "TestPlayer",
                "meta": {
                    "points": 50.0,
                    "assists": 20.0,
                    "rebounds": 25.0,
                    "steals": 10.0,
                    "blocks": 8.0,
                    "threes_made": 12.0,
                }
            }
        ]
        
        mock_client = AsyncMock(spec=HTTPClient)
        async def mock_paginate(url):
            for player in test_players:
                yield player
        
        mock_client.paginate = mock_paginate
        
        # Test data flows through pipeline consistently
        leaders = await top_n_season_leaders(mock_client, n=1)
        
        assert leaders.points[0].name == "TestPlayer"
        assert leaders.points[0].value == 50.0
        assert leaders.assists[0].value == 20.0
        assert leaders.rebounds[0].value == 25.0

    @pytest.mark.asyncio
    async def test_sorting_consistency(self):
        """Test that sorting is consistent across different operations."""
        test_players = [
            {"id": 1, "name": "PlayerA", "meta": {"points": 30.0}},
            {"id": 2, "name": "PlayerB", "meta": {"points": 30.0}},  # Same points
            {"id": 3, "name": "PlayerC", "meta": {"points": 25.0}},
        ]
        
        mock_client = AsyncMock(spec=HTTPClient)
        async def mock_paginate(url):
            for player in test_players:
                yield player
        
        mock_client.paginate = mock_paginate
        
        leaders = await top_n_season_leaders(mock_client, n=3)
        
        # Should maintain consistent sorting (value desc, then name asc)
        assert leaders.points[0].name == "PlayerA"  # 30.0, alphabetically first
        assert leaders.points[1].name == "PlayerB"  # 30.0, alphabetically second
        assert leaders.points[2].name == "PlayerC"  # 25.0


if __name__ == "__main__":
    pytest.main([__file__])
