import random

from .message_catalog import (
    ACHIEVEMENT_REASONS,
    DATE_REASONS,
    FORGIVENESS_REASONS,
    MEAL_REASONS,
    MOOD_REASONS,
    PLAN_REASONS,
    RAMEN_ARUARU,
    RAMEN_TYPE_LABELS,
    REASON_NOT_TO_EAT_REASONS,
)
from .models import DiagnosisInput, DiagnosisResult, DiagnosisScores
from .scoring import determine_result_type


def select_sister_image(scores: DiagnosisScores, result_type: str) -> str:
    if result_type == "sleep":
        return "prayer.png"
    if result_type == "ogre":
        return "ogreleft.png"
    if result_type == "angry":
        return "angry_eating.png"
    return "eating.png"


def _caution_reason(danger_score: int, rng=random) -> str:
    if danger_score >= 4:
        return rng.choice(("通常なら少し立ち止まって休むべきです", "シスターも少し心配しています"))
    if danger_score >= 2:
        return rng.choice(("慎重に受け止めるべき迷いがあります", "無理をしないことも大切です"))
    return rng.choice(("特に大きな迷いは見当たりません", "シスターは穏やかに話を聞きました"))


def _date_context(data: DiagnosisInput) -> str:
    key = f"{data.current_month:02d}-{data.current_day:02d}"
    text = DATE_REASONS.get(key, "名もなき一日だから、好きな一杯で印をつけてもよいのです")
    return f"{data.current_month}月{data.current_day}日、{text}"


def _time_context(hour: int) -> str:
    if 5 <= hour < 11:
        return "朝の一杯には、その後を動かす力があります"
    if 11 <= hour < 14:
        return "ちょうど昼どき。ラーメンには申し分のない時間です"
    if 14 <= hour < 18:
        return "遅い昼食としてなら、十分に説明がつく時間です"
    if 18 <= hour < 22:
        return "一日の締めに、湯気の立つ丼が似合う時間です"
    return f"現在は{hour}時なので、食べるなら軽めにしてください"


def _ramen_count_context(data: DiagnosisInput) -> str:
    if data.meals < 3:
        return ""
    return {
        0: "三食の中にラーメンはなく、本日一杯目として穏やかに赦されます",
        1: "すでに一杯食べていますが、まだ赦しの余地はあります",
        2: "今日はすでに二杯。十分に麺へ尽くしています",
        3: "今日は三杯以上。これは食事というより巡礼です",
    }[data.ramen_count_today]


def _natural_reasons(data: DiagnosisInput, scores: DiagnosisScores, rng=random) -> tuple[str, ...]:
    personal = [
        rng.choice(ACHIEVEMENT_REASONS[data.achievement]),
        rng.choice(MOOD_REASONS[data.mood]),
    ]
    meal_and_time = [
        rng.choice(MEAL_REASONS[data.meals]),
        _time_context(data.current_hour),
        _date_context(data),
    ]
    ramen_count = _ramen_count_context(data)
    if ramen_count:
        meal_and_time.append(ramen_count)
    judgment = [
        rng.choice(PLAN_REASONS[data.after_plan]),
        rng.choice(REASON_NOT_TO_EAT_REASONS[data.reason_not_to_eat]),
        rng.choice(FORGIVENESS_REASONS[data.forgiveness_style]),
        _caution_reason(scores.danger_score, rng),
    ]
    return tuple(f"{rng.choice(group).rstrip('。')}。" for group in (personal, meal_and_time, judgment))


def _ramen_selection(data: DiagnosisInput, scores: DiagnosisScores, rng=random) -> tuple[str, str]:
    selected = data.ramen_type
    if selected == "other":
        candidates = tuple(key for key in RAMEN_TYPE_LABELS if key != "other")
        selected = scores.ramen_bias if scores.ramen_bias in candidates else rng.choice(candidates)
    return RAMEN_TYPE_LABELS[selected], rng.choice(RAMEN_ARUARU[selected])


def generate_result_text(
    data: DiagnosisInput,
    scores: DiagnosisScores,
    result_type: str | None = None,
    rng: random.Random | None = None,
) -> DiagnosisResult:
    rng = rng or random
    result_type = result_type or determine_result_type(scores)
    ramen_label, ramen_aruaru = _ramen_selection(data, scores, rng)
    reasons = _natural_reasons(data, scores, rng)

    if result_type == "sleep":
        title, verdict, tone = "今日は寝ろ", "休息の勧め", "sleep"
        conclusion = "今日は寝ろ"
        full_text = "今日は寝ろ"
    else:
        metadata = {
            "forgiven": ("完全なる赦し", "ささやかな懺悔", "success"),
            "worry": ("見守りの赦し", "素直な懺悔", "warning"),
            "angry": ("反省を促す赦し", "深い懺悔", "danger"),
            "ogre": ("やむなき慈悲の赦し", "魂の懺悔", "danger"),
        }
        title, verdict, tone = metadata[result_type]
        conclusion = f"{ramen_label}ラーメンへの欲は赦されました。ラーメン。"
        full_text = "\n".join(
            (*reasons, f"{ramen_label}ラーメンへの欲を赦します。", "ラーメン。")
        )

    return DiagnosisResult(
        result_type=result_type,
        title=title,
        verdict=verdict,
        reasons=reasons,
        conclusion=conclusion,
        full_text=full_text,
        advice=f"ラーメンあるある：{ramen_aruaru}",
        tone=tone,
        image=select_sister_image(scores, result_type),
        ramen_label=ramen_label,
        ramen_aruaru=ramen_aruaru,
        scores=scores,
        input_achievement=data.achievement,
    )
