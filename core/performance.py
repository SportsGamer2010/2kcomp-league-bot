"""Performance monitoring and optimization for the Discord bot."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    active_connections: int = 0
    background_tasks: int = 0
    api_calls_per_minute: float = 0.0
    response_time_avg_ms: float = 0.0
    error_rate: float = 0.0


@dataclass
class PerformanceBenchmark:
    """Performance benchmark results."""
    
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    success: bool
    metrics: PerformanceMetrics
    notes: str = ""


class PerformanceMonitor:
    """Performance monitoring and optimization coordinator."""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.benchmarks: List[PerformanceBenchmark] = []
        self.start_time = time.time()
        self.last_metrics_time = time.time()
        self.metrics_interval = 60  # Collect metrics every 60 seconds
        self.max_history_size = 1440  # Keep 24 hours of metrics (1440 minutes)
        
        # Performance counters
        self.api_calls = 0
        self.api_errors = 0
        self.response_times: List[float] = []
        self.max_response_times = 100  # Keep last 100 response times
        
        # Optimization flags
        self.auto_optimize = True
        self.performance_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'response_time_ms': 1000.0,
            'error_rate': 5.0
        }
    
    def collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics."""
        try:
            process = psutil.Process()
            
            # CPU and memory
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Disk I/O
            disk_io = process.io_counters()
            disk_read_mb = disk_io.read_bytes / 1024 / 1024
            disk_write_mb = disk_io.write_bytes / 1024 / 1024
            
            # Network I/O
            network_io = psutil.net_io_counters()
            net_sent_mb = network_io.bytes_sent / 1024 / 1024
            net_recv_mb = network_io.bytes_recv / 1024 / 1024
            
            # Calculate API metrics
            current_time = time.time()
            time_diff = current_time - self.last_metrics_time
            api_calls_per_minute = (self.api_calls / time_diff * 60) if time_diff > 0 else 0
            
            # Calculate response time average
            response_time_avg = (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0
            )
            
            # Calculate error rate
            total_calls = self.api_calls + self.api_errors
            error_rate = (self.api_errors / total_calls * 100) if total_calls > 0 else 0
            
            metrics = PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_mb=memory_info.rss / 1024 / 1024,
                memory_percent=memory_percent,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=net_sent_mb,
                network_recv_mb=net_recv_mb,
                api_calls_per_minute=api_calls_per_minute,
                response_time_avg_ms=response_time_avg,
                error_rate=error_rate
            )
            
            # Reset counters for next interval
            self.api_calls = 0
            self.api_errors = 0
            self.last_metrics_time = current_time
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return PerformanceMetrics()
    
    def record_api_call(self, response_time_ms: float, success: bool = True):
        """Record an API call for performance tracking."""
        self.api_calls += 1
        if not success:
            self.api_errors += 1
        
        # Add response time to rolling window
        self.response_times.append(response_time_ms)
        if len(self.response_times) > self.max_response_times:
            self.response_times.pop(0)
    
    def add_metrics(self, metrics: PerformanceMetrics):
        """Add metrics to history."""
        self.metrics_history.append(metrics)
        
        # Trim history if it exceeds max size
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
    
    def get_recent_metrics(self, minutes: int = 60) -> List[PerformanceMetrics]:
        """Get metrics from the last N minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
    
    def get_performance_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for the last N minutes."""
        recent_metrics = self.get_recent_metrics(minutes)
        
        if not recent_metrics:
            return {"status": "no_data", "message": "No metrics available"}
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_mb for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.response_time_avg_ms for m in recent_metrics) / len(recent_metrics)
        avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
        
        # Find peaks
        max_cpu = max(m.cpu_percent for m in recent_metrics)
        max_memory = max(m.memory_mb for m in recent_metrics)
        max_response_time = max(m.response_time_avg_ms for m in recent_metrics)
        
        return {
            "status": "healthy",
            "period_minutes": minutes,
            "metrics_count": len(recent_metrics),
            "averages": {
                "cpu_percent": round(avg_cpu, 2),
                "memory_mb": round(avg_memory, 2),
                "response_time_ms": round(avg_response_time, 2),
                "error_rate": round(avg_error_rate, 2)
            },
            "peaks": {
                "cpu_percent": round(max_cpu, 2),
                "memory_mb": round(max_memory, 2),
                "response_time_ms": round(max_response_time, 2)
            },
            "current": {
                "cpu_percent": round(recent_metrics[-1].cpu_percent, 2),
                "memory_mb": round(recent_metrics[-1].memory_mb, 2),
                "response_time_ms": round(recent_metrics[-1].response_time_avg_ms, 2)
            }
        }
    
    def check_performance_health(self) -> Dict[str, Any]:
        """Check if performance is within acceptable thresholds."""
        current_metrics = self.collect_system_metrics()
        
        issues = []
        warnings = []
        
        # Check CPU usage
        if current_metrics.cpu_percent > self.performance_thresholds['cpu_percent']:
            issues.append(f"High CPU usage: {current_metrics.cpu_percent:.1f}%")
        elif current_metrics.cpu_percent > self.performance_thresholds['cpu_percent'] * 0.7:
            warnings.append(f"Elevated CPU usage: {current_metrics.cpu_percent:.1f}%")
        
        # Check memory usage
        if current_metrics.memory_percent > self.performance_thresholds['memory_percent']:
            issues.append(f"High memory usage: {current_metrics.memory_percent:.1f}%")
        elif current_metrics.memory_percent > self.performance_thresholds['memory_percent'] * 0.8:
            warnings.append(f"Elevated memory usage: {current_metrics.memory_percent:.1f}%")
        
        # Check response times
        if current_metrics.response_time_avg_ms > self.performance_thresholds['response_time_ms']:
            issues.append(f"Slow response time: {current_metrics.response_time_avg_ms:.1f}ms")
        elif current_metrics.response_time_avg_ms > self.performance_thresholds['response_time_ms'] * 0.8:
            warnings.append(f"Elevated response time: {current_metrics.response_time_avg_ms:.1f}ms")
        
        # Check error rate
        if current_metrics.error_rate > self.performance_thresholds['error_rate']:
            issues.append(f"High error rate: {current_metrics.error_rate:.1f}%")
        elif current_metrics.error_rate > self.performance_thresholds['error_rate'] * 0.8:
            warnings.append(f"Elevated error rate: {current_metrics.error_rate:.1f}%")
        
        status = "healthy"
        if issues:
            status = "critical"
        elif warnings:
            status = "degraded"
        
        return {
            "status": status,
            "timestamp": current_metrics.timestamp.isoformat(),
            "issues": issues,
            "warnings": warnings,
            "metrics": {
                "cpu_percent": round(current_metrics.cpu_percent, 2),
                "memory_mb": round(current_metrics.memory_mb, 2),
                "memory_percent": round(current_metrics.memory_percent, 2),
                "response_time_ms": round(current_metrics.response_time_avg_ms, 2),
                "error_rate": round(current_metrics.error_rate, 2)
            }
        }
    
    @asynccontextmanager
    async def benchmark(self, test_name: str):
        """Context manager for performance benchmarking."""
        start_time = datetime.now()
        start_metrics = self.collect_system_metrics()
        
        try:
            yield
            success = True
            notes = "Benchmark completed successfully"
        except Exception as e:
            success = False
            notes = f"Benchmark failed: {e}"
            raise
        finally:
            end_time = datetime.now()
            end_metrics = self.collect_system_metrics()
            
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            benchmark = PerformanceBenchmark(
                test_name=test_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                success=success,
                metrics=end_metrics,
                notes=notes
            )
            
            self.benchmarks.append(benchmark)
            logger.info(f"Benchmark '{test_name}': {duration_ms:.2f}ms ({'SUCCESS' if success else 'FAILED'})")
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        summary = self.get_performance_summary(60)  # Last hour
        
        if summary.get("status") == "no_data":
            return ["Insufficient performance data for recommendations"]
        
        avg_metrics = summary.get("averages", {})
        
        # CPU optimization
        if avg_metrics.get("cpu_percent", 0) > 70:
            recommendations.append("Consider reducing background task frequency")
            recommendations.append("Optimize API call batching")
        
        # Memory optimization
        if avg_metrics.get("memory_mb", 0) > 500:  # 500MB threshold
            recommendations.append("Review memory usage in data processing")
            recommendations.append("Consider implementing data pagination")
        
        # Response time optimization
        if avg_metrics.get("response_time_ms", 0) > 500:
            recommendations.append("Optimize API response handling")
            recommendations.append("Consider implementing caching")
        
        # Error rate optimization
        if avg_metrics.get("error_rate", 0) > 2:
            recommendations.append("Review error handling and retry logic")
            recommendations.append("Check API rate limiting configuration")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable ranges")
        
        return recommendations
    
    def optimize_background_tasks(self) -> Dict[str, Any]:
        """Automatically optimize background task intervals based on performance."""
        if not self.auto_optimize:
            return {"status": "disabled", "message": "Auto-optimization is disabled"}
        
        summary = self.get_performance_summary(30)  # Last 30 minutes
        
        if summary.get("status") == "no_data":
            return {"status": "no_data", "message": "Insufficient data for optimization"}
        
        current_cpu = summary.get("current", {}).get("cpu_percent", 0)
        current_memory = summary.get("current", {}).get("memory_percent", 0)
        
        optimizations = {}
        
        # CPU-based optimization
        if current_cpu > 80:
            optimizations["poll_interval"] = "increase"
            optimizations["reason"] = "High CPU usage detected"
        elif current_cpu < 30:
            optimizations["poll_interval"] = "decrease"
            optimizations["reason"] = "Low CPU usage, can increase responsiveness"
        
        # Memory-based optimization
        if current_memory > 85:
            optimizations["memory_cleanup"] = "enabled"
            optimizations["reason"] = "High memory usage detected"
        
        return {
            "status": "optimized" if optimizations else "no_changes_needed",
            "optimizations": optimizations,
            "current_metrics": {
                "cpu_percent": current_cpu,
                "memory_percent": current_memory
            }
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return performance_monitor


async def start_performance_monitoring():
    """Start continuous performance monitoring."""
    monitor = get_performance_monitor()
    
    while True:
        try:
            # Collect metrics
            metrics = monitor.collect_system_metrics()
            monitor.add_metrics(metrics)
            
            # Check health
            health = monitor.check_performance_health()
            if health["status"] != "healthy":
                logger.warning(f"Performance health check: {health['status']}")
                if health["issues"]:
                    logger.error(f"Performance issues: {health['issues']}")
                if health["warnings"]:
                    logger.warning(f"Performance warnings: {health['warnings']}")
            
            # Auto-optimize if enabled
            if monitor.auto_optimize:
                optimization = monitor.optimize_background_tasks()
                if optimization["status"] == "optimized":
                    logger.info(f"Performance optimization applied: {optimization['optimizations']}")
            
            # Wait for next collection interval
            await asyncio.sleep(monitor.metrics_interval)
            
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
            await asyncio.sleep(10)  # Wait before retrying


def record_api_performance(response_time_ms: float, success: bool = True):
    """Record API call performance (convenience function)."""
    get_performance_monitor().record_api_call(response_time_ms, success)


@asynccontextmanager
async def performance_benchmark(test_name: str):
    """Context manager for performance benchmarking (convenience function)."""
    async with get_performance_monitor().benchmark(test_name):
        yield
