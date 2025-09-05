"""HTTP client utilities for SportsPress API integration."""

import asyncio
import logging
from typing import Any, AsyncIterator, Dict, Optional
from urllib.parse import urlencode

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import settings

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client with retry logic and rate limiting."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self._rate_limit_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    )
    async def get_json(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Make a GET request and return JSON response with retry logic.

        Args:
            url: Target URL
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response

        Raises:
            aiohttp.ClientError: On HTTP errors
            asyncio.TimeoutError: On timeout
        """
        timeout = timeout or settings.HTTP_TIMEOUT

        async with self._rate_limit_semaphore:
            logger.debug(f"Making HTTP request to {url} with params {params}")

            try:
                async with self.session.get(
                    url, params=params, timeout=timeout
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    logger.debug(f"HTTP request successful for {url}, status: {response.status}, data length: {len(str(data)) if data else 0}")
                    return data

            except aiohttp.ClientResponseError as e:
                logger.warning(f"HTTP request failed for {url}, status: {e.status}, message: {e.message}")
                raise
            except Exception as e:
                logger.error(f"HTTP request error for {url}: {e}")
                raise

    async def paginate(
        self, base_url: str, *, per_page: int = 100, max_pages: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Paginate through a WordPress REST API endpoint.

        Args:
            base_url: Base URL to paginate
            per_page: Items per page
            max_pages: Maximum pages to fetch (None for unlimited)

        Yields:
            Individual items from all pages
        """
        page = 1
        total_pages = None

        while True:
            if max_pages and page > max_pages:
                break

            params = {"per_page": per_page, "page": page}
            url = f"{base_url}?{urlencode(params)}"

            try:
                data = await self.get_json(url)

                if not data:
                    logger.debug(f"No data returned, stopping pagination at page {page}")
                    break

                # Check if this is the last page
                if isinstance(data, list):
                    if len(data) < per_page:
                        total_pages = page
                    for item in data:
                        yield item
                else:
                    # Handle non-list responses
                    yield data
                    break

                page += 1

                # Small delay to be respectful to the API
                await asyncio.sleep(0.1)

            except aiohttp.ClientResponseError as e:
                if e.status == 400:  # Bad request, likely past last page
                    logger.debug(f"Reached end of pagination at page {page}")
                    break
                raise
            except Exception as e:
                logger.error(f"Pagination error for {url} page {page}: {e}")
                raise

        logger.info(f"Pagination completed for {base_url}, total pages: {total_pages or page - 1}")


async def create_http_session() -> aiohttp.ClientSession:
    """Create and configure an aiohttp session."""
    timeout = aiohttp.ClientTimeout(total=settings.HTTP_TIMEOUT)

    session = aiohttp.ClientSession(
        timeout=timeout,
        headers={
            "User-Agent": "2KCompLeague-Discord-Bot/1.0",
            "Accept": "application/json",
        },
    )

    logger.info("HTTP session created")
    return session


async def close_http_session(session: aiohttp.ClientSession) -> None:
    """Close an aiohttp session."""
    await session.close()
    logger.info("HTTP session closed")
