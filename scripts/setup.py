#!/usr/bin/env python3
"""Install Super Vault's local dependencies and initialize one isolated corpus."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def setup_plan(vault_root: Path, *, start_qdrant: bool, obsidian: bool = False) -> list[str]:
    root = str(Path(vault_root).expanduser())
    bootstrap = f".venv/bin/python scripts/bootstrap.py --root {root}"
    if obsidian:
        bootstrap += " --obsidian"
    commands = [
        "uv venv .venv",
        "uv pip install -r requirements.txt --python .venv/bin/python",
        bootstrap,
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
    parser.add_argument("--obsidian", action="store_true", help="Mark the vault for optional use in Obsidian")
    parser.add_argument("--dry-run", action="store_true", help="Print setup commands without running them")
    args = parser.parse_args()
    start_qdrant = not args.no_qdrant
    if start_qdrant:
        docker_ok = shutil.which("docker") is not None and subprocess.run(
            ["docker", "compose", "version"], capture_output=True
        ).returncode == 0
        if not docker_ok:
            raise SystemExit("Docker Compose is required for Qdrant. Install Docker Compose, or rerun with --no-qdrant.")
    commands = setup_plan(Path(args.root), start_qdrant=start_qdrant, obsidian=args.obsidian)
    if args.dry_run:
        print("\n".join(commands))
        return
    env_path, example = REPO_ROOT / ".env", REPO_ROOT / ".env.example"
    if not env_path.exists():
        env_path.write_text(example.read_text())
        print(f"Created {env_path}; add only the connector keys you need.")
    for command in commands:
        run(command)
    print(f"Super Vault is ready at {Path(args.root).expanduser()}")


if __name__ == "__main__":
    main()
