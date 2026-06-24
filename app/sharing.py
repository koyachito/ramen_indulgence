from urllib.parse import quote

from .message_catalog import ACHIEVEMENT_SHARE_REASONS
from .models import DiagnosisResult


def share_text(result: DiagnosisResult, app_url: str) -> str:
    if result.result_type == "sleep":
        return (
            "ラーメン免罪符を求めたところ、シスターに止められました。\n\n"
            "診断結果：今日は寝ろ\n\n"
            "今日はラーメンではなく、睡眠が赦されました。\n"
            "おやすみ……\n\n"
            f"{app_url}\n"
            "#ラーメン免罪符"
        )
    return (
        "ラーメン免罪符を授かりました。\n\n"
        f"診断結果：{result.title}\n"
        f"理由：{ACHIEVEMENT_SHARE_REASONS[result.input_achievement]}\n\n"
        f"よって、{result.ramen_label}一杯が赦されました。\n"
        "ラーメン……。\n\n"
        f"{app_url}\n"
        "#ラーメン免罪符"
    )


def x_share_url(text: str) -> str:
    return f"https://twitter.com/intent/tweet?text={quote(text)}"


def maps_url(ramen_label: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote(f'近くの {ramen_label} ラーメン')}"
