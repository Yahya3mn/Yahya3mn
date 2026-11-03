"""
Render the most recently pushed public repositories as `ls`-style row cards
(repos/1.svg .. repos/N.svg) and rewrite the block of README.md between the
<!-- repos:start --> and <!-- repos:end --> markers to show them, each card
wrapped in a link to its repo.

Each row is its own image so every one stays clickable -- links inside an SVG
shown through <img> never work on GitHub. The cards are exactly 780px wide,
like every other panel, so the column edges line up (an HTML table would size
itself to the longest repo name instead).

Uses the public REST API. Without a token that's 60 requests/hour per IP,
plenty for one call a day; in Actions the workflow passes GITHUB_TOKEN so the
shared runner IPs never hit that limit.

    python scripts/update_readme_repos.py
"""
import datetime
import html
import os
import re

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "..", "README.md")
OUT_DIR = os.path.join(HERE, "..", "repos")
USERNAME = "Yahya3mn"
COUNT = 5
SKIP = {USERNAME}                  # the profile repo itself

START, END = "<!-- repos:start -->", "<!-- repos:end -->"

W = 780
H = 40
RADIUS = 10
FONT = 13
CW = FONT * 0.6                    # monospace advance, pinned with textLength
X0 = 18
# column starts, in characters from X0
NAME_COLS = 38
LANG_AT, LANG_COLS = 41, 16
DESC_AT, DESC_COLS = 60, 19

BG = "#0a0b14"
BG2 = "#141327"
ACCENT_1 = "#8b5cf6"
ACCENT_2 = "#22d3ee"
NAME_C = "#c4b5fd"
MUTED = "#8b93a7"
INK = "#e7e9f3"

# GitHub linguist colors for the languages these repos actually use
LANG_COLORS = {
    "Jupyter Notebook": "#DA5B0B", "Python": "#3572A5", "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6", "Kotlin": "#A97BFF", "Java": "#b07219", "C": "#555555",
    "C++": "#f34b7d", "C#": "#178600", "PHP": "#4F5D95", "HTML": "#e34c26",
    "CSS": "#563d7c", "Shell": "#89e051",
}

ROW_STAGGER = 0.12                 # each row slides in a little after the one above


def fetch():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": f"{USERNAME}-profile-readme"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(f"https://api.github.com/users/{USERNAME}/repos",
                     params={"sort": "pushed", "per_page": 30, "type": "owner"},
                     headers=headers, timeout=30)
    r.raise_for_status()
    repos = [x for x in r.json() if not x["fork"] and not x["archived"] and x["name"] not in SKIP]
    return repos[:COUNT]


def clip(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


def cell(col, s, color, size=FONT, weight="400", anchor_end=False):
    w = len(s) * size * 0.6
    x = (W - X0 - w) if anchor_end else (X0 + col * CW)
    return (f'<text x="{x:.1f}" y="{H/2 + size*0.36:.1f}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}" textLength="{w:.1f}" lengthAdjust="spacing" '
            f'xml:space="preserve">{html.escape(s)}</text>')


def row_svg(repo, i):
    pushed = datetime.datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))
    lang = repo["language"] or "—"
    desc = (repo["description"] or "").strip()
    begin = 0.2 + i * ROW_STAGGER
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs>',
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        f'<linearGradient id="bd" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{ACCENT_1}"/><stop offset="1" stop-color="{ACCENT_2}"/></linearGradient>',
        '</defs>',
        f'<rect width="{W}" height="{H}" rx="{RADIUS}" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="{RADIUS}" fill="none" '
        f'stroke="url(#bd)" stroke-opacity="0.28"/>',
        '<g opacity="0">'
        f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="0.35s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="-12 0" to="0 0" '
        f'begin="{begin:.2f}s" dur="0.35s" fill="freeze"/>',
        cell(0, "›", ACCENT_2, weight="700"),
        cell(2, clip(repo["name"], NAME_COLS - 2), NAME_C, weight="700"),
        f'<circle cx="{X0 + LANG_AT*CW + 4:.1f}" cy="{H/2:.1f}" r="4.5" '
        f'fill="{LANG_COLORS.get(lang, MUTED)}"/>',
        cell(LANG_AT + 1.6, clip(lang, LANG_COLS), INK),
    ]
    if desc:
        p.append(cell(DESC_AT, clip(desc, DESC_COLS), MUTED))
    p.append(cell(0, f'{pushed.strftime("%b %Y")}  ↗', MUTED, anchor_end=True))
    p.append('</g></svg>')
    return "".join(p)


def render_block(repos):
    os.makedirs(OUT_DIR, exist_ok=True)
    links = []
    for i, repo in enumerate(repos, 1):
        with open(os.path.join(OUT_DIR, f"{i}.svg"), "w", encoding="utf-8") as fh:
            fh.write(row_svg(repo, i - 1))
        alt = html.escape(f'{repo["name"]} — {repo["language"] or "no language"}', quote=True)
        links.append(f'<a href="{repo["html_url"]}"><img src="./repos/{i}.svg" width="{W}" alt="{alt}" /></a><br>')
    # drop cards left over from a day with more repos than today
    for f in os.listdir(OUT_DIR):
        m = re.fullmatch(r"(\d+)\.svg", f)
        if m and int(m.group(1)) > len(repos):
            os.remove(os.path.join(OUT_DIR, f))
    return f"{START}\n" + "\n".join(links) + f"\n{END}"


def main():
    with open(README, encoding="utf-8") as fh:
        text = fh.read()
    if START not in text or END not in text:
        raise SystemExit(f"README.md has no {START} ... {END} block")
    block = render_block(fetch())
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    if new != text:
        with open(README, "w", encoding="utf-8") as fh:
            fh.write(new)
    print("README repos block", "updated" if new != text else "unchanged")


if __name__ == "__main__":
    main()
