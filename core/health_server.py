"""Simple HTTP server for health check endpoints."""

import logging
from typing import Optional

from aiohttp import ClientSession, web
from aiohttp.web import Request, Response

from .health import HealthChecker, create_health_response, create_metrics_response

logger = logging.getLogger(__name__)


class HealthServer:
    """Simple HTTP server for health check endpoints."""

    def __init__(
        self, health_checker: HealthChecker, host: str = "0.0.0.0", port: int = 8080
    ):
        self.health_checker = health_checker
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None

        # Setup routes
        self.setup_routes()

    def setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get("/health", self.health_endpoint)
        self.app.router.add_get("/health/", self.health_endpoint)
        self.app.router.add_get("/metrics", self.metrics_endpoint)
        self.app.router.add_get("/metrics/", self.metrics_endpoint)
        self.app.router.add_get("/performance", self.performance_endpoint)
        self.app.router.add_get("/performance/", self.performance_endpoint)
        self.app.router.add_get("/performance/optimizations", self.optimizations_endpoint)
        self.app.router.add_get("/performance/load-test", self.load_test_endpoint)
        self.app.router.add_get("/", self.root_endpoint)
        self.app.router.add_get("/status", self.status_endpoint)

    async def health_endpoint(self, request: Request) -> Response:
        """Health check endpoint."""
        try:
            # Get bot instance from request
            bot = request.app.get("bot")
            if not bot:
                return web.json_response(
                    {"error": "Bot instance not available"}, status=503
                )

            # Run health check
            health_status = self.health_checker.run_health_check(bot)
            response_data = create_health_response(health_status)

            # Set appropriate status code
            status_code = 200
            if health_status.status == "unhealthy":
                status_code = 503
            elif health_status.status == "degraded":
                status_code = 200  # Still operational but degraded

            return web.json_response(response_data, status=status_code)

        except Exception as e:
            logger.error(f"Health check endpoint error: {e}")
            return web.json_response(
                {"error": "Health check failed", "details": str(e)}, status=500
            )

    async def metrics_endpoint(self, request: Request) -> Response:
        """Prometheus metrics endpoint."""
        try:
            # Get bot instance from request
            bot = request.app.get("bot")
            if not bot:
                return web.Response(
                    text="# Bot instance not available\n",
                    status=503,
                    content_type="text/plain",
                )

            # Run health check and format as metrics
            health_status = self.health_checker.run_health_check(bot)
            metrics_text = create_metrics_response(health_status)

            return web.Response(text=metrics_text, content_type="text/plain")

        except Exception as e:
            logger.error(f"Metrics endpoint error: {e}")
            return web.Response(
                text=f"# Metrics collection failed: {e}\n",
                status=500,
                content_type="text/plain",
            )

    async def performance_endpoint(self, request: Request) -> Response:
        """Performance metrics endpoint."""
        try:
            from .performance import get_performance_monitor
            
            monitor = get_performance_monitor()
            summary = monitor.get_performance_summary(60)  # Last hour
            
            return web.json_response(summary)
            
        except Exception as e:
            logger.error(f"Performance endpoint error: {e}")
            return web.json_response(
                {"error": "Performance metrics collection failed", "details": str(e)}, 
                status=500
            )

    async def optimizations_endpoint(self, request: Request) -> Response:
        """Performance optimizations status endpoint."""
        try:
            from .performance_optimizer import get_performance_optimizer
            
            optimizer = get_performance_optimizer()
            status = optimizer.get_optimization_status()
            
            return web.json_response(status)
            
        except Exception as e:
            logger.error(f"Optimizations endpoint error: {e}")
            return web.json_response(
                {"error": "Optimizations status collection failed", "details": str(e)}, 
                status=500
            )

    async def load_test_endpoint(self, request: Request) -> Response:
        """Load testing status endpoint."""
        try:
            from .performance_testing import get_load_tester
            
            load_tester = get_load_tester()
            summary = load_tester.get_test_summary()
            
            return web.json_response(summary)
            
        except Exception as e:
            logger.error(f"Load test endpoint error: {e}")
            return web.json_response(
                {"error": "Load test status collection failed", "details": str(e)}, 
                status=500
            )

    async def root_endpoint(self, request: Request) -> Response:
        """Root endpoint with basic info."""
        return web.json_response(
            {
                "service": "2KCompLeague Discord Bot",
                "version": self.health_checker.version,
                "endpoints": {
                    "health": "/health",
                    "metrics": "/metrics",
                    "performance": "/performance",
                    "optimizations": "/performance/optimizations",
                    "load_testing": "/performance/load-test",
                    "status": "/status"
                },
            }
        )

    async def status_endpoint(self, request: Request) -> Response:
        """Status endpoint with summary."""
        try:
            summary = self.health_checker.get_health_summary()
            return web.json_response(summary)
        except Exception as e:
            logger.error(f"Status endpoint error: {e}")
            return web.json_response(
                {"error": "Status check failed", "details": str(e)}, status=500
            )

    async def start(self, bot_instance):
        """Start the health server."""
        try:
            # Store bot instance in app for endpoints to access
            self.app["bot"] = bot_instance

            # Create runner and site
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            logger.info(f"Health server started on {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
            raise

    async def stop(self):
        """Stop the health server."""
        try:
            if self.site:
                await self.site.stop()
                logger.info("Health server site stopped")

            if self.runner:
                await self.runner.cleanup()
                logger.info("Health server runner cleaned up")

        except Exception as e:
            logger.error(f"Error stopping health server: {e}")

    def get_url(self) -> str:
        """Get the server URL."""
        return f"http://{self.host}:{self.port}"


async def start_health_server(
    health_checker: HealthChecker, bot_instance, host: str = "0.0.0.0", port: int = 8080
) -> HealthServer:
    """Start a health server instance."""
    server = HealthServer(health_checker, host, port)
    await server.start(bot_instance)
    return server


# Utility function for Docker health checks
async def simple_health_check(host: str = "localhost", port: int = 8080) -> bool:
    """Simple health check for Docker health checks."""
    try:
        async with ClientSession() as session:
            async with session.get(
                f"http://{host}:{port}/health", timeout=5
            ) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
