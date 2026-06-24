import random
from pathlib import Path
from urllib.parse import quote

from .models import DiagnosisInput, DiagnosisResult, DiagnosisScores

RAMEN_TYPE_LABELS = {
    "shoyu": "醤油",
    "miso": "味噌",
    "shio": "塩",
    "tonkotsu": "豚骨",
    "iekei": "家系",
    "jiro": "二郎系",
    "tsukemen": "つけ麺",
    "other": "その他",
}
RAMEN_TYPES = tuple(RAMEN_TYPE_LABELS.values())
DATE_REASONS_PATH = Path(__file__).with_name("date_reasons.txt")

ACHIEVEMENT_REASONS = {
    "worked": ("労働または学習という尊い務めを果たしました", "今日やるべきことに向き合いました", "少なくとも、何かを前に進めました"),
    "went_out": ("外の世界へ足を踏み出しました", "玄関を越えるという務めを果たしました", "きちんと外出を成し遂げました"),
    "walked": ("自らの足で今日を進みました", "歩くという確かな実績を残しました", "麺へ向かう脚力を養いました"),
    "housework": ("暮らしを維持する家事を果たしました", "生活を整える務めを果たしました", "名もなき家事をきちんと片づけました"),
    "woke_early": ("いつもより少し早く起きました", "起床という第一の修行を終えました", "朝の時間を少しだけ取り戻しました"),
    "kindness": ("誰かにやさしくする善行を積みました", "人へのやさしさを忘れませんでした", "今日ひとつ、善い行いを残しました"),
    "oshi": ("推しを見守る精神的労働を完遂しました", "大切な配信を最後まで見届けました", "推しへの務めを果たしました"),
    "shorts": ("時間を電子の海に捧げました", "タイムラインの巡礼を終えました", "短い動画を無数に見届けました"),
    "nothing": ("何もしていないという事実を正直に申告しました", "今日はまだ、力を温存しています", "これから何かをする可能性を残しています"),
}

MOOD_REASONS = {
    "tired": ("心身に疲労が見られます", "休息と塩分を求めているようです"),
    "hungry": ("空腹という重大な証言があります", "胃袋が正式に申し立てを行っています"),
    "angry": ("心にむしゃくしゃした気配があります", "気持ちを落ち着ける温かいものが必要です"),
    "lonely": ("温かいものを必要としているようです", "丼のぬくもりが必要な状態です"),
    "proud": ("達成感があり、今日は少し誇らしい気分です", "今日の成果を祝う準備ができています"),
    "empty": ("考える力を使い切っているようです", "券売機に判断を委ねたい状態です"),
}

FORGIVENESS_REASONS = {
    "praise": ("今日を乗り切ったあなたには報いが必要です", "よくやったあなたには温かい一杯が必要です"),
    "spoil": ("今日はラーメンに甘やかされてもよいでしょう", "今日はスープに抱きしめられてください"),
    "strict": ("反省は必要ですが、ラーメンとの両立は可能です", "罪はありますが、まだ赦しの余地もあります"),
    "push": ("背中は押しました。あとは店を選ぶだけです", "暖簾は、くぐる者の前にだけ現れます"),
    "oracle": ("麺は示され、スープは満ちています", "丼は沈黙し、しかし確かにあなたを呼んでいます"),
}

MEAL_REASONS = {
    0: ("今日はまだ何も食べていないため、まず食事が必要です", "空腹のまま終えるより、温かい一杯を入れるべきです"),
    1: ("今日の食事はまだ一食だけで、丼を迎える余地があります", "一食だけでここまで来たなら、追加の一杯は妥当です"),
    2: ("今日は二食なので、食事量としては穏当です", "二食を済ませた程度なら、まだ一杯を検討できます"),
    3: ("すでに三食なので、追加の一杯には少し注意が必要です", "三食を終えた胃袋には、普通盛りがよさそうです"),
    4: ("四食以上なので、量だけは控えるべきです", "食事回数があいまいです。大盛りは見送りましょう"),
}

