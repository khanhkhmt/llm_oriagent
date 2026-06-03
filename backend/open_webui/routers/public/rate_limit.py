"""
Rate limiting helper for OriAgent Public API.

TODO: Implement Redis-backed rate limiting when Redis is available in app state.
Currently provides a framework and no-op placeholder for rate limiting.

Proposed limits:
- /chat/completions: 60 req/min/API key
- /audio/transcriptions: 20 req/min/API key
- /images/generations: 10 req/min/API key
- /files: 30 req/min/API key
- /models: 120 req/min/API key
"""

import logging
import time
from typing import Optional
from collections import defaultdict

from fastapi import Request, HTTPException, status

log = logging.getLogger(__name__)

# In-memory rate limit store (fallback when Redis is not available)
# Structure: { "user_id:endpoint": [(timestamp, ...)] }
_in_memory_store: dict[str, list[float]] = defaultdict(list)

# Rate limit configuration: endpoint_prefix -> (max_requests, window_seconds)
RATE_LIMITS = {
    "chat_completions": (60, 60),
    "agents_run": (20, 60),
    "audio_transcriptions": (20, 60),
    "images_generations": (10, 60),
    "files": (30, 60),
    "models": (120, 60),
    "knowledge": (60, 60),
    "audio_speech": (30, 60),
}


async def check_rate_limit(
    request: Request,
    user_id: str,
    endpoint_key: str,
    request_id: str = "",
) -> None:
    """
    Check rate limit for a user/endpoint combination.

    If Redis is available, uses Redis-based rate limiting.
    Otherwise falls back to in-memory (single-instance only).

    Raises HTTP 429 if rate limit is exceeded.

    Args:
        request: FastAPI request object (for Redis access)
        user_id: The authenticated user's ID
        endpoint_key: One of the keys in RATE_LIMITS dict
        request_id: Request ID for error response
    """
    if endpoint_key not in RATE_LIMITS:
        return  # No rate limit configured for this endpoint

    max_requests, window_seconds = RATE_LIMITS[endpoint_key]
    redis = getattr(request.app.state, "redis", None)

    if redis is not None:
        await _check_rate_limit_redis(redis, user_id, endpoint_key, max_requests, window_seconds, request_id)
    else:
        _check_rate_limit_memory(user_id, endpoint_key, max_requests, window_seconds, request_id)


async def _check_rate_limit_redis(
    redis,
    user_id: str,
    endpoint_key: str,
    max_requests: int,
    window_seconds: int,
    request_id: str,
) -> None:
    """Redis-backed sliding window rate limiter."""
    from open_webui.env import REDIS_KEY_PREFIX

    key = f"{REDIS_KEY_PREFIX}:public_api:rate:{user_id}:{endpoint_key}"
    now = time.time()

    try:
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds + 1)
        results = await pipe.execute()

        current_count = results[1]
        if current_count >= max_requests:
            log.warning(
                "Rate limit exceeded: user_id=%s endpoint=%s count=%d limit=%d request_id=%s",
                user_id,
                endpoint_key,
                current_count,
                max_requests,
                request_id,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
    except HTTPException:
        raise
    except Exception as e:
        # If Redis fails, log and allow the request (fail open)
        log.warning("Rate limit Redis error (allowing request): %s", str(e))


def _check_rate_limit_memory(
    user_id: str,
    endpoint_key: str,
    max_requests: int,
    window_seconds: int,
    request_id: str,
) -> None:
    """In-memory fallback rate limiter (single instance only)."""
    key = f"{user_id}:{endpoint_key}"
    now = time.time()
    cutoff = now - window_seconds

    # Clean old entries
    _in_memory_store[key] = [ts for ts in _in_memory_store[key] if ts > cutoff]

    if len(_in_memory_store[key]) >= max_requests:
        log.warning(
            "Rate limit exceeded (memory): user_id=%s endpoint=%s count=%d limit=%d request_id=%s",
            user_id,
            endpoint_key,
            len(_in_memory_store[key]),
            max_requests,
            request_id,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    _in_memory_store[key].append(now)
