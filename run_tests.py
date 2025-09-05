#!/usr/bin/env python3
"""Test runner script for 2KCompLeague Discord Bot."""

import sys
import subprocess
import os
from pathlib import Path


def run_tests():
    """Run the test suite."""
    print("🧪 Running 2KCompLeague Discord Bot Test Suite")
    print("=" * 50)
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} found")
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"], check=True)
    
    # Run the tests
    print("\n🚀 Starting test execution...")
    print("-" * 30)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--color=yes"
        ], check=False)
        
        print("\n" + "=" * 50)
        if result.returncode == 0:
            print("🎉 All tests passed!")
        else:
            print(f"❌ Some tests failed (exit code: {result.returncode})")
        
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running tests: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1


def run_specific_test(test_path):
    """Run a specific test file or test function."""
    print(f"🧪 Running specific test: {test_path}")
    print("=" * 50)
    
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            test_path,
            "-v",
            "--tb=short",
            "--color=yes"
        ], check=False)
        
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running test: {e}")
        return 1


def show_test_coverage():
    """Show test coverage information."""
    print("📊 Test Coverage Information")
    print("=" * 50)
    
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    try:
        # Check if coverage is installed
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pytest-cov"
        ], check=True)
        
        # Run tests with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "--cov=core",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "-v"
        ], check=False)
        
        print(f"\n📁 Coverage report generated in: {project_dir}/htmlcov/")
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running coverage: {e}")
        return 1


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "coverage":
            return show_test_coverage()
        elif command == "help":
            print("""
🧪 2KCompLeague Discord Bot Test Runner

Usage:
  python run_tests.py              # Run all tests
  python run_tests.py coverage     # Run tests with coverage report
  python run_tests.py help         # Show this help message

Examples:
  python run_tests.py tests/test_records.py
  python run_tests.py tests/test_records.py::TestRecordCandidate
  python run_tests.py -k "test_points"  # Run tests matching pattern
            """)
            return 0
        else:
            # Treat as specific test path
            return run_specific_test(command)
    else:
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())
