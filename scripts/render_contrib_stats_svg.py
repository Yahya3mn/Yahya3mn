#!/usr/bin/env python3
"""
Render a second contribution graphic: a monthly activity bar chart (grows
in, staggered) beside an animated activity-ring (draws in like a fitness
ring), inside the same glass-card language as the heatmap and wordmark.

Run manually after data/contributions.json is refreshed; not required by
the daily workflow (it reads the same JSON the heatmap already regenerates).
"""
import datetime
import json
import os

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-stats.svg")

# shared palette with the heatmap / wordmark
BG_TOP = "#141327"
BG_BOTTOM = "#0a0b14"
ACCENT_1 = "#8b5cf6"   # violet
ACCENT_2 = "#22d3ee"   # cyan
MUTED = "#8b93a7"
TEXT = "#e7e9f3"
TRACK = "#232a3d"
BAR_LOW = "#0e4429"
BAR_HIGH = "#6bf5a8"

PAD = 22
TITLEBAR_H = 32
RADIUS = 16
CARD_W = 780
CHART_W = 530
CHART_H = 130
GAP_X = 34           # gutter between the bar chart and the ring panel
RING_R = 52
RING_STROKE = 11

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

MONO_ADVANCE = 0.6


def right_text(x_end, y, s, size, color, weight="400"):
    w = len(s) * size * MONO_ADVANCE
    return (f'<text x="{x_end - w:.1f}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}">{s}</text>')


