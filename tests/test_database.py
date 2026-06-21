import os
from pathlib import Path

from app import database


def test_stats_track_verdicts_and_ramen_types(tmp_path: Path):
    original = os.environ.get("RAMEN_DB_PATH")
    os.environ["RAMEN_DB_PATH"] = str(tmp_path / "stats.db")
    try:
        database.init_db()
        database.record_result("conditional", "味噌", 23)
        database.record_result("conditional", "味噌", 22)
        database.record_result("full", "醤油", 12)
        database.record_judgment("sleep")
        stats = database.get_stats(23)
    finally:
        if original is None:
            os.environ.pop("RAMEN_DB_PATH", None)
        else:
            os.environ["RAMEN_DB_PATH"] = original

    assert stats["total"] == 4
    assert stats["results"]["conditional"] == 2
    assert stats["results"]["sleep"] == 1
    assert stats["ramen"]["味噌"] == 2
    assert stats["ramen_total"] == 2
    assert stats["time_bucket"] == "night"
