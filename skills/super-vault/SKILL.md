---
name: super-vault
description: Use when @scan or Vault questions need durable source capture.
version: 0.1.0
author: 4D Studios
license: MIT
metadata:
  hermes:
    tags: [vault, rag, knowledge-graph, ingestion]
    related_skills: []
---

# Super Vault 🧠

A portable personal-source system for Hermes. It captures full source material, preserves it locally, and makes it searchable by keywords, meaning, and relationships.

## When to Use

- `@scan <URL>` or `@scan <pasted text>`
- “What have I saved about X?”
- “What connects X and Y?”
- “Build my vault graph” or “show new Vault Pulse items”

## @scan Contract

For every `@scan` request:

1. Fetch or accept the **full** original source text. Never substitute a summary.
2. Run the canonical saver: `python3 scripts/scan.py URL --title TITLE --content TEXT --root VAULT_ROOT`.
3. Report saved/duplicate status, title, source type, and file path.
4. Queue optional index projections: FTS5 is immediate; Qdrant and LightRAG run after capture and must never risk the source file.

The command works through any Hermes chat surface because this skill teaches the agent the trigger; it is not a platform-specific slash-command implementation.

## Queries

- Exact retrieval: SQLite FTS5
- Semantic retrieval: Qdrant vectors + reranking
- Connected questions: LightRAG hybrid graph query

## Visualization

Export only entity labels, types, communities, and indexed edges. Never put source text, URLs, filesystem paths, tokens, or embeddings into a shareable visualization. Build a local explorer with `python3 scripts/visualize.py --input graph.json --output super-vault-graph.html`.

## Verification Checklist

- [ ] Source Markdown exists with canonical URL and hash
- [ ] Duplicate URL returns `duplicate`, not a second file
- [ ] FTS5 can be rebuilt from corpus files
- [ ] Graph export is metadata-only
