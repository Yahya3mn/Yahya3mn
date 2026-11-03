"""
Rewrite the "recent repos" block of README.md -- everything between the
<!-- repos:start --> and <!-- repos:end --> markers -- with the most recently
pushed public repositories. Unlike the SVGs this is plain HTML in the README,
so every repo name stays a real, clickable link.

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
USERNAME = "Yahya3mn"
COUNT = 5
SKIP = {USERNAME}                  # the profile repo itself

START, END = "<!-- repos:start -->", "<!-- repos:end -->"


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


def row(repo):
    pushed = datetime.datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))
    name = html.escape(repo["name"])
    lang = html.escape(repo["language"] or "—")
    desc = html.escape((repo["description"] or "").strip()) or "&nbsp;"
    return (f'    <tr><td><a href="{repo["html_url"]}"><b>{name}</b></a></td>'
            f'<td>{desc}</td><td><code>{lang}</code></td>'
            f'<td>{pushed.strftime("%b %Y")}</td></tr>')


def render(repos):
    body = "\n".join(row(r) for r in repos)
    return (f"{START}\n<table>\n"
            f"  <thead><tr><th>repo</th><th>about</th><th>lang</th><th>pushed</th></tr></thead>\n"
            f"  <tbody>\n{body}\n  </tbody>\n</table>\n{END}")


def main():
    with open(README, encoding="utf-8") as fh:
        text = fh.read()
    if START not in text or END not in text:
        raise SystemExit(f"README.md has no {START} ... {END} block")
    block = render(fetch())
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    if new != text:
        with open(README, "w", encoding="utf-8") as fh:
            fh.write(new)
    print("README repos block", "updated" if new != text else "unchanged")


if __name__ == "__main__":
    main()
