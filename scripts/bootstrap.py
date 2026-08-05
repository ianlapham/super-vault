#!/usr/bin/env python3
"""Create an isolated, rebuildable Super Vault corpus."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DIRECTORIES = ("sources", "raw", "notes", "concepts", "digests", "state", "db", "exports")


def create_layout(vault_root: Path) -> Path:
    vault_root = Path(vault_root).expanduser().resolve()
    for directory in DIRECTORIES:
        (vault_root / directory).mkdir(parents=True, exist_ok=True)
    db_path = vault_root / "vault.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS sources (canonical_url TEXT PRIMARY KEY, path TEXT NOT NULL, content_sha256 TEXT NOT NULL, captured_at TEXT NOT NULL)"
        )
        connection.execute("CREATE VIRTUAL TABLE IF NOT EXISTS source_fts USING fts5(title, content, path UNINDEXED)")
    return vault_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize an isolated Super Vault")
    parser.add_argument("--root", default="~/super-vault-data", help="Vault data directory")
    args = parser.parse_args()
    print(create_layout(Path(args.root)))


if __name__ == "__main__":
    main()
