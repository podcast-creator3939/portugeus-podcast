#!/usr/bin/env python3
"""Rebuild the podcast site: one HTML page per episode, index.html and feed.xml.

Each episode lives in episodes/YYYY-MM-DD/ with:
  script.md     full episode script + study notes (Markdown)
  meta.json     {"title": "...", "summary": "..."}
  episode.mp3   audio (only the newest KEEP_AUDIO episodes keep their MP3)

Usage: python3 tools/build_site.py
"""
import html
import json
import subprocess
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import markdown

REPO = Path(__file__).resolve().parent.parent
BASE_URL = "https://podcast-creator3939.github.io/portugeus-podcast"
SHOW_TITLE = "Podcast Brasil — Português do dia a dia"
SHOW_DESC = ("Um mini podcast diário em português brasileiro com a Ana e o Rafa: "
             "notícias do Brasil, vocabulário e uma expressão do dia, para estudantes de nível B1–B2.")
KEEP_AUDIO = 30

PAGE = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{title}</title>
<style>
body{{font-family:Georgia,serif;max-width:720px;margin:2rem auto;padding:0 1rem;line-height:1.6;color:#1d2b24;background:#fbf8f1}}
h1,h2,h3{{font-family:system-ui,sans-serif;color:#0b6b3a}} a{{color:#0b6b3a}}
table{{border-collapse:collapse;width:100%;font-size:.95rem}} td,th{{border:1px solid #d8d2c2;padding:.35rem .5rem;text-align:left}}
audio{{width:100%;margin:1rem 0}} .muted{{color:#6b6b6b;font-size:.9rem}}
</style></head><body>
{body}
</body></html>
"""


def duration_seconds(mp3: Path) -> int:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(mp3)], capture_output=True, text=True)
    try:
        return int(float(out.stdout.strip()))
    except ValueError:
        return 0


def main():
    eps = sorted((p for p in (REPO / "episodes").glob("*/") if (p / "meta.json").exists()),
                 reverse=True)
    for old in eps[KEEP_AUDIO:]:
        (old / "episode.mp3").unlink(missing_ok=True)

    items, links = [], []
    for ep in eps:
        meta = json.loads((ep / "meta.json").read_text(encoding="utf-8"))
        date = ep.name
        url = f"{BASE_URL}/episodes/{date}/"
        mp3 = ep / "episode.mp3"
        body = markdown.markdown((ep / "script.md").read_text(encoding="utf-8"),
                                 extensions=["tables"])
        audio = f'<audio controls src="episode.mp3"></audio>' if mp3.exists() else ""
        (ep / "index.html").write_text(PAGE.format(
            title=html.escape(meta["title"]),
            body=f'<p class="muted"><a href="../../">← Todos os episódios</a></p>{audio}{body}'),
            encoding="utf-8")
        links.append(f'<li><a href="episodes/{date}/">{html.escape(meta["title"])}</a></li>')
        if not mp3.exists():
            continue
        pub = datetime.strptime(date, "%Y-%m-%d").replace(hour=11, tzinfo=timezone.utc)
        desc = f'{meta.get("summary", "")}\n\nNotas de estudo e roteiro completo: {url}'
        items.append(f"""    <item>
      <title>{html.escape(meta["title"])}</title>
      <description>{html.escape(desc)}</description>
      <link>{url}</link>
      <guid isPermaLink="false">podcast-brasil-{date}</guid>
      <pubDate>{format_datetime(pub)}</pubDate>
      <enclosure url="{BASE_URL}/episodes/{date}/episode.mp3" length="{mp3.stat().st_size}" type="audio/mpeg"/>
      <itunes:duration>{duration_seconds(mp3)}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{html.escape(SHOW_TITLE)}</title>
    <link>{BASE_URL}/</link>
    <description>{html.escape(SHOW_DESC)}</description>
    <language>pt-br</language>
    <itunes:author>Ana e Rafa</itunes:author>
    <itunes:image href="{BASE_URL}/artwork.png"/>
    <image><url>{BASE_URL}/artwork.png</url><title>{html.escape(SHOW_TITLE)}</title><link>{BASE_URL}/</link></image>
    <itunes:category text="Education"><itunes:category text="Language Learning"/></itunes:category>
    <itunes:explicit>false</itunes:explicit>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (REPO / "feed.xml").write_text(feed, encoding="utf-8")
    (REPO / "index.html").write_text(PAGE.format(
        title=html.escape(SHOW_TITLE),
        body=(f"<h1>{html.escape(SHOW_TITLE)}</h1><p>{html.escape(SHOW_DESC)}</p>"
              f'<p>Feed: <a href="feed.xml">{BASE_URL}/feed.xml</a></p>'
              f"<h2>Episódios</h2><ul>{''.join(links)}</ul>")), encoding="utf-8")
    (REPO / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    (REPO / ".nojekyll").write_text("")
    print(f"Built {len(eps)} episode pages, {len(items)} feed items.")


if __name__ == "__main__":
    main()
