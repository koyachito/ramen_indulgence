import asyncio
import os

os.environ["RAMEN_DB_PATH"] = "/tmp/ramen-menzaifu-test.db"

import httpx

from app.database import init_db
from app.main import app


async def request(method: str, path: str, **kwargs) -> httpx.Response:
    init_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.request(method, path, **kwargs)


def test_health_endpoint():
    response = asyncio.run(request("GET", "/health"))
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_top_and_diagnosis_pages_render():
    assert asyncio.run(request("GET", "/")).status_code == 200
    response = asyncio.run(request("GET", "/diagnosis"))
    assert asyncio.run(request("GET", "/about")).status_code == 200
    stats = asyncio.run(request("GET", "/stats"))
    assert stats.status_code == 200
    assert "免罪判決の分布" in stats.text
    assert "この時間帯、みんなが食べたい一杯" in stats.text
    assert "今日は寝ろ（幻の判決）" in stats.text
    assert response.status_code == 200
    assert "質問は、全3問です。" in response.text
    assert "QUESTION 1 / 3" in response.text
    assert "QUESTION 3 / 3" in response.text


def test_posting_diagnosis_returns_certificate():
    response = asyncio.run(
        request(
            "POST",
            "/result",
            data={
                "current_hour": "20",
                "current_month": "6",
                "current_day": "21",
                "meals": "1",
                "walked": "true",
                "worked": "true",
                "ramen_type": "味噌",
            },
        )
    )
    assert response.status_code == 200
    assert "ラーメン免罪符" in response.text
    assert "完全免罪" in response.text
    assert "あなたのラーメン欲は、ここに赦されました。" in response.text
    assert "share-certificate" in response.text
    assert "味噌ラーメン" in response.text


def test_hidden_command_skips_questions_and_records_sleep_judgment():
    trial = asyncio.run(request("GET", "/hidden-confession"))
    result = asyncio.run(request("POST", "/hidden-judgment"))
    assert trial.status_code == 200
    assert "審議中..." in trial.text
    assert "data-auto-submit" in trial.text
    assert result.status_code == 200
    assert "今日は寝ろ" in result.text
