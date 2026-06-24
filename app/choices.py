"""Single source of truth for diagnosis choices and interview reactions."""

from dataclasses import dataclass


class Achievement:
    WORKED = "worked"
    WENT_OUT = "went_out"
    WALKED = "walked"
    HOUSEWORK = "housework"
    WOKE_EARLY = "woke_early"
    KINDNESS = "kindness"
    OSHI = "oshi"
    SHORTS = "shorts"
    NOTHING = "nothing"


class Mood:
    TIRED = "tired"
    HUNGRY = "hungry"
    ANGRY = "angry"
    LONELY = "lonely"
    PROUD = "proud"
    EMPTY = "empty"


class AfterPlan:
    WORK_MORE = "work_more"
    SLEEP = "sleep"
    GO_HOME = "go_home"
    MEET_PEOPLE = "meet_people"
    NOTHING = "nothing"
    MORE_SHORTS = "more_shorts"


class ReasonNotToEat:
    NONE = "none"
    YES = "yes"
    IGNORE = "ignore"


class RamenType:
    SHOYU = "shoyu"
    MISO = "miso"
    SHIO = "shio"
    TONKOTSU = "tonkotsu"
    IEKEI = "iekei"
    JIRO = "jiro"
    TSUKEMEN = "tsukemen"
    OTHER = "other"


class ForgivenessStyle:
    PRAISE = "praise"
    SPOIL = "spoil"
    STRICT = "strict"
    PUSH = "push"
    ORACLE = "oracle"


@dataclass(frozen=True)
class Choice:
    value: str | int
    label: str
    reaction_image: str
    reaction_text: str
    result_label: str | None = None


@dataclass(frozen=True)
class Question:
    name: str
    aria_label: str
    number: str
    prompt_image: str
    prompt_text: str
    choices: tuple[Choice, ...]
    css_class: str = ""
    conditional: bool = False


