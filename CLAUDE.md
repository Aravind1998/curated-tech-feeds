# Curated Tech Feeds - Claude Code Guide

## Common Commands
- **Refresh Feeds & Rebuild Dashboard:** `python3 pull_feeds.py`
- **Run Pipeline Directly:** `python3 pipeline/feed_reader.py`
- **Test Locally:** Open `index.html` in browser

## Project Structure
- `config/curated_tech_feeds.json`: Feed source definitions (name, feed URL, site URL, category, badge color).
- `pipeline/feed_reader.py`: Concurrent RSS/Atom parsing and static HTML compiler.
- `pull_feeds.py`: CLI wrapper.
- `index.html`: Compiled static dashboard with embedded data and vanilla ES6 search/filtering.
- `feeds.opml`: Standard OPML export for RSS readers.
- `.github/workflows/update-feeds.yml`: Scheduled 6-hour GitHub Actions workflow.
- `docs/` and `data/`: Cached feed data.

## Hosting & Deployment
- Hosted on GitHub Pages: `https://aravind1998.github.io/curated-tech-feeds/`
- Branch: `main`, path `/`
- Static HTML5, zero cloudflare, zero build tools required.
