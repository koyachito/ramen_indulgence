import asyncio
import csv
import json
import os
import re
from pathlib import Path
from urllib.parse import unquote

os.environ["RAMEN_DB_PATH"] = "/tmp/ramen-menzaifu-test.db"

import httpx

from app import rate_limit
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


def test_top_shows_concise_concept_copy():
    response = asyncio.run(request("GET", "/"))

    assert response.status_code == 200
    assert "今日の行いをシスターに告白して、" in response.text
    assert "ラーメン欲を赦されよう。" in response.text
    assert 'class="concept-copy"' in response.text

    stylesheet = Path("app/static/style.css").read_text(encoding="utf-8")
    assert ".concept-copy span { display: block; }" in stylesheet


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
    assert 'from "./js/interview_flow.js?v=16-reaction-total-2300ms"' in entrypoint
    assert 'input.addEventListener("click"' in interview_flow
    assert "JSON.parse(questionConfig.textContent)" in question_messages
    assert "const SISTER_REACTION_TOTAL_MS = 2300;" in interview_flow
    assert "const QUESTION_ENTER_ANIMATION_MS = 450;" in interview_flow
    assert "SISTER_REACTION_TOTAL_MS - QUESTION_ENTER_ANIMATION_MS" in interview_flow
    assert "}, SISTER_REACTION_ADVANCE_MS);" in interview_flow
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


