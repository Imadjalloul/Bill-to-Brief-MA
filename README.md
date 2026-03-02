# Bill-to-Brief-MA

Automated data ingestion starter for a Morocco-focused legislative tracker.

## What this adds

- Scheduled sync script that can pull from RSS and JSON sources.
- Change detection to only publish new/updated items.
- Persisted state for "keep it updated" behavior.
- Static web UI (`web/`) that renders bills and recent updates.
- GitHub Pages deployment workflow for the web app.
- Basic tests using local fixtures.

## Quick start (data sync)

```bash
python3 automation/sync_legislation.py \
  --sources config/sources.json \
  --output data/bills.json \
  --state data/state.json \
  --updates data/updates.json
```

The script writes:

- `data/bills.json`: full normalized catalog
- `data/state.json`: source-level and item-level sync metadata
- `data/updates.json`: only newly discovered/changed items

## Keep it updated automatically

Use a scheduler:

- GitHub Actions cron (`.github/workflows/sync.yml`)
- or server cron (`*/30 * * * *`)

Each run:

1. Fetches every configured source.
2. Normalizes records into common fields (`id`, `title`, `summary`, `url`, `published_at`, `source`).
3. Computes a hash of each record to detect content changes.
4. Updates state and emits only changed items.

## Deploy as a web app on GitHub

This repo now includes a static web app and a deployment workflow.

1. Push to `main`.
2. In GitHub repo settings, enable **Pages** and set source to **GitHub Actions**.
3. The workflow `.github/workflows/deploy-web.yml` will publish the `web/` app with live JSON from `data/`.

Web files:

- `web/index.html`
- `web/app.js`
- `web/styles.css`

## Source config format

`config/sources.json`:

```json
[
  {
    "name": "official-rss",
    "type": "rss",
    "url": "https://example.gov.ma/feed.xml"
  },
  {
    "name": "open-data-api",
    "type": "json",
    "url": "https://example.gov.ma/api/bills",
    "items_path": "data.items",
    "field_map": {
      "id": "id",
      "title": "title",
      "summary": "description",
      "url": "url",
      "published_at": "published_at"
    }
  }
]
```

## Notes

- Start with manual curation + one reliable official feed.
- Expand with more sources once normalization is stable.
- Add anti-blocking etiquette (respect robots, rate-limit, cache) before scaling.
