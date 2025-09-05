#!/usr/bin/env python3
"""Simplified production readiness verification script for the 2KCompLeague Discord Bot."""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleProductionReadinessChecker:
    """Check essential components for production readiness without importing modules."""
    
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
            ("Makefile", "Build and deployment commands"),
            ("PRODUCTION_DEPLOYMENT.md", "Production deployment guide")
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
            "scripts/performance_test.py",
            "scripts/production_ready.py"
        ]
        
        for script_file in script_files:
            self.check_file_exists(script_file, f"Script: {script_file}")
    
    def check_core_modules(self) -> None:
        """Check core module files exist."""
        logger.info("🔍 Checking core modules...")
        
        core_modules = [
            "core/__init__.py",
            "core/types.py",
            "core/config.py",
            "core/logging.py",
            "core/http.py",
            "core/sportspress.py",
            "core/leaders.py",
            "core/records.py",
            "core/milestones.py",
            "core/health.py",
            "core/health_server.py",
            "core/performance.py",
            "core/performance_testing.py",
            "core/performance_optimizer.py"
        ]
        
        for module_file in core_modules:
            self.check_file_exists(module_file, f"Core module: {module_file}")
    
    def check_python_syntax(self) -> None:
        """Check Python syntax of key files."""
        logger.info("🔍 Checking Python syntax...")
        
        key_files = [
            "bot.py",
            "core/types.py",
            "core/config.py",
            "core/performance.py"
        ]
        
        for file_path in key_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        compile(f.read(), file_path, 'exec')
                    self.add_check(f"Python syntax: {file_path}", True)
                except SyntaxError as e:
                    self.add_check(f"Python syntax: {file_path}", False, f"Syntax error: {e}")
                except Exception as e:
                    self.add_check(f"Python syntax: {file_path}", False, f"Error: {e}")
            else:
                self.add_check(f"Python syntax: {file_path}", False, "File not found")
    
    def check_requirements(self) -> None:
        """Check requirements.txt for essential dependencies."""
        logger.info("🔍 Checking requirements...")
        
        requirements_path = Path("requirements.txt")
        if requirements_path.exists():
            content = requirements_path.read_text()
            essential_deps = [
                "discord.py",
                "aiohttp",
                "pydantic",
                "pytest"
            ]
            
            for dep in essential_deps:
                if dep in content:
                    self.add_check(f"Required dependency: {dep}", True)
                else:
                    self.add_check(f"Required dependency: {dep}", False, f"Missing: {dep}")
        else:
            for dep in ["discord.py", "aiohttp", "pydantic", "pytest"]:
                self.add_check(f"Required dependency: {dep}", False, "requirements.txt not found")
    
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
    
    def run_all_checks(self) -> Dict:
        """Run all production readiness checks."""
        logger.info("🚀 Starting simplified production readiness verification...")
        logger.info("=" * 60)
        
        # Run all checks
        self.check_file_structure()
        self.check_core_modules()
        self.check_test_coverage()
        self.check_docker_configuration()
        self.check_scripts()
        self.check_python_syntax()
        self.check_requirements()
        
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


def main():
    """Main function."""
    checker = SimpleProductionReadinessChecker()
    report = checker.run_all_checks()
    
    # Exit with appropriate code
    if report['summary']['production_ready']:
        logger.info("\n🎉 Production readiness verification completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n⚠️  Production readiness verification failed!")
        logger.error("Please fix all issues before proceeding with deployment.")
        sys.exit(1)


if __name__ == "__main__":
    main()