def render(data):
    monthly = data["monthly"][-12:]
    n = len(monthly)
    max_val = max((m["total"] for m in monthly), default=0) or 1

    chart_top = TITLEBAR_H + 26
    chart_left = PAD
    axis_y = chart_top + CHART_H

    ring_panel_x = chart_left + CHART_W + GAP_X
    ring_cx = ring_panel_x + RING_R + 4
    ring_cy = chart_top + CHART_H / 2 - 6

    canvas_w = ring_panel_x + RING_R * 2 + 90
    canvas_h = axis_y + 46

    active_days = data["active_days"]
    range_days = (datetime.date.fromisoformat(data["range"]["end"])
                  - datetime.date.fromisoformat(data["range"]["start"])).days + 1
    pct = active_days / range_days if range_days else 0

    circumference = 2 * 3.14159265 * RING_R
    target_offset = circumference * (1 - pct)

    css = f"""
@keyframes grow {{ from {{ transform: scaleY(0); }} to {{ transform: scaleY(1); }} }}
@keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes draw {{ from {{ stroke-dashoffset: {circumference:.2f}; }} to {{ stroke-dashoffset: {target_offset:.2f}; }} }}
.bar {{
  transform-box: fill-box; transform-origin: bottom; opacity: 0;
  animation: grow 0.7s cubic-bezier(.2,.8,.2,1) both, fade 0.25s ease-out both;
}}
.ring-fg {{
  stroke-dasharray: {circumference:.2f}; stroke-dashoffset: {circumference:.2f};
  animation: draw 1.3s 0.25s cubic-bezier(.2,.7,.2,1) forwards;
}}
.fadein {{ opacity: 0; animation: fade 0.6s ease-out both; }}
@media (prefers-reduced-motion: reduce) {{
  .bar, .fadein {{ opacity: 1 !important; animation: none !important; }}
  .ring-fg {{ stroke-dashoffset: {target_offset:.2f} !important; animation: none !important; }}
}}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w:.0f}" height="{canvas_h:.0f}" '
        f'viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs>',
        f'<linearGradient id="sbg" x1="0" y1="0" x2="0.3" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/></linearGradient>',
        f'<linearGradient id="sborder" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{ACCENT_1}"/><stop offset="1" stop-color="{ACCENT_2}"/></linearGradient>',
        f'<linearGradient id="ssheen" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#ffffff" stop-opacity="0.07"/>'
        f'<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>',
        f'<linearGradient id="barGrad" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{BAR_LOW}"/><stop offset="1" stop-color="{BAR_HIGH}"/></linearGradient>',
        f'<linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{ACCENT_1}"/><stop offset="1" stop-color="{ACCENT_2}"/></linearGradient>',
        '</defs>',
        f'<rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" rx="{RADIUS}" fill="url(#sbg)"/>',
        f'<rect width="{canvas_w:.0f}" height="{canvas_h * 0.4:.0f}" rx="{RADIUS}" fill="url(#ssheen)"/>',
        f'<rect x="0.75" y="0.75" width="{canvas_w-1.5:.0f}" height="{canvas_h-1.5:.0f}" rx="{RADIUS}" '
        f'fill="none" stroke="url(#sborder)" stroke-width="1.25" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w:.0f}" y2="{TITLEBAR_H}" stroke="url(#sborder)" stroke-opacity="0.25"/>',
    ]
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{canvas_w/2:.0f}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
                 f'letter-spacing="0.3" text-anchor="middle">yahya@github: ~/contributions --monthly</text>')

    # ---- monthly bar chart ----
    slot_w = CHART_W / n
    bar_w = slot_w * 0.5
    for i, m in enumerate(monthly):
        val = m["total"]
        h = (val / max_val) * CHART_H if max_val else 0
        h = max(h, 2)  # always show a sliver so the axis reads as a baseline
        x = chart_left + i * slot_w + (slot_w - bar_w) / 2
        y = axis_y - h
        delay = 0.35 + i * 0.05
        month_idx = int(m["month"][5:7]) - 1
        parts.append(
            f'<rect class="bar" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
            f'rx="{min(3, bar_w/3):.1f}" fill="{"url(#barGrad)" if val else TRACK}" '
            f'style="animation-delay:{delay:.2f}s">'
            f'<title>{m["month"]}: {val} contribution{"s" if val != 1 else ""}</title></rect>'
        )
        if i % max(1, n // 6) == 0 or i == n - 1:
            parts.append(f'<text x="{x + bar_w/2:.1f}" y="{axis_y + 14}" fill="{MUTED}" '
                         f'font-size="9" text-anchor="middle">{MONTH_ABBR[month_idx]}</text>')

    parts.append(f'<line x1="{chart_left}" y1="{axis_y}" x2="{chart_left + CHART_W}" y2="{axis_y}" '
                 f'stroke="{TRACK}" stroke-width="1"/>')
    parts.append(right_text(chart_left + CHART_W, chart_top - 8, f'peak {max_val}/mo', 10, MUTED))

    # ---- vertical divider ----
    div_x = ring_panel_x - GAP_X / 2
    parts.append(f'<line x1="{div_x:.1f}" y1="{chart_top - 4}" x2="{div_x:.1f}" y2="{axis_y + 4}" '
                 f'stroke="{TRACK}" stroke-width="1"/>')

    # ---- activity ring ----
    parts.append(f'<g class="fadein" style="animation-delay:0.2s">')
    parts.append(f'<circle cx="{ring_cx:.1f}" cy="{ring_cy:.1f}" r="{RING_R}" fill="none" '
                 f'stroke="{TRACK}" stroke-width="{RING_STROKE}"/>')
    parts.append(f'<circle class="ring-fg" cx="{ring_cx:.1f}" cy="{ring_cy:.1f}" r="{RING_R}" fill="none" '
                 f'stroke="url(#ringGrad)" stroke-width="{RING_STROKE}" stroke-linecap="round" '
                 f'transform="rotate(-90 {ring_cx:.1f} {ring_cy:.1f})"/>')
    parts.append(f'<text x="{ring_cx:.1f}" y="{ring_cy - 2:.1f}" fill="{TEXT}" font-size="20" '
                 f'font-weight="700" text-anchor="middle">{pct*100:.0f}%</text>')
    parts.append(f'<text x="{ring_cx:.1f}" y="{ring_cy + 15:.1f}" fill="{MUTED}" font-size="9" '
                 f'text-anchor="middle">active days</text>')
    parts.append('</g>')

    stat_x = ring_panel_x - GAP_X / 2 + 14
    stat_y = axis_y + 14
    parts.append(f'<g class="fadein" style="animation-delay:0.5s">')
    for dx, color, label in [
        (0, ACCENT_2, f'{active_days} active / {range_days} days'),
        (16, ACCENT_1, f'{data["avg_per_active_day"]} avg / active day'),
    ]:
        y = stat_y + dx
        parts.append(f'<circle cx="{stat_x}" cy="{y-3.5:.1f}" r="3" fill="{color}"/>')
        parts.append(f'<text x="{stat_x + 10}" y="{y:.1f}" fill="{MUTED}" font-size="10">{label}</text>')
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
