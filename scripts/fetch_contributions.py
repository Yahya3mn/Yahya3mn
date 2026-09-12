#!/usr/bin/env python3
"""Scrape the public contribution calendar HTML fragment (no token needed)
and write data/contributions.json with raw days + derived stats."""

import json
import os
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GITHUB_PROFILE_USER", "Yahya3mn")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")

COUNT_RE = re.compile(r"^(No|\d+)\s+contributions?\s+on\s+(.+?)\.?$")


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tooltips = {}
    for tip in soup.select("tool-tip"):
        target = tip.get("for")
        if target:
            tooltips[target] = tip.get_text(strip=True)

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        level = int(td.get("data-level", 0))
        count = 0
        tip_text = tooltips.get(td.get("id"))
        if tip_text:
            m = COUNT_RE.match(tip_text)
            if m:
                count = 0 if m.group(1) == "No" else int(m.group(1))
        days.append({"date": date, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)

    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = {}
    for d in days:
        month = d["date"][:7]
        monthly[month] = monthly.get(month, 0) + d["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly": monthly,
    }


def main():
    days = fetch_days()
    if not days:
        print("no contribution days parsed, aborting", file=sys.stderr)
        sys.exit(1)

    stats = compute_stats(days)
    out = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)

    print(f"wrote {len(days)} days, {stats['total']} total contributions -> {OUT_PATH}")


if __name__ == "__main__":
    main()
