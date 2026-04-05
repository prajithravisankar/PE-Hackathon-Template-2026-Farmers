import functools
import json
import logging
import os

import redis

log = logging.getLogger(__name__)

_redis = None


def get_redis():
    global _redis
    if _redis is None:
        _redis = redis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        )
    return _redis


def cache_response(key_prefix, ttl=60):
    """Cache-aside decorator for Flask view functions.

    Caches the JSON response body in Redis with a TTL. Returns an
    ``X-Cache: HIT`` or ``X-Cache: MISS`` header so operators can
    verify caching behaviour during load tests.

    On any Redis failure the request falls through to the database
    (cache miss) — Redis is never a single point of failure.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            from flask import request as _req

            # Build a cache key from prefix + full query string so that
            # different filter/pagination combos get their own entries.
            cache_key = f"{key_prefix}:{_req.full_path}"

            try:
                r = get_redis()
                cached = r.get(cache_key)
                if cached is not None:
                    response = json.loads(cached)
                    from flask import jsonify

                    resp = jsonify(response)
                    resp.headers["X-Cache"] = "HIT"
                    return resp, 200
            except redis.RedisError:
                log.warning("cache_read_failed", extra={"key": cache_key})

            # Cache miss — execute the real view
            result = fn(*args, **kwargs)

            # result is (response_body, status_code) from success()
            response_body, status_code = result

            # Only cache successful responses
            if status_code == 200:
                try:
                    r = get_redis()
                    r.setex(
                        cache_key,
                        ttl,
                        json.dumps(response_body.get_json()),
                    )
                except redis.RedisError:
                    log.warning("cache_write_failed", extra={"key": cache_key})

            response_body.headers["X-Cache"] = "MISS"
            return response_body, status_code

        return wrapper

    return decorator


def invalidate_cache(key_prefix):
    """Delete all Redis keys matching ``key_prefix:*``.

    Uses SCAN to avoid blocking the Redis instance.  Failures are
    logged but never propagated — a stale cache entry will simply
    expire via TTL.
    """
    try:
        r = get_redis()
        cursor = 0
        pattern = f"{key_prefix}:*"
        while True:
            cursor, keys = r.scan(cursor, match=pattern, count=100)
            if keys:
                r.delete(*keys)
            if cursor == 0:
                break
    except redis.RedisError:
        log.warning("cache_invalidate_failed", extra={"prefix": key_prefix})
