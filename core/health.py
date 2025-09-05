"""Health check and monitoring functionality for the Discord bot."""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status information."""

    status: str  # "healthy", "unhealthy", "degraded"
    timestamp: datetime
    uptime_seconds: float
    version: str
    checks: Dict[str, Dict[str, Any]]


class HealthChecker:
    """Health check coordinator for the Discord bot."""

    def __init__(self, bot_start_time: float, version: str = "1.0.0"):
        self.bot_start_time = bot_start_time
        self.version = version
        self.last_check_time = time.time()
        self.health_history = []

    def get_uptime(self) -> float:
        """Get bot uptime in seconds."""
        return time.time() - self.bot_start_time

    def format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}h"
        else:
            days = seconds / 86400
            return f"{days:.1f}d"

    def check_bot_status(self) -> Dict[str, Any]:
        """Check basic bot status."""
        try:
            uptime = self.get_uptime()
            return {
                "status": "healthy",
                "uptime": uptime,
                "uptime_formatted": self.format_uptime(uptime),
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Bot status check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    def check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage (basic implementation)."""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            return {
                "status": "healthy" if memory_percent < 80 else "degraded",
                "memory_mb": memory_info.rss / 1024 / 1024,
                "memory_percent": memory_percent,
                "last_check": datetime.now().isoformat(),
            }
        except ImportError:
            # psutil not available, return basic status
            return {
                "status": "healthy",
                "note": "psutil not available for detailed memory monitoring",
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    def check_discord_connection(self, bot) -> Dict[str, Any]:
        """Check Discord connection status."""
        try:
            if bot.is_ready():
                latency = bot.latency * 1000  # Convert to milliseconds
                return {
                    "status": "healthy" if latency < 200 else "degraded",
                    "latency_ms": latency,
                    "guilds_count": len(bot.guilds),
                    "last_check": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Bot not ready",
                    "last_check": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Discord connection check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    def check_background_tasks(self, bot) -> Dict[str, Any]:
        """Check background task status."""
        try:
            # Check if background tasks are running
            task_status = {}

            # Check leaders monitoring task
            if hasattr(bot, "leaders_task") and bot.leaders_task:
                task_status["leaders_monitoring"] = {
                    "status": "running" if not bot.leaders_task.done() else "completed",
                    "done": bot.leaders_task.done(),
                    "cancelled": bot.leaders_task.cancelled(),
                }

            # Check milestones task
            if hasattr(bot, "milestones_task") and bot.milestones_task:
                task_status["milestones_monitoring"] = {
                    "status": (
                        "running" if not bot.milestones_task.done() else "completed"
                    ),
                    "done": bot.milestones_task.done(),
                    "cancelled": bot.milestones_task.cancelled(),
                }

            # Check records task
            if hasattr(bot, "records_task") and bot.records_task:
                task_status["records_monitoring"] = {
                    "status": "running" if not bot.records_task.done() else "completed",
                    "done": bot.records_task.done(),
                    "cancelled": bot.records_task.cancelled(),
                }

            overall_status = "healthy"
            if not task_status:
                overall_status = "degraded"
            elif any(task.get("done", False) for task in task_status.values()):
                overall_status = "degraded"

            return {
                "status": overall_status,
                "tasks": task_status,
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Background tasks check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    def run_health_check(self, bot) -> HealthStatus:
        """Run comprehensive health check."""
        logger.info("Running health check...")

        checks = {
            "bot_status": self.check_bot_status(),
            "memory_usage": self.check_memory_usage(),
            "discord_connection": self.check_discord_connection(bot),
            "background_tasks": self.check_background_tasks(bot),
        }

        # Determine overall status
        status_counts = {}
        for _check_name, check_result in checks.items():
            check_status = check_result.get("status", "unknown")
            status_counts[check_status] = status_counts.get(check_status, 0) + 1

        overall_status = "healthy"
        if status_counts.get("unhealthy", 0) > 0:
            overall_status = "unhealthy"
        elif status_counts.get("degraded", 0) > 0:
            overall_status = "degraded"

        health_status = HealthStatus(
            status=overall_status,
            timestamp=datetime.now(),
            uptime_seconds=self.get_uptime(),
            version=self.version,
            checks=checks,
        )

        # Store in history (keep last 10 checks)
        self.health_history.append(health_status)
        if len(self.health_history) > 10:
            self.health_history.pop(0)

        self.last_check_time = time.time()
        logger.info(f"Health check completed: {overall_status}")

        return health_status

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health check summary for monitoring."""
        if not self.health_history:
            return {"status": "unknown", "message": "No health checks performed yet"}

        latest = self.health_history[-1]

        # Calculate availability percentage
        total_checks = len(self.health_history)
        healthy_checks = sum(1 for h in self.health_history if h.status == "healthy")
        availability = (healthy_checks / total_checks) * 100 if total_checks > 0 else 0

        return {
            "current_status": latest.status,
            "availability_percent": round(availability, 2),
            "uptime": self.format_uptime(latest.uptime_seconds),
            "version": latest.version,
            "last_check": latest.timestamp.isoformat(),
            "checks_performed": total_checks,
        }


def create_health_response(health_status: HealthStatus) -> Dict[str, Any]:
    """Create HTTP response for health check endpoint."""
    return {
        "status": health_status.status,
        "timestamp": health_status.timestamp.isoformat(),
        "uptime": health_status.uptime_seconds,
        "uptime_formatted": f"{health_status.uptime_seconds / 3600:.1f}h",
        "version": health_status.version,
        "checks": health_status.checks,
    }


def create_metrics_response(health_status: HealthStatus) -> str:
    """Create Prometheus metrics format response."""
    metrics = []

    # Bot metrics
    metrics.append("# HELP bot_uptime_seconds Bot uptime in seconds")
    metrics.append("# TYPE bot_uptime_seconds gauge")
    metrics.append(f"bot_uptime_seconds {health_status.uptime_seconds}")

    # Health status (1 = healthy, 0 = unhealthy/degraded)
    health_value = 1 if health_status.status == "healthy" else 0
    metrics.append(
        "# HELP bot_health_status Bot health status (1=healthy, 0=unhealthy)"
    )
    metrics.append("# TYPE bot_health_status gauge")
    metrics.append(f"bot_health_status {health_value}")

    # Individual check metrics
    for check_name, check_result in health_status.checks.items():
        check_value = 1 if check_result.get("status") == "healthy" else 0
        metrics.append(
            f"# HELP bot_check_{check_name}_status {check_name} check status"
        )
        metrics.append(f"# TYPE bot_check_{check_name}_status gauge")
        metrics.append(f"bot_check_{check_name}_status {check_value}")

    return "\n".join(metrics)
