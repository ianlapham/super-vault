from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_readme_explains_the_product_and_stack():
    text = (ROOT / "README.md").read_text()
    for heading in [
        "# Super Vault 🧠",
        "## Usage ✏️",
        "## Stack 🛠️",
        "### Ingestion",
        "### Storage",
        "### Retrieval",
        "### Knowledge Graph",
        "@scan",
        "Vault Pulse",
        "Visualization",
    ]:
        assert heading in text


def test_skill_declares_scan_trigger_and_installer():
    text = (ROOT / "skills" / "super-vault" / "SKILL.md").read_text()
    assert "@scan" in text
    assert "scripts/scan.py" in text
    assert text.startswith("---\n")


def test_installer_creates_isolated_vault_layout(tmp_path):
    from scripts.bootstrap import create_layout

    create_layout(tmp_path)
    for relative in [
        "sources", "raw", "notes", "concepts", "digests", "state", "db", "exports", "vault.sqlite3"
    ]:
        assert (tmp_path / relative).exists()


def test_vector_and_background_guide_states_current_boundaries():
    text = (ROOT / "docs" / "VECTOR_AND_BACKGROUND.md").read_text()
    for required in [
        "Local Qdrant", "Qdrant Cloud", "QDRANT_URL", "QDRANT_API_KEY",
        "Current implementation", "not automatically", "Background jobs",
    ]:
        assert required in text


def test_bootstrap_creates_an_obsidian_compatible_vault_marker(tmp_path):
    from scripts.bootstrap import create_layout

    create_layout(tmp_path)
    assert (tmp_path / "OBSIDIAN.md").exists()


def test_agent_install_guide_covers_required_services_and_verification():
    text = (ROOT / "INSTALL_WITH_AGENT.md").read_text()
    for required in [
        "Docker Compose", "Qdrant", "OPENAI_API_KEY", "SUPADATA_API_KEY",
        "uv pip install", "docker compose up -d qdrant", "@scan", "Verification",
    ]:
        assert required in text


def test_setup_plan_installs_dependencies_initializes_corpus_and_starts_qdrant(tmp_path):
    from scripts.setup import setup_plan

    commands = setup_plan(tmp_path / "vault", start_qdrant=True)
    assert any("uv venv" in command for command in commands)
    assert any("uv pip install -r requirements.txt" in command for command in commands)
    assert any("bootstrap.py" in command for command in commands)
    assert any("docker compose up -d qdrant" in command for command in commands)


def test_setup_dry_run_does_not_create_env_file(tmp_path, monkeypatch):
    import sys
    import scripts.setup as setup

    monkeypatch.setattr(setup, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["setup.py", "--root", str(tmp_path / "vault"), "--no-qdrant", "--dry-run"])
    (tmp_path / ".env.example").write_text("OPENAI_API_KEY=\n")
    setup.main()
    assert not (tmp_path / ".env").exists()


def test_web_html_extraction_keeps_article_text():
    from scripts.scan import html_to_text

    text = html_to_text("<html><title>Ignored</title><body><nav>Menu</nav><article><h1>Real title</h1><p>Useful source text.</p></article></body></html>")
    assert "Real title" in text
    assert "Useful source text." in text


def test_visualization_exports_metadata_only(tmp_path):
    from scripts.visualize import build_html

    output = tmp_path / "graph.html"
    build_html(
        nodes=[{"label": "Qdrant", "type": "tool", "community": 1}],
        edges=[],
        output=output,
    )
    text = output.read_text()
    assert "Qdrant" in text
    assert "https://private.example" not in text
    assert "CanvasRenderingContext2D" in text


def test_scan_writes_full_markdown_and_is_idempotent(tmp_path):
    from scripts.scan import save_source

    first = save_source(
        vault_root=tmp_path,
        title="A Source",
        source_url="https://example.com/article?utm_source=test",
        content="This is the original source text. " * 20,
        source_type="article",
        tags=["demo"],
    )
    second = save_source(
        vault_root=tmp_path,
        title="A Source",
        source_url="https://example.com/article",
        content="This is the original source text. " * 20,
        source_type="article",
        tags=["demo"],
    )
    text = first.path.read_text()
    assert first.status == "saved"
    assert second.status == "duplicate"
    assert "source_url: https://example.com/article" in text
    assert "This is the original source text." in text
