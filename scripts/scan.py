#!/usr/bin/env python3
"""Canonical source save path for @scan: full text in, durable Markdown out."""
from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


@dataclass(frozen=True)
class ScanResult:
    status: str
    path: Path


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = urlencode([(key, value) for key, value in parse_qsl(parts.query) if not key.lower().startswith("utm_")])
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:80] or "source"


def esc_yaml(value: str) -> str:
    return value.replace("\n", " ").replace('"', "\\\"")


def save_source(*, vault_root: Path, title: str, source_url: str, content: str, source_type: str, tags: list[str]) -> ScanResult:
    if len(content.strip()) < 50:
        raise ValueError("Refusing to save a short or empty source")
    vault_root = Path(vault_root)
    # @scan is safe to call directly: initialize registry/FTS before saving.
    try:
        from scripts.bootstrap import create_layout  # package import (tests/library)
    except ModuleNotFoundError:
        from bootstrap import create_layout  # direct `python scripts/scan.py`
    create_layout(vault_root)
    sources_dir = vault_root / "sources"
    canonical_url = canonicalize_url(source_url)
    digest = hashlib.sha256(content.encode()).hexdigest()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    db_path = vault_root / "vault.sqlite3"
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("SELECT path FROM sources WHERE canonical_url = ?", (canonical_url,)).fetchone()
        if row:
            return ScanResult("duplicate", Path(row[0]))
        filename = f"{datetime.now().date().isoformat()}-{slugify(title)}.md"
        path = sources_dir / filename
        suffix = 2
        while path.exists():
            path = sources_dir / f"{datetime.now().date().isoformat()}-{slugify(title)}-{suffix}.md"
            suffix += 1
        frontmatter = "\n".join([
            "---", f'title: "{esc_yaml(title)}"', f"source_url: {canonical_url}",
            f"canonical_url: {canonical_url}", f"source_type: {source_type}",
            f"captured_at: {now}", f"content_sha256: {digest}",
            f"tags: [{', '.join(tags)}]", "status: captured", "---", "",
        ])
        path.write_text(frontmatter + content.strip() + "\n")
        connection.execute("INSERT INTO sources VALUES (?, ?, ?, ?)", (canonical_url, str(path), digest, now))
        connection.execute("INSERT INTO source_fts VALUES (?, ?, ?)", (title, content, str(path)))
    return ScanResult("saved", path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Save a source to Super Vault")
    parser.add_argument("url")
    parser.add_argument("--title", required=True)
    parser.add_argument("--content", required=True, help="Full extracted source text")
    parser.add_argument("--type", default="article")
    parser.add_argument("--tags", default="")
    parser.add_argument("--root", default="~/super-vault-data")
    args = parser.parse_args()
    from bootstrap import create_layout
    root = create_layout(Path(args.root).expanduser())
    result = save_source(vault_root=root, title=args.title, source_url=args.url, content=args.content, source_type=args.type, tags=[tag.strip() for tag in args.tags.split(",") if tag.strip()])
    print(f"{result.status}: {result.path}")


if __name__ == "__main__":
    main()
