#!/usr/bin/env python3
"""
Render data/contributions.json (produced by fetch_contributions.py) as a
modern glass-style GitHub contribution heatmap SVG: a grid of rounded,
colored BOXES in the classic 53-week x 7-day calendar, inside a rounded
terminal card with a gradient background, a violet->cyan gradient border,
and a soft glass sheen. Each box pops in with a scale-bounce +
brightness-flash once (diagonal stagger), then freezes -- no looping
"glow". Includes a Less->More legend and a two-line stats footer with
small icon glyphs, plus prefers-reduced-motion support.

Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.
"""
import datetime
import json
import os

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# GitHub-ish green ramp: empty -> brightest. Level 0 is tinted to match the
# new indigo card background instead of GitHub's neutral gray.
PALETTE = ["#1b2036", "#0e4429", "#00743a", "#26a641", "#39d353", "#6bf5a8"]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 30
TOP_LABEL_H = 20
TITLEBAR_H = 32
RADIUS = 16

# modern palette: deep indigo glass card, violet -> cyan accent gradient
BG_TOP = "#141327"
BG_BOTTOM = "#0a0b14"
ACCENT_1 = "#8b5cf6"   # violet
ACCENT_2 = "#22d3ee"   # cyan
MUTED = "#8b93a7"
TEXT = "#e7e9f3"
GREEN = "#39d353"
GOLD = "#f2c94c"

# reveal timing (one-shot)
COL_T = 0.018   # per-column delay contribution (left -> right sweep)
ROW_T = 0.045   # per-row delay contribution (top -> bottom cascade)
CELL_DUR = 0.55

# monospace advance width as a fraction of font-size -- lets right-aligned
# text be positioned by character count instead of text-anchor="end", which
# some SVG renderers mishandle once a <tspan> with different styling sits
# inside the string.
MONO_ADVANCE = 0.6


def level_for(count):
    if count == 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    if count <= 50:
        return 4
    return 5


def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7  # sunday=0
    grid = []
    col = [None] * lead_pad
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        while len(col) < 7:
            col.append(None)
        grid.append(col)
    return grid


def right_text(x_end, y, s, size, color, weight="400"):
    """Right-align plain text at x_end by measured char width, sidestepping
    text-anchor="end" (which some renderers mishandle with mixed tspans)."""
    w = len(s) * size * MONO_ADVANCE
    return (f'<text x="{x_end - w:.1f}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}">{s}</text>')


def flame_icon(x, y, color):
    return (f'<path transform="translate({x},{y}) scale(0.62)" fill="{color}" '
            f'd="M8 0c1 2.5-2.2 3.6-2.2 6.4C5.8 8.9 7.6 10 8.4 10c-0.8-1.6 0.2-2.7 0.8-3.6 '
            f'0.5 1 0.3 1.9 0.9 2.6 1.6-1 2.3-2.9 1.6-4.8 1.8 1 2.9 3 2.5 5.1-0.5 2.7-3 4.7-5.9 4.7 '
            f'-3.3 0-6-2.6-6-5.8C2.3 4.9 5.6 2.9 8 0z"/>')


def star_icon(x, y, color):
    pts = "5,0 6.5,3.4 10,3.8 7.3,6.1 8.1,9.5 5,7.6 1.9,9.5 2.7,6.1 0,3.8 3.5,3.4"
    return f'<polygon transform="translate({x},{y}) scale(0.62)" fill="{color}" points="{pts}"/>'


