"""Performance optimization tests for the Discord bot."""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from core.performance import (
    PerformanceMonitor, PerformanceMetrics, PerformanceBenchmark,
    get_performance_monitor, record_api_performance, performance_benchmark
)
from core.performance_testing import (
    LoadTester, LoadTestConfig, LoadTestResult, StressTester,
    get_load_tester, get_stress_tester
)
from core.performance_optimizer import (
    PerformanceOptimizer, OptimizationAction, get_performance_optimizer
)


class TestPerformanceMonitor:
    """Test the PerformanceMonitor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
        self.monitor.metrics_history.clear()
        self.monitor.benchmarks.clear()
    
    def test_collect_system_metrics(self):
        """Test system metrics collection."""
        with patch('core.performance.psutil.Process') as mock_process:
            # Mock process metrics
            mock_process.return_value.cpu_percent.return_value = 25.5
            mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
            mock_process.return_value.memory_percent.return_value = 15.2
            mock_process.return_value.io_counters.return_value.read_bytes = 50 * 1024 * 1024
            mock_process.return_value.io_counters.return_value.write_bytes = 25 * 1024 * 1024
            
            with patch('core.performance.psutil.net_io_counters') as mock_net:
                mock_net.return_value.bytes_sent = 10 * 1024 * 1024
                mock_net.return_value.bytes_recv = 20 * 1024 * 1024
                
                metrics = self.monitor.collect_system_metrics()
                
                assert isinstance(metrics, PerformanceMetrics)
                assert metrics.cpu_percent == 25.5
                assert metrics.memory_mb == 100.0
                assert metrics.memory_percent == 15.2
                assert metrics.disk_io_read_mb == 50.0
                assert metrics.disk_io_write_mb == 25.0
                assert metrics.network_sent_mb == 10.0
                assert metrics.network_recv_mb == 20.0
    
    def test_record_api_call(self):
        """Test API call recording."""
        # Reset counters for this test
        self.monitor.api_calls = 0
        self.monitor.api_errors = 0
        self.monitor.response_times.clear()
        
        # Record some API calls
        self.monitor.record_api_call(150.0, True)   # 150ms, success
        self.monitor.record_api_call(200.0, False)  # 200ms, failure
        self.monitor.record_api_call(100.0, True)   # 100ms, success
        
        # Check that all calls are counted in api_calls
        assert self.monitor.api_calls == 3  # All calls (successful + failed)
        assert self.monitor.api_errors == 1
        assert len(self.monitor.response_times) == 3
        assert 150.0 in self.monitor.response_times
        assert 200.0 in self.monitor.response_times
        assert 100.0 in self.monitor.response_times
    
    def test_add_metrics(self):
        """Test metrics addition to history."""
        metrics = PerformanceMetrics(
            cpu_percent=30.0,
            memory_mb=200.0,
            response_time_avg_ms=150.0
        )
        
        self.monitor.add_metrics(metrics)
        assert len(self.monitor.metrics_history) == 1
        assert self.monitor.metrics_history[0] == metrics
    
    def test_get_recent_metrics(self):
        """Test getting recent metrics."""
        # Add some metrics with different timestamps
        now = datetime.now()
        metrics1 = PerformanceMetrics(timestamp=now - timedelta(minutes=30))
        metrics2 = PerformanceMetrics(timestamp=now - timedelta(minutes=15))
        metrics3 = PerformanceMetrics(timestamp=now)
        
        self.monitor.add_metrics(metrics1)
        self.monitor.add_metrics(metrics2)
        self.monitor.add_metrics(metrics3)
        
        # Get metrics from last 20 minutes
        recent = self.monitor.get_recent_metrics(20)
        assert len(recent) == 2  # metrics2 and metrics3
        assert metrics1 not in recent
        assert metrics2 in recent
        assert metrics3 in recent
    
    def test_get_performance_summary(self):
        """Test performance summary generation."""
        # Add some test metrics
        for i in range(5):
            metrics = PerformanceMetrics(
                cpu_percent=20.0 + i * 10,
                memory_mb=100.0 + i * 50,
                response_time_avg_ms=100.0 + i * 25
            )
            self.monitor.add_metrics(metrics)
        
        summary = self.monitor.get_performance_summary(60)
        
        assert summary["status"] == "healthy"
        assert summary["period_minutes"] == 60
        assert summary["metrics_count"] == 5
        assert "averages" in summary
        assert "peaks" in summary
        assert "current" in summary
    
    def test_check_performance_health(self):
        """Test performance health checking."""
        with patch('core.performance.psutil.Process') as mock_process:
            # Mock high CPU usage
            mock_process.return_value.cpu_percent.return_value = 85.0
            mock_process.return_value.memory_info.return_value.rss = 200 * 1024 * 1024
            mock_process.return_value.memory_percent.return_value = 20.0
            mock_process.return_value.io_counters.return_value.read_bytes = 0
            mock_process.return_value.io_counters.return_value.write_bytes = 0
            
            with patch('core.performance.psutil.net_io_counters') as mock_net:
                mock_net.return_value.bytes_sent = 0
                mock_net.return_value.bytes_recv = 0
                
                health = self.monitor.check_performance_health()
                
                assert health["status"] == "critical"
                assert "High CPU usage: 85.0%" in health["issues"]
    
    @pytest.mark.asyncio
    async def test_benchmark_context_manager(self):
        """Test benchmark context manager."""
        async with self.monitor.benchmark("test_benchmark"):
            await asyncio.sleep(0.01)  # Small delay
        
        assert len(self.monitor.benchmarks) == 1
        benchmark = self.monitor.benchmarks[0]
        assert benchmark.test_name == "test_benchmark"
        assert benchmark.success is True
        assert benchmark.duration_ms > 0
    
    def test_get_optimization_recommendations(self):
        """Test optimization recommendations."""
        # Add some metrics that would trigger recommendations
        for i in range(10):
            metrics = PerformanceMetrics(
                cpu_percent=75.0,  # High CPU
                memory_mb=600.0,   # High memory
                response_time_avg_ms=600.0,  # High response time
                error_rate=3.0     # Elevated error rate
            )
            self.monitor.add_metrics(metrics)
        
        recommendations = self.monitor.get_optimization_recommendations()
        
        assert len(recommendations) > 0
        assert any("background task frequency" in rec for rec in recommendations)
        assert any("memory usage" in rec for rec in recommendations)
        assert any("caching" in rec for rec in recommendations)
    
    def test_optimize_background_tasks(self):
        """Test background task optimization."""
        # Add some metrics
        for i in range(5):
            metrics = PerformanceMetrics(
                cpu_percent=85.0,  # High CPU
                memory_mb=300.0,
                response_time_avg_ms=200.0
            )
            self.monitor.add_metrics(metrics)
        
        optimization = self.monitor.optimize_background_tasks()
        
        assert optimization["status"] == "optimized"
        assert "poll_interval" in optimization["optimizations"]
        assert optimization["optimizations"]["poll_interval"] == "increase"


class TestLoadTester:
    """Test the LoadTester class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.load_tester = LoadTester()
        self.load_tester.test_results.clear()
    
    def test_test_scenarios(self):
        """Test predefined test scenarios."""
        scenarios = self.load_tester.test_scenarios
        
        assert "light_load" in scenarios
        assert "normal_load" in scenarios
        assert "heavy_load" in scenarios
        assert "stress_test" in scenarios
        
        # Check light load scenario
        light_load = scenarios["light_load"]
        assert light_load.concurrent_users == 5
        assert light_load.requests_per_second == 2.0
        assert light_load.duration_seconds == 120
    
    @pytest.mark.asyncio
    async def test_run_scenario(self):
        """Test running a predefined scenario."""
        async def mock_test_function():
            await asyncio.sleep(0.01)
            return "success"
        
        # Run light load scenario
        result = await self.load_tester.run_scenario("light_load", mock_test_function)
        
        assert isinstance(result, LoadTestResult)
        assert result.test_name == "Light Load Test"
        assert result.total_requests > 0
        assert result.successful_requests > 0
        assert result.status in ["passed", "degraded", "failed"]
    
    def test_get_test_summary(self):
        """Test test summary generation."""
        # No tests run yet
        summary = self.load_tester.get_test_summary()
        assert summary["status"] == "no_tests"
        
        # Add a mock test result
        mock_result = LoadTestResult(
            test_name="Test",
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            total_response_time_ms=5000,
            min_response_time_ms=50,
            max_response_time_ms=200,
            avg_response_time_ms=100,
            p95_response_time_ms=150,
            p99_response_time_ms=180,
            requests_per_second=10.0,
            error_rate=5.0,
            cpu_usage_avg=30.0,
            memory_usage_avg=200.0,
            status="passed"
        )
        
        self.load_tester.test_results.append(mock_result)
        
        summary = self.load_tester.get_test_summary()
        assert summary["status"] == "summary"
        assert summary["total_tests"] == 1
        assert summary["test_results"]["passed"] == 1
        assert summary["test_results"]["success_rate"] == 100.0


