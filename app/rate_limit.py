import hashlib
import hmac
import os
import time

from fastapi import Request
from starlette.responses import Response

RESULT_RECORD_COOKIE = "ramen_result_recorded_at"
HIDDEN_RECORD_COOKIE = "ramen_hidden_recorded_at"
RECORD_RATE_LIMIT_SECONDS = 30


def _secret() -> bytes:
    return os.getenv("RATE_LIMIT_SECRET", "dev-only-insecure-key").encode()


def _sign(ts_str: str) -> str:
    return hmac.new(_secret(), ts_str.encode(), hashlib.sha256).hexdigest()


def _verify_and_parse(cookie_value: str) -> float | None:
    try:
        ts_str, sig = cookie_value.rsplit(":", 1)
        if not hmac.compare_digest(_sign(ts_str), sig):
            return None
        return float(ts_str)
    except (ValueError, AttributeError):
        return None


def can_record(request: Request, cookie_name: str, now: float | None = None) -> bool:
    current_time = time.time() if now is None else now
    cookie_value = request.cookies.get(cookie_name)
    if not cookie_value:
        return True
    recorded_at = _verify_and_parse(cookie_value)
    if recorded_at is None:
        return True
    return current_time - recorded_at >= RECORD_RATE_LIMIT_SECONDS


def mark_recorded(
    response: Response,
    request: Request,
    cookie_name: str,
    now: float | None = None,
) -> None:
    recorded_at = time.time() if now is None else now
    ts_str = str(recorded_at)
    value = f"{ts_str}:{_sign(ts_str)}"
    response.set_cookie(
        key=cookie_name,
        value=value,
        max_age=RECORD_RATE_LIMIT_SECONDS,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
