import random
from dataclasses import replace

from app.diagnosis import (
    DATE_REASONS,
    RAMEN_TYPE_LABELS,
    _date_context,
    calculate_scores,
    diagnose,
    generate_result_text,
    is_hidden_sleep_result,
    maps_url,
    select_sister_image,
    share_text,
    x_share_url,
)
from app.models import DiagnosisInput


def make_input(**overrides):
    values = {
        "current_hour": 20,
        "current_month": 6,
        "current_day": 22,
        "meals": 2,
        "ramen_count_today": 0,
        "achievement": "worked",
        "mood": "tired",
        "after_plan": "work_more",
        "reason_not_to_eat": "none",
        "ramen_type": "miso",
        "forgiveness_style": "praise",
    }
    values.update(overrides)
    return DiagnosisInput(**values)


def test_low_risk_input_is_forgiven_and_ends_with_ramen():
    result = diagnose(make_input())
    assert result.result_type == "forgiven"
    assert result.image == "eating.png"
    assert result.full_text.endswith("ラーメン。")
    assert "味噌ラーメン一杯を赦します" in result.full_text
    assert "事情があります" not in result.full_text
    assert "迷っている時間" not in result.full_text
    assert len(result.reasons) == 3
    assert len(result.full_text.splitlines()) == 5


def test_all_date_reasons_have_consistent_polite_endings():
    assert len(DATE_REASONS) == 366
    assert all(reason.endswith(("なのです", "のです")) for reason in DATE_REASONS.values())
    context = _date_context(make_input())
    assert "6月22日" in context
    assert "ボウリングの日" in context
    assert context.endswith(("なのです", "のです"))


def test_scores_follow_oni_conditions():
    data = make_input(
        meals=4,
        ramen_count_today=2,
        achievement="shorts",
        after_plan="more_shorts",
        reason_not_to_eat="ignore",
        ramen_type="jiro",
        forgiveness_style="strict",
    )
    scores = calculate_scores(data)
    assert scores.oni_flag == 8
    assert scores.danger_score == 6
    assert scores.confession_score == 6
    assert diagnose(data).result_type == "ogre"
    assert diagnose(data).image == "ogre.png"


def test_angry_mood_does_not_add_oni_flag():
    calm = calculate_scores(make_input(mood="tired"))
    angry = calculate_scores(make_input(mood="angry"))
    assert angry.oni_flag == calm.oni_flag
    assert angry.confession_score == calm.confession_score + 1


def test_strict_three_meals_and_shorts_reaches_ogre():
    result = diagnose(
        make_input(
            meals=3,
            achievement="shorts",
            ramen_type="tonkotsu",
            forgiveness_style="strict",
        )
    )
    assert result.scores.oni_flag >= 4
    assert result.result_type == "ogre"


def test_deep_night_never_directly_forces_sleep():
    normal = diagnose(make_input(current_hour=23, meals=3, after_plan="sleep"))
    extreme = diagnose(
        make_input(
            current_hour=23,
            meals=4,
            ramen_count_today=3,
            achievement="shorts",
            after_plan="more_shorts",
            reason_not_to_eat="ignore",
            ramen_type="jiro",
            forgiveness_style="strict",
        )
    )
    assert normal.result_type != "sleep"
    assert extreme.result_type == "ogre"


def test_result_image_priority():
    base = calculate_scores(make_input())
    assert select_sister_image(replace(base, merit_score=0), "forgiven") == "eating.png"
    assert select_sister_image(base, "worry") == "eating.png"
    assert select_sister_image(base, "angry") == "angry_eating.png"
    assert select_sister_image(base, "ogre") == "ogre.png"
    assert select_sister_image(base, "sleep") == "prayer.png"


def test_tonkotsu_and_jiro_add_oni_flag():
    base = calculate_scores(make_input(ramen_type="shoyu"))
    tonkotsu = calculate_scores(make_input(ramen_type="tonkotsu"))
    jiro = calculate_scores(make_input(ramen_type="jiro"))
    assert tonkotsu.oni_flag == base.oni_flag + 1
    assert jiro.oni_flag == base.oni_flag + 1


def test_sleep_result_requires_exact_answer_combination():
    exact = make_input(
        meals=4,
        ramen_count_today=3,
        achievement="shorts",
        mood="empty",
        after_plan="more_shorts",
        reason_not_to_eat="yes",
        ramen_type="tonkotsu",
        forgiveness_style="strict",
    )
    assert is_hidden_sleep_result(exact)
    assert diagnose(exact).result_type == "sleep"

    for field, value in {
        "meals": 3,
        "ramen_count_today": 2,
        "achievement": "worked",
        "mood": "tired",
        "after_plan": "sleep",
        "reason_not_to_eat": "none",
        "ramen_type": "miso",
        "forgiveness_style": "praise",
    }.items():
        changed = replace(exact, **{field: value})
        assert not is_hidden_sleep_result(changed)
        assert diagnose(changed).result_type != "sleep"


def test_other_selects_a_concrete_ramen_recommendation():
    result = diagnose(make_input(ramen_type="other"))
    assert result.ramen_label in set(RAMEN_TYPE_LABELS.values()) - {"その他"}
    assert result.ramen_aruaru


def test_seeded_result_generation_is_reproducible():
    data = make_input()
    scores = calculate_scores(data)

    first = generate_result_text(data, scores, rng=random.Random(42))
    second = generate_result_text(data, scores, rng=random.Random(42))

    assert first == second


def test_seed_changes_wording_without_changing_judgment():
    data = make_input()
    scores = calculate_scores(data)

    first = generate_result_text(data, scores, rng=random.Random(1))
    second = generate_result_text(data, scores, rng=random.Random(2))

    assert first.full_text != second.full_text
    assert first.result_type == second.result_type
    assert first.scores == second.scores == scores


def test_external_urls_are_encoded():
    result = diagnose(make_input(achievement="kindness", ramen_type="jiro"))
    text = share_text(result, "https://ramen-indulgence.onrender.com/")
    share = x_share_url(text)
    assert "twitter.com/intent/tweet" in share
    assert "%E3%83%A9%E3%83%BC%E3%83%A1%E3%83%B3" in share
    assert "https://ramen-indulgence.onrender.com/" in text
    assert "理由：今日は人に優しくしたので" in text
    assert "よって、二郎系一杯が赦されました。" in text
    assert "ラーメン……。" in text
    assert "#ラーメン免罪符" in text
    assert "%E5%91%B3%E5%99%8C" in maps_url("味噌")


def test_sleep_result_has_dedicated_share_text():
    data = make_input(
        current_hour=23,
        meals=4,
        ramen_count_today=3,
        achievement="shorts",
        after_plan="more_shorts",
        reason_not_to_eat="ignore",
        ramen_type="jiro",
        forgiveness_style="strict",
    )
    base = diagnose(data)
    result = generate_result_text(data, base.scores, "sleep")
    text = share_text(result, "https://ramen-indulgence.onrender.com/")
    assert "シスターに止められました" in text
    assert "診断結果：今日は寝ろ" in text
    assert "睡眠が赦されました" in text
    assert "おやすみ……" in text
    assert "本日の一杯" not in text
