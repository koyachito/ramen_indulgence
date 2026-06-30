"""Public entry point for diagnosis generation.

The re-exports keep the existing ``app.diagnosis`` API stable while the
implementation lives in modules grouped by responsibility.
"""

from .choices import RAMEN_TYPE_LABELS, RAMEN_TYPES
from .message_catalog import DATE_REASONS
from .models import DiagnosisInput, DiagnosisResult
from .result_generator import generate_result_text, select_sister_image
from .scoring import calculate_scores, determine_result_type, is_hidden_sleep_result
from .sharing import maps_url, share_text, x_share_url


def diagnose(data: DiagnosisInput) -> DiagnosisResult:
    scores = calculate_scores(data)
    result_type = "sleep" if is_hidden_sleep_result(data) else determine_result_type(scores)
    return generate_result_text(data, scores, result_type)


__all__ = [
    "DATE_REASONS",
    "RAMEN_TYPE_LABELS",
    "RAMEN_TYPES",
    "calculate_scores",
    "determine_result_type",
    "diagnose",
    "generate_result_text",
    "is_hidden_sleep_result",
    "maps_url",
    "select_sister_image",
    "share_text",
    "x_share_url",
]
