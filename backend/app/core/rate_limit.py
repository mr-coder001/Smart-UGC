import time
from typing import Dict, Tuple
from fastapi import HTTPException, Request, status
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger

# In-memory sliding window fallback if Redis is unavailable
_memory_rate_limit: Dict[str, list[float]] = {}
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis | None:
    global _redis_client
    if _redis_client is None and settings.REDIS_URL:
        try:
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1.5,
                socket_connect_timeout=1.5,
            )
            # Ping to verify
            await _redis_client.ping()
        except Exception as e:
            logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}. Falling back to in-memory rate limiter.")
            _redis_client = None
    return _redis_client


async def check_rate_limit(request: Request, limit: int = settings.RATE_LIMIT_PER_MINUTE, window_seconds: int = 60) -> None:
    """
    Check if the client has exceeded the upload rate limit (e.g. 20 uploads per minute).
    Uses Redis when available, otherwise falls back gracefully to in-memory tracking.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"rate_limit:upload:{client_ip}"
    current_time = time.time()

    redis_conn = await get_redis()
    if redis_conn:
        try:
            pipe = redis_conn.pipeline()
            # Clean up older timestamps
            pipe.zremrangebyscore(key, 0, current_time - window_seconds)
            # Add current timestamp
            pipe.zadd(key, {str(current_time): current_time})
            # Count elements in window
            pipe.zcard(key)
            # Set key expiry
            pipe.expire(key, window_seconds + 5)
            _, _, count, _ = await pipe.execute()

            if count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {limit} uploads per {window_seconds} seconds."
                )
            return
        except HTTPException:
            raise
        except Exception as err:
            logger.warning(f"Redis rate limit check failed: {err}. Using memory fallback.")

    # In-memory fallback
    now = time.time()
    history = _memory_rate_limit.setdefault(key, [])
    # Filter out requests older than window_seconds
    valid_history = [t for t in history if now - t < window_seconds]
    if len(valid_history) >= limit:
        _memory_rate_limit[key] = valid_history
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {limit} uploads per {window_seconds} seconds."
        )
    valid_history.append(now)
    _memory_rate_limit[key] = valid_history