def render(data):
    days = data["days"]
    grid = build_grid(days)
    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP

    month_labels = []
    seen_months = set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen_months and date.day <= 7:
                seen_months.add(key)
                month_labels.append((ci, date.strftime("%b")))
            break

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    stats_h = 92
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + stats_h + PAD

    css = f"""
@keyframes pop {{
  0%   {{ opacity: 0; transform: scale(0.2); }}
  60%  {{ opacity: 1; transform: scale(1.12); }}
  100% {{ opacity: 1; transform: scale(1); }}
}}
@keyframes flash {{
  0%   {{ filter: brightness(2.6); }}
  45%  {{ filter: brightness(2.6); }}
  100% {{ filter: brightness(1); }}
}}
@keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
.c {{
  opacity: 0; transform-box: fill-box; transform-origin: center;
  animation: pop {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both;
}}
.g {{ animation: pop {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both, flash {CELL_DUR + 0.15:.2f}s ease-out both; }}
.footer {{ opacity: 0; animation: fade 0.6s ease-out {0.9:.2f}s both; }}
@media (prefers-reduced-motion: reduce) {{
  .c, .footer {{ opacity: 1 !important; animation: none !important; }}
}}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs>',
        f'<linearGradient id="hbg" x1="0" y1="0" x2="0.3" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/></linearGradient>',
        f'<linearGradient id="border" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{ACCENT_1}"/><stop offset="1" stop-color="{ACCENT_2}"/></linearGradient>',
        f'<linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#ffffff" stop-opacity="0.07"/>'
        f'<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>',
        '</defs>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="{RADIUS}" fill="url(#hbg)"/>',
        f'<rect width="{canvas_w}" height="{canvas_h * 0.4:.0f}" rx="{RADIUS}" fill="url(#sheen)"/>',
        f'<rect x="0.75" y="0.75" width="{canvas_w-1.5}" height="{canvas_h-1.5}" rx="{RADIUS}" '
        f'fill="none" stroke="url(#border)" stroke-width="1.25" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="url(#border)" stroke-opacity="0.25"/>',
    ]
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
                 f'letter-spacing="0.3" text-anchor="middle">yahya@github: ~/contributions --graph</text>')

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    for ci, label in month_labels:
        x = grid_left + ci * STEP
        parts.append(f'<text x="{x}" y="{TITLEBAR_H + 15}" fill="{MUTED}" font-size="10">{label}</text>')

    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + wi * STEP + CELL * 0.78
        parts.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="9">{wname}</text>')

    # the boxes -- pop + flash reveal, diagonal stagger (once, freeze)
    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy = grid_top + ri * STEP
            delay = ci * COL_T + ri * ROW_T
            plural = "s" if count != 1 else ""
            cls = "c g" if lvl >= 1 else "c"
            parts.append(
                f'<rect class="{cls}" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="3" '
                f'fill="{PALETTE[lvl]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{date_s}: {count} contribution{plural}</title></rect>'
            )

    # legend: Less [][][][][] More (bottom-right of the grid)
    leg_y = grid_top + art_h + 6
    leg_w_est = len(PALETTE) * CELL + 70
    leg_x = canvas_w - PAD - leg_w_est
    parts.append(right_text(leg_x + 30, leg_y + CELL * 0.8, "Less", 10, MUTED))
    lx = leg_x + 36
    for lvl, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL-1}" height="{CELL-1}" rx="2.5" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">More</text>')

    sep_y = leg_y + CELL + 14
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="url(#border)" stroke-opacity="0.2"/>')

    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    total = data["total_contributions"]
    best = data["best_day"]
    rng = data["range"]

    ly = sep_y + 26
    parts.append(f'<g class="footer">')
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="14" fill="{GREEN}">'
                 f'<tspan font-weight="700">{total:,}</tspan>'
                 f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>')
    parts.append(right_text(canvas_w - PAD, ly, f'{rng["start"]} → {rng["end"]}', 12, MUTED))
    ly += 26
    parts.append(flame_icon(PAD, ly - 10, ACCENT_2))
    parts.append(f'<text x="{PAD + 16}" y="{ly}" font-size="13" fill="{MUTED}">streak '
                 f'<tspan fill="{ACCENT_2}" font-weight="700">{cs}d</tspan>'
                 f'<tspan fill="{MUTED}"> current &#183; </tspan>'
                 f'<tspan fill="{ACCENT_1}" font-weight="700">{ls}d</tspan>'
                 f'<tspan fill="{MUTED}"> best</tspan></text>')
    best_str = f'best day {best["count"]} on {best["date"]}'
    parts.append(right_text(canvas_w - PAD - 16, ly, best_str, 12, MUTED))
    parts.append(star_icon(canvas_w - PAD - 12, ly - 9, GOLD))
    parts.append('</g>')

    parts.append("</svg>")
    return "".join(parts)


def main():
    data = json.load(open(IN_PATH))
    svg = render(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
