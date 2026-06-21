import os
from pathlib import Path

from app import database
from app.diagnosis import diagnose
from app.models import DiagnosisInput


def test_stats_track_diagnosis_logs(tmp_path: Path):
    original = os.environ.get("RAMEN_DB_PATH")
    os.environ["RAMEN_DB_PATH"] = str(tmp_path / "stats.db")
    try:
        database.init_db()
        data = DiagnosisInput(
            current_hour=23,
            current_month=6,
            current_day=22,
            meals=2,
            ramen_count_today=0,
            achievement="worked",
            mood="tired",
            after_plan="go_home",
            reason_not_to_eat="none",
            ramen_type="miso",
            forgiveness_style="praise",
        )
        result = diagnose(data)
        database.record_result(data, result)
        database.record_result(data, result)
        database.record_judgment("sleep")
        database.record_judgment("banzai")
        stats = database.get_stats(23)
    finally:
        if original is None:
            os.environ.pop("RAMEN_DB_PATH", None)
        else:
            os.environ["RAMEN_DB_PATH"] = original

    assert stats["total"] == 4
    assert stats["results"]["forgiven"] == 2
    assert stats["results"]["sleep"] == 1
    assert stats["results"]["banzai"] == 1
    assert stats["ramen"]["味噌"] == 2
    assert stats["ramen_total"] == 2
    assert stats["time_bucket"] == "night"
