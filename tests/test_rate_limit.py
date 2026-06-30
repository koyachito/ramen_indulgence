from starlette.requests import Request
from starlette.responses import Response

from app.rate_limit import RECORD_RATE_LIMIT_SECONDS, _sign, can_record, mark_recorded


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


def signed_cookie(name: str, ts: float) -> str:
    ts_str = str(ts)
    return f"{name}={ts_str}:{_sign(ts_str)}"


def test_can_record_accepts_missing_and_malformed_cookie():
    # No cookie → can record
    assert can_record(request_with_cookie(), "recorded_at", now=1_000.0)
    # Unsigned / tampered cookie → treated as absent → can record
    assert can_record(
        request_with_cookie("recorded_at=invalid"),
        "recorded_at",
        now=1_000.0,
    )
    # Plain timestamp without HMAC → treated as tampered → can record
    assert can_record(
        request_with_cookie("recorded_at=970"),
        "recorded_at",
        now=1_000.0,
    )


def test_can_record_accepts_signed_expired_cookie():
    assert can_record(
        request_with_cookie(signed_cookie("recorded_at", 970.0)),
        "recorded_at",
        now=970.0 + RECORD_RATE_LIMIT_SECONDS,
    )


def test_can_record_rejects_signed_cookie_inside_limit():
    assert not can_record(
        request_with_cookie(signed_cookie("recorded_at", 971.0)),
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
    assert "recorded_at=1000.0:" in cookie  # value: timestamp:hmac
    assert f"max-age={RECORD_RATE_LIMIT_SECONDS}" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "secure" in cookie
