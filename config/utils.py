from django_redis import get_redis_connection
from ninja.errors import HttpError
from functools import wraps
import time

def rate_limit(limit=60, period=60):
    """
    Simple Redis-based rate limiter decorator for Ninja.
    limit: Number of requests allowed
    period: Time period in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Use IP address or user ID as key
            identifier = request.auth.id if hasattr(request, 'auth') and request.auth else request.META.get('REMOTE_ADDR')
            key = f"ratelimit:{func.__name__}:{identifier}"
            
            redis_conn = get_redis_connection("default")
            
            # Use Redis pipeline for atomic operations
            pipe = redis_conn.pipeline()
            now = time.time()
            pipe.zremrangebyscore(key, 0, now - period)
            pipe.zadd(key, {now: now})
            pipe.zcard(key)
            pipe.expire(key, period)
            results = pipe.execute()
            
            request_count = results[2]
            
            if request_count > limit:
                raise HttpError(429, "Rate limit exceeded. Try again later.")
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
