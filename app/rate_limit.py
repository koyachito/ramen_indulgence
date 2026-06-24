import time

from fastapi import Request
from starlette.responses import Response

RESULT_RECORD_COOKIE = "ramen_result_recorded_at"
HIDDEN_RECORD_COOKIE = "ramen_hidden_recorded_at"
RECORD_RATE_LIMIT_SECONDS = 30


def can_record(request: Request, cookie_name: str, now: float | None = None) -> bool:
    current_time = time.time() if now is None else now
    try:
        recorded_at = float(request.cookies[cookie_name])
    except (KeyError, TypeError, ValueError):
        return True
    return current_time - recorded_at >= RECORD_RATE_LIMIT_SECONDS


def mark_recorded(
    response: Response,
    request: Request,
    cookie_name: str,
    now: float | None = None,
) -> None:
    recorded_at = time.time() if now is None else now
    response.set_cookie(
        key=cookie_name,
        value=str(recorded_at),
        max_age=RECORD_RATE_LIMIT_SECONDS,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