PLAN_REASONS = {
    "work_more": ("このあとも作業があるため、一杯を燃料にできます", "残った仕事を進めるための補給が必要です"),
    "sleep": ("このあとは寝るだけなので、量は控えめがよいでしょう", "食後すぐ眠るなら、重すぎない一杯にしてください"),
    "go_home": ("あとは帰るだけなので、帰路の一杯には十分な余白があります", "今日の締めとして、帰り道の一杯が似合います"),
    "meet_people": ("このあと人に会うため、にんにくの量には注意してください", "人と会う予定まで含めて、香りの穏やかな一杯を選びましょう"),
    "nothing": ("このあと予定がないなら、ラーメンを今日の予定にできます", "空いた時間に、温かい一杯を置いてもよいでしょう"),
    "more_shorts": ("このあとも動画を見るなら、せめて麺が伸びる前に食べてください", "画面へ戻る前に、丼にはきちんと向き合いましょう"),
}

REASON_NOT_TO_EAT_REASONS = {
    "none": ("食べない理由はなく、審議を妨げるものもありません", "止める理由がないなら、残る問題は店選びだけです"),
    "yes": ("ためらう理由があるため、量と体調には気を配ってください", "食べない理由も尊重し、無茶をしないことが条件です"),
    "ignore": ("都合の悪い理由から目をそらした点は反省してください", "食べない理由を無視するなら、少なくとも水は飲みなさい"),
}

RAMEN_ARUARU = {
    "shoyu": ("結局「こういうのでいい」に戻ってくる", "香りを嗅いだ瞬間、王道の強さを思い知る"),
    "miso": ("寒い日でも暑い日でも、結局うまい", "コーンを最後まで追いかけてしまう"),
    "shio": ("あっさりの顔をして、しっかり満足させてくる", "透明なスープほど底まで見届けたくなる"),
    "tonkotsu": ("替え玉を頼むか、食べ始める前から考えている", "紅しょうがを入れるタイミングで毎回迷う"),
    "iekei": ("ライスを付けるかどうかで最後まで悩む", "海苔をスープに浸す順番に自分なりの流儀がある"),
    "jiro": ("今日は軽めにするつもりが、気づいたら全マシになっている", "並びながらコールを心の中で何度も練習する"),
    "tsukemen": ("麺を少しだけ残してスープ割りの配分を考える", "一口目の麺だけで、もう大盛りにすればよかったと思う"),
}

ACHIEVEMENT_SHARE_REASONS = {
    "worked": "今日は仕事・勉強をしたので",
    "went_out": "今日は外に出たので",
    "walked": "今日は自分の足で歩いたので",
    "housework": "今日は家事をしたので",
    "woke_early": "今日はいつもより少し早く起きたので",
    "kindness": "今日は人に優しくしたので",
    "oshi": "今日は推しの配信を見守ったので",
    "shorts": "今日は短い動画を無数に見届けたので",
    "nothing": "今日は何もしていないと正直に申告したので",
}


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


def select_sister_image(scores: DiagnosisScores, result_type: str) -> str:
    if result_type == "sleep":
        return "prayer.png"
    if result_type == "ogre":
        return "ogre.png"
    if result_type == "angry":
        return "angry_eating.png"
    return "eating.png"


def _caution_reason(danger_score: int, rng=random) -> str:
    if danger_score >= 4:
        return rng.choice(("通常であれば止めるべき案件です", "かなり厳しい審議となりました"))
    if danger_score >= 2:
        return rng.choice(("慎重な判断が必要です", "罪の気配がないとは言えません"))
    return rng.choice(("特に大きな問題は見当たりません", "審議は比較的穏やかに進みました"))


def _load_date_reasons() -> dict[str, str]:
    reasons = {}
    for line in DATE_REASONS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            key, text = line.split(",", 1)
            reasons[key] = text
    return reasons


DATE_REASONS = _load_date_reasons()


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


def diagnose(data: DiagnosisInput) -> DiagnosisResult:
    scores = calculate_scores(data)
    result_type = "sleep" if is_hidden_sleep_result(data) else determine_result_type(scores)
    return generate_result_text(data, scores, result_type)


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
