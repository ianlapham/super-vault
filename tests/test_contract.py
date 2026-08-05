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
