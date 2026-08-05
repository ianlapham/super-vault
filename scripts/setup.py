#!/usr/bin/env python3
"""Install Super Vault's local dependencies and initialize one isolated corpus."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def setup_plan(vault_root: Path, *, start_qdrant: bool) -> list[str]:
    root = str(Path(vault_root).expanduser())
    commands = [
        "uv venv .venv",
        "uv pip install -r requirements.txt --python .venv/bin/python",
        f".venv/bin/python scripts/bootstrap.py --root {root}",
    ]
    if start_qdrant:
        commands.append("docker compose up -d qdrant")
    return commands


def run(command: str) -> None:
    print(f"→ {command}")
    subprocess.run(command, cwd=REPO_ROOT, shell=True, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Install Super Vault locally")
    parser.add_argument("--root", default="~/super-vault-data", help="Where source files and SQLite data will live")
    parser.add_argument("--no-qdrant", action="store_true", help="Skip starting the optional vector database")
    parser.add_argument("--dry-run", action="store_true", help="Print setup commands without running them")
    args = parser.parse_args()
    start_qdrant = not args.no_qdrant
    if start_qdrant and shutil.which("docker") is None:
        raise SystemExit("Docker is required for Qdrant. Install Docker Compose, or rerun with --no-qdrant.")
    env_path, example = REPO_ROOT / ".env", REPO_ROOT / ".env.example"
    if not env_path.exists():
        env_path.write_text(example.read_text())
        print(f"Created {env_path}; add only the connector keys you need.")
    commands = setup_plan(Path(args.root), start_qdrant=start_qdrant)
    if args.dry_run:
        print("\n".join(commands))
        return
    for command in commands:
        run(command)
    print(f"Super Vault is ready at {Path(args.root).expanduser()}")


if __name__ == "__main__":
    main()
