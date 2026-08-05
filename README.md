# Super Vault 🧠

> Your internet rabbit holes, newsletters, bookmarks, videos, and notes—turned into a searchable second brain.

**Super Vault** is a portable, Hermes-native personal knowledge system. It reads the sources you choose, keeps the full original material in a local vault, finds what matters later, and sends a small **Vault Pulse** when new things arrive.

It is a repo and Hermes skill, **not a hosted database and not a copy of anyone else’s reading history**. Install it, connect your own sources, and your vault stays yours.

## Super Vault 🧠

Think of it as a quiet research assistant running in the background:

- 🌐 **Articles & URLs** — save a page before it disappears into your tabs
- 🎥 **YouTube** — transcript via [Supadata](https://supadata.ai/) (preferred) or [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) fallback
- 📰 **RSS / Atom** — follow blogs and publications with [`feedparser`](https://github.com/kurtmckee/feedparser)
- ✉️ **Substack** — optional authenticated newsletter intake
- 🔖 **X bookmarks** — optional intake through [`xurl`](https://github.com/xdevplatform/xurl)
- 📝 **Pasted notes, PDFs, GitHub READMEs** — anything you want to keep and ask about later

Every item becomes a full Markdown source with clear metadata. The vault can then answer *“what did I save about agent memory?”*, connect people to ideas across sources, or deliver a daily/weekly **Vault Pulse** of genuinely new entries.

## Usage ✏️

Super Vault is a [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill. Once installed, it runs wherever you already talk to Hermes: CLI, Discord, Telegram, and more.

```text
@scan https://example.com/great-article
@scan https://youtube.com/watch?v=...
@scan Here is a note I never want to lose...
```

`@scan` is the front door: Hermes fetches or accepts the **full** source, deduplicates it, saves readable Markdown, and indexes it for later. Background jobs can check feeds, newsletters, and bookmarks; a Vault Pulse sends a short recap rather than another firehose.

The Hermes integration is optional. The same folders, Python scripts, SQLite database, Qdrant index, and graph tooling can be adapted to another agent or app.

### Install shape

```bash
# From a GitHub skill tap after this project is published
hermes skills tap add OWNER/super-vault
hermes skills install super-vault

# Create a separate local corpus and start the vector database
python3 scripts/bootstrap.py --root ~/super-vault-data
docker compose up -d
```

Copy `.env.example` to `.env` and only add keys for the connectors you enable. Run `python3 -m pytest tests -q` to verify the local core.

## Stack 🛠️

### Ingestion

**Job:** track chosen sources, get the real content, normalize it once.

- **Canonical pipeline:** Python `scripts/scan.py` saves one source format for every connector. A URL is canonicalized and deduplicated before it writes.
- **Web:** [`requests`](https://requests.readthedocs.io/) + [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) extract readable page text.
- **YouTube:** [Supadata Transcript API](https://docs.supadata.ai/) is the preferred transcript integration; [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) is a fallback.
- **RSS:** [`feedparser`](https://github.com/kurtmckee/feedparser) parses RSS/Atom feeds; SQLite remembers what was already seen.
- **Substack:** an opt-in authenticated API connector fetches subscribed posts; never commit its cookies.
- **Bookmarks:** [`xurl`](https://github.com/xdevplatform/xurl) can pull a user’s authenticated X bookmarks; it is optional.

### Storage

**Job:** keep durable source material first; treat every database as a rebuildable convenience.

- **Source of truth:** full **Markdown + YAML frontmatter** on your own disk. Each source keeps title, canonical URL, type, capture time, tags, and SHA-256 content hash.
- **Exact search + state:** [SQLite](https://sqlite.org/) and **FTS5** store source registry, ingest state, and fast keyword/full-text search.
- **Semantic encoding:** sources are split into small overlapping chunks (~200 words), embedded with an embedding model, and stored in [Qdrant](https://qdrant.tech/). This finds passages by meaning rather than exact wording.
- **Safety:** raw text lives separately from generated summaries and graphs. Git may back up the code and, only if you choose, a private corpus. `.env`, cookies, vector data, and personal sources stay ignored.

### Retrieval

**Job:** give an agent the right evidence—not just a plausible answer.

1. **FTS5** catches exact names, quotes, and titles.
2. **Qdrant** finds semantically similar source chunks.
3. [`sentence-transformers`](https://www.sbert.net/) reranks the candidate passages using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
4. Hermes receives the best passages with source links and can cite the underlying Markdown.

This is RAG with receipts: a short answer should always be traceable back to the saved source.

### Knowledge Graph

**Job:** surface relationships that ordinary search misses.

[LightRAG](https://github.com/HKUDS/LightRAG) extracts entities and relations from sources—people, companies, tools, claims, and ideas—then combines graph traversal with vector retrieval.

```text
"OpenAI" ── builds ──> "embeddings" ── powers ──> "Qdrant"
       └── discussed in ──> "a saved newsletter"
```

Ask *“what connects agent memory, Qdrant, and this founder?”* and LightRAG can follow those chains across documents. For a visual map, [NetworkX](https://networkx.org/) reads the graph, Louvain community detection groups related regions, and a zero-dependency HTML5 Canvas explorer renders entities, clusters, and search locally.

**Visualization:** the included zero-dependency HTML5 Canvas explorer lets you search the metadata-only entity graph locally.

**Privacy rule:** the visualization payload contains only entity labels, types, community IDs, and edges—never original source text, source URLs, filesystem paths, tokens, or embeddings.

## What this repo never ships

- Your saved sources, PDFs, notes, or private graph
- API keys, cookies, X sessions, or `.env`
- Qdrant/SQLite production data or logs

Super Vault ships the machine. You bring the memories.

## License

MIT
