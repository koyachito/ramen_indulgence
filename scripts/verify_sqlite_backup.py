#!/usr/bin/env python3
import argparse
from pathlib import Path
import sqlite3
import sys

REQUIRED_TABLES = ("diagnosis_logs", "standalone_judgments")


class VerificationError(RuntimeError):
    pass


def verify_backup(backup_path: Path) -> dict[str, int]:
    backup_path = backup_path.expanduser().resolve()
    if not backup_path.is_file():
        raise VerificationError(f"検証対象のバックアップDBが見つかりません: {backup_path}")

    uri = f"{backup_path.as_uri()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            integrity = connection.execute("PRAGMA quick_check").fetchone()
            if not integrity or integrity[0] != "ok":
                detail = integrity[0] if integrity else "結果なし"
                raise VerificationError(f"SQLite整合性チェックに失敗しました: {detail}")

            counts = {}
            for table in REQUIRED_TABLES:
                try:
                    counts[table] = connection.execute(
                        f"SELECT COUNT(*) FROM {table}"
                    ).fetchone()[0]
                except sqlite3.Error as error:
                    raise VerificationError(
                        f"必須テーブルを読み取れません: {table}: {error}"
                    ) from error
    except sqlite3.Error as error:
        raise VerificationError(f"バックアップDBを開けません: {error}") from error

    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SQLiteバックアップの整合性と必須テーブルを検証します。"
    )
    parser.add_argument("backup_path", type=Path, help="検証するバックアップDB")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        counts = verify_backup(args.backup_path)
    except VerificationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"SQLiteバックアップを検証しました: {args.backup_path.resolve()}")
    for table, count in counts.items():
        print(f"- {table}: {count} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
