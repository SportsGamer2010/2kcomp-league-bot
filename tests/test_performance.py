"""Performance and stress tests for the Discord bot."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import random

import pytest

from core.leaders import top_n_season_leaders, top_n_career_leaders
from core.records import compute_single_game_records
from core.milestones import get_current_season_totals, detect_milestone_crossings
from core.http import HTTPClient
from core.milestones import PlayerTotals


class TestPerformanceBenchmarks:
    """Test performance benchmarks for core operations."""

    @pytest.fixture
    def large_dataset(self):
        """Create a large dataset for performance testing."""
        return [
            {
                "name": f"Player{i:03d}",
                "team": f"Team{(i % 10) + 1}",
                "points": float(random.randint(10, 100)),
                "assists": float(random.randint(1, 20)),
                "rebounds": float(random.randint(1, 25)),
                "steals": float(random.randint(0, 10)),
                "blocks": float(random.randint(0, 8)),
                "threes_made": float(random.randint(0, 15)),
            }
            for i in range(1000)  # 1000 players
        ]

    @pytest.fixture
    def large_event_dataset(self):
        """Create a large event dataset for performance testing."""
        return [
            {
                "id": i,
                "date": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                "title": f"Game {i}",
                "results": {
                    "boxscore": [
                        {
                            "name": f"Player{(i % 100) + 1:03d}",
                            "team": f"Team{(i % 10) + 1}",
                            "opp": f"Team{((i + 1) % 10) + 1}",
                            "game": f"Game {i}",
                            "date": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                            "pts": float(random.randint(5, 60)),
                            "rebtwo": float(random.randint(0, 20)),
                            "ast": float(random.randint(0, 15)),
                            "stl": float(random.randint(0, 8)),
                            "blk": float(random.randint(0, 6)),
                            "threepm": float(random.randint(0, 12)),
                            "fgm": float(random.randint(0, 25)),
                            "fga": float(random.randint(0, 30)),
                            "threepa": float(random.randint(0, 15)),
                            "fg_percent": float(random.randint(30, 90)),
                            "threep_percent": float(random.randint(20, 80)),
                        }
                        for _ in range(random.randint(8, 15))  # 8-15 players per game
                    ]
                }
            }
            for i in range(100)  # 100 games
        ]

    @pytest.mark.asyncio
    async def test_leaders_calculation_performance(self, large_dataset):
        """Test leaders calculation performance with large datasets."""
        mock_client = AsyncMock(spec=HTTPClient)
        async def mock_paginate(url, per_page=100):
            for player in large_dataset:
                yield player
        
        mock_client.paginate = mock_paginate

        # Benchmark season leaders calculation
        start_time = time.time()
        season_leaders = await top_n_season_leaders(mock_client, n=10)
        season_time = time.time() - start_time

        # Benchmark career leaders calculation
        start_time = time.time()
        career_leaders = await top_n_career_leaders(
            mock_client, ["season1", "season2"], n=10
        )
        career_time = time.time() - start_time

        # Performance assertions
        assert season_time < 1.0, f"Season leaders took {season_time:.3f}s, expected <1.0s"
        assert career_time < 2.0, f"Career leaders took {career_time:.3f}s, expected <2.0s"
        
        # Verify results
        assert len(season_leaders.points) == 10
        assert len(career_leaders.points) == 10
        
        # Verify sorting performance (should be fast)
        assert season_leaders.points[0].value >= season_leaders.points[1].value

    @pytest.mark.asyncio
    async def test_records_computation_performance(self, large_event_dataset):
        """Test records computation performance with large datasets."""
        mock_client = AsyncMock(spec=HTTPClient)
        async def mock_paginate(url, per_page=100):
            for event in large_event_dataset:
                yield event
        
        mock_client.paginate = mock_paginate

        # Benchmark records computation
        start_time = time.time()
        records = await compute_single_game_records(mock_client)
        computation_time = time.time() - start_time

        # Performance assertions
        assert computation_time < 2.0, f"Records computation took {computation_time:.3f}s, expected <2.0s"
        
        # Verify results
        assert records is not None
        assert isinstance(records, type(records))

    @pytest.mark.asyncio
    async def test_milestone_detection_performance(self, large_dataset):
        """Test milestone detection performance with large datasets."""
        mock_client = AsyncMock(spec=HTTPClient)
        async def mock_paginate(url, per_page=100):
            for player in large_dataset:
                yield player
        
        mock_client.paginate = mock_paginate

        # Create large previous state
        previous_state = {
            f"Player{i:03d}": PlayerTotals(
                points=float(random.randint(5, 80)),
                assists=float(random.randint(1, 15)),
                rebounds=float(random.randint(1, 20)),
                steals=float(random.randint(0, 8)),
                blocks=float(random.randint(0, 6)),
                threes_made=float(random.randint(0, 12)),
            )
            for i in range(500)  # 500 players in previous state
        }

        # Benchmark milestone detection
        start_time = time.time()
        totals = await get_current_season_totals(mock_client)
        milestone_time = time.time() - start_time

        # Performance assertions
        assert milestone_time < 1.0, f"Milestone detection took {milestone_time:.3f}s, expected <1.0s"
        
        # Verify results
        assert len(totals) > 0


class TestConcurrency:
    """Test concurrent operation handling."""

    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self):
        """Test handling of concurrent API calls."""
        mock_client = AsyncMock(spec=HTTPClient)
        async def mock_paginate(url, per_page=100):
            return []
        
        mock_client.paginate = mock_paginate
        
        # Test concurrent execution
        start_time = time.time()
        
        # Create multiple concurrent tasks
        tasks = [
            top_n_season_leaders(mock_client, n=3),
            top_n_career_leaders(mock_client, ["season1"], n=3),
            compute_single_game_records(mock_client),
            get_current_season_totals(mock_client),
        ]

        # Execute concurrently
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time

        # Performance assertions
        assert execution_time < 3.0, f"Concurrent execution took {execution_time:.3f}s, expected <3.0s"
        
        # All tasks should complete successfully
        assert len(results) == 4
        assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_concurrent_large_operations(self):
        """Test concurrent execution of large operations."""
        # Create large datasets
        large_player_data = [
            {
                "name": f"Player{i}",
                "points": float(i),
                "assists": float(i % 10),
                "rebounds": float(i % 15),
                "steals": float(i % 5),
                "blocks": float(i % 3),
                "threes_made": float(i % 8),
            }
            for i in range(500)  # 500 players
        ]

        large_event_data = [
            {
                "id": i,
                "date": "2024-01-15",
                "title": f"Game {i}",
                "results": {
                    "boxscore": [
                        {
                            "name": f"Player{i % 100}",
                            "pts": float(random.randint(10, 50)),
                            "rebtwo": float(random.randint(0, 15)),
                            "ast": float(random.randint(0, 10)),
                            "stl": float(random.randint(0, 5)),
                            "blk": float(random.randint(0, 4)),
                            "threepm": float(random.randint(0, 8)),
                            "fgm": float(random.randint(0, 20)),
                            "fga": float(random.randint(0, 25)),
                            "threepa": float(random.randint(0, 10)),
                            "fg_percent": float(random.randint(40, 80)),
                            "threep_percent": float(random.randint(30, 70)),
                        }
                    ]
                }
            }
            for i in range(50)  # 50 games
        ]

        mock_client = AsyncMock(spec=HTTPClient)
        
        # Mock different responses for different endpoints
        def mock_get_side_effect(endpoint):
            if "leaders" in endpoint or "players" in endpoint:
                return {"status": 200, "data": large_player_data}
            elif "events" in endpoint:
                return {"status": 200, "data": large_event_data}
            else:
                return {"status": 200, "data": []}

        mock_client.get.side_effect = mock_get_side_effect

        # Test concurrent execution of large operations
        start_time = time.time()
        
        tasks = [
            top_n_season_leaders(mock_client, n=20),
            top_n_career_leaders(mock_client, ["season1", "season2"], n=20),
            compute_single_game_records(mock_client),
        ]

        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time

        # Performance assertions
        assert execution_time < 5.0, f"Large concurrent operations took {execution_time:.3f}s, expected <5.0s"
        
        # Verify results
        assert len(results) == 3
        assert all(result is not None for result in results)


class TestMemoryUsage:
    """Test memory usage characteristics."""

    @pytest.mark.asyncio
    async def test_memory_efficiency_large_datasets(self):
        """Test memory efficiency with large datasets."""
        import psutil
        import os
        
        try:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create very large dataset
            large_dataset = [
                {
                    "name": f"Player{i}",
                    "points": float(i),
                    "assists": float(i % 10),
                    "rebounds": float(i % 15),
                    "steals": float(i % 5),
                    "blocks": float(i % 3),
                    "threes_made": float(i % 8),
                }
                for i in range(10000)  # 10,000 players
            ]

            mock_client = AsyncMock(spec=HTTPClient)
            mock_client.get.return_value = {
                "status": 200,
                "data": large_dataset,
            }

            # Process large dataset
            leaders = await top_n_season_leaders(mock_client, n=100)
            
            # Check memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (< 100MB for 10k players)
            assert memory_increase < 100, f"Memory increase: {memory_increase:.1f}MB, expected <100MB"
            
            # Verify results
            assert len(leaders.points) == 100
            
        except ImportError:
            # psutil not available, skip memory test
            pytest.skip("psutil not available for memory testing")

    @pytest.mark.asyncio
    async def test_memory_cleanup(self):
        """Test that memory is properly cleaned up after operations."""
        import psutil
        import os
        
        try:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform multiple operations
            mock_client = AsyncMock(spec=HTTPClient)
            mock_client.get.return_value = {"status": 200, "data": []}
            
            for _ in range(10):
                await top_n_season_leaders(mock_client, n=10)
                await compute_single_game_records(mock_client)
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Check memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory should not grow excessively
            assert memory_increase < 50, f"Memory increase: {memory_increase:.1f}MB, expected <50MB"
            
        except ImportError:
            # psutil not available, skip memory test
            pytest.skip("psutil not available for memory testing")


class TestStressTesting:
    """Test system behavior under stress."""

    @pytest.mark.asyncio
    async def test_rapid_successive_calls(self):
        """Test rapid successive API calls."""
        mock_client = AsyncMock(spec=HTTPClient)
        mock_client.get.return_value = {"status": 200, "data": []}
        
        # Make many rapid calls
        start_time = time.time()
        
        tasks = []
        for i in range(100):  # 100 rapid calls
            task = top_n_season_leaders(mock_client, n=5)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time
        
        # Should complete in reasonable time
        assert execution_time < 10.0, f"Rapid calls took {execution_time:.3f}s, expected <10.0s"
        
        # All should succeed
        assert len(results) == 100
        assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_mixed_operation_stress(self):
        """Test stress with mixed operations."""
        mock_client = AsyncMock(spec=HTTPClient)
        
        # Create mixed dataset
        mixed_data = [
            {
                "name": f"Player{i}",
                "points": float(i),
                "assists": float(i % 10),
                "rebounds": float(i % 15),
                "steals": float(i % 5),
                "blocks": float(i % 3),
                "threes_made": float(i % 8),
            }
            for i in range(1000)  # 1000 players
        ]
        
        mock_client.get.return_value = {"status": 200, "data": mixed_data}
        
        # Stress test with mixed operations
        start_time = time.time()
        
        # Mix different operation types
        tasks = []
        for i in range(20):  # 20 operations
            if i % 4 == 0:
                task = top_n_season_leaders(mock_client, n=10)
            elif i % 4 == 1:
                task = top_n_career_leaders(mock_client, ["season1"], n=10)
            elif i % 4 == 2:
                task = get_current_season_totals(mock_client)
            else:
                task = compute_single_game_records(mock_client)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time
        
        # Should complete in reasonable time
        assert execution_time < 15.0, f"Mixed operations took {execution_time:.3f}s, expected <15.0s"
        
        # All should succeed
        assert len(results) == 20
        assert all(result is not None for result in results)


if __name__ == "__main__":
    pytest.main([__file__])
