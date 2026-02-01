"""
In-memory rate limiting for security-sensitive endpoints.

Features:
- Sliding window rate limiting
- Automatic periodic cleanup to prevent memory leaks
- Thread-safe with asyncio.Lock
"""
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException
from typing import Optional


class RateLimiter:
    """
    Thread-safe in-memory rate limiter using sliding window.

    Includes automatic cleanup to prevent memory growth from stale entries.
    """

    def __init__(self, cleanup_interval: int = 300):
        """
        Initialize rate limiter.

        Args:
            cleanup_interval: How often to run cleanup (in seconds). Default 5 minutes.
        """
        self.requests: dict[str, list[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = cleanup_interval

    async def check(self, key: str, max_requests: int, window_seconds: int) -> None:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier (e.g., "email:user@example.com" or "ip:192.168.1.1")
            max_requests: Maximum number of requests allowed in window
            window_seconds: Time window in seconds

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)

        async with self._lock:
            # Clean old requests outside the window
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]

            if len(self.requests[key]) >= max_requests:
                raise HTTPException(
                    status_code=429,
                    detail="Trop de requêtes. Réessayez plus tard."
                )

            self.requests[key].append(now)

    def check_sync(self, key: str, max_requests: int, window_seconds: int) -> None:
        """
        Synchronous version of check for non-async contexts.

        Args:
            key: Unique identifier (e.g., "email:user@example.com" or "ip:192.168.1.1")
            max_requests: Maximum number of requests allowed in window
            window_seconds: Time window in seconds

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)

        # Clean old requests outside the window
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

        if len(self.requests[key]) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail="Trop de requêtes. Réessayez plus tard."
            )

        self.requests[key].append(now)

    async def cleanup(self, max_age_seconds: int = 3600) -> int:
        """
        Remove stale entries older than max_age to prevent memory growth.

        Args:
            max_age_seconds: Maximum age of entries to keep (default 1 hour)

        Returns:
            Number of keys removed
        """
        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
        keys_removed = 0

        async with self._lock:
            keys_to_remove = []

            for key, timestamps in self.requests.items():
                # Remove old timestamps
                self.requests[key] = [t for t in timestamps if t > cutoff]
                # Mark empty keys for removal
                if not self.requests[key]:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.requests[key]
                keys_removed += 1

        return keys_removed

    async def _cleanup_loop(self):
        """Background task that runs cleanup periodically."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                removed = await self.cleanup()
                if removed > 0:
                    print(f"[RATE_LIMITER] Cleaned up {removed} stale entries")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[RATE_LIMITER] Cleanup error: {e}")

    def start_cleanup_task(self) -> asyncio.Task:
        """
        Start the background cleanup task.

        Returns:
            The asyncio Task running the cleanup loop
        """
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        return self._cleanup_task

    async def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        if self._cleanup_task is not None and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        return {
            "total_keys": len(self.requests),
            "total_entries": sum(len(v) for v in self.requests.values()),
        }


# Global singleton instance
rate_limiter = RateLimiter()
