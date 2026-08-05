# Install Super Vault with an Agent

This document is for an agent that must install Super Vault on a new machine. It lists the required services, files, API keys, commands, and checks. Do not skip a check and do not say setup is complete until the verification section passes.

## Copy this prompt into Hermes

```text
Install Super Vault from https://github.com/ianlapham/super-vault on this machine.

Work in a new directory. Follow INSTALL_WITH_AGENT.md exactly. Use ~/super-vault-data as the data directory unless I give another path. Before changing anything, report which prerequisites are missing. Ask me only for API keys or login steps that cannot be completed by the machine.

Install every required dependency, create the data directory and SQLite database, start Qdrant with Docker Compose, create a local .env from .env.example, and install the Hermes skill. Configure only the source connectors for which I provide credentials. Do not put API keys, cookies, or source data in Git.

Then run every Verification command. Perform one real @scan on a public web page, confirm a Markdown file and SQLite FTS record exist, confirm Qdrant is healthy, and report the exact local paths and enabled connectors. Do not claim that RSS, Substack, X bookmarks, LightRAG, or scheduled Vault Pulse jobs are enabled unless you configured and tested each one.
```

## 1. Required machine prerequisites

The installer needs these local tools:

- **Git** — clone the repository.
- **Python 3.11 or newer** — run the scripts.
- **uv** — create the Python environment and install packages.
- **Docker Compose** — run [Qdrant](https://qdrant.tech/), the vector database.
- **Hermes Agent** — recognize `@scan`, run scheduled jobs, and answer retrieval questions.

Check them before installing:

```bash
git --version
python3 --version
uv --version
docker compose version
hermes --version
```

If `docker compose version` fails, install Docker Desktop (macOS/Windows) or Docker Engine plus the Compose plugin (Linux). Do not substitute a hosted vector database without the owner’s approval.

## 2. Clone the repository and install Python packages

```bash
git clone https://github.com/ianlapham/super-vault.git
cd super-vault
uv venv .venv
uv pip install -r requirements.txt --python .venv/bin/python
cp .env.example .env
```

`.env` is local-only. It is ignored by Git. Do not paste its contents into chat, a commit, or a log.

## 3. Create the local vault and start the vector database

Choose a directory outside the Git checkout for private sources and generated data.

```bash
.venv/bin/python scripts/bootstrap.py --root ~/super-vault-data
docker compose up -d qdrant
```

This creates:

```text
~/super-vault-data/
  sources/       # Markdown source files
  raw/           # optional originals such as PDFs/HTML
  notes/         # owner-authored notes
  concepts/      # synthesized concept files
  digests/       # Vault Pulse output
  state/         # connector/checkpoint state
  db/            # future service databases
  vault.sqlite3  # source registry + SQLite FTS5 index
```

Qdrant stores its own vector data in `./.data/qdrant/` inside the repository directory by default. Set `SUPER_VAULT_DATA_DIR` in `.env` if it should live elsewhere.

## 3a. Open the same folder as an Obsidian vault

The directory passed to `--root` is the Markdown corpus and is already Obsidian-compatible. It contains an `OBSIDIAN.md` marker plus the source, note, concept, and digest folders.

1. Install and open Obsidian.
2. Choose **Open folder as vault**.
3. Select `~/super-vault-data` (or the custom path passed to `--root`).
4. Read, edit, tag, and link the Markdown files in Obsidian. Super Vault and Obsidian use the same files.

There is no second “Obsidian sync” process inside Super Vault. For multi-device access, configure **one** sync transport in Obsidian: Obsidian Sync, iCloud/Dropbox, or a private Git workflow. Do not point a public Git repository at a vault containing private sources.

## 4. Add only the API keys needed for enabled connectors

Add keys to `.env` or the host’s secret manager. A key is required only for the matching feature.

| Feature | Environment variable | Purpose |
| --- | --- | --- |
| Vector embeddings and LightRAG | `OPENAI_API_KEY` | Create embeddings and extract graph entities/relationships. |
| YouTube transcripts | `SUPADATA_API_KEY` | Preferred Supadata transcript API. |
| RSS ranking or optional summaries | `ANTHROPIC_API_KEY` | Score/filter items when an Anthropic model is configured. |
| X bookmarks | authenticated `xurl` session | Read the owner’s own saved X bookmarks. |
| Substack | authenticated browser cookies | Read posts from the owner’s subscriptions. |

No API key is needed for Markdown, SQLite FTS5, local Qdrant, generic web extraction, or basic `@scan` of a public web page.

## 5. Install the Hermes skill

The skill tells Hermes what `@scan` means and how to use the local scripts.

```bash
hermes skills tap add ianlapham/super-vault
hermes skills install super-vault
```

Start a fresh Hermes session after installing the skill. Tool/skill lists are loaded when a session begins.

## 6. Configure source connectors

Enable one connector at a time and test it before enabling the next.

1. **Web pages:** no credential. `@scan https://example.com/article` fetches HTML, removes non-article content, and stores Markdown.
2. **YouTube:** add `SUPADATA_API_KEY`. `@scan https://youtube.com/watch?v=VIDEO_ID` requests a transcript. If Supadata is not configured, use `youtube-transcript-api` as the fallback.
3. **RSS:** add feed URLs to a local feed list. Poll with `feedparser`; save the feed item URL and ID in SQLite so already-seen items are skipped.
4. **Substack:** add browser session cookies to a local ignored secret file. Test one subscribed publication before enabling a scheduled poll.
5. **X bookmarks:** authenticate `xurl` as the owner. Test `xurl whoami`, then ingest one bookmark through the canonical scan pipeline.
6. **Vault Pulse:** create a Hermes cron only after at least one source connector works. The job should query sources captured since its last run and send a small digest with source links.

## 7. Indexing and retrieval configuration

Run these layers in order:

1. **Markdown:** save the full normalized source text and YAML frontmatter.
2. **SQLite + FTS5:** insert title, text, and Markdown path for exact search.
3. **Qdrant:** split the text into approximately 200-word chunks, create an embedding for each chunk, and upsert each chunk with source URL/path metadata.
4. **LightRAG:** insert the same source text to extract entities and relationships. Keep the LightRAG working directory inside the private vault data directory.
5. **Reranking:** use `sentence-transformers` with `cross-encoder/ms-marco-MiniLM-L-6-v2` to rerank keyword/vector candidates before giving them to Hermes.

The current repository contains the corpus, SQLite, web/YouTube scanner, Qdrant service definition, and graph viewer. Treat Qdrant indexing, LightRAG ingestion, RSS/Substack/X polling, and cron creation as explicit setup modules: configure and test them before marking them enabled.

## 8. Visualization setup

The graph viewer is local and static. It should receive only sanitized graph metadata:

```json
{
  "nodes": [{"label": "Qdrant", "type": "tool", "community": 1}],
  "edges": []
}
```

Build it:

```bash
.venv/bin/python scripts/visualize.py \
  --input ~/super-vault-data/graph.json \
  --output ~/super-vault-data/super-vault-graph.html
```

Do not include document text, URLs, API keys, embeddings, or file paths in `graph.json` when the HTML could be shared.

## 9. Verification

Run all checks:

```bash
# Python code and repository tests
.venv/bin/python -m pytest tests -q

# Qdrant health; expect HTTP 200 and JSON output
curl -fsS http://localhost:6333/collections

# Create and scan a real public source
@scan https://example.com

# Confirm the scan wrote a Markdown file and SQLite database
find ~/super-vault-data/sources -name '*.md' -print
sqlite3 ~/super-vault-data/vault.sqlite3 'SELECT canonical_url, path FROM sources;'

# Build and open a local graph file after graph data exists
ls -lh ~/super-vault-data/super-vault-graph.html
```

A completed install reports: vault root, Qdrant health result, enabled API-backed connectors, one saved `@scan` source, test output, and any modules intentionally not enabled.
