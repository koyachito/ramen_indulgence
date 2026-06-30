import asyncio
import os
from unittest.mock import patch

os.environ["RAMEN_DB_PATH"] = "/tmp/ramen-menzaifu-test.db"

import httpx

from app.database import init_db
from app.main import app

VALID_DATA = {
    "current_hour": "20",
    "current_month": "6",
    "current_day": "22",
    "meals": "1",
    "ramen_count_today": "0",
    "achievement": "worked",
    "mood": "tired",
    "after_plan": "work_more",
    "reason_not_to_eat": "none",
    "ramen_type": "miso",
    "forgiveness_style": "praise",
}

SECURITY_HEADER_ENDPOINTS = ["/", "/diagnosis", "/result", "/stats", "/about", "/health"]
EXPECTED_HEADERS = [
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
    "content-security-policy",
]


async def get(path: str, **kwargs) -> httpx.Response:
    init_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request("GET", path, **kwargs)


async def post(path: str, **kwargs) -> httpx.Response:
    init_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request("POST", path, **kwargs)


def test_security_headers_on_index():
    response = asyncio.run(get("/"))
    assert response.status_code == 200
    for header in EXPECTED_HEADERS:
        assert header in response.headers, f"Missing header: {header}"


def test_security_headers_on_diagnosis():
    response = asyncio.run(get("/diagnosis"))
    assert response.status_code == 200
    for header in EXPECTED_HEADERS:
        assert header in response.headers


def test_security_headers_on_result():
    response = asyncio.run(post("/result", data=VALID_DATA))
    assert response.status_code == 200
    for header in EXPECTED_HEADERS:
        assert header in response.headers


def test_security_headers_on_stats():
    response = asyncio.run(get("/stats"))
    assert response.status_code == 200
    for header in EXPECTED_HEADERS:
        assert header in response.headers


def test_security_headers_on_about():
    response = asyncio.run(get("/about"))
    assert response.status_code == 200
    for header in EXPECTED_HEADERS:
        assert header in response.headers


def test_security_headers_on_health():
    response = asyncio.run(get("/health"))
    assert response.status_code == 200
    for header in EXPECTED_HEADERS:
        assert header in response.headers


def test_csp_header_has_expected_directives():
    response = asyncio.run(get("/"))
    csp = response.headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "img-src 'self' data:" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "form-action 'self'" in csp


def test_x_frame_options_is_deny():
    response = asyncio.run(get("/"))
    assert response.headers.get("x-frame-options") == "DENY"


def test_x_content_type_options_is_nosniff():
    response = asyncio.run(get("/"))
    assert response.headers.get("x-content-type-options") == "nosniff"


def test_result_shown_even_when_record_result_fails():
    with patch("app.main.record_result", side_effect=Exception("db error")):
        response = asyncio.run(post("/result", data=VALID_DATA))
    assert response.status_code == 200
    assert "ラーメン" in response.text


def test_result_shown_even_when_get_stats_fails():
    with patch("app.main.get_stats", side_effect=Exception("db error")):
        response = asyncio.run(post("/result", data=VALID_DATA))
    assert response.status_code == 200
    assert "ラーメン" in response.text


def test_hidden_judgment_shown_even_when_record_judgment_fails():
    with patch("app.main.record_judgment", side_effect=Exception("db error")):
        response = asyncio.run(post("/hidden-judgment"))
    assert response.status_code == 200
    assert "ラーメンばんざい" in response.text


def test_index_shown_even_when_get_stats_fails():
    with patch("app.main.get_stats", side_effect=Exception("db error")):
        response = asyncio.run(get("/"))
    assert response.status_code == 200


def test_stats_shown_even_when_get_stats_fails():
    with patch("app.main.get_stats", side_effect=Exception("db error")):
        response = asyncio.run(get("/stats"))
    assert response.status_code == 200
