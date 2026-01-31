"""
In-memory rate limiting for security-sensitive endpoints.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self):
        self.requests: dict[str, list[datetime]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int) -> None:
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

        # Clean old requests outside the window
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

        if len(self.requests[key]) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail="Trop de requêtes. Réessayez plus tard."
            )

        self.requests[key].append(now)

    def cleanup(self, max_age_seconds: int = 3600) -> None:
        """
        Remove stale entries older than max_age to prevent memory growth.
        Should be called periodically in production.
        """
        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
        keys_to_remove = []

        for key, timestamps in self.requests.items():
            # Remove old timestamps
            self.requests[key] = [t for t in timestamps if t > cutoff]
            # Mark empty keys for removal
            if not self.requests[key]:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.requests[key]


# Global singleton instance
rate_limiter = RateLimiter()