class TestStressTester:
    """Test the StressTester class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.stress_tester = StressTester()
    
    @pytest.mark.asyncio
    async def test_find_breakpoint(self):
        """Test finding system breakpoint."""
        async def mock_test_function():
            await asyncio.sleep(0.01)
            return "success"
        
        # Test with a small range to avoid long test execution
        result = await self.stress_tester.find_breakpoint(
            mock_test_function,
            start_users=1,
            max_users=5,
            step_size=1,
            test_duration=10
        )
        
        assert "breakpoint_found" in result
        assert "breakpoint_metrics" in result
        assert "max_users_tested" in result
        assert "recommendation" in result


class TestPerformanceOptimizer:
    """Test the PerformanceOptimizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = PerformanceOptimizer()
        self.optimizer.optimizations_applied.clear()
        self.optimizer.optimization_history.clear()
    
    def test_available_optimizations(self):
        """Test available optimizations."""
        optimizations = self.optimizer.available_optimizations
        
        assert "background_task_optimization" in optimizations
        assert "memory_cleanup" in optimizations
        assert "api_batching" in optimizations
        assert "response_caching" in optimizations
        assert "connection_pooling" in optimizations
        assert "rate_limiting" in optimizations
        
        # Check one optimization in detail
        bg_opt = optimizations["background_task_optimization"]
        assert bg_opt.name == "Background Task Optimization"
        assert bg_opt.impact == "high"
        assert bg_opt.risk == "low"
        assert bg_opt.implemented is False
    
    def test_analyze_performance(self):
        """Test performance analysis."""
        # Create test metrics
        metrics = PerformanceMetrics(
            cpu_percent=85.0,      # High CPU
            memory_percent=80.0,   # High memory
            response_time_avg_ms=2500.0,  # High response time
            error_rate=8.0         # High error rate
        )
        
        analysis = self.optimizer.analyze_performance(metrics)
        
        assert analysis["priority"] == "high"
        assert "high_cpu_usage" in analysis["optimization_opportunities"]
        assert "elevated_memory_usage" in analysis["optimization_opportunities"]
        assert "slow_response_time" in analysis["optimization_opportunities"]
        assert "elevated_error_rate" in analysis["optimization_opportunities"]
        
        # Check recommended actions
        assert "background_task_optimization" in analysis["recommended_actions"]
        assert "memory_cleanup" in analysis["recommended_actions"]
        assert "api_batching" in analysis["recommended_actions"]
        assert "rate_limiting" in analysis["recommended_actions"]
    
    @pytest.mark.asyncio
    async def test_apply_optimization(self):
        """Test applying optimizations."""
        # Test applying memory cleanup
        result = await self.optimizer.apply_optimization("memory_cleanup")
        
        assert result["success"] is True
        assert result["optimization"] == "memory_cleanup"
        assert "garbage_collection" in result
        assert "memory_cleanup" in result
        
        # Check that optimization is marked as implemented
        memory_opt = self.optimizer.available_optimizations["memory_cleanup"]
        assert memory_opt.implemented is True
        assert memory_opt.applied_at is not None
        assert memory_opt.results == result
    
    def test_get_optimization_status(self):
        """Test optimization status retrieval."""
        status = self.optimizer.get_optimization_status()
        
        assert "available_optimizations" in status
        assert "applied_optimizations" in status
        assert "optimization_history" in status
        assert "summary" in status
        
        summary = status["summary"]
        assert summary["total_available"] == 6
        assert summary["total_applied"] == 0
        assert summary["implementation_rate"] == "0.0%"
    
    @pytest.mark.asyncio
    async def test_auto_optimize(self):
        """Test automatic optimization."""
        # Test with low priority (no optimization needed)
        result = await self.optimizer.auto_optimize()
        
        assert result["success"] is True
        assert result["action"] == "no_optimization_needed"
        assert result["priority"] == "low"


