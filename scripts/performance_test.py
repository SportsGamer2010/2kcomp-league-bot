#!/usr/bin/env python3
"""Performance testing script for the 2KCompLeague Discord Bot."""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.performance import get_performance_monitor
from core.performance_testing import get_load_tester, get_stress_tester
from core.performance_optimizer import get_performance_optimizer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_performance_analysis():
    """Run comprehensive performance analysis."""
    logger.info("Starting performance analysis...")
    
    monitor = get_performance_monitor()
    optimizer = get_performance_optimizer()
    
    # Collect current metrics
    current_metrics = monitor.collect_system_metrics()
    logger.info(f"Current CPU usage: {current_metrics.cpu_percent:.1f}%")
    logger.info(f"Current memory usage: {current_metrics.memory_mb:.1f}MB ({current_metrics.memory_percent:.1f}%)")
    
    # Get performance summary
    summary = monitor.get_performance_summary(60)
    logger.info(f"Performance summary: {summary['status']}")
    
    # Check performance health
    health = monitor.check_performance_health()
    logger.info(f"Performance health: {health['status']}")
    
    if health['issues']:
        logger.warning(f"Performance issues: {health['issues']}")
    
    if health['warnings']:
        logger.warning(f"Performance warnings: {health['warnings']}")
    
    # Get optimization recommendations
    recommendations = monitor.get_optimization_recommendations()
    logger.info("Optimization recommendations:")
    for rec in recommendations:
        logger.info(f"  - {rec}")
    
    # Analyze performance for optimizations
    analysis = optimizer.analyze_performance(current_metrics)
    logger.info(f"Optimization priority: {analysis['priority']}")
    
    if analysis['recommended_actions']:
        logger.info("Recommended optimizations:")
        for action in analysis['recommended_actions']:
            logger.info(f"  - {action}")
    
    return {
        "current_metrics": {
            "cpu_percent": current_metrics.cpu_percent,
            "memory_mb": current_metrics.memory_mb,
            "memory_percent": current_metrics.memory_percent,
            "response_time_ms": current_metrics.response_time_avg_ms,
            "error_rate": current_metrics.error_rate
        },
        "performance_summary": summary,
        "health_status": health,
        "optimization_analysis": analysis,
        "recommendations": recommendations
    }


async def run_load_test(scenario: str, duration: int = None):
    """Run a load test with the specified scenario."""
    logger.info(f"Starting load test: {scenario}")
    
    load_tester = get_load_tester()
    
    if scenario not in load_tester.test_scenarios:
        logger.error(f"Unknown scenario: {scenario}")
        logger.info(f"Available scenarios: {list(load_tester.test_scenarios.keys())}")
        return None
    
    # Override duration if specified
    config = load_tester.test_scenarios[scenario]
    if duration:
        config.duration_seconds = duration
    
    logger.info(f"Test configuration: {config.duration_seconds}s, {config.concurrent_users} users, {config.requests_per_second} RPS")
    
    async def mock_test_function():
        """Mock test function that simulates bot operations."""
        # Simulate some work
        await asyncio.sleep(0.01)
        return "success"
    
    try:
        result = await load_tester.run_load_test(config, mock_test_function)
        
        logger.info(f"Load test completed: {result.status}")
        logger.info(f"Total requests: {result.total_requests}")
        logger.info(f"Successful requests: {result.successful_requests}")
        logger.info(f"Failed requests: {result.failed_requests}")
        logger.info(f"Average response time: {result.avg_response_time_ms:.2f}ms")
        logger.info(f"Error rate: {result.error_rate:.2f}%")
        logger.info(f"CPU usage average: {result.cpu_usage_avg:.2f}%")
        logger.info(f"Memory usage average: {result.memory_usage_avg:.2f}%")
        
        return result
        
    except Exception as e:
        logger.error(f"Load test failed: {e}")
        return None


