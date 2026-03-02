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

## How to host this app on GitHub (GitHub Pages)

### 1) Push repository to GitHub

```bash
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
git push -u origin main
```

### 2) Enable GitHub Pages

1. Open your repo on GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, choose **Source: GitHub Actions**.

### 3) Confirm workflows are enabled

- `.github/workflows/deploy-web.yml` deploys the static UI.
- `.github/workflows/sync.yml` refreshes `data/*.json` every 30 minutes.

### 4) Set Actions permissions (important)

In **Settings → Actions → General**:

- Set **Workflow permissions** to **Read and write permissions**.
- Enable **Allow GitHub Actions to create and approve pull requests** (optional but useful).

### 5) Visit your live URL

After the deploy workflow succeeds, your app is at:

- `https://<YOUR_USERNAME>.github.io/<YOUR_REPO>/`

> If you renamed your default branch from `main`, update workflow branch filters accordingly.

## Quick troubleshooting

### Page loads but shows `0` records / `No records found`

- Your `config/sources.json` still has placeholder `example.org` URLs.
- Replace them with real Moroccan legislative RSS/API sources, then run sync once locally or trigger workflow manually.

### Sync workflow fails on push

- Check Actions permissions are set to **Read and write**.
- Ensure branch protection rules allow workflow bot pushes, or change workflow to open PRs instead.

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
