#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG: a title bar plus colored
key/value rows that fade+slide in on a short stagger, then freeze.

Set STATIC=1 to emit a frozen (no-animation) frame for local previews.
"""

import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

USERNAME = "yahya"
TITLE = f"{USERNAME}@github"

ROWS = [
    ("Now", "AI Engineering MSc @ Karabuk University"),
    ("Prev", "BSc Computer Engineering"),
    ("Stack", "Python  C  HTML  CSS  JavaScript"),
    ("Tools", "Git  Linux  VS Code"),
    ("Focus", "Quantum Computing, Quantum AI"),
    ("Mail", "yahyazakryakhan@gmail.com"),
]

LABEL_COLOR = "#39d353"
VALUE_COLOR = "#c9d1d9"
TITLE_COLOR = "#8b949e"
BG = "#0d1117"
BORDER = "#30363d"

WIDTH = 490
ROW_H = 30
TOP_PAD = 46
BOTTOM_PAD = 18
HEIGHT = TOP_PAD + ROW_H * len(ROWS) + BOTTOM_PAD
LABEL_W = 70


def escape(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render():
    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )

    anim_rule = "" if STATIC else "animation: fadein 0.5s ease-out forwards;"
    parts.append(
        f"""
  <style>
    .bg {{ fill: {BG}; stroke: {BORDER}; stroke-width: 1; }}
    .titlebar {{ fill: #161b22; }}
    .dot {{ }}
    .title {{ fill: {TITLE_COLOR}; font-size: 12px; }}
    .label {{ fill: {LABEL_COLOR}; font-size: 13px; font-weight: bold; }}
    .value {{ fill: {VALUE_COLOR}; font-size: 13px; }}
    .row {{ opacity: {"1" if STATIC else "0"}; {anim_rule} }}
    @keyframes fadein {{
      from {{ opacity: 0; transform: translateX(-8px); }}
      to   {{ opacity: 1; transform: translateX(0); }}
    }}
  </style>
"""
    )

    parts.append(f'<rect class="bg" x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8"/>')

    parts.append(f'<path class="titlebar" d="M0.5,8 a8,8 0 0 1 8,-7.5 h{WIDTH - 17} a8,8 0 0 1 8,7.5 v22 h-{WIDTH - 1} z"/>')
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{18 + i * 16}" cy="15" r="5" fill="{color}"/>')
    parts.append(f'<text class="title" x="{WIDTH / 2}" y="19" text-anchor="middle">{TITLE} — neofetch</text>')

    for i, (label, value) in enumerate(ROWS):
        y = TOP_PAD + i * ROW_H
        delay = 0.15 + i * 0.12
        style = "" if STATIC else f' style="animation-delay:{delay:.2f}s"'
        parts.append(f'<g class="row"{style}>')
        parts.append(f'<text class="label" x="20" y="{y}">{escape(label)}</text>')
        parts.append(f'<text class="value" x="{20 + LABEL_W}" y="{y}">{escape(value)}</text>')
        parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    with open(OUT_PATH, "w") as f:
        f.write(render())
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
