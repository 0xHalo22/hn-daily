# hn-daily

a daily snapshot of the [hacker news](https://news.ycombinator.com) front page,
committed to git.

the git history of this repo is a time capsule. want to know what HN was
talking about on a given day? run:

```bash
git log --oneline snapshots/
cat snapshots/2026-04-11.md
```

or just browse [`snapshots/`](./snapshots) in the web UI.

## how it works

a [github actions workflow](.github/workflows/scrape.yml) runs once a day,
fetches the top 30 stories via the [public firebase api](https://github.com/HackerNews/API),
writes a dated markdown file to `snapshots/`, and commits if anything changed.

no scraping, no auth, no babysitting.

## files

- [`latest.md`](./latest.md) — always the most recent snapshot
- [`snapshots/YYYY-MM-DD.md`](./snapshots) — the full archive

## credits

story titles, URLs, and metadata are the property of their respective
authors and hacker news. this repo exists only to preserve a publicly
accessible time series.
