"""
Render the README's section headers as terminal prompts that type their
command out character by character, then park a blinking cursor -- the same
card language as the other SVGs, sized to the 780px column.

Each prompt carries its own vertical spacing as transparent margin (MARGIN_TOP
above the bar, MARGIN_BOTTOM below), since GitHub strips the CSS that would
otherwise space README elements -- the README just joins everything with <br>.

Static content, so this only needs re-running when a command below changes:
    python scripts/make_prompt_svg.py      # writes prompts/<name>.svg
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "prompts")
STATIC = os.environ.get("STATIC") == "1"

# name -> (command, muted note shown on the right)
PROMPTS = {
    "whoami": ("whoami", "portrait + neofetch"),
    "contributions": ("./contributions.sh --last-year", "auto-refreshed daily"),
    "repos": ("ls -t ~/repos | head -5", "most recently pushed"),
    "stack": ("cat ~/.stack", ""),
    "contact": ("cat contact.txt", ""),
}

W = 780
H = 44                 # the bar itself
MARGIN_TOP = 24        # gap to the section above
MARGIN_BOTTOM = 6      # gap to this section's content
RADIUS = 12
FONT = 15
CW = FONT * 0.6        # monospace advance; textLength pins every glyph to it
X0 = 20

BG = "#0a0b14"
BG2 = "#141327"
ACCENT_1 = "#8b5cf6"
ACCENT_2 = "#22d3ee"
USER_C = "#a78bfa"
MUTED = "#8b93a7"
INK = "#e7e9f3"

TYPE_DELAY = 0.35      # seconds before the first keystroke
TYPE_STEP = 0.065      # seconds per character


def seg(x, s, color, weight="400"):
    return (f'<text x="{x:.1f}" y="{H/2 + FONT*0.35:.1f}" fill="{color}" font-weight="{weight}" '
            f'textLength="{len(s)*CW:.1f}" lengthAdjust="spacing" xml:space="preserve">{html.escape(s)}</text>')


def render(cmd, note):
    full_h = MARGIN_TOP + H + MARGIN_BOTTOM
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{full_h}" viewBox="0 0 {W} {full_h}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="{FONT}">',
        '<defs>',
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        f'<linearGradient id="bd" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{ACCENT_1}"/><stop offset="1" stop-color="{ACCENT_2}"/></linearGradient>',
    ]
    prefix = [("yahya", USER_C, "700"), ("@", MUTED, "400"), ("github", ACCENT_2, "700"),
              (":", MUTED, "400"), ("~", ACCENT_2, "400"), ("$ ", MUTED, "400")]
    cmd_x = X0 + sum(len(s) for s, _, _ in prefix) * CW
    n = len(cmd)
    type_dur = n * TYPE_STEP
    if not STATIC:
        widths = ";".join(f"{i*CW:.1f}" for i in range(n + 1))
        p.append(f'<clipPath id="typed"><rect x="{cmd_x:.1f}" y="0" height="{H}" width="0">'
                 f'<animate attributeName="width" values="{widths}" calcMode="discrete" '
                 f'begin="{TYPE_DELAY}s" dur="{type_dur:.2f}s" fill="freeze"/></rect></clipPath>')
    p.append('</defs>')
    p.append(f'<g transform="translate(0 {MARGIN_TOP})">')
    p += [
        f'<rect width="{W}" height="{H}" rx="{RADIUS}" fill="url(#bg)"/>',
        f'<rect x="0.75" y="0.75" width="{W-1.5}" height="{H-1.5}" rx="{RADIUS}" fill="none" '
        f'stroke="url(#bd)" stroke-width="1.1" stroke-opacity="0.45"/>',
    ]
    x = X0
    for s, c, w in prefix:
        p.append(seg(x, s, c, w))
        x += len(s) * CW
    clip = "" if STATIC else ' clip-path="url(#typed)"'
    p.append(f'<g{clip}>{seg(cmd_x, cmd, INK)}</g>')

    if note:                                   # right-aligned shell comment
        note = f"# {note}"
        nw = len(note) * CW * 0.85
        p.append(f'<text x="{W - X0 - nw:.1f}" y="{H/2 + FONT*0.32:.1f}" fill="{MUTED}" '
                 f'font-size="{FONT*0.85:.1f}" textLength="{nw:.1f}" lengthAdjust="spacing" '
                 f'xml:space="preserve">{html.escape(note)}</text>')

    # cursor: rides the typing, then blinks where the command ends
    cy = H / 2 - FONT * 0.62
    if STATIC:
        p.append(f'<rect x="{cmd_x + n*CW + 2:.1f}" y="{cy:.1f}" width="{CW:.1f}" height="{FONT*1.1:.1f}" fill="{ACCENT_2}"/>')
    else:
        xs = ";".join(f"{cmd_x + i*CW + 2:.1f}" for i in range(n + 1))
        p.append(f'<rect x="{cmd_x + 2:.1f}" y="{cy:.1f}" width="{CW:.1f}" height="{FONT*1.1:.1f}" fill="{ACCENT_2}">'
                 f'<animate attributeName="x" values="{xs}" calcMode="discrete" begin="{TYPE_DELAY}s" '
                 f'dur="{type_dur:.2f}s" fill="freeze"/>'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" '
                 f'begin="{TYPE_DELAY + type_dur:.2f}s" repeatCount="indefinite"/></rect>')
    p.append('</g></svg>')
    return "".join(p)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, (cmd, note) in PROMPTS.items():
        out = os.path.join(OUT_DIR, f"{name}.svg")
        with open(out, "w") as fh:
            fh.write(render(cmd, note))
        print("wrote", os.path.relpath(out))


if __name__ == "__main__":
    main()
