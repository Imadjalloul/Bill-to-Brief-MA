# Bill-to-Brief MA 🇲🇦

[![Try it live](https://img.shields.io/badge/Try%20it-live-0ea5e9?style=for-the-badge)](https://<YOUR_USERNAME>.github.io/<YOUR_REPO>/)

A lightweight Morocco-focused legislative tracker that:

- collects bill/project updates from online sources,
- normalizes them into one format,
- keeps a change log of newly updated records,
- and publishes a static web app on GitHub Pages.

---

## Project structure

```text
.
├── automation/
│   └── sync_legislation.py      # fetch + normalize + diff detection
├── config/
│   └── sources.json             # data source configuration
├── data/
│   ├── bills.json               # full current dataset
│   ├── updates.json             # only new/changed records
│   └── state.json               # fingerprints + sync state
├── web/
│   ├── index.html               # static UI
│   ├── app.js                   # fetch/render logic
│   └── styles.css               # styling
├── tests/
│   └── test_sync_legislation.py
└── .github/workflows/
    ├── sync.yml                 # scheduled data refresh
    └── deploy-web.yml           # GitHub Pages deployment
```

---

## Quick start

### 1) Run sync locally

```bash
python3 automation/sync_legislation.py \
  --sources config/sources.json \
  --output data/bills.json \
  --state data/state.json \
  --updates data/updates.json
```

### 2) Run tests

```bash
python3 -m unittest -v tests/test_sync_legislation.py
```

### 3) Preview web app locally

```bash
python3 -m http.server 4173
```

Open: `http://localhost:4173/web/index.html`

---

## Configure real sources

Edit `config/sources.json` and replace placeholders with real Moroccan sources.

Example formats:

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

> If the UI shows 0 records, it usually means sources are still placeholders or fetch failed.

---

## Deploy on GitHub Pages

1. Push repo to GitHub (`main` branch).
2. In **Settings → Pages**, set **Source = GitHub Actions**.
3. In **Settings → Actions → General**, set **Workflow permissions = Read and write**.
4. Trigger workflows:
   - `Sync Legislative Sources` (fills `data/*.json`)
   - `Deploy Bill-to-Brief Web App` (publishes site)

Live URL format:

```text
https://<YOUR_USERNAME>.github.io/<YOUR_REPO>/
```

After your first successful deploy, replace the placeholder link at the top of this README with your real URL so the **Try it live** button works.

---

## Notes

- Start with a small list of trusted official sources.
- Keep summaries short and useful for end users.
- Respect robots.txt and source terms when scraping.
