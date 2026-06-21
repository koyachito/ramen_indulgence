from dataclasses import dataclass


@dataclass(frozen=True)
class DiagnosisInput:
    current_hour: int
    current_month: int
    current_day: int
    meals: int
    ramen_count_today: int
    achievement: str
    mood: str
    after_plan: str
    reason_not_to_eat: str
    ramen_type: str
    forgiveness_style: str


@dataclass(frozen=True)
class DiagnosisScores:
    merit_score: int = 0
    danger_score: int = 0
    confession_score: int = 0
    comfort_need: int = 0
    comfort_type: str = "praise"
    ramen_bias: str | None = None
    oni_flag: int = 0


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
    ramen_label: str
    ramen_aruaru: str
    scores: DiagnosisScores
    input_achievement: str
