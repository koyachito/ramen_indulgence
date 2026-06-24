import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import DiagnosisInput, DiagnosisResult

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "ramen.db"
JAPAN_TIMEZONE = ZoneInfo("Asia/Tokyo")

TIME_BUCKETS = {
    "morning": "朝（7〜11時）",
    "lunch": "昼（11〜14時）",
    "snack": "おやつ（14〜18時）",
    "dinner": "夕食（18〜20時）",
    "night": "夜・深夜（20〜7時）",
}


def time_bucket(hour: int) -> str:
    if 7 <= hour < 11:
        return "morning"
    if 11 <= hour < 14:
        return "lunch"
    if 14 <= hour < 18:
        return "snack"
    if 18 <= hour < 20:
        return "dinner"
    return "night"


def japan_now() -> datetime:
    return datetime.now(JAPAN_TIMEZONE)


def db_path() -> Path:
    return Path(os.getenv("RAMEN_DB_PATH", DEFAULT_DB))


def database_url() -> str | None:
    value = os.getenv("DATABASE_URL")
    if value and value.startswith(("postgresql://", "postgres://")):
        return value
    return None


def _connect():
    url = database_url()
    if url:
        import psycopg

        return psycopg.connect(url)
    return sqlite3.connect(db_path())


def _placeholder() -> str:
    return "%s" if database_url() else "?"


def init_db() -> None:
    if not database_url():
        path = db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
    id_column = (
        "INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
        if database_url()
        else "INTEGER PRIMARY KEY AUTOINCREMENT"
    )
    with closing(_connect()) as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS diagnosis_logs (
                id {id_column},
                created_at TEXT NOT NULL,
                current_hour INTEGER NOT NULL,
                time_bucket TEXT NOT NULL,
                ramen_type TEXT NOT NULL,
                meals INTEGER NOT NULL,
                ramen_count_today INTEGER NOT NULL,
                achievement TEXT NOT NULL,
                mood TEXT NOT NULL,
                reason_not_to_eat TEXT NOT NULL,
                forgiveness_style TEXT NOT NULL,
                after_plan TEXT NOT NULL,
                merit_score INTEGER NOT NULL,
                danger_score INTEGER NOT NULL,
                confession_score INTEGER NOT NULL,
                oni_flag INTEGER NOT NULL,
                result_type TEXT NOT NULL
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS standalone_judgments (
                id {id_column},
                created_at TEXT NOT NULL,
                result_type TEXT NOT NULL
            )
            """
        )
        conn.commit()


def record_result(data: DiagnosisInput, result: DiagnosisResult) -> None:
    scores = result.scores
    placeholders = ", ".join([_placeholder()] * 16)
    with closing(_connect()) as conn:
        conn.execute(
            f"""
            INSERT INTO diagnosis_logs (
                created_at, current_hour, time_bucket, ramen_type, meals,
                ramen_count_today, achievement, mood, reason_not_to_eat,
                forgiveness_style, after_plan, merit_score, danger_score,
                confession_score, oni_flag, result_type
            )
            VALUES ({placeholders})
            """,
            (
                japan_now().isoformat(),
                data.current_hour,
                time_bucket(data.current_hour),
                result.ramen_label,
                data.meals,
                data.ramen_count_today,
                data.achievement,
                data.mood,
                data.reason_not_to_eat,
                data.forgiveness_style,
                data.after_plan,
                scores.merit_score,
                scores.danger_score,
                scores.confession_score,
                scores.oni_flag,
                result.result_type,
            ),
        )
        conn.commit()


def record_judgment(result_type: str) -> None:
    placeholder = _placeholder()
    with closing(_connect()) as conn:
        conn.execute(
            f"INSERT INTO standalone_judgments (created_at, result_type) VALUES ({placeholder}, {placeholder})",
            (japan_now().isoformat(), result_type),
        )
        conn.commit()


def get_stats(current_hour: int | None = None) -> dict[str, object]:
    hour = japan_now().hour if current_hour is None else current_hour
    bucket = time_bucket(hour)
    with closing(_connect()) as conn:
        result_rows = conn.execute(
            """
            SELECT result_type, COUNT(*)
            FROM (
                SELECT result_type FROM diagnosis_logs
                UNION ALL
                SELECT result_type FROM standalone_judgments
            )
            GROUP BY result_type
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()
        ramen_rows = conn.execute(
            f"""
            SELECT ramen_type, COUNT(*)
            FROM diagnosis_logs
            WHERE time_bucket = {_placeholder()}
            GROUP BY ramen_type
            ORDER BY COUNT(*) DESC
            """,
            (bucket,),
        ).fetchall()
    results = dict(result_rows)
    ramen = dict(ramen_rows)
    return {
        "total": sum(results.values()),
        "results": results,
        "ramen": ramen,
        "ramen_total": sum(ramen.values()),
        "time_bucket": bucket,
        "time_label": TIME_BUCKETS[bucket],
    }
