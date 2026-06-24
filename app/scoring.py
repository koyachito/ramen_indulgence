import random

from .choices import (
    Achievement,
    AfterPlan,
    ForgivenessStyle,
    Mood,
    RamenType,
    ReasonNotToEat,
)
from .models import DiagnosisInput, DiagnosisScores


def calculate_scores(data: DiagnosisInput) -> DiagnosisScores:
    merit = {
        Achievement.WORKED: 2,
        Achievement.WENT_OUT: 1,
        Achievement.WALKED: 1,
        Achievement.HOUSEWORK: 2,
        Achievement.WOKE_EARLY: 1,
        Achievement.KINDNESS: 2,
        Achievement.OSHI: 1,
        Achievement.SHORTS: -1,
        Achievement.NOTHING: 0,
    }[data.achievement]
    danger = {0: -1, 1: 0, 2: 0, 3: 1, 4: 2}[data.meals]
    confession = {
        Achievement.SHORTS: 2,
        Achievement.NOTHING: 1,
    }.get(data.achievement, 0)
    comfort = {
        Mood.TIRED: 1,
        Mood.HUNGRY: 1,
        Mood.LONELY: 2,
        Mood.EMPTY: 2,
    }.get(data.mood, 0)
    oni = int(data.meals == 4)
    ramen_bias = {
        Mood.TIRED: RamenType.MISO,
        Mood.HUNGRY: RamenType.JIRO,
        Mood.ANGRY: RamenType.IEKEI,
    }.get(data.mood)

    if data.mood == Mood.ANGRY:
        confession += 1
    elif data.mood == Mood.PROUD:
        merit += 1
    if data.mood == Mood.LONELY:
        ramen_bias = random.choice((RamenType.MISO, RamenType.SHIO))

    if data.meals >= 3:
        danger += {0: 0, 1: 1, 2: 2, 3: 3}[data.ramen_count_today]
        oni += {0: 0, 1: 0, 2: 1, 3: 2}[data.ramen_count_today]

    if data.achievement == Achievement.SHORTS:
        oni += 1
        ramen_bias = random.choice((RamenType.IEKEI, RamenType.JIRO))

    if data.reason_not_to_eat == ReasonNotToEat.YES:
        danger += 1
    elif data.reason_not_to_eat == ReasonNotToEat.IGNORE:
        confession += 2
        oni += 1

    if data.ramen_type == RamenType.TONKOTSU:
        oni += 1
    elif data.ramen_type == RamenType.IEKEI:
        danger += 1
    elif data.ramen_type == RamenType.JIRO:
        danger += 2
        oni += 1

    if data.forgiveness_style == ForgivenessStyle.STRICT:
        oni += 1
        if data.meals >= 3 and data.achievement == Achievement.SHORTS:
            oni += 1

    if data.after_plan == AfterPlan.WORK_MORE:
        merit += 1
    elif data.after_plan in {AfterPlan.SLEEP, AfterPlan.MEET_PEOPLE}:
        danger += 1
    elif data.after_plan == AfterPlan.NOTHING:
        confession += 1
    elif data.after_plan == AfterPlan.MORE_SHORTS:
        confession += 2
        oni += 1

    return DiagnosisScores(
        merit_score=merit,
        danger_score=danger,
        confession_score=confession,
        comfort_need=comfort,
        comfort_type=data.forgiveness_style,
        ramen_bias=ramen_bias,
        oni_flag=oni,
    )


def determine_result_type(scores: DiagnosisScores) -> str:
    if scores.oni_flag >= 4:
        return "ogre"
    if scores.danger_score >= 3:
        return "angry"
    if scores.danger_score >= 2:
        return "worry"
    return "forgiven"


def is_hidden_sleep_result(data: DiagnosisInput) -> bool:
    return (
        data.meals == 4
        and data.ramen_count_today == 3
        and data.achievement == Achievement.SHORTS
        and data.mood == Mood.EMPTY
        and data.after_plan == AfterPlan.MORE_SHORTS
        and data.reason_not_to_eat in {ReasonNotToEat.YES, ReasonNotToEat.IGNORE}
        and data.ramen_type in {RamenType.TONKOTSU, RamenType.IEKEI, RamenType.JIRO}
        and data.forgiveness_style == ForgivenessStyle.STRICT
    )
