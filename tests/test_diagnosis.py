from datetime import date

from app.diagnosis import (
    DATE_REASONS,
    diagnose,
    get_date_reason,
    get_food_reason,
    get_time_reason,
    maps_url,
    x_share_url,
)
from app.models import DiagnosisInput


def make_input(**overrides):
    values = {
        "current_hour": 20,
        "meals": 2,
        "walked": True,
        "worked": True,
        "current_date": date(2026, 6, 16),
        "ramen_type": "味噌",
    }
    values.update(overrides)
    return DiagnosisInput(**values)


def test_time_reason_boundaries():
    assert "一日の始まり" in get_time_reason(7)
    assert "午後のエネルギー" in get_time_reason(11)
    assert "おやつ" in get_time_reason(14)
    assert "一日の疲れ" in get_time_reason(18)
    assert "もう20時" in get_time_reason(20)
    assert "もう3時" in get_time_reason(3)


def test_food_reason_always_supports_ramen():
    assert "何も食べてない" in get_food_reason(0)
    assert "2食しか" in get_food_reason(2)
    assert "別腹" in get_food_reason(5)


def test_special_and_default_date_reasons():
    assert "細長いもの界の王" in get_date_reason(date(2026, 11, 11))
    assert "和菓子の日" in get_date_reason(date(2026, 6, 16))


def test_date_reason_file_covers_every_day_including_leap_day():
    assert len(DATE_REASONS) == 366
    assert "四年に一度" in DATE_REASONS["02-29"]
    assert "大晦日" in DATE_REASONS["12-31"]


def test_full_absolution_contains_all_reasons_and_fixed_conclusion():
    result = diagnose(make_input())
    assert result.result_type == "full"
    assert result.title == "完全免罪"
    assert len(result.reasons) == 5
    assert result.conclusion == "あなたのラーメン欲は、ここに赦されました。"
    assert "8000歩以上" in result.full_text
    assert "仕事・学習" in result.full_text


def test_activity_reasons_are_omitted_without_blame():
    result = diagnose(make_input(walked=False, worked=False))
    assert len(result.reasons) == 3
    assert "歩いて" not in result.full_text
    assert "仕事・学習" not in result.full_text


def test_conditional_and_restricted_verdicts_remain_available():
    conditional = diagnose(make_input(current_hour=20, meals=2, walked=False, worked=True))
    no_rice = diagnose(make_input(current_hour=20, meals=3, walked=False, worked=False))
    soup = diagnose(make_input(current_hour=23, meals=4, walked=False, worked=False))
    assert conditional.result_type == "conditional"
    assert no_rice.result_type == "no_rice"
    assert soup.result_type == "soup"
    assert {conditional.image, no_rice.image, soup.image} == {"eating.png"}


def test_external_urls_are_encoded():
    result = diagnose(make_input())
    share = x_share_url(result, "味噌", "https://example.com")
    assert "twitter.com/intent/tweet" in share
    assert "%E8%B5%A6%E3%81%95%E3%82%8C" in share
    assert len(share) < 500
    assert "%E5%91%B3%E5%99%8C" in maps_url("味噌")
