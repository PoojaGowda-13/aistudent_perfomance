import time
from fastapi import Request, HTTPException, status

# In-memory rate limiter for local dev (no Redis needed)
_request_log: dict = {}


async def rate_limit_middleware(request: Request, call_next):
    """Simple in-memory sliding-window rate limiter: 120 requests/min per IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = int(time.time())
    window = 60
    max_requests = 120

    if client_ip not in _request_log:
        _request_log[client_ip] = []

    # Remove old entries outside the window
    _request_log[client_ip] = [t for t in _request_log[client_ip] if t > now - window]
    _request_log[client_ip].append(now)

    if len(_request_log[client_ip]) > max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again in a minute.",
        )
    return await call_next(request)
