# Vector Database and Background Jobs

This document explains where Super Vault stores semantic vectors, how to choose local or hosted Qdrant, and which work currently happens automatically.

## Current implementation

Today, `scripts/setup.py` can create the Markdown/SQLite vault and start a **Local Qdrant** container. `scripts/scan.py` immediately saves normalized Markdown and inserts a SQLite FTS5 record.

Vector embedding/upsert, LightRAG graph insertion, RSS/Substack/X polling, and Vault Pulse cron creation are **not automatically** performed by the current starter code. They are documented integration modules. An agent must configure, test, and schedule them before reporting them as enabled.

## Local Qdrant

Use local Qdrant when the agent and the vault run on the same machine or private server. Source vectors remain on that machine.

```bash
# Start the local vector database
docker compose up -d qdrant

# Check that it is running
curl -fsS http://localhost:6333/collections
```

Use this configuration:

```dotenv
QDRANT_URL=http://localhost:6333
# QDRANT_API_KEY is empty for the default local Docker service
QDRANT_API_KEY=
```

The Qdrant Docker volume defaults to `./.data/qdrant`. Set `SUPER_VAULT_DATA_DIR=/absolute/private/path` in `.env` to move that volume. Back up this volume only if you need to preserve the vector index; the Markdown corpus remains the canonical content store.

## Hosted Qdrant / Qdrant Cloud

Use [Qdrant Cloud](https://cloud.qdrant.io/) when the agent runs in a serverless environment, multiple workers need the same index, or the host cannot run Docker.

1. Create a Qdrant Cloud cluster in the region appropriate for the owner’s data.
2. Create an API key with access only to that cluster.
3. Put the cluster HTTPS URL and key in the local secret file:

```dotenv
QDRANT_URL=https://YOUR-CLUSTER.REGION.cloud.qdrant.io:6333
QDRANT_API_KEY=YOUR_QDRANT_CLOUD_KEY
```

4. Do **not** run `docker compose up -d qdrant` for that deployment.
5. Verify the credentials without printing the key:

```bash
curl -fsS -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections"
```

A hosted Qdrant collection stores text embeddings and metadata. It does not replace the owner’s Markdown corpus. Keep Markdown, SQLite, raw files, and secrets in the private vault directory.

## Embeddings and collections

For each saved Markdown source:

1. Read the full normalized text.
2. Split it into approximately 200-word chunks, retaining source URL, title, file path, and chunk number as metadata.
3. Call an embedding provider, normally OpenAI using `OPENAI_API_KEY`.
4. Upsert the embedding vector and metadata into a Qdrant collection such as `super_vault`.
5. On a query, embed the query, search Qdrant, then rerank candidate chunks with `sentence-transformers` before Hermes answers.

Use a consistent embedding model and vector size for one collection. If the embedding model changes, create a new collection and reindex every Markdown source rather than mixing vectors from different models.

## Background jobs

Background jobs are optional. They run without a person sending `@scan` and must be installed only after the corresponding connector works manually.

| Job | Trigger | What it does | Required proof before enabling |
| --- | --- | --- | --- |
| RSS poll | Hermes cron, e.g. every 6 hours | Fetch feeds, skip seen IDs, scan new URLs | One feed item saved and deduplicated |
| Substack poll | Hermes cron | Fetch subscribed posts through the owner session | One permitted post saved |
| X bookmark poll | Hermes cron | Read authenticated bookmarks and scan unseen posts | `xurl whoami` plus one saved bookmark |
| Index retry | Hermes cron or worker queue | Retry Qdrant/LightRAG work after a failed API call | A saved source appears in the intended index |
| Vault Pulse | Hermes cron | Find sources captured since the previous pulse and send links | Digest includes only real newly captured sources |

A safe order is: run `@scan` manually → verify Markdown and SQLite → verify vectors → verify graph → add one background job → observe one successful run. Never enable all polling jobs first and assume the output is correct.

## Verification

Report the following after setup:

- Vector mode: `local` or `hosted`.
- Qdrant URL only, never the API key.
- Qdrant health/collections response.
- Embedding model and collection name.
- Which Background jobs exist, their schedules, and their most recent successful run.
- Which modules remain intentionally disabled.
