from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from scripts.backup_sqlite import BackupError, create_backup, database_path
from scripts.verify_sqlite_backup import VerificationError, verify_backup


def create_source_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE diagnosis_logs (id INTEGER PRIMARY KEY, result_type TEXT)"
        )
        connection.execute(
            "CREATE TABLE standalone_judgments (id INTEGER PRIMARY KEY, result_type TEXT)"
        )
        connection.execute(
            "INSERT INTO diagnosis_logs (result_type) VALUES ('forgiven')"
        )
        connection.execute(
            "INSERT INTO standalone_judgments (result_type) VALUES ('banzai')"
        )
        connection.commit()


def test_create_and_verify_sqlite_backup(tmp_path: Path):
    source = tmp_path / "ramen.db"
    backup_directory = tmp_path / "backups"
    create_source_database(source)

    backup = create_backup(
        source,
        backup_directory,
        datetime(2026, 6, 25, 7, 30, tzinfo=timezone.utc),
    )

    assert backup == backup_directory / "ramen-20260625-073000.db"
    assert backup.is_file()
    assert verify_backup(backup) == {
        "diagnosis_logs": 1,
        "standalone_judgments": 1,
    }


def test_backup_uses_unique_name_when_timestamp_collides(tmp_path: Path):
    source = tmp_path / "ramen.db"
    backup_directory = tmp_path / "backups"
    timestamp = datetime(2026, 6, 25, 7, 30, tzinfo=timezone.utc)
    create_source_database(source)

    first = create_backup(source, backup_directory, timestamp)
    second = create_backup(source, backup_directory, timestamp)

    assert first.name == "ramen-20260625-073000.db"
    assert second.name == "ramen-20260625-073000-1.db"


def test_backup_fails_clearly_when_source_does_not_exist(tmp_path: Path):
    with pytest.raises(BackupError, match="SQLite DBが見つかりません"):
        create_backup(tmp_path / "missing.db", tmp_path / "backups")


def test_database_path_uses_environment_variable(monkeypatch, tmp_path: Path):
    source = tmp_path / "configured.db"
    monkeypatch.setenv("RAMEN_DB_PATH", str(source))

    assert database_path() == source


def test_verify_fails_when_required_table_is_missing(tmp_path: Path):
    backup = tmp_path / "incomplete.db"
    with sqlite3.connect(backup) as connection:
        connection.execute("CREATE TABLE diagnosis_logs (id INTEGER PRIMARY KEY)")

    with pytest.raises(VerificationError, match="standalone_judgments"):
        verify_backup(backup)


def test_backup_and_verify_commands(tmp_path: Path):
    source = tmp_path / "ramen.db"
    backup_directory = tmp_path / "backups"
    create_source_database(source)

    backup_result = subprocess.run(
        [
            sys.executable,
            "scripts/backup_sqlite.py",
            "--source",
            str(source),
            "--backup-dir",
            str(backup_directory),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    backups = list(backup_directory.glob("*.db"))

    assert backup_result.returncode == 0
    assert "SQLiteバックアップを作成しました" in backup_result.stdout
    assert len(backups) == 1

    verify_result = subprocess.run(
        [sys.executable, "scripts/verify_sqlite_backup.py", str(backups[0])],
        check=False,
        capture_output=True,
        text=True,
    )

    assert verify_result.returncode == 0
    assert "diagnosis_logs: 1 rows" in verify_result.stdout
    assert "standalone_judgments: 1 rows" in verify_result.stdout
