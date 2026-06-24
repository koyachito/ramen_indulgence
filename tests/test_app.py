import asyncio
import json
import os
from pathlib import Path
from urllib.parse import unquote

os.environ["RAMEN_DB_PATH"] = "/tmp/ramen-menzaifu-test.db"

import httpx

from app.choices import (
    DIAGNOSIS_QUESTIONS,
    QUESTION_MESSAGES,
    RAMEN_TYPE_LABELS,
    VALID_CHOICE_VALUES,
)
from app.database import get_stats, init_db
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


def test_top_and_diagnosis_show_about_and_hide_stats_navigation():
    top = asyncio.run(request("GET", "/"))
    diagnosis = asyncio.run(request("GET", "/diagnosis"))
    assert top.status_code == diagnosis.status_code == 200
    assert 'href="/stats"' not in top.text
    assert 'href="/stats"' not in diagnosis.text
    assert 'class="about-nav-link" href="/about"' in top.text
    assert 'class="about-nav-link" href="/about"' in diagnosis.text
    assert "QUESTION 1 / 7" in diagnosis.text
    assert "QUESTION 7 / 7" in diagnosis.text
    assert "ramen_count_today" in diagnosis.text
    assert 'id="next-question"' not in diagnosis.text
    assert "回答を選ぶと自動で次へ進みます" in diagnosis.text
    assert "<legend" not in diagnosis.text
    for question in DIAGNOSIS_QUESTIONS:
        assert f'data-question="{question.name}"' in diagnosis.text
        for choice in question.choices:
            assert f'name="{question.name}" value="{choice.value}"' in diagnosis.text
            assert choice.label in diagnosis.text
    assert "diagnosis-question-config" in diagnosis.text
    embedded_config = diagnosis.text.split(
        '<script id="diagnosis-question-config" type="application/json">', 1
    )[1].split("</script>", 1)[0]
    assert json.loads(embedded_config) == QUESTION_MESSAGES
    entrypoint = Path("app/static/script.js").read_text(encoding="utf-8")
    interview_flow = Path("app/static/js/interview_flow.js").read_text(encoding="utf-8")
    question_messages = Path("app/static/js/question_messages.js").read_text(encoding="utf-8")
    assert 'type="module"' in diagnosis.text
    assert 'from "./js/interview_flow.js"' in entrypoint
    assert 'input.addEventListener("click"' in interview_flow
    assert "JSON.parse(questionConfig.textContent)" in question_messages
    assert "const SISTER_REACTION_DISPLAY_MS = 3000;" in interview_flow
    assert "}, SISTER_REACTION_DISPLAY_MS);" in interview_flow
    assert "}, 1250);" not in interview_flow
    assert "const QUESTION_MESSAGES = {" not in entrypoint


def test_frontend_modules_exist():
    module_paths = (
        "clock.js",
        "reveal.js",
        "question_messages.js",
        "interview_flow.js",
        "certificate_canvas.js",
        "download_certificate.js",
        "page_enhancements.js",
        "dom.js",
    )
    for module_path in module_paths:
        assert Path("app/static/js", module_path).is_file()


def test_server_choice_validation_uses_central_definitions():
    assert set(QUESTION_MESSAGES) == set(VALID_CHOICE_VALUES)
    for name, messages in QUESTION_MESSAGES.items():
        assert set(messages["reactions"]) == VALID_CHOICE_VALUES[name]
    assert RAMEN_TYPE_LABELS["other"] == "その他"

    for name, values in VALID_CHOICE_VALUES.items():
        if name not in VALID_DATA:
            continue
        response = asyncio.run(
            request(
                "POST",
                "/result",
                data={**VALID_DATA, name: next(iter(values))},
            )
        )
        assert response.status_code == 200

    response = asyncio.run(
        request("POST", "/result", data={**VALID_DATA, "mood": "not-defined"})
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/diagnosis"


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
    assert 'class="about-nav-link" href="/about"' in response.text


def test_mobile_navigation_keeps_all_available_links_visible():
    stylesheet = Path("app/static/style.css").read_text(encoding="utf-8")

    assert ".stats-nav-link { display: none; }" not in stylesheet
    assert ".about-nav-link { display: none; }" not in stylesheet
    assert "a:last-child" not in stylesheet
    assert "a:nth-child(2)" not in stylesheet
    assert ".site-header { flex-wrap: wrap; }" in stylesheet
    assert ".site-nav { width: 100%; justify-content: flex-end; }" in stylesheet


def test_about_shows_creator_and_github_repository_link():
    response = asyncio.run(request("GET", "/about"))

    assert response.status_code == 200
    assert "このアプリは <b>koyachito</b> が制作しました。" in response.text
    assert "GitHub: koyachito/ramen_indulgence" in response.text
    assert (
        'href="https://github.com/koyachito/ramen_indulgence" '
        'target="_blank" rel="noopener"'
    ) in response.text


def test_reroll_does_not_increment_total():
    init_db()
    total_before_diagnosis = get_stats()["total"]

    diagnosis = asyncio.run(request("POST", "/result", data=VALID_DATA))
    total_after_diagnosis = get_stats()["total"]

    reroll_data = {**VALID_DATA, "reroll": "true"}
    reroll = asyncio.run(request("POST", "/result", data=reroll_data))
    total_after_reroll = get_stats()["total"]

    assert diagnosis.status_code == reroll.status_code == 200
    assert total_after_diagnosis == total_before_diagnosis + 1
    assert total_after_reroll == total_after_diagnosis


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
