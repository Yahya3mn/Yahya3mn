"""
Convert source-prepped.png (from prep_photo.py) into a monochrome ASCII
portrait that types itself in, as an SVG GitHub will animate (SMIL only, no JS).

Each pixel of the downsampled grid picks a glyph from a density ramp: sparse
for bright, dense for dark, with a leading space so the white backdrop prints
as nothing. One light ink color -- per-character color is what makes most
ASCII portraits read as static.

Animation: every row sits behind its own clip that wipes left -> right with a
block cursor riding the edge, staggered top to bottom. It prints once and
freezes; nothing loops.

Env overrides: PORTRAIT_SRC, PORTRAIT_COLS, PORTRAIT_GAMMA, PORTRAIT_INVERT=1
(bright -> dense instead), STATIC=1 (frozen final frame, for local previews).
"""
import argparse
import html
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))

SRC = os.environ.get("PORTRAIT_SRC", os.path.join(HERE, "..", "source-prepped.png"))
COLS = int(os.environ.get("PORTRAIT_COLS", 72))
GAMMA = float(os.environ.get("PORTRAIT_GAMMA", 0.7))   # <1 pushes skin mid-tones denser
INVERT = os.environ.get("PORTRAIT_INVERT") == "1"
STATIC = os.environ.get("STATIC") == "1"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
BLANK_ABOVE = 0.93       # brightness above this always prints as a space

# same cell + terminal-window chrome as make_wordmark_svg.py, so the two panels
# read as one set when they sit side by side
CELL_W = 9.0
CELL_H = 15.5
PAD = 18
TITLEBAR_H = 30
RADIUS = 16

BG = "#0a0b14"
BG2 = "#141327"
ACCENT_1 = "#8b5cf6"
ACCENT_2 = "#22d3ee"
TITLE_TEXT = "#8b93a7"
INK = "#e7e9f3"

ROW_DUR = 0.45           # seconds for one row's wipe
ROW_STAGGER = 0.055      # delay between consecutive rows


def to_ascii(src):
    img = Image.open(src).convert("L")
    rows = max(1, round(img.height / img.width * COLS * CELL_W / CELL_H))
    a = np.asarray(img.resize((COLS, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    dark = a if INVERT else 1.0 - a
    idx = np.rint(np.power(dark, GAMMA) * (len(RAMP) - 1)).astype(int)
    idx[a > BLANK_ABOVE] = 0
    lines = ["".join(RAMP[i] for i in r) for r in idx]
    # drop blank rows at the top and bottom
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def emit(lines, out, title_text):
    art_w = COLS * CELL_W
    art_h = len(lines) * CELL_H
    canvas_w = art_w + PAD * 2
    canvas_h = TITLEBAR_H + PAD * 0.6 + art_h + PAD
    art_top = TITLEBAR_H + PAD * 0.6
    fs = CELL_H * 0.92

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w:.0f}" height="{canvas_h:.0f}" '
        f'viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">',
        '<defs>',
        f'<linearGradient id="pbg" x1="0" y1="0" x2="0.3" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        '</linearGradient>',
        f'<linearGradient id="pborder" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{ACCENT_1}"/><stop offset="1" stop-color="{ACCENT_2}"/></linearGradient>',
        f'<linearGradient id="psheen" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#ffffff" stop-opacity="0.07"/>'
        f'<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>',
    ]
    rows = []                                  # (y, x, body, row index)
    for ry, line in enumerate(lines):
        s = line.rstrip()
        if not s.strip():
            continue
        lead = len(s) - len(s.lstrip(" "))
        rows.append((ry, lead, s[lead:]))

    if not STATIC:
        # one clip per row; the wipe runs across the full art width so every
        # row takes the same time regardless of where its glyphs start
        for ry, _, _ in rows:
            begin = ry * ROW_STAGGER
            y = art_top + ry * CELL_H
            p.append(f'<clipPath id="r{ry}"><rect x="{PAD}" y="{y:.1f}" height="{CELL_H:.1f}" width="0">'
                     f'<animate attributeName="width" from="0" to="{art_w:.0f}" begin="{begin:.3f}s" '
                     f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>')
    p.append('</defs>')

    p += [
        f'<rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" rx="{RADIUS}" fill="url(#pbg)"/>',
        f'<rect width="{canvas_w:.0f}" height="{canvas_h * 0.4:.0f}" rx="{RADIUS}" fill="url(#psheen)"/>',
        f'<rect x="0.75" y="0.75" width="{canvas_w-1.5:.0f}" height="{canvas_h-1.5:.0f}" rx="{RADIUS}" '
        f'fill="none" stroke="url(#pborder)" stroke-width="1.25" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w:.0f}" y2="{TITLEBAR_H}" stroke="url(#pborder)" stroke-opacity="0.25"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*15}" cy="{TITLEBAR_H/2}" r="4.5" fill="{dot}"/>')
    p.append(f'<text x="{canvas_w/2:.0f}" y="{TITLEBAR_H/2 + 4:.0f}" fill="{TITLE_TEXT}" '
             f'font-size="11.5" letter-spacing="0.3" text-anchor="middle">{html.escape(title_text)}</text>')

    p.append(f'<g fill="{INK}">')
    for ry, lead, body in rows:
        x = PAD + lead * CELL_W
        y = art_top + ry * CELL_H + CELL_H * 0.78
        clip = "" if STATIC else f' clip-path="url(#r{ry})"'
        p.append(f'<text xml:space="preserve" x="{x:.1f}" y="{y:.1f}" font-size="{fs:.1f}" '
                 f'textLength="{len(body)*CELL_W:.1f}" lengthAdjust="spacing"{clip}>{html.escape(body)}</text>')
    p.append('</g>')

    if not STATIC:
        # block cursor riding each row's wipe edge, hidden before and after
        for ry, _, _ in rows:
            begin = ry * ROW_STAGGER
            y = art_top + ry * CELL_H + 1
            p.append(f'<rect x="{PAD}" y="{y:.1f}" width="{CELL_W:.1f}" height="{CELL_H-2:.1f}" '
                     f'fill="{INK}" opacity="0">'
                     f'<set attributeName="opacity" to="0.85" begin="{begin:.3f}s"/>'
                     f'<animate attributeName="x" from="{PAD}" to="{PAD+art_w:.0f}" begin="{begin:.3f}s" '
                     f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
                     f'<set attributeName="opacity" to="0" begin="{begin+ROW_DUR:.3f}s"/></rect>')

    p.append('</svg>')
    svg = "".join(p)
    with open(out, "w") as fh:
        fh.write(svg)
    print(f"wrote {out}  {len(svg)/1024:.1f} KB  {COLS}x{len(lines)} chars  {canvas_w:.0f}x{canvas_h:.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "yahya-ascii.svg"))
    ap.add_argument("--title", default="yahya@github: ~$ cat portrait.txt")
    ap.add_argument("--preview", action="store_true", help="print the art to stdout instead")
    a = ap.parse_args()

    lines = to_ascii(a.src)
    if a.preview:
        print("\n".join(lines))
        return
    emit(lines, a.out, a.title)


if __name__ == "__main__":
    main()
