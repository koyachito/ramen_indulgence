import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "ramen.db"

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


def db_path() -> Path:
    return Path(os.getenv("RAMEN_DB_PATH", DEFAULT_DB))


def init_db() -> None:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnosis_counts (
                result_type TEXT PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ramen_counts (
                ramen_type TEXT PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ramen_time_counts (
                time_bucket TEXT NOT NULL,
                ramen_type TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (time_bucket, ramen_type)
            )
            """
        )
        conn.commit()


def record_result(result_type: str, ramen_type: str, current_hour: int) -> None:
    with closing(sqlite3.connect(db_path())) as conn:
        conn.execute(
            """
            INSERT INTO diagnosis_counts (result_type, count)
            VALUES (?, 1)
            ON CONFLICT(result_type) DO UPDATE SET count = count + 1
            """,
            (result_type,),
        )
        conn.execute(
            """
            INSERT INTO ramen_counts (ramen_type, count)
            VALUES (?, 1)
            ON CONFLICT(ramen_type) DO UPDATE SET count = count + 1
            """,
            (ramen_type,),
        )
        conn.execute(
            """
            INSERT INTO ramen_time_counts (time_bucket, ramen_type, count)
            VALUES (?, ?, 1)
            ON CONFLICT(time_bucket, ramen_type) DO UPDATE SET count = count + 1
            """,
            (time_bucket(current_hour), ramen_type),
        )
        conn.commit()


def get_stats(current_hour: int | None = None) -> dict[str, object]:
    hour = datetime.now().hour if current_hour is None else current_hour
    bucket = time_bucket(hour)
    with closing(sqlite3.connect(db_path())) as conn:
        result_rows = conn.execute(
            "SELECT result_type, count FROM diagnosis_counts ORDER BY count DESC"
        ).fetchall()
        ramen_rows = conn.execute(
            """
            SELECT ramen_type, count
            FROM ramen_time_counts
            WHERE time_bucket = ?
            ORDER BY count DESC
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
