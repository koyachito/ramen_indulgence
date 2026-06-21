from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

from .models import DiagnosisInput, DiagnosisResult

RAMEN_TYPES = (
    "醤油",
    "味噌",
    "塩",
    "豚骨",
    "家系",
    "二郎系",
    "担々麺",
    "つけ麺",
    "その他",
)

DATE_REASONS_PATH = Path(__file__).with_name("date_reasons.txt")


def load_date_reasons(path: Path = DATE_REASONS_PATH) -> dict[str, str]:
    reasons: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line:
            continue
        try:
            key, reason = line.split(",", 1)
        except ValueError as error:
            raise ValueError(f"日付理由の形式が不正です: {path}:{line_number}") from error
        if key in reasons:
            raise ValueError(f"日付理由が重複しています: {key}")
        reasons[key] = reason

    current = date(2000, 1, 1)
    expected_keys = set()
    while current.year == 2000:
        expected_keys.add(current.strftime("%m-%d"))
        current += timedelta(days=1)
    missing = expected_keys - reasons.keys()
    unexpected = reasons.keys() - expected_keys
    if missing or unexpected:
        raise ValueError(
            f"日付理由のキーが不完全です: missing={sorted(missing)}, "
            f"unexpected={sorted(unexpected)}"
        )
    return reasons


DATE_REASONS = load_date_reasons()


def get_time_reason(hour: int) -> str:
    if 7 <= hour < 11:
        return "一日の始まりにはラーメンを食べるべきだし"
    if 11 <= hour < 14:
        return "昼時にラーメンを食べて午後のエネルギーを蓄えるべきだし"
    if 14 <= hour < 18:
        return "おやつのラーメンはなによりも元気の源だし"
    if 18 <= hour < 20:
        return "夕飯のラーメンは一日の疲れをとってくれるし"
    return f"もう{hour}時なので、理性よりもラーメンを優先すべきだし"


def get_food_reason(meals: int) -> str:
    if meals == 0:
        return "今日はまだ何も食べてないし"
    if meals <= 2:
        return f"今日はまだ{meals}食しか食べてないし"
    return f"{meals}食食べたあとでもラーメンは別腹だし"


def get_date_reason(value) -> str:
    key = value.strftime("%m-%d")
    return DATE_REASONS.get(
        key, "特に何もない日だから、ラーメンで意味を与えるべきだし"
    )


def diagnose(data: DiagnosisInput) -> DiagnosisResult:
    reasons = [
        get_time_reason(data.current_hour),
        get_food_reason(data.meals),
    ]
    if data.walked:
        reasons.append("今日は8000歩以上歩いてるし")
    if data.worked:
        reasons.append("今日は仕事・学習・作業をしっかりやったし")
    reasons.append(get_date_reason(data.current_date))

    score = {0: 3, 1: 2, 2: 1, 3: 0, 4: -1, 5: -2}[data.meals]
    score += 2 if data.walked else 0
    score += 2 if data.worked else 0
    if data.current_hour >= 23 or data.current_hour < 5:
        score -= 2
    if data.ramen_type == "二郎系":
        score -= 1

    if score >= 5:
        result_type, title, verdict = "full", "完全免罪", "無条件許可"
        advice, tone, image = "本日の一杯に異議なし。熱いうちに堂々と食べること。", "success", "eating.png"
    elif score >= 2:
        result_type, title, verdict = "conditional", "条件付き免罪", "条件付き許可"
        advice, tone, image = "スープ完飲は慎み、水も一緒に飲むこと。", "success", "eating.png"
    elif score >= 0:
        result_type, title, verdict = "no_rice", "半ライス禁止付き免罪", "限定許可"
        advice, tone, image = "大盛り・替え玉・半ライスの三権を一時停止する。", "warning", "eating.png"
    else:
        result_type, title, verdict = "soup", "スープ残し推奨", "慎重許可"
        advice, tone, image = "麺量は普通まで。スープを残し、サイドメニューは付けないこと。", "warning", "eating.png"

    if data.ramen_type == "担々麺":
        advice += " 白シャツへの飛沫にも警戒せよ。"
    elif data.ramen_type == "家系":
        advice += " 海苔の運用は計画的に。"
    elif data.ramen_type == "二郎系":
        advice += " コールは平常心で。"

    conclusion = "あなたのラーメン欲は、ここに赦されました。"
    full_text = "、\n".join(reasons[:-1]) + f"、\n{reasons[-1]}。\n\n{conclusion}"
    return DiagnosisResult(
        result_type=result_type,
        title=title,
        verdict=verdict,
        reasons=tuple(reasons),
        conclusion=conclusion,
        full_text=full_text,
        advice=advice,
        tone=tone,
        image=image,
    )


def x_share_url(result: DiagnosisResult, ramen_type: str, app_url: str) -> str:
    text = (
        f"本日のラーメン免罪：{result.title}\n"
        f"{ramen_type}ラーメンへの欲は赦されました。\n"
        "#ラーメン免罪符"
    )
    return f"https://twitter.com/intent/tweet?text={quote(text)}&url={quote(app_url)}"


def maps_url(ramen_type: str) -> str:
    keyword = "近くの ラーメン" if ramen_type == "その他" else f"近くの {ramen_type}ラーメン"
    return f"https://www.google.com/maps/search/?api=1&query={quote(keyword)}"