DIAGNOSIS_QUESTIONS = (
    Question(
        "meals", "今日すでに何食食べましたか？", "QUESTION 1 / 7", "thinking.png",
        "まず確認します。今日、すでに何食食べましたか？",
        (
            Choice(0, "まだ何も食べていない", "worry.png", "むしろ食べてください！ラーメン以前に、まず食事です！"),
            Choice(1, "1食だけ", "thinking.png", "まだ余地がありますね。話を続けましょう。"),
            Choice(2, "2食食べた", "thinking.png", "一般的な食生活の範囲です。落ち着いて審議できます。"),
            Choice(3, "3食食べた", "worry.png", "すでに三食……慎重な判断が必要です。"),
            Choice(4, "4食以上 / 記憶があいまい", "angry.png", "記憶があいまいになるほど食べたのですか……？"),
        ),
    ),
    Question(
        "ramen_count_today", "そのうちラーメンは何回でしたか？", "追加審議", "worry.png",
        "念のため確認します。そのうちラーメンは何回でしたか？",
        (
            Choice(0, "まだ食べていない", "thinking.png", "本日一杯目につき、情状酌量の余地があります。"),
            Choice(1, "1回", "thinking.png", "本日二杯目ですが、まだ情状酌量の余地はあります。"),
            Choice(2, "2回", "worry.png", "体調は大丈夫ですか……？ 少し水も飲んでくださいね。"),
            Choice(3, "3回以上", "worry.png", "これはもはやラーメン巡礼です。体調は本当に大丈夫ですか……？"),
        ),
        conditional=True,
    ),
    Question(
        "achievement", "今日なしとげたことは？", "QUESTION 2 / 7", "thinking.png",
        "次に、今日なしとげたことを教えてください。小さなことでも構いません。",
        (
            Choice(Achievement.WORKED, "仕事・勉強をした", "thumbup.png", "労働または学習の実績を確認しました。これは強い赦し材料です。"),
            Choice(Achievement.WENT_OUT, "外に出た", "thumbup.png", "外に出た。それだけで今日はもう一仕事です。"),
            Choice(Achievement.WALKED, "歩いた", "thumbup.png", "歩いた者には、麺へ向かう資格があります。"),
            Choice(Achievement.HOUSEWORK, "家事をした", "thumbup.png", "生活を維持した者には、温かい一杯が必要です。"),
            Choice(Achievement.WOKE_EARLY, "少し早く起きた", "thinking.png", "起床という第一の修行を終えていますね。"),
            Choice(Achievement.KINDNESS, "人にやさしくした", "thumbup.png", "人にやさしくしたなら、今日はあなたにもやさしくしてよいでしょう。"),
            Choice(Achievement.OSHI, "推しの配信を見守った", "thinking.png", "推しを見守る精神的労働を確認しました。"),
            Choice(Achievement.SHORTS, "ショート動画をずっと見た", "angry.png", "それは……少し懺悔が必要ですね。"),
            Choice(Achievement.NOTHING, "何もしていない", "thinking.png", "これから何かをするための原動力、ということにしましょう。"),
        ),
        css_class="choice-grid-wide",
    ),
    Question(
        "mood", "今日の心の状態は？", "QUESTION 3 / 7", "thinking.png",
        "では、今の心の状態を教えてください。",
        (
            Choice(Mood.TIRED, "疲れている", "worry.png", "疲れているのですね。温かいものが必要かもしれません。"),
            Choice(Mood.HUNGRY, "腹が減っている", "thumbup.png", "空腹は重要な証言です。これは食事の必要性があります。"),
            Choice(Mood.ANGRY, "むしゃくしゃしている", "worry.png", "むしゃくしゃしているのですね。まずは深呼吸しましょう。"),
            Choice(Mood.LONELY, "ちょっと寂しい", "worry.png", "それなら、せめて温かい丼にそばにいてもらいましょう。"),
            Choice(Mood.PROUD, "達成感がある", "thumbup.png", "達成感がある日のラーメンは、ほぼ祝杯です。"),
            Choice(Mood.EMPTY, "もう何も考えたくない", "worry.png", "何も考えたくない日もあります。券売機に判断を委ねましょう。"),
        ),
    ),
    Question(
        "after_plan", "今から何をする予定ですか？", "QUESTION 4 / 7", "thinking.png",
        "ラーメンのあと、何をする予定ですか？",
        (
            Choice(AfterPlan.WORK_MORE, "まだ作業する", "thumbup.png", "追加作業の燃料として、ラーメンが申請されています。"),
            Choice(AfterPlan.SLEEP, "寝るだけ", "worry.png", "寝るだけなら、本当に食べる必要がありますか……？"),
            Choice(AfterPlan.GO_HOME, "帰るだけ", "thinking.png", "帰路の一杯。古くからある赦しです。"),
            Choice(AfterPlan.MEET_PEOPLE, "人と会う", "thinking.png", "人と会う前のラーメンは、においも含めて審議します。"),
            Choice(AfterPlan.NOTHING, "特に何もない", "thinking.png", "予定がないなら、ラーメンを予定にできます。"),
            Choice(AfterPlan.MORE_SHORTS, "ショート動画を見る", "angry.png", "まだ見るのですか……？ それは懺悔が必要です。"),
        ),
    ),
    Question(
        "reason_not_to_eat", "ラーメンを食べない理由はありますか？", "QUESTION 5 / 7", "thinking.png",
        "ラーメンを食べない理由はありますか？",
        (
            Choice(ReasonNotToEat.NONE, "ない", "thumbup.png", "では、障害はありませんね。"),
            Choice(ReasonNotToEat.YES, "ある", "worry.png", "あるのですね……それでも食べたい、と。記録します。"),
            Choice(ReasonNotToEat.IGNORE, "ある気がするが、見ないことにした", "angry.png", "見ないことにした罪は軽くありません。"),
        ),
    ),
    Question(
        "ramen_type", "食べたいラーメンの系統は？", "QUESTION 6 / 7", "thinking.png",
        "食べたい系統を選んでください。ここでは全て赦しの対象です。",
        (
            Choice(RamenType.SHOYU, "醤油", "thumbup.png", "醤油、王道ですね。よい選択です。"),
            Choice(RamenType.MISO, "味噌", "thumbup.png", "味噌は疲労に寄り添います。よい選択です。"),
            Choice(RamenType.SHIO, "塩", "thumbup.png", "塩、澄んだ赦しですね。よい選択です。"),
            Choice(RamenType.TONKOTSU, "豚骨", "thumbup.png", "豚骨、濃厚な赦しを求めていますね。"),
            Choice(RamenType.IEKEI, "家系", "thumbup.png", "家系、覚悟のあるよい選択です。"),
            Choice(RamenType.JIRO, "二郎系", "thumbup.png", "二郎系、強い意志を感じます。よいでしょう。"),
            Choice(RamenType.TSUKEMEN, "つけ麺", "thumbup.png", "つけ麺、冷静さの残る選択です。"),
            Choice(
                RamenType.OTHER,
                "その他・おすすめしてほしい",
                "thumbup.png",
                "名付けきれない欲望も、赦しの対象です。",
                result_label="その他",
            ),
        ),
        css_class="ramen-choice-grid",
    ),
    Question(
        "forgiveness_style", "どんなふうに赦されたいですか？", "QUESTION 7 / 7", "thinking.png",
        "最後の審議です。どんなふうに赦されたいですか？",
        (
            Choice(ForgivenessStyle.PRAISE, "褒めてほしい", "thumbup.png", "あなたの今日を肯定する方向で審議します。"),
            Choice(ForgivenessStyle.SPOIL, "甘やかしてほしい", "thinking.png", "今日は甘やかされたい日なのですね。よいでしょう。"),
            Choice(ForgivenessStyle.STRICT, "厳しくてもいい", "angry.png", "厳しくてもいい、と言いましたね？"),
            Choice(ForgivenessStyle.PUSH, "雑に背中を押してほしい", "thumbup.png", "迷いを断ち切る赦しを希望ですね。"),
            Choice(ForgivenessStyle.ORACLE, "神のお告げっぽく", "thinking.png", "麺の啓示を求める者として記録します。"),
        ),
    ),
)

CHOICES_BY_NAME = {
    question.name: question.choices for question in DIAGNOSIS_QUESTIONS
}
VALID_CHOICE_VALUES = {
    name: frozenset(str(choice.value) for choice in choices)
    for name, choices in CHOICES_BY_NAME.items()
}
RAMEN_TYPE_LABELS = {
    str(choice.value): choice.result_label or choice.label
    for choice in CHOICES_BY_NAME["ramen_type"]
}
RAMEN_TYPES = tuple(RAMEN_TYPE_LABELS.values())
QUESTION_MESSAGES = {
    question.name: {
        "prompt": [question.prompt_image, question.prompt_text],
        "reactions": {
            str(choice.value): [choice.reaction_image, choice.reaction_text]
            for choice in question.choices
        },
    }
    for question in DIAGNOSIS_QUESTIONS
}
