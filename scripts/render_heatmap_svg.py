#!/usr/bin/env python3
"""Render data/contributions.json as an animated GitHub-style contribution
heatmap SVG: a 53-week x 7-day grid of rounded boxes that slide in
diagonally once, then a Less->More legend and a stats footer."""

import json
import os
from datetime import date, datetime, timedelta

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT_PAD = 28
TOP_PAD = 20
BOTTOM_PAD = 46
RIGHT_PAD = 12

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def load_data():
    with open(DATA_PATH) as f:
        return json.load(f)


def build_weeks(days):
    """Bucket days into GitHub-style weeks (columns), Sunday-start."""
    by_date = {d["date"]: d for d in days}
    if not days:
        return []

    last = datetime.strptime(days[-1]["date"], "%Y-%m-%d").date()
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()

    end = last
    start = end - timedelta(weeks=53)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # snap back to Sunday
    if start < first:
        start = first - timedelta(days=(first.weekday() + 1) % 7)

    weeks = []
    cur = start
    week = []
    while cur <= end:
        entry = by_date.get(cur.isoformat(), {"date": cur.isoformat(), "level": 0, "count": 0})
        week.append(entry)
        if len(week) == 7:
            weeks.append(week)
            week = []
        cur += timedelta(days=1)
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    return weeks


def month_labels(weeks):
    labels = []
    seen_month = None
    for wi, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            d = datetime.strptime(day["date"], "%Y-%m-%d").date()
            if d.day <= 7 and d.month != seen_month:
                labels.append((wi, MONTH_NAMES[d.month - 1]))
                seen_month = d.month
            break
    return labels


def escape(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render(data):
    weeks = build_weeks(data["days"])
    n_weeks = len(weeks)
    stats = data["stats"]

    grid_w = n_weeks * STEP - GAP
    grid_h = 7 * STEP - GAP
    width = LEFT_PAD + grid_w + RIGHT_PAD
    height = TOP_PAD + grid_h + BOTTOM_PAD

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )
    parts.append(
        """
  <style>
    .bg { fill: #0d1117; }
    .cell {
      stroke: rgba(27,31,35,0.06);
      stroke-width: 1;
      opacity: 0;
      transform-box: fill-box;
      transform-origin: center;
      animation: reveal 0.5s ease-out forwards;
    }
    .dow, .month { fill: #8b949e; font-size: 9px; }
    .footer { fill: #c9d1d9; font-size: 12px; }
    .legend-label { fill: #8b949e; font-size: 9px; }
    @keyframes reveal {
      from { opacity: 0; transform: translate(-6px, -6px) scale(0.4); }
      to   { opacity: 1; transform: translate(0, 0) scale(1); }
    }
  </style>
"""
    )
    parts.append(f'<rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="6"/>')

    for label_col, name in month_labels(weeks):
        x = LEFT_PAD + label_col * STEP
        parts.append(f'<text class="month" x="{x}" y="{TOP_PAD - 7}">{name}</text>')

    for dow, name in DOW_LABELS.items():
        y = TOP_PAD + dow * STEP + CELL - 2
        parts.append(f'<text class="dow" x="0" y="{y}">{name}</text>')

    max_delay_slot = n_weeks + 7
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if day is None:
                continue
            level = min(max(day.get("level", 0), 0), len(PALETTE) - 1)
            color = PALETTE[level]
            x = LEFT_PAD + wi * STEP
            y = TOP_PAD + di * STEP
            delay = (wi + di) * (0.9 / max_delay_slot)
            title = f'{day["count"]} contribution{"s" if day["count"] != 1 else ""} on {day["date"]}'
            parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{color}" style="animation-delay:{delay:.3f}s">'
                f"<title>{escape(title)}</title></rect>"
            )

    legend_y = TOP_PAD + grid_h + 20
    parts.append(f'<text class="legend-label" x="{LEFT_PAD}" y="{legend_y + 8}">Less</text>')
    lx = LEFT_PAD + 32
    for i, color in enumerate(PALETTE):
        parts.append(
            f'<rect x="{lx + i * STEP}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>'
        )
    parts.append(
        f'<text class="legend-label" x="{lx + len(PALETTE) * STEP + 6}" y="{legend_y + 8}">More</text>'
    )

    best = stats.get("best_day") or {}
    footer = (
        f'{stats["total"]:,} contributions in the last year  ·  '
        f'current streak {stats["current_streak"]}d  ·  longest streak {stats["longest_streak"]}d  ·  '
        f'best day {best.get("count", 0)} ({best.get("date", "n/a")})'
    )
    parts.append(f'<text class="footer" x="{LEFT_PAD}" y="{height - 10}">{escape(footer)}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    data = load_data()
    svg = render(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
