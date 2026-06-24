#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "ramen.db"
DEFAULT_BACKUP_DIRECTORY = PROJECT_ROOT / "backups"


class BackupError(RuntimeError):
    pass


def database_path() -> Path:
    return Path(os.getenv("RAMEN_DB_PATH", DEFAULT_DATABASE)).expanduser()


def next_backup_path(backup_directory: Path, timestamp: datetime) -> Path:
    stem = timestamp.astimezone(timezone.utc).strftime("ramen-%Y%m%d-%H%M%S")
    candidate = backup_directory / f"{stem}.db"
    suffix = 1
    while candidate.exists():
        candidate = backup_directory / f"{stem}-{suffix}.db"
        suffix += 1
    return candidate


def create_backup(
    source: Path,
    backup_directory: Path,
    timestamp: datetime | None = None,
) -> Path:
    source = source.expanduser().resolve()
    backup_directory = backup_directory.expanduser().resolve()
    if not source.is_file():
        raise BackupError(f"バックアップ元のSQLite DBが見つかりません: {source}")

    backup_directory.mkdir(parents=True, exist_ok=True)
    destination = next_backup_path(
        backup_directory,
        timestamp or datetime.now(timezone.utc),
    )

    try:
        with sqlite3.connect(source) as source_connection:
            with sqlite3.connect(destination) as destination_connection:
                source_connection.backup(destination_connection)
    except sqlite3.Error as error:
        destination.unlink(missing_ok=True)
        raise BackupError(f"SQLiteバックアップに失敗しました: {error}") from error

    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ラーメン免罪符のSQLite DBを安全にバックアップします。"
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=database_path(),
        help="バックアップ元DB。既定値はRAMEN_DB_PATHまたはdata/ramen.db。",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIRECTORY,
        help="バックアップ先ディレクトリ。既定値はbackups/。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        destination = create_backup(args.source, args.backup_dir)
    except BackupError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"SQLiteバックアップを作成しました: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
