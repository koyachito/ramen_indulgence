from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DiagnosisInput:
    current_hour: int
    meals: int
    walked: bool
    worked: bool
    current_date: date
    ramen_type: str


@dataclass(frozen=True)
class DiagnosisResult:
    result_type: str
    title: str
    verdict: str
    reasons: tuple[str, ...]
    conclusion: str
    full_text: str
    advice: str
    tone: str
    image: str
