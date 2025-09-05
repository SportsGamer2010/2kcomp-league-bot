#!/usr/bin/env python3
"""Production readiness verification script for the 2KCompLeague Discord Bot."""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.performance import get_performance_monitor
from core.health import HealthChecker

# Try to import settings, but don't fail if environment is not configured
try:
    from core.config import settings
    SETTINGS_AVAILABLE = True
except Exception:
    SETTINGS_AVAILABLE = False
    settings = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionReadinessChecker:
    """Check all components for production readiness."""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_total = 0
        self.issues = []
        
    def add_check(self, name: str, passed: bool, details: str = ""):
        """Add a check result."""
        self.checks_total += 1
        if passed:
            self.checks_passed += 1
            logger.info(f"✅ {name}: PASSED")
        else:
            logger.error(f"❌ {name}: FAILED - {details}")
            self.issues.append(f"{name}: {details}")
    
    def check_file_exists(self, file_path: str, description: str) -> bool:
        """Check if a file exists."""
        path = Path(file_path)
        exists = path.exists()
        self.add_check(description, exists, f"File not found: {file_path}")
        return exists
    
    def check_imports(self) -> None:
        """Check if all core modules can be imported."""
        logger.info("🔍 Checking module imports...")
        
        try:
            from core.types import PlayerStats, LeaderEntry, SingleGameRecord
            self.add_check("Core types import", True)
        except ImportError as e:
            self.add_check("Core types import", False, str(e))
        
        try:
            from core.config import settings
            self.add_check("Configuration import", True)
        except Exception as e:
            self.add_check("Configuration import", False, f"Environment not configured: {str(e)[:100]}")
        
        try:
            from core.http import HTTPClient
            self.add_check("HTTP client import", True)
        except ImportError as e:
            self.add_check("HTTP client import", False, str(e))
        
        try:
            from core.sportspress import SportsPressAPI
            self.add_check("SportsPress API import", True)
        except ImportError as e:
            self.add_check("SportsPress API import", False, str(e))
        
        try:
            from core.leaders import LeadersModule
            self.add_check("Leaders module import", True)
        except ImportError as e:
            self.add_check("Leaders module import", False, str(e))
        
        try:
            from core.records import RecordsModule
            self.add_check("Records module import", True)
        except ImportError as e:
            self.add_check("Records module import", False, str(e))
        
        try:
            from core.milestones import MilestonesModule
            self.add_check("Milestones module import", True)
        except ImportError as e:
            self.add_check("Milestones module import", False, str(e))
        
        try:
            from core.health import HealthChecker
            self.add_check("Health module import", True)
        except ImportError as e:
            self.add_check("Health module import", False, str(e))
        
        try:
            from core.performance import PerformanceMonitor
            self.add_check("Performance module import", True)
        except ImportError as e:
            self.add_check("Performance module import", False, str(e))
    
    def check_configuration(self) -> None:
        """Check configuration settings."""
        logger.info("🔍 Checking configuration...")
        
        if not SETTINGS_AVAILABLE:
            self.add_check("Configuration validation", False, "Settings not available - environment not configured")
            return
        
        try:
            # Check required environment variables
            required_vars = [
                'DISCORD_TOKEN',
                'GUILD_ID',
                'ANNOUNCE_CHANNEL_ID',
                'HISTORY_CHANNEL_ID',
                'SPORTSPRESS_BASE'
            ]
            
            for var in required_vars:
                value = getattr(settings, var, None)
                if value:
                    self.add_check(f"Config: {var}", True)
                else:
                    self.add_check(f"Config: {var}", False, f"Missing or empty: {var}")
            
            # Check configuration values
            if hasattr(settings, 'POLL_INTERVAL_SECONDS'):
                interval = settings.POLL_INTERVAL_SECONDS
                if 60 <= interval <= 3600:  # Between 1 minute and 1 hour
                    self.add_check("Poll interval validation", True)
                else:
                    self.add_check("Poll interval validation", False, f"Invalid interval: {interval}s")
            
            if hasattr(settings, 'HTTP_TIMEOUT'):
                timeout = settings.HTTP_TIMEOUT
                if 10 <= timeout <= 120:  # Between 10 and 120 seconds
                    self.add_check("HTTP timeout validation", True)
                else:
                    self.add_check("HTTP timeout validation", False, f"Invalid timeout: {timeout}s")
                    
        except Exception as e:
            self.add_check("Configuration validation", False, str(e))
    
    def check_file_structure(self) -> None:
        """Check required file structure."""
        logger.info("🔍 Checking file structure...")
        
        required_files = [
            ("Dockerfile", "Docker configuration"),
            ("docker-compose.yml", "Docker Compose configuration"),
            ("docker-compose.prod.yml", "Production Docker configuration"),
            ("requirements.txt", "Python dependencies"),
            ("README.md", "Project documentation"),
            ("env.example", "Environment template"),
            ("pyproject.toml", "Python project configuration"),
            ("Makefile", "Build and deployment commands")
        ]
        
        for file_path, description in required_files:
            self.check_file_exists(file_path, description)
        
        required_dirs = [
            ("core/", "Core modules directory"),
            ("tests/", "Test suite directory"),
            ("scripts/", "Utility scripts directory"),
            ("data/", "Data storage directory")
        ]
        
        for dir_path, description in required_dirs:
            path = Path(dir_path)
            exists = path.exists() and path.is_dir()
            self.add_check(description, exists, f"Directory not found: {dir_path}")
    
    def check_test_coverage(self) -> None:
        """Check test coverage and results."""
        logger.info("🔍 Checking test coverage...")
        
        # Check if test files exist
        test_files = [
            "tests/test_records.py",
            "tests/test_leaders.py", 
            "tests/test_types.py",
            "tests/test_milestones.py",
            "tests/test_health.py",
            "tests/test_integration.py",
            "tests/test_performance_optimization.py"
        ]
        
        for test_file in test_files:
            self.check_file_exists(test_file, f"Test file: {test_file}")
        
        # Check if tests can be imported (basic syntax check)
        try:
            import tests.test_records
            import tests.test_leaders
            import tests.test_types
            import tests.test_milestones
            import tests.test_health
            import tests.test_integration
            import tests.test_performance_optimization
            self.add_check("Test module imports", True)
        except Exception as e:
            self.add_check("Test module imports", False, str(e))
    
    def check_docker_configuration(self) -> None:
        """Check Docker configuration files."""
        logger.info("🔍 Checking Docker configuration...")
        
        # Check Dockerfile
        dockerfile_path = Path("Dockerfile")
        if dockerfile_path.exists():
            content = dockerfile_path.read_text()
            if "FROM python" in content:
                self.add_check("Dockerfile base image", True)
            else:
                self.add_check("Dockerfile base image", False, "Not using Python base image")
            
            if "COPY requirements.txt" in content:
                self.add_check("Dockerfile requirements copy", True)
            else:
                self.add_check("Dockerfile requirements copy", False, "Missing requirements.txt copy")
        else:
            self.add_check("Dockerfile base image", False, "Dockerfile not found")
            self.add_check("Dockerfile requirements copy", False, "Dockerfile not found")
        
        # Check docker-compose files
        compose_files = ["docker-compose.yml", "docker-compose.prod.yml"]
        for compose_file in compose_files:
            if Path(compose_file).exists():
                self.add_check(f"Docker Compose: {compose_file}", True)
            else:
                self.add_check(f"Docker Compose: {compose_file}", False, f"File not found: {compose_file}")
    
    def check_scripts(self) -> None:
        """Check utility scripts."""
        logger.info("🔍 Checking utility scripts...")
        
        script_files = [
            "scripts/deploy.sh",
            "scripts/health-monitor.sh",
            "scripts/send-alert.sh",
            "scripts/performance_test.py"
        ]
        
        for script_file in script_files:
            self.check_file_exists(script_file, f"Script: {script_file}")
    
    async def check_performance_monitoring(self) -> None:
        """Check performance monitoring setup."""
        logger.info("🔍 Checking performance monitoring...")
        
        try:
            monitor = get_performance_monitor()
            if monitor:
                self.add_check("Performance monitor instance", True)
                
                # Check if monitor can collect metrics
                metrics = monitor.collect_system_metrics()
                if metrics:
                    self.add_check("System metrics collection", True)
                else:
                    self.add_check("System metrics collection", False, "No metrics returned")
            else:
                self.add_check("Performance monitor instance", False, "Monitor not available")
        except Exception as e:
            self.add_check("Performance monitoring", False, str(e))
    
    async def check_health_monitoring(self) -> None:
        """Check health monitoring setup."""
        logger.info("🔍 Checking health monitoring...")
        
        try:
            # Create a health checker instance for testing
            checker = HealthChecker(bot_start_time=time.time(), version="1.0.0")
            if checker:
                self.add_check("Health checker instance", True)
                
                # Check if health check can run
                health_status = checker.check_bot_status()
                if health_status:
                    self.add_check("Health check execution", True)
                else:
                    self.add_check("Health check execution", False, "No health status returned")
            else:
                self.add_check("Health checker instance", False, "Health checker not available")
        except Exception as e:
            self.add_check("Health monitoring", False, str(e))
    
    def generate_report(self) -> Dict:
        """Generate production readiness report."""
        success_rate = (self.checks_passed / self.checks_total * 100) if self.checks_total > 0 else 0
        
        report = {
            "summary": {
                "total_checks": self.checks_total,
                "passed_checks": self.checks_passed,
                "failed_checks": self.checks_total - self.checks_passed,
                "success_rate": round(success_rate, 2),
                "production_ready": success_rate >= 95.0
            },
            "issues": self.issues,
            "recommendations": []
        }
        
        if success_rate < 95.0:
            report["recommendations"].append("Fix all failed checks before production deployment")
        
        if not self.issues:
            report["recommendations"].append("All checks passed! Ready for production deployment")
        
        return report
    
    async def run_all_checks(self) -> Dict:
        """Run all production readiness checks."""
        logger.info("🚀 Starting production readiness verification...")
        logger.info("=" * 60)
        
        # Run all checks
        self.check_file_structure()
        self.check_imports()
        self.check_configuration()
        self.check_test_coverage()
        self.check_docker_configuration()
        self.check_scripts()
        await self.check_performance_monitoring()
        await self.check_health_monitoring()
        
        # Generate and display report
        logger.info("=" * 60)
        report = self.generate_report()
        
        logger.info(f"📊 Production Readiness Report:")
        logger.info(f"   Total Checks: {report['summary']['total_checks']}")
        logger.info(f"   Passed: {report['summary']['passed_checks']}")
        logger.info(f"   Failed: {report['summary']['failed_checks']}")
        logger.info(f"   Success Rate: {report['summary']['success_rate']}%")
        logger.info(f"   Production Ready: {'✅ YES' if report['summary']['production_ready'] else '❌ NO'}")
        
        if report['issues']:
            logger.info(f"\n🚨 Issues Found:")
            for issue in report['issues']:
                logger.info(f"   • {issue}")
        
        if report['recommendations']:
            logger.info(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                logger.info(f"   • {rec}")
        
        return report


async def main():
    """Main function."""
    checker = ProductionReadinessChecker()
    report = await checker.run_all_checks()
    
    # Exit with appropriate code
    if report['summary']['production_ready']:
        logger.info("\n🎉 Production readiness verification completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n⚠️  Production readiness verification failed!")
        logger.error("Please fix all issues before proceeding with deployment.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