class TestPerformanceIntegration:
    """Integration tests for performance modules."""
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test integration between performance monitor and optimizer."""
        monitor = get_performance_monitor()
        optimizer = get_performance_optimizer()
        
        # Collect metrics
        metrics = monitor.collect_system_metrics()
        monitor.add_metrics(metrics)
        
        # Analyze performance
        analysis = optimizer.analyze_performance(metrics)
        
        # Apply optimization if needed
        if analysis["priority"] != "low":
            result = await optimizer.apply_optimization(
                analysis["recommended_actions"][0]
            )
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_load_testing_with_performance_monitoring(self):
        """Test load testing with performance monitoring."""
        load_tester = get_load_tester()
        
        async def mock_test_function():
            # Simulate some work
            await asyncio.sleep(0.01)
            return "success"
        
        # Run a quick load test
        result = await load_tester.run_scenario("light_load", mock_test_function)
        
        assert result.total_requests > 0
        assert result.status in ["passed", "degraded", "failed"]
        
        # Check test summary
        summary = load_tester.get_test_summary()
        assert summary["status"] == "summary"
        assert summary["total_tests"] > 0


class TestPerformanceUtilities:
    """Test performance utility functions."""
    
    def test_record_api_performance(self):
        """Test API performance recording utility."""
        monitor = get_performance_monitor()
        initial_calls = monitor.api_calls
        initial_errors = monitor.api_errors
        
        # Reset counters for this test
        monitor.api_calls = 0
        monitor.api_errors = 0
        
        # Record some API calls
        record_api_performance(150.0, True)
        record_api_performance(200.0, False)
        
        assert monitor.api_calls == 2  # All calls (successful + failed)
        assert monitor.api_errors == 1
    
    @pytest.mark.asyncio
    async def test_performance_benchmark_decorator(self):
        """Test performance benchmark decorator."""
        monitor = get_performance_monitor()
        initial_benchmarks = len(monitor.benchmarks)
        
        async with performance_benchmark("test_benchmark"):
            await asyncio.sleep(0.01)
        
        assert len(monitor.benchmarks) == initial_benchmarks + 1
        benchmark = monitor.benchmarks[-1]
        assert benchmark.test_name == "test_benchmark"
        assert benchmark.success is True


if __name__ == "__main__":
    pytest.main([__file__])
