from pathlib import Path


def test_render_persistent_disk_matches_sqlite_path():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    blueprint = Path("render.yaml").read_text(encoding="utf-8")

    assert "ENV RAMEN_DB_PATH=/app/data/ramen.db" in dockerfile
    assert "plan: starter" in blueprint
    assert "mountPath: /app/data" in blueprint
    assert "value: /app/data/ramen.db" in blueprint
    assert "healthCheckPath: /health" in blueprint
