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
        return "ogre.png"
    if result_type == "angry":
        return "angry_eating.png"
    return "eating.png"


def _caution_reason(danger_score: int) -> str:
    if danger_score >= 4:
        return random.choice(("通常であれば止めるべき案件です", "かなり厳しい審議となりました"))
    if danger_score >= 2:
        return random.choice(("慎重な判断が必要です", "罪の気配がないとは言えません"))
    return random.choice(("特に大きな問題は見当たりません", "審議は比較的穏やかに進みました"))


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
        0: "三食の中にラーメンはなく、今日の一杯はまだ初犯です",
        1: "すでに一杯食べているため、次は二杯目です",
        2: "今日はすでに二杯。十分に麺へ尽くしています",
        3: "今日は三杯以上。これは食事というより巡礼です",
    }[data.ramen_count_today]


def _natural_reasons(data: DiagnosisInput, scores: DiagnosisScores) -> tuple[str, ...]:
    personal = [
        random.choice(ACHIEVEMENT_REASONS[data.achievement]),
        random.choice(MOOD_REASONS[data.mood]),
    ]
    meal_and_time = [
        random.choice(MEAL_REASONS[data.meals]),
        _time_context(data.current_hour),
        _date_context(data),
    ]
    ramen_count = _ramen_count_context(data)
    if ramen_count:
        meal_and_time.append(ramen_count)
    judgment = [
        random.choice(PLAN_REASONS[data.after_plan]),
        random.choice(REASON_NOT_TO_EAT_REASONS[data.reason_not_to_eat]),
        random.choice(FORGIVENESS_REASONS[data.forgiveness_style]),
        _caution_reason(scores.danger_score),
    ]
    return tuple(f"{random.choice(group).rstrip('。')}。" for group in (personal, meal_and_time, judgment))


def _ramen_selection(data: DiagnosisInput, scores: DiagnosisScores) -> tuple[str, str]:
    selected = data.ramen_type
    if selected == "other":
        candidates = tuple(key for key in RAMEN_TYPE_LABELS if key != "other")
        selected = scores.ramen_bias if scores.ramen_bias in candidates else random.choice(candidates)
    return RAMEN_TYPE_LABELS[selected], random.choice(RAMEN_ARUARU[selected])


def generate_result_text(
    data: DiagnosisInput,
    scores: DiagnosisScores,
    result_type: str | None = None,
) -> DiagnosisResult:
    result_type = result_type or determine_result_type(scores)
    ramen_label, ramen_aruaru = _ramen_selection(data, scores)
    reasons = _natural_reasons(data, scores)

    if result_type == "sleep":
        title, verdict, tone = "今日は寝ろ", "特別判決", "sleep"
        conclusion = "今日は寝ろ"
        full_text = "今日は寝ろ"
    else:
        metadata = {
            "forgiven": ("赦し", "免罪判決", "success"),
            "worry": ("慎重な赦し", "要注意判決", "warning"),
            "angry": ("反省付きの赦し", "厳重審議", "danger"),
            "ogre": ("鬼審議の末の赦し", "重大審議", "danger"),
        }
        title, verdict, tone = metadata[result_type]
        conclusion = f"{ramen_label}ラーメン一杯は赦されました。ラーメン。"
        full_text = "\n".join(
            (*reasons, f"{ramen_label}ラーメン一杯を赦します。", "ラーメン。")
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
