# Super Vault 🧠

Super Vault is a self-hosted source-ingestion and retrieval system for [Hermes Agent](https://github.com/NousResearch/hermes-agent). It collects content from sources you choose, stores the original text and metadata locally, indexes that content for search, and lets Hermes answer questions using the stored sources.

## Install with an agent

For a machine-readable, step-by-step install procedure—including prerequisite checks, Qdrant, API keys, source connectors, indexing, visualization, and verification—use [INSTALL_WITH_AGENT.md](./INSTALL_WITH_AGENT.md). It includes a copy-paste prompt that tells a Hermes agent exactly what to install and what evidence it must return before claiming success.

For local versus hosted Qdrant, embedding collections, and background-job setup, read [VECTOR_AND_BACKGROUND.md](./docs/VECTOR_AND_BACKGROUND.md). It explicitly separates the starter’s current automatic behavior from modules that an agent must configure and test.

## Super Vault 🧠

Use Super Vault when you want an agent to keep track of information you read or save over time.

It can store:

- 🌐 **Web pages and articles** — fetch the page, extract readable text, and save it as Markdown.
- 🎥 **YouTube videos** — fetch a transcript with [Supadata](https://supadata.ai/) or [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api).
- 📰 **RSS and Atom feeds** — monitor publications with [`feedparser`](https://github.com/kurtmckee/feedparser) and ingest new articles.
- ✉️ **Substack posts** — optionally fetch posts from subscribed publications using an authenticated session.
- 🔖 **X bookmarks** — optionally read a user’s saved X posts through [`xurl`](https://github.com/xdevplatform/xurl).
- 📝 **Pasted notes, PDFs, and GitHub READMEs** — save material that does not come from a tracked feed.

For each source, the system stores the full source text, URL, title, source type, tags, capture time, and a content hash. It can then search that material by keywords, by semantic similarity, or by relationships between extracted entities.

A **Vault Pulse** is a scheduled digest of new sources added since the last pulse. It is intended to show what entered the vault, not to replace the original source material.

## Usage ✏️

Super Vault installs as a Hermes skill. The skill recognizes `@scan` in any Hermes surface that supports chat messages, including CLI, Discord, and Telegram.

```text
@scan https://example.com/article
@scan https://youtube.com/watch?v=VIDEO_ID
@scan A pasted note or research excerpt
```

When you use `@scan`, Hermes should:

1. Fetch the source text or accept the pasted text.
2. Convert it to clean text when needed.
3. Normalize the source URL and check whether it was already saved.
4. Write a Markdown file with YAML metadata.
5. Add the content to full-text, vector, and graph indexes.
6. Return the saved or duplicate status and the source location.

The repository includes the local storage bootstrapper, canonical Markdown saver, web/YouTube scanner, Hermes skill definition, Qdrant Docker service, and local graph viewer. RSS, Substack, X bookmark polling, scheduled pulses, and full Qdrant/LightRAG indexing are connector modules to enable as the project expands.

### Fast local install

The full agent-oriented procedure is in [INSTALL_WITH_AGENT.md](./INSTALL_WITH_AGENT.md). For a normal local install:

```bash
git clone https://github.com/ianlapham/super-vault.git
cd super-vault
python3 scripts/setup.py --root ~/super-vault-data

# Install the Hermes instruction layer, then start a fresh Hermes session.
hermes skills tap add ianlapham/super-vault
hermes skills install super-vault
```

`setup.py` creates a Python environment, installs `requirements.txt`, copies `.env.example` to local `.env`, creates the source/SQLite layout, and starts Qdrant. It stops with an error if Docker is missing; use `--no-qdrant` only when intentionally setting up without vector search.

### Obsidian vault

The Super Vault data directory is already an **Obsidian-compatible Markdown vault**. Set `--root` to a new or existing Obsidian vault folder, then open that same folder in Obsidian. Super Vault writes Markdown directly into it; no separate export or file-sync script is required.

For multi-device sync, choose and configure one external transport in Obsidian: Obsidian Sync, iCloud/Dropbox, or a private Git workflow. The installer does not automate an Obsidian account login or publish personal source files to Git.

## Stack 🛠️

### Ingestion

**Job: track data sources, fetch their contents, and convert each source into clean text that can be stored and indexed.**

| Source type | How it is fetched and parsed | Technology |
| --- | --- | --- |
| Web page | Download HTML, remove navigation/scripts/styles, keep article/main text | [requests](https://requests.readthedocs.io/), [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) |
| YouTube | Request a transcript, then join transcript segments into text | [Supadata Transcript API](https://docs.supadata.ai/), [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) fallback |
| RSS / Atom | Poll feed XML, compare article URLs against saved state, ingest new URLs | [`feedparser`](https://github.com/kurtmckee/feedparser), SQLite |
| Substack | Use an authenticated Substack session to request post HTML, then convert HTML to text | Substack API, Python `urllib`, Beautiful Soup |
| X bookmarks | Read authenticated bookmarks and post text, then send each item through the same scan pipeline | [`xurl`](https://github.com/xdevplatform/xurl) |
| Pasted text | Save the supplied text without fetching a URL | Hermes `@scan` trigger, Python |

All source types should use the same scan pipeline. This gives every source the same metadata format, deduplication rule, storage layout, and indexes.

### Storage

**Job: smartly store the contents and information for any data source.**

1. **Markdown files store the source content.** Each source is written as a separate Markdown file. The body contains the full extracted text. YAML frontmatter contains title, original URL, canonical URL, source type, capture time, tags, and SHA-256 content hash.
2. **SQLite stores source records and full-text search.** SQLite records which URLs were scanned and prevents duplicate saves. Its [FTS5](https://www.sqlite.org/fts5.html) extension indexes titles and source text for fast keyword search.
3. **Qdrant stores vector embeddings.** The system splits each source into small text chunks (typically about 200 words), creates an embedding for each chunk, and stores that embedding plus source metadata in [Qdrant](https://qdrant.tech/). This supports meaning-based search, such as finding documents about “agent memory” even when they do not use those exact words.
4. **Raw and derived data stay separate.** Original source text, Markdown, database records, vector embeddings, summaries, and graph data are separate files or stores. If an index is deleted, it can be recreated from the Markdown corpus.

### Retrieval

**Job: find the source text most relevant to a user question and give Hermes enough context to answer with citations.**

1. **Keyword search:** SQLite FTS5 finds exact titles, names, phrases, and terms.
2. **Semantic search:** Qdrant finds text chunks with similar embedding vectors to the query.
3. **Reranking:** [`sentence-transformers`](https://www.sbert.net/) scores the candidate chunks again with `cross-encoder/ms-marco-MiniLM-L-6-v2` and keeps the most relevant results.
4. **Answer generation:** Hermes receives the ranked source passages and their URLs/files, then generates an answer that points back to those sources.

Example: a search for “how are AI agents evaluated?” can return a saved article about benchmarks, a newsletter about eval harnesses, and a note that uses the phrase “testing agent behavior,” even if it does not use the exact query wording.

### Knowledge Graph

**Job: extract entities and relationships from source text so the system can answer connection questions across multiple documents.**

[LightRAG](https://github.com/HKUDS/LightRAG) reads saved text and extracts entities such as people, companies, products, concepts, and claims. It also extracts relationships between them.

```text
Saved newsletter
  └─ mentions → OpenAI
       └─ provides → embedding model
            └─ indexes text in → Qdrant
```

A graph query can answer questions such as: “What sources connect OpenAI, embeddings, and Qdrant?” LightRAG combines relationship traversal with vector retrieval, so it can use both graph connections and relevant text passages.

### Visualization

For visualization, [NetworkX](https://networkx.org/) reads the entity graph, Louvain community detection groups related entities, and the included HTML5 Canvas viewer displays nodes, clusters, and search. The visualization export contains entity labels, types, community IDs, and edges only. It must not include source text, source URLs, filesystem paths, API keys, or embeddings.

## Data and security boundaries

This repository contains code and configuration templates only. It does not contain:

- Saved sources, notes, PDFs, raw documents, or personal graph data
- API keys, browser cookies, X sessions, or `.env` files
- Local SQLite databases, Qdrant data, LightRAG storage, or logs

## License

MIT
