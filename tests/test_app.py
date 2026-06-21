import asyncio
import os
from pathlib import Path
from urllib.parse import unquote

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


async def request(method: str, path: str, **kwargs) -> httpx.Response:
    init_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, path, **kwargs)


def test_health_endpoint():
    response = asyncio.run(request("GET", "/health"))
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_top_and_diagnosis_hide_stats_navigation():
    top = asyncio.run(request("GET", "/"))
    diagnosis = asyncio.run(request("GET", "/diagnosis"))
    assert top.status_code == diagnosis.status_code == 200
    assert 'href="/stats"' not in top.text
    assert 'href="/stats"' not in diagnosis.text
    assert "QUESTION 1 / 7" in diagnosis.text
    assert "QUESTION 7 / 7" in diagnosis.text
    assert "ramen_count_today" in diagnosis.text
    assert 'id="next-question"' not in diagnosis.text
    assert "回答を選ぶと自動で次へ進みます" in diagnosis.text
    assert "<legend" not in diagnosis.text
    script = Path("app/static/script.js").read_text(encoding="utf-8")
    assert 'input.addEventListener("click"' in script


def test_posting_diagnosis_returns_new_result_structure():
    response = asyncio.run(request("POST", "/result", data=VALID_DATA))
    assert response.status_code == 200
    assert "味噌ラーメン一杯を赦します" in response.text
    assert "事情があります" not in response.text
    assert "ラーメン。" in response.text
    assert "近くのラーメンを探す" in response.text
    assert "診断結果を画像で保存" in response.text
    assert "診断結果をツイート" in response.text
    assert "投稿文をコピー" not in response.text
    assert "https://ramen-indulgence.onrender.com/" in unquote(response.text)
    assert "他の文言で赦される" in response.text
    assert response.text.index("ラーメン。") < response.text.index("近くのラーメンを探す")
    assert response.text.index("近くのラーメンを探す") < response.text.index("診断結果を画像で保存")
    assert "麺欲<br>赦免" in response.text
    assert "images/eating.png" in response.text
    assert 'href="/stats"' in response.text


def test_reroll_does_not_increment_total():
    first = asyncio.run(request("POST", "/result", data=VALID_DATA))
    reroll_data = {**VALID_DATA, "reroll": "true"}
    second = asyncio.run(request("POST", "/result", data=reroll_data))
    assert first.status_code == second.status_code == 200


def test_diagnosis_flow_never_returns_hidden_sleep_judgment():
    async def scenario():
        init_db()
        transport = httpx.ASGITransport(app=app)
        data = {
            **VALID_DATA,
            "meals": "4",
            "ramen_count_today": "3",
            "achievement": "shorts",
            "after_plan": "more_shorts",
            "reason_not_to_eat": "ignore",
            "ramen_type": "jiro",
            "forgiveness_style": "strict",
        }
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            first = await client.post("/result", data=data)
            second = await client.post("/result", data=data)
            third = await client.post("/result", data=data)
            return first, second, third, client.cookies

    first, second, third, cookies = asyncio.run(scenario())
    assert "鬼審議の末の赦し" in first.text
    assert "鬼審議の末の赦し" in second.text
    assert "鬼審議の末の赦し" in third.text
    assert "今日は寝ろ" not in third.text
    assert "oni_count" not in cookies
    assert "sleep_until" not in cookies


def test_exact_hidden_sleep_combination_returns_sleep_from_diagnosis():
    response = asyncio.run(
        request(
            "POST",
            "/result",
            data={
                **VALID_DATA,
                "meals": "4",
                "ramen_count_today": "3",
                "achievement": "shorts",
                "mood": "empty",
                "after_plan": "more_shorts",
                "reason_not_to_eat": "ignore",
                "ramen_type": "iekei",
                "forgiveness_style": "strict",
            },
        )
    )
    assert response.status_code == 200
    assert "今日は寝ろ" in response.text
    assert "睡眠<br>直行" in response.text


def test_hidden_command_records_banzai_judgment_with_share_actions():
    trial = asyncio.run(request("GET", "/hidden-confession"))
    result = asyncio.run(request("POST", "/hidden-judgment"))
    assert trial.status_code == 200
    assert "data-auto-submit" in trial.text
    assert result.status_code == 200
    assert "ラーメンばんざい！" in result.text
    assert "banzai.png" in result.text
    assert "診断結果を画像で保存" in result.text
    assert "診断結果をツイート" in result.text
    assert "麺愛<br>永遠" in result.text
    assert "今日も堂々と、ラーメンを愛します" in unquote(result.text)


def test_stats_list_sleep_and_hidden_banzai_separately():
    stats = asyncio.run(request("GET", "/stats"))
    assert stats.status_code == 200
    assert "今日は寝ろ（幻の判決）" in stats.text
    assert "ラーメンばんざい！（どこかに隠された祝福）" in stats.text
