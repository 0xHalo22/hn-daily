#!/usr/bin/env python3
"""
hn-daily: snapshot the hacker news front page once a day.

uses the public firebase api (no auth, no rate limit concerns at 1 req/day).
writes a dated markdown file to snapshots/ and overwrites latest.md.
the git history of this repo becomes a time capsule of what the internet
cared about on any given day.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
HN_THREAD_URL = "https://news.ycombinator.com/item?id={id}"

# be a polite citizen — tell HN who we are
USER_AGENT = "hn-daily-bot (+https://github.com/0xHalo22/hn-daily)"

TOP_N = 30
ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "snapshots"
LATEST_FILE = ROOT / "latest.md"


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fmt_item(rank: int, item: dict) -> str:
    title = item.get("title", "(no title)").strip()
    url = item.get("url") or HN_THREAD_URL.format(id=item["id"])
    score = item.get("score", 0)
    comments = item.get("descendants", 0)
    by = item.get("by", "anon")
    thread = HN_THREAD_URL.format(id=item["id"])
    return (
        f"{rank}. **[{title}]({url})** — "
        f"{score} points, {comments} comments, by {by} "
        f"([thread]({thread}))"
    )


def render(items: list[dict], today: str) -> str:
    lines = [f"# HN top {len(items)} — {today}", ""]
    for i, item in enumerate(items, start=1):
        if item is None:
            continue
        lines.append(fmt_item(i, item))
    lines.append("")
    lines.append(f"_snapshot taken at {datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    lines.append("")
    return "\n".join(lines)


def run_git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, cwd=ROOT)


def main() -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[hn-daily] fetching top stories for {today}")

    top_ids = fetch_json(TOP_STORIES_URL)[:TOP_N]
    items = []
    for i, sid in enumerate(top_ids, start=1):
        try:
            item = fetch_json(ITEM_URL.format(id=sid))
            items.append(item)
            print(f"  [{i}/{len(top_ids)}] {item.get('title', '?')[:60]}")
        except Exception as e:
            print(f"  [{i}/{len(top_ids)}] FAILED: {e}", file=sys.stderr)

    body = render(items, today)
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    snapshot_path = SNAPSHOT_DIR / f"{today}.md"
    snapshot_path.write_text(body, encoding="utf-8")
    LATEST_FILE.write_text(body, encoding="utf-8")
    print(f"[hn-daily] wrote {snapshot_path} and latest.md")

    # commit only if something actually changed
    if os.environ.get("GITHUB_ACTIONS"):
        run_git("add", str(snapshot_path), str(LATEST_FILE))
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
        )
        if not status.stdout.strip():
            print("[hn-daily] no changes to commit")
            return 0
        top_title = items[0].get("title", "?") if items else "?"
        msg = f"snapshot {today}: {top_title[:72]}"
        run_git("commit", "-m", msg)
        print(f"[hn-daily] committed: {msg}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