async def run_stress_test(max_users: int = 50, step_size: int = 5):
    """Run a stress test to find system breakpoint."""
    logger.info(f"Starting stress test (max users: {max_users}, step size: {step_size})")
    
    stress_tester = get_stress_tester()
    
    async def mock_test_function():
        """Mock test function for stress testing."""
        await asyncio.sleep(0.01)
        return "success"
    
    try:
        result = await stress_tester.find_breakpoint(
            mock_test_function,
            start_users=1,
            max_users=max_users,
            step_size=step_size,
            test_duration=30  # Short duration for testing
        )
        
        logger.info(f"Stress test completed")
        logger.info(f"Breakpoint found: {result['breakpoint_found']}")
        
        if result['breakpoint_found']:
            metrics = result['breakpoint_metrics']
            logger.info(f"Breakpoint at {metrics.get('concurrent_users', 'unknown')} users")
            if 'error_rate' in metrics:
                logger.info(f"Error rate at breakpoint: {metrics['error_rate']:.2f}%")
        
        logger.info(f"Recommendation: {result['recommendation']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Stress test failed: {e}")
        return None


async def run_optimizations():
    """Run performance optimizations."""
    logger.info("Starting performance optimizations...")
    
    optimizer = get_performance_optimizer()
    
    # Get current status
    status = optimizer.get_optimization_status()
    logger.info(f"Current optimization status: {status['summary']['implementation_rate']} implemented")
    
    # Run auto-optimization
    result = await optimizer.auto_optimize()
    
    logger.info(f"Auto-optimization result: {result['action']}")
    
    if result['action'] == 'auto_optimization':
        if result['applied_optimizations']:
            logger.info(f"Applied optimizations: {result['applied_optimizations']}")
        if result['failed_optimizations']:
            logger.warning(f"Failed optimizations: {result['failed_optimizations']}")
    
    # Get updated status
    updated_status = optimizer.get_optimization_status()
    logger.info(f"Updated optimization status: {updated_status['summary']['implementation_rate']} implemented")
    
    return {
        "optimization_result": result,
        "status_before": status,
        "status_after": updated_status
    }


async def run_comprehensive_test():
    """Run a comprehensive performance test suite."""
    logger.info("Starting comprehensive performance test suite...")
    
    results = {}
    
    # 1. Performance analysis
    logger.info("\n=== Performance Analysis ===")
    results['analysis'] = await run_performance_analysis()
    
    # 2. Load tests
    logger.info("\n=== Load Testing ===")
    load_results = {}
    
    for scenario in ['light_load', 'normal_load']:
        logger.info(f"\n--- {scenario.upper()} ---")
        load_results[scenario] = await run_load_test(scenario, duration=30)  # Short duration for testing
    
    results['load_tests'] = load_results
    
    # 3. Stress test
    logger.info("\n=== Stress Testing ===")
    results['stress_test'] = await run_stress_test(max_users=20, step_size=2)
    
    # 4. Optimizations
    logger.info("\n=== Performance Optimizations ===")
    results['optimizations'] = await run_optimizations()
    
    # 5. Final analysis
    logger.info("\n=== Final Performance Analysis ===")
    results['final_analysis'] = await run_performance_analysis()
    
    return results


def save_results(results: dict, output_file: str):
    """Save test results to a JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Performance testing for 2KCompLeague Discord Bot")
    parser.add_argument(
        '--mode',
        choices=['analysis', 'load-test', 'stress-test', 'optimize', 'comprehensive'],
        default='comprehensive',
        help='Testing mode'
    )
    parser.add_argument(
        '--scenario',
        choices=['light_load', 'normal_load', 'heavy_load', 'stress_test'],
        help='Load test scenario (for load-test mode)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        help='Test duration in seconds (overrides scenario default)'
    )
    parser.add_argument(
        '--max-users',
        type=int,
        default=50,
        help='Maximum users for stress test'
    )
    parser.add_argument(
        '--step-size',
        type=int,
        default=5,
        help='Step size for stress test'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='performance_test_results.json',
        help='Output file for results'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("2KCompLeague Discord Bot - Performance Testing")
    logger.info(f"Mode: {args.mode}")
    
    try:
        if args.mode == 'analysis':
            results = asyncio.run(run_performance_analysis())
        elif args.mode == 'load-test':
            if not args.scenario:
                logger.error("--scenario is required for load-test mode")
                sys.exit(1)
            results = asyncio.run(run_load_test(args.scenario, args.duration))
        elif args.mode == 'stress-test':
            results = asyncio.run(run_stress_test(args.max_users, args.step_size))
        elif args.mode == 'optimize':
            results = asyncio.run(run_optimizations())
        elif args.mode == 'comprehensive':
            results = asyncio.run(run_comprehensive_test())
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
        
        # Save results
        if results:
            save_results(results, args.output)
            logger.info("Performance testing completed successfully!")
        else:
            logger.error("Performance testing failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Performance testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Performance testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
