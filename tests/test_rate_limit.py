from starlette.requests import Request
from starlette.responses import Response

from app.rate_limit import RECORD_RATE_LIMIT_SECONDS, can_record, mark_recorded


def request_with_cookie(cookie: str = "", scheme: str = "http") -> Request:
    headers = []
    if cookie:
        headers.append((b"cookie", cookie.encode()))
    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": scheme,
            "path": "/result",
            "headers": headers,
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 12345),
        }
    )


def test_can_record_accepts_missing_malformed_and_expired_cookie():
    assert can_record(request_with_cookie(), "recorded_at", now=1_000.0)
    assert can_record(
        request_with_cookie("recorded_at=invalid"),
        "recorded_at",
        now=1_000.0,
    )
    assert can_record(
        request_with_cookie("recorded_at=970"),
        "recorded_at",
        now=970.0 + RECORD_RATE_LIMIT_SECONDS,
    )


def test_can_record_rejects_cookie_inside_limit():
    assert not can_record(
        request_with_cookie("recorded_at=971"),
        "recorded_at",
        now=1_000.0,
    )


def test_mark_recorded_sets_short_lived_http_only_cookie():
    response = Response()
    mark_recorded(
        response,
        request_with_cookie(scheme="https"),
        "recorded_at",
        now=1_000.0,
    )

    cookie = response.headers["set-cookie"].lower()
    assert "recorded_at=1000.0" in cookie
    assert f"max-age={RECORD_RATE_LIMIT_SECONDS}" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "secure" in cookie
