from fastapi import HTTPException, Request
from app.redis_client import redis_client


def rate_limit(
    request: Request,
    limit: int = 5,
    window: int = 60
):
    client_ip = request.client.host

    key = f"rate_limit:{request.url.path}:{client_ip}"

    current_count = redis_client.get(key)

    if current_count is None:
        redis_client.setex(key, window, 1)
        return

    if int(current_count) >= limit:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )

    redis_client.incr(key)