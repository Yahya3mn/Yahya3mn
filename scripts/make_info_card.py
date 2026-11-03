"""
Render a neofetch-style info card that sits beside the ASCII portrait: a
user@host header, colored key/value rows, and the classic row of color blocks.

The top block is hand-written profile info; the bottom block is live, read
from data/contributions.json, so the daily workflow re-runs this right after
fetch_contributions.py and the numbers never go stale.

Each line fades and slides in on a short stagger, as if neofetch were printing
next to the portrait, then a prompt cursor blinks under it. STATIC=1 emits the
final frame with no animation, for local previews.

The README places the portrait and this card as two adjacent <img>s (no
table: its borders and padding push past the 780px column). So the card's
height is matched to yahya-ascii.svg at the README's display widths, and the
gap between the two is transparent margin on the card's left edge.
"""
import datetime
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
PORTRAIT_PATH = os.path.join(HERE, "..", "yahya-ascii.svg")
OUT_PATH = os.path.join(HERE, "..", "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

# keep these in sync with the <img width> values in README.md (they sum to 780)
PORTRAIT_DISPLAY_W = 380
CARD_DISPLAY_W = 400
GAP_DISPLAY_W = 12     # part of CARD_DISPLAY_W: the gap after the portrait

W = 500
PAD = 26
TITLEBAR_H = 30
RADIUS = 16
FONT = 14.5
LINE_H = 23.5
KEY_W = 92             # x offset of values from the key column

BG = "#0a0b14"
BG2 = "#141327"
ACCENT_1 = "#8b5cf6"   # violet
ACCENT_2 = "#22d3ee"   # cyan
KEY = "#a78bfa"
MUTED = "#8b93a7"
INK = "#e7e9f3"
GOOD = "#39d353"       # heatmap green, for the live numbers

USER, HOST = "yahya", "github"
PROFILE = [
    ("OS", "Linux"),
    ("Study", "MSc AI Engineering"),
    ("Uni", "Karabük University"),
    ("BSc", "Computer Engineering"),
    ("Focus", "Quantum Computing · QAI"),
    ("Langs", "Python · C · JavaScript"),
    ("Web", "HTML5 · CSS3"),
]
BLOCKS = ["#0a0b14", "#ff5f56", "#27c93f", "#ffbd2e", "#8b5cf6", "#c084fc", "#22d3ee", "#e7e9f3"]

FADE_DUR = 0.35
STAGGER = 0.11
START = 0.3


def short_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.strftime('%b')} {d.day}"


def live_rows(data):
    cur = data["current_streak"]
    best = data["best_day"]
    first = next((m["month"] for m in data["monthly"] if m["total"] > 0), None)
    rows = [
        ("Commits", [(f"{data['total_contributions']:,}", GOOD), (" in the last year", INK)]),
        ("Streak", [(f"{cur['length']} days", GOOD),
                    (f" · longest {data['longest_streak']['length']}", MUTED)]),
        ("Best day", [(f"{best['count']}", GOOD), (f" on {short_date(best['date'])}", INK)]),
        ("Active", [(f"{data['active_days']} days", GOOD),
                    (f" · {data['avg_per_active_day']} per day", MUTED)]),
    ]
    if first:
        y, m = map(int, first.split("-"))
        today = datetime.date.fromisoformat(data["range"]["end"])
        months = (today.year - y) * 12 + today.month - m
        since = datetime.date(y, m, 1).strftime("%b %Y")
        rows.append(("Uptime", [(f"{months} months", GOOD), (f" · since {since}", MUTED)]))
    return rows


def card_geometry():
    """(left margin, height) in card units, so the card lines up with the portrait."""
    scale = (CARD_DISPLAY_W - GAP_DISPLAY_W) / W        # display px per card unit
    try:
        with open(PORTRAIT_PATH) as fh:
            m = re.search(r'width="(\d+)" height="(\d+)"', fh.read(400))
        pw, ph = int(m.group(1)), int(m.group(2))
        h = round(ph / pw * PORTRAIT_DISPLAY_W / scale)
    except (OSError, AttributeError):
        h = 490
    return GAP_DISPLAY_W / scale, h


def render(data):
    margin, H = card_geometry()
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W + margin:.1f}" height="{H}" '
        f'viewBox="{-margin:.2f} 0 {W + margin:.2f} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="{FONT}">',
        '<defs>',
        f'<linearGradient id="ibg" x1="0" y1="0" x2="0.3" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        f'<linearGradient id="iborder" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{ACCENT_1}"/><stop offset="1" stop-color="{ACCENT_2}"/></linearGradient>',
        f'<linearGradient id="isheen" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#ffffff" stop-opacity="0.07"/>'
        f'<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>',
        '</defs>',
        f'<rect width="{W}" height="{H}" rx="{RADIUS}" fill="url(#ibg)"/>',
        f'<rect width="{W}" height="{H * 0.4:.0f}" rx="{RADIUS}" fill="url(#isheen)"/>',
        f'<rect x="0.75" y="0.75" width="{W-1.5}" height="{H-1.5}" rx="{RADIUS}" fill="none" '
        f'stroke="url(#iborder)" stroke-width="1.25" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="url(#iborder)" stroke-opacity="0.25"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{18 + i*15}" cy="{TITLEBAR_H/2}" r="4.5" fill="{dot}"/>')
    p.append(f'<text x="{W/2:.0f}" y="{TITLEBAR_H/2 + 4:.0f}" fill="{MUTED}" font-size="11.5" '
             f'letter-spacing="0.3" text-anchor="middle">{USER}@{HOST}: ~$ neofetch</text>')

    lines = []                                 # each: list of svg fragments at that line's y
    header = f'<tspan fill="{KEY}" font-weight="700">{USER}</tspan><tspan fill="{MUTED}">@</tspan>' \
             f'<tspan fill="{ACCENT_2}" font-weight="700">{HOST}</tspan>'
    lines.append(("text", header))
    lines.append(("text", f'<tspan fill="{MUTED}">{"─" * (len(USER) + len(HOST) + 1)}</tspan>'))
    for k, v in PROFILE:
        lines.append(("kv", (k, [(v, INK)])))
    lines.append(("gap", None))
    for k, parts in live_rows(data):
        lines.append(("kv", (k, parts)))
    lines.append(("gap", None))
    lines.append(("blocks", None))

    used = sum(LINE_H * (0.55 if kind == "gap" else 1) for kind, _ in lines) + LINE_H
    y = TITLEBAR_H + max(PAD, (H - TITLEBAR_H - used) / 2) + FONT
    i = 0
    for kind, payload in lines:
        if kind == "gap":
            y += LINE_H * 0.55
            continue
        begin = START + i * STAGGER
        anim = "" if STATIC else (
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="{FADE_DUR}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="-10 0" to="0 0" '
            f'begin="{begin:.2f}s" dur="{FADE_DUR}s" fill="freeze"/>')
        op = "" if STATIC else ' opacity="0"'
        if kind == "text":
            body = f'<text x="{PAD}" y="{y:.1f}">{payload}</text>'
        elif kind == "kv":
            k, parts = payload
            val = "".join(f'<tspan fill="{c}">{html.escape(s)}</tspan>' for s, c in parts)
            body = (f'<text x="{PAD}" y="{y:.1f}" fill="{KEY}" font-weight="700">{html.escape(k)}</text>'
                    f'<text x="{PAD + KEY_W}" y="{y:.1f}">{val}</text>')
        else:                                  # neofetch's color blocks
            bw, bh = 26, 14
            body = "".join(f'<rect x="{PAD + j*bw}" y="{y - FONT + 2:.1f}" width="{bw}" height="{bh}" '
                           f'fill="{c}"/>' for j, c in enumerate(BLOCKS))
        p.append(f'<g{op}>{body}{anim}</g>')
        y += LINE_H
        i += 1

    # a fresh prompt with a blinking cursor once everything has printed
    begin = START + i * STAGGER
    op = "" if STATIC else ' opacity="0"'
    p.append(f'<g{op}>'
             f'<text x="{PAD}" y="{y + 4:.1f}" fill="{ACCENT_2}">~ $</text>'
             f'<rect x="{PAD + FONT * 0.6 * 4:.1f}" y="{y + 4 - FONT + 2:.1f}" width="{FONT * 0.6:.1f}" '
             f'height="{FONT}" fill="{INK}">'
             + ("" if STATIC else
                '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" '
                'repeatCount="indefinite"/>')
             + '</rect>'
             + ("" if STATIC else
                f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>')
             + '</g>')

    p.append('</svg>')
    return "".join(p)


def main():
    with open(IN_PATH) as fh:
        data = json.load(fh)
    svg = render(data)
    with open(OUT_PATH, "w") as fh:
        fh.write(svg)
    print(f"wrote {OUT_PATH}  {len(svg)/1024:.1f} KB")


if __name__ == "__main__":
    main()
