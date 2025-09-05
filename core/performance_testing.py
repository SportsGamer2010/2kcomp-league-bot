"""Performance testing and load testing for the Discord bot."""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor

import psutil

from .performance import get_performance_monitor, performance_benchmark

logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    
    test_name: str
    duration_seconds: int = 300  # 5 minutes default
    concurrent_users: int = 10
    requests_per_second: float = 5.0
    ramp_up_seconds: int = 60
    ramp_down_seconds: int = 60
    target_response_time_ms: float = 1000.0
    max_error_rate: float = 5.0


@dataclass
class LoadTestResult:
    """Results from a load test."""
    
    test_name: str
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate: float
    cpu_usage_avg: float
    memory_usage_avg: float
    status: str  # "passed", "failed", "degraded"


class LoadTester:
    """Load testing coordinator for the Discord bot."""
    
    def __init__(self):
        self.performance_monitor = get_performance_monitor()
        self.test_results: List[LoadTestResult] = []
        self.current_test: Optional[LoadTestConfig] = None
        self.is_running = False
        
        # Test scenarios
        self.test_scenarios = {
            "light_load": LoadTestConfig(
                test_name="Light Load Test",
                duration_seconds=120,
                concurrent_users=5,
                requests_per_second=2.0,
                target_response_time_ms=500.0
            ),
            "normal_load": LoadTestConfig(
                test_name="Normal Load Test",
                duration_seconds=300,
                concurrent_users=10,
                requests_per_second=5.0,
                target_response_time_ms=1000.0
            ),
            "heavy_load": LoadTestConfig(
                test_name="Heavy Load Test",
                duration_seconds=600,
                concurrent_users=25,
                requests_per_second=10.0,
                target_response_time_ms=2000.0
            ),
            "stress_test": LoadTestConfig(
                test_name="Stress Test",
                duration_seconds=900,
                concurrent_users=50,
                requests_per_second=20.0,
                target_response_time_ms=5000.0
            )
        }
    
    async def run_load_test(
        self,
        config: LoadTestConfig,
        test_function: Callable[[], Awaitable[Any]]
    ) -> LoadTestResult:
        """Run a load test with the specified configuration."""
        
        if self.is_running:
            raise RuntimeError("Another load test is already running")
        
        self.is_running = True
        self.current_test = config
        
        logger.info(f"Starting load test: {config.test_name}")
        logger.info(f"Duration: {config.duration_seconds}s, Users: {config.concurrent_users}, RPS: {config.requests_per_second}")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=config.duration_seconds)
        
        # Performance tracking
        response_times: List[float] = []
        request_results: List[bool] = []
        cpu_samples: List[float] = []
        memory_samples: List[float] = []
        
        # Calculate request intervals
        request_interval = 1.0 / config.requests_per_second
        total_requests = int(config.requests_per_second * config.duration_seconds)
        
        # Start performance monitoring
        monitor_task = asyncio.create_task(self._monitor_performance(cpu_samples, memory_samples))
        
        try:
            # Run the load test
            await self._execute_load_test(
                config, test_function, response_times, request_results,
                request_interval, total_requests, end_time
            )
            
        finally:
            # Stop monitoring
            monitor_task.cancel()
            self.is_running = False
            self.current_test = None
        
        # Calculate results
        end_time = datetime.now()
        result = self._calculate_test_results(
            config, start_time, end_time, response_times, request_results,
            cpu_samples, memory_samples
        )
        
        self.test_results.append(result)
        logger.info(f"Load test completed: {result.status}")
        logger.info(f"Total requests: {result.total_requests}, Success rate: {((result.successful_requests / result.total_requests) * 100):.1f}%")
        
        return result
    
    async def _execute_load_test(
        self,
        config: LoadTestConfig,
        test_function: Callable[[], Awaitable[Any]],
        response_times: List[float],
        request_results: List[bool],
        request_interval: float,
        total_requests: int,
        end_time: datetime
    ):
        """Execute the actual load test."""
        
        # Create semaphore to limit concurrent users
        semaphore = asyncio.Semaphore(config.concurrent_users)
        
        async def single_request():
            """Execute a single test request."""
            async with semaphore:
                start_time = time.time()
                try:
                    await test_function()
                    success = True
                except Exception as e:
                    logger.debug(f"Request failed: {e}")
                    success = False
                
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
                request_results.append(success)
        
        # Calculate ramp-up and ramp-down periods
        ramp_up_end = datetime.now() + timedelta(seconds=config.ramp_up_seconds)
        ramp_down_start = end_time - timedelta(seconds=config.ramp_down_seconds)
        
        current_rps = 0
        target_rps = config.requests_per_second
        
        while datetime.now() < end_time:
            # Ramp up
            if datetime.now() < ramp_up_end:
                progress = (datetime.now() - datetime.now() + timedelta(seconds=config.ramp_up_seconds)).total_seconds() / config.ramp_up_seconds
                current_rps = target_rps * progress
            # Ramp down
            elif datetime.now() > ramp_down_start:
                progress = (end_time - datetime.now()).total_seconds() / config.ramp_down_seconds
                current_rps = target_rps * progress
            else:
                current_rps = target_rps
            
            # Execute requests based on current RPS
            if current_rps > 0:
                interval = 1.0 / current_rps
                await asyncio.sleep(interval)
                
                # Create multiple concurrent requests
                tasks = []
                for i in range(min(config.concurrent_users, int(current_rps))):
                    tasks.append(asyncio.create_task(single_request()))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _monitor_performance(
        self,
        cpu_samples: List[float],
        memory_samples: List[float]
    ):
        """Monitor system performance during the load test."""
        while self.is_running:
            try:
                process = psutil.Process()
                cpu_samples.append(process.cpu_percent())
                memory_samples.append(process.memory_percent())
                await asyncio.sleep(1)  # Sample every second
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(5)
    
    def _calculate_test_results(
        self,
        config: LoadTestConfig,
        start_time: datetime,
        end_time: datetime,
        response_times: List[float],
        request_results: List[bool],
        cpu_samples: List[float],
        memory_samples: List[float]
    ) -> LoadTestResult:
        """Calculate test results from collected data."""
        
        total_requests = len(request_results)
        successful_requests = sum(request_results)
        failed_requests = total_requests - successful_requests
        
        if not response_times:
            return LoadTestResult(
                test_name=config.test_name,
                start_time=start_time,
                end_time=end_time,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                total_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                requests_per_second=0,
                error_rate=100.0,
                cpu_usage_avg=0,
                memory_usage_avg=0,
                status="failed"
            )
        
        # Response time statistics
        total_response_time = sum(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        avg_response_time = total_response_time / len(response_times)
        
        # Percentiles
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p99_index = int(len(sorted_times) * 0.99)
        p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
        p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
        
        # Calculate RPS and error rate
        duration = (end_time - start_time).total_seconds()
        requests_per_second = total_requests / duration if duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Performance averages
        cpu_usage_avg = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        memory_usage_avg = sum(memory_samples) / len(memory_samples) if memory_samples else 0
        
        # Determine test status
        status = "passed"
        if error_rate > config.max_error_rate:
            status = "failed"
        elif avg_response_time > config.target_response_time_ms:
            status = "degraded"
        
        return LoadTestResult(
            test_name=config.test_name,
            start_time=start_time,
            end_time=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_response_time_ms=total_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            cpu_usage_avg=cpu_usage_avg,
            memory_usage_avg=memory_usage_avg,
            status=status
        )
    
    async def run_scenario(self, scenario_name: str, test_function: Callable[[], Awaitable[Any]]) -> LoadTestResult:
        """Run a predefined test scenario."""
        if scenario_name not in self.test_scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(self.test_scenarios.keys())}")
        
        config = self.test_scenarios[scenario_name]
        return await self.run_load_test(config, test_function)
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all test results."""
        if not self.test_results:
            return {"status": "no_tests", "message": "No tests have been run"}
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.status == "passed")
        failed_tests = sum(1 for r in self.test_results if r.status == "failed")
        degraded_tests = sum(1 for r in self.test_results if r.status == "degraded")
        
        # Calculate overall performance metrics
        all_response_times = []
        all_error_rates = []
        all_cpu_usage = []
        all_memory_usage = []
        
        for result in self.test_results:
            if result.total_requests > 0:
                all_response_times.append(result.avg_response_time_ms)
                all_error_rates.append(result.error_rate)
                all_cpu_usage.append(result.cpu_usage_avg)
                all_memory_usage.append(result.memory_usage_avg)
        
        return {
            "status": "summary",
            "total_tests": total_tests,
            "test_results": {
                "passed": passed_tests,
                "failed": failed_tests,
                "degraded": degraded_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "performance_summary": {
                "avg_response_time_ms": sum(all_response_times) / len(all_response_times) if all_response_times else 0,
                "avg_error_rate": sum(all_error_rates) / len(all_error_rates) if all_error_rates else 0,
                "avg_cpu_usage": sum(all_cpu_usage) / len(all_cpu_usage) if all_cpu_usage else 0,
                "avg_memory_usage": sum(all_memory_usage) / len(all_memory_usage) if all_memory_usage else 0
            },
            "recent_tests": [
                {
                    "name": r.test_name,
                    "status": r.status,
                    "duration": (r.end_time - r.start_time).total_seconds(),
                    "requests": r.total_requests,
                    "avg_response_time": r.avg_response_time_ms,
                    "error_rate": r.error_rate
                }
                for r in self.test_results[-5:]  # Last 5 tests
            ]
        }


class StressTester:
    """Stress testing coordinator for the Discord bot."""
    
    def __init__(self):
        self.load_tester = LoadTester()
        self.breakpoint_found = False
        self.breakpoint_metrics: Optional[Dict[str, Any]] = None
    
    async def find_breakpoint(
        self,
        test_function: Callable[[], Awaitable[Any]],
        start_users: int = 1,
        max_users: int = 100,
        step_size: int = 5,
        test_duration: int = 60
    ) -> Dict[str, Any]:
        """Find the system breakpoint by gradually increasing load."""
        
        logger.info("Starting stress test to find system breakpoint")
        
        current_users = start_users
        breakpoint_found = False
        
        while current_users <= max_users and not breakpoint_found:
            logger.info(f"Testing with {current_users} concurrent users")
            
            # Create custom config for this test
            config = LoadTestConfig(
                test_name=f"Stress Test - {current_users} users",
                duration_seconds=test_duration,
                concurrent_users=current_users,
                requests_per_second=current_users * 2,  # 2 RPS per user
                target_response_time_ms=5000.0,  # Higher tolerance for stress tests
                max_error_rate=10.0  # Higher error tolerance
            )
            
            try:
                result = await self.load_tester.run_load_test(config, test_function)
                
                # Check if we've hit the breakpoint
                if result.status == "failed" or result.error_rate > 20:
                    breakpoint_found = True
                    self.breakpoint_found = True
                    self.breakpoint_metrics = {
                        "concurrent_users": current_users,
                        "error_rate": result.error_rate,
                        "avg_response_time": result.avg_response_time_ms,
                        "cpu_usage": result.cpu_usage_avg,
                        "memory_usage": result.memory_usage_avg
                    }
                    logger.info(f"Breakpoint found at {current_users} concurrent users")
                    break
                
                # If test passed, increase load
                current_users += step_size
                
            except Exception as e:
                logger.error(f"Stress test failed at {current_users} users: {e}")
                breakpoint_found = True
                self.breakpoint_metrics = {
                    "concurrent_users": current_users,
                    "error": str(e),
                    "status": "exception"
                }
                break
        
        if not breakpoint_found:
            logger.info(f"No breakpoint found up to {max_users} users")
            self.breakpoint_metrics = {
                "concurrent_users": max_users,
                "status": "no_breakpoint",
                "message": "System handled maximum load without breaking"
            }
        
        return {
            "breakpoint_found": self.breakpoint_found,
            "breakpoint_metrics": self.breakpoint_metrics,
            "max_users_tested": current_users,
            "recommendation": self._get_stress_test_recommendation()
        }
    
    def _get_stress_test_recommendation(self) -> str:
        """Get recommendations based on stress test results."""
        if not self.breakpoint_metrics:
            return "No stress test data available"
        
        if self.breakpoint_metrics.get("status") == "no_breakpoint":
            return "System is robust and can handle high loads. Consider testing with even higher loads."
        
        users = self.breakpoint_metrics.get("concurrent_users", 0)
        error_rate = self.breakpoint_metrics.get("error_rate", 0)
        
        if error_rate > 20:
            return f"System breaks at {users} concurrent users due to high error rate. Consider implementing better error handling and retry logic."
        else:
            return f"System becomes unstable at {users} concurrent users. Consider optimizing resource usage and implementing rate limiting."


# Global instances
load_tester = LoadTester()
stress_tester = StressTester()


def get_load_tester() -> LoadTester:
    """Get the global load tester instance."""
    return load_tester


def get_stress_tester() -> StressTester:
    """Get the global stress tester instance."""
    return stress_tester
