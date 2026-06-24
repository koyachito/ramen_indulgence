import random

from .models import DiagnosisInput, DiagnosisScores


def calculate_scores(data: DiagnosisInput) -> DiagnosisScores:
    merit = {"worked": 2, "went_out": 1, "walked": 1, "housework": 2, "woke_early": 1, "kindness": 2, "oshi": 1, "shorts": -1, "nothing": 0}[data.achievement]
    danger = {0: -1, 1: 0, 2: 0, 3: 1, 4: 2}[data.meals]
    confession = {"shorts": 2, "nothing": 1}.get(data.achievement, 0)
    comfort = {"tired": 1, "hungry": 1, "lonely": 2, "empty": 2}.get(data.mood, 0)
    oni = int(data.meals == 4)
    ramen_bias = {"tired": "miso", "hungry": "jiro", "angry": "iekei"}.get(data.mood)

    if data.mood == "angry":
        confession += 1
    elif data.mood == "proud":
        merit += 1
    if data.mood == "lonely":
        ramen_bias = random.choice(("miso", "shio"))

    if data.meals >= 3:
        danger += {0: 0, 1: 1, 2: 2, 3: 3}[data.ramen_count_today]
        oni += {0: 0, 1: 0, 2: 1, 3: 2}[data.ramen_count_today]

    if data.achievement == "shorts":
        oni += 1
        ramen_bias = random.choice(("iekei", "jiro"))

    if data.reason_not_to_eat == "yes":
        danger += 1
    elif data.reason_not_to_eat == "ignore":
        confession += 2
        oni += 1

    if data.ramen_type == "tonkotsu":
        oni += 1
    elif data.ramen_type == "iekei":
        danger += 1
    elif data.ramen_type == "jiro":
        danger += 2
        oni += 1

    if data.forgiveness_style == "strict":
        oni += 1
        if data.meals >= 3 and data.achievement == "shorts":
            oni += 1

    if data.after_plan == "work_more":
        merit += 1
    elif data.after_plan in {"sleep", "meet_people"}:
        danger += 1
    elif data.after_plan == "nothing":
        confession += 1
    elif data.after_plan == "more_shorts":
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
        and data.achievement == "shorts"
        and data.mood == "empty"
        and data.after_plan == "more_shorts"
        and data.reason_not_to_eat in {"yes", "ignore"}
        and data.ramen_type in {"tonkotsu", "iekei", "jiro"}
        and data.forgiveness_style == "strict"
    )