def test_stamp_assets_are_used_by_result_pages_and_canvas():
    for asset in ("menyoku.png", "suimin.png", "menai.png", "ogreleft.png"):
        assert Path("app/static/images", asset).is_file()

    standard = asyncio.run(request("POST", "/result", data=VALID_DATA))
    sleep = asyncio.run(
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
    banzai = asyncio.run(request("POST", "/hidden-judgment"))

    assert "images/menyoku.png" in standard.text
    assert "images/suimin.png" in sleep.text
    assert "images/menai.png" in banzai.text

    canvas = Path("app/static/js/certificate_canvas.js").read_text(encoding="utf-8")
    assert "certificate.dataset.sealImage" in canvas
    assert "context.drawImage(sealImage" in canvas
    assert "context.drawImage(sealImage, 900, 48, 230, 230);" in canvas
    assert "context.drawImage(sealImage, 900, 70, 180, 180);" in canvas
    assert "drawCanvasSeal" not in canvas


def test_standard_result_card_uses_dark_background():
    stylesheet = Path("app/static/style.css").read_text(encoding="utf-8")
    base_template = Path("app/templates/base.html").read_text(encoding="utf-8")
    canvas = Path("app/static/js/certificate_canvas.js").read_text(encoding="utf-8")

    assert ".result-card {" in stylesheet
    assert "color: #eee8dd;" in stylesheet
    assert "background: transparent !important;" in stylesheet
    assert "box-shadow: none;" in stylesheet
    assert "linear-gradient(145deg, #110b15, #1a0f20 48%, #0c0910) !important;" in stylesheet
    assert "?v=16-result-spacing-4" in base_template
    assert "?v=16-reaction-total-2300ms" in base_template
    assert 'context.fillStyle = "#110b15";' in canvas
    assert 'context.fillStyle = "#f7f0df";' not in canvas
    assert 'context.strokeStyle = "#a94855";' in canvas
    assert 'context.strokeStyle = "rgba(169,72,85,.45)";' in canvas


def test_ramen_count_copy_uses_confession_language():
    choices_source = Path("app/choices.py").read_text(encoding="utf-8")
    generator_source = Path("app/result_generator.py").read_text(encoding="utf-8")

    assert "本日一杯目として、穏やかに赦されます。" in choices_source
    assert "本日二杯目ですが、まだ赦しの余地はあります。" in choices_source
    assert "初犯" not in choices_source
    assert "再犯" not in choices_source
    assert "初犯" not in generator_source
    assert 'Choice(1, "1回", "thinking.png"' in choices_source


def test_clock_uses_japan_time_for_diagnosis_and_stats():
    clock = Path("app/static/js/clock.js").read_text(encoding="utf-8")

    assert 'const JAPAN_TIMEZONE = "Asia/Tokyo";' in clock
    assert "timeZone: JAPAN_TIMEZONE" in clock
    assert "hour.value = japan.hour" in clock
    assert 'link.href = "/stats"' in clock
    assert "new Date().getHours()" not in clock


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
    assert "味噌ラーメンへの欲を赦します" in response.text
    assert "事情があります" not in response.text
    assert "ラーメン。" in response.text
    assert "近くのラーメンを探す" in response.text
    assert "赦しの画像を保存" in response.text
    assert "赦しの結果をツイート" in response.text
    assert "投稿文をコピー" not in response.text
    assert "https://ramen-indulgence.onrender.com/" in unquote(response.text)
    assert "他の文言で赦される" in response.text
    assert response.text.index("ラーメン。") < response.text.index("近くのラーメンを探す")
    assert response.text.index("近くのラーメンを探す") < response.text.index("赦しの画像を保存")
    assert "images/menyoku.png" in response.text
    assert 'alt="麺欲赦免"' in response.text
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
    assert 'href="/stats"' not in response.text
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


def test_result_rate_limit_skips_repeated_statistics_without_breaking_display(
    monkeypatch,
):
    async def scenario():
        init_db()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            monkeypatch.setattr(rate_limit.time, "time", lambda: 1_000.0)
            total_before = get_stats()["total"]
            first = await client.post("/result", data=VALID_DATA)
            total_after_first = get_stats()["total"]
            second = await client.post("/result", data=VALID_DATA)
            total_after_second = get_stats()["total"]
            reroll = await client.post(
                "/result", data={**VALID_DATA, "reroll": "true"}
            )
            total_after_reroll = get_stats()["total"]
            monkeypatch.setattr(
                rate_limit.time,
                "time",
                lambda: 1_000.0 + rate_limit.RECORD_RATE_LIMIT_SECONDS,
            )
            after_limit = await client.post("/result", data=VALID_DATA)
            total_after_limit = get_stats()["total"]
            return (
                first,
                second,
                reroll,
                after_limit,
                total_before,
                total_after_first,
                total_after_second,
                total_after_reroll,
                total_after_limit,
                client.cookies,
            )

    (
        first,
        second,
        reroll,
        after_limit,
        total_before,
        total_after_first,
        total_after_second,
        total_after_reroll,
        total_after_limit,
        cookies,
    ) = asyncio.run(scenario())

    assert (
        first.status_code
        == second.status_code
        == reroll.status_code
        == after_limit.status_code
        == 200
    )
    assert "味噌ラーメンへの欲を赦します" in first.text
    assert "味噌ラーメンへの欲を赦します" in second.text
    assert total_after_first == total_before + 1
    assert total_after_second == total_after_first
    assert total_after_reroll == total_after_first
    assert total_after_limit == total_after_first + 1
    assert "ramen_result_recorded_at" in cookies
    cookie_header = first.headers["set-cookie"].lower()
    assert f"max-age={rate_limit.RECORD_RATE_LIMIT_SECONDS}" in cookie_header
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header


def test_hidden_judgment_rate_limit_skips_repeated_statistics():
    async def scenario():
        init_db()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            total_before = get_stats()["total"]
            first = await client.post("/hidden-judgment")
            total_after_first = get_stats()["total"]
            second = await client.post("/hidden-judgment")
            total_after_second = get_stats()["total"]
            return (
                first,
                second,
                total_before,
                total_after_first,
                total_after_second,
                client.cookies,
            )

    (
        first,
        second,
        total_before,
        total_after_first,
        total_after_second,
        cookies,
    ) = asyncio.run(scenario())

    assert first.status_code == second.status_code == 200
    assert "ラーメンばんざい！" in first.text
    assert "ラーメンばんざい！" in second.text
    assert total_after_first == total_before + 1
    assert total_after_second == total_after_first
    assert "ramen_hidden_recorded_at" in cookies


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
    assert "やむなき慈悲の赦し" in first.text
    assert "やむなき慈悲の赦し" in second.text
    assert "やむなき慈悲の赦し" in third.text
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
    assert "images/suimin.png" in response.text
    assert 'alt="睡眠直行"' in response.text


def test_hidden_command_records_banzai_judgment_with_share_actions():
    trial = asyncio.run(request("GET", "/hidden-confession"))
    result = asyncio.run(request("POST", "/hidden-judgment"))
    assert trial.status_code == 200
    assert "data-auto-submit" in trial.text
    assert result.status_code == 200
    assert "ラーメンばんざい！" in result.text
    assert "banzai.png" in result.text
    assert "祝福の画像を保存" in result.text
    assert "祝福の結果をツイート" in result.text
    assert "images/menai.png" in result.text
    assert 'alt="麺愛永遠"' in result.text
    assert "今日も堂々と、ラーメンを愛します" in unquote(result.text)


def test_stats_list_sleep_and_hidden_banzai_separately():
    stats = asyncio.run(request("GET", "/stats"))
    assert stats.status_code == 200
    assert "完全なる赦し" in stats.text
    assert "見守りの赦し" in stats.text
    assert "反省を促す赦し" in stats.text
    assert "やむなき慈悲の赦し" in stats.text
    assert "今日は寝ろ（幻の助言）" in stats.text
    assert "ラーメンばんざい！（どこかに隠された祝福）" in stats.text


def test_copy_matches_mongonshusei_csv():
    with Path("mongonshusei.csv").open(encoding="utf-8-sig", newline="") as file:
        rows = csv.DictReader(file)
        changed_rows = [row for row in rows if row["文言"] != row["修正後文言"]]

    for row in changed_rows:
        source = Path(row["ファイル名"]).read_text(encoding="utf-8")
        source_without_tags = re.sub(r"<[^>]+>", "", source)
        assert (
            row["修正後文言"] in source
            or row["修正後文言"] in source_without_tags
        ), f'{row["ファイル名"]}: {row["修正後文言"]}'


def test_result_stamp_does_not_overlap_result_heading():
    stylesheet = Path("app/static/style.css").read_text(encoding="utf-8")
    canvas = Path("app/static/js/certificate_canvas.js").read_text(encoding="utf-8")
    template = Path("app/templates/result.html").read_text(encoding="utf-8")

    assert "right: 18px;" in stylesheet
    assert "top: 34px;" in stylesheet
    assert "padding: 136px 20px 25px;" in stylesheet
    assert "right: 18px; top: 26px;" in stylesheet
    assert "padding-top: 150px;" in stylesheet
    assert "font-size: clamp(52px, 16vw, 64px); white-space: nowrap;" in stylesheet
    assert "context.drawImage(sealImage, 900, 70, 180, 180);" in canvas
    assert "context.drawImage(image, 435, 55, 330, 330);" in canvas
    assert "context.fillText(verdict, 600, 435);" in canvas
    assert "context.fillText(title, 600, 520);" in canvas
    assert "margin: 0 auto 32px;" in stylesheet
    assert "margin: 8px 0 46px;" in stylesheet
    assert "margin-bottom: 12px;" in stylesheet
    assert '.result-card[data-result-type="ogre"] .result-sister' not in stylesheet
    assert 'resultType === "ogre" ? 350 : 420' not in canvas
    assert "let y = 610;" in canvas
    standard_result = template[template.index('{% else %}'):]
    assert standard_result.index('class="result-sister"') < standard_result.index('class="verdict-label"')
    assert standard_result.index('class="verdict-label"') < standard_result.index("<h1")
    assert 'alt="赦しを伝えるシスター"' in standard_result
    assert 'alt="判決を伝えるシスター"' not in standard_result
