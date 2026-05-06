#!/usr/bin/env python3
"""
RSS-Feed-Fetcher für die AI Tageszeitung.
Arbeitet alle Kreise aus config.py ab.
Behält bestehende Artikel, fügt nur neue hinzu.
"""
import json
import hashlib
import re
import sys
import ssl
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    import feedparser
except ImportError:
    print("feedparser nicht installiert. Bitte: pip install feedparser")
    sys.exit(1)

from config import BASE, KREISE

def strip_html(text: str) -> str:
    clean = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', clean).strip()

def article_id(entry) -> str:
    raw = entry.get("link", "") + entry.get("title", "")
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def classify_article(title: str, summary: str, feed_coverage: str, keywords: dict) -> list:
    matches = set()
    if feed_coverage and feed_coverage != "kreisweite-nachrichten":
        matches.add(feed_coverage)
    text = (title + " " + summary).lower()
    for slug, kws in keywords.items():
        for kw in kws:
            if kw in text:
                matches.add(slug)
                break
    return list(matches) if matches else ["kreisweite-nachrichten"]

def load_existing(data_dir: Path) -> dict:
    f = data_dir / "all_articles.json"
    if f.exists():
        try:
            return {a["id"]: a for a in json.loads(f.read_text())}
        except Exception:
            pass
    return {}

def fetch_kreis(kreis_slug: str, kreis_cfg: dict):
    data_dir = BASE / kreis_slug
    feeds_file = data_dir / "feeds.json"
    if not feeds_file.exists():
        print(f"SKIP {kreis_slug}: keine feeds.json")
        return

    print(f"\n{'='*60}")
    print(f"  {kreis_cfg['name']}")
    print(f"{'='*60}")

    config = json.loads(feeds_file.read_text())
    keywords = kreis_cfg["keywords"]
    kommunen = kreis_cfg["kommunen"]
    all_slugs = list(kommunen.keys()) + ["kreisweite-nachrichten"]

    all_articles = load_existing(data_dir)
    new_count = 0
    ctx = ssl.create_default_context()

    for feed_cfg in config["feeds"]:
        url = feed_cfg["url"]
        name = feed_cfg["name"]
        coverage = feed_cfg.get("coverage", "kreisweite-nachrichten")
        max_pages = feed_cfg.get("pages", 1)  # WordPress-Feeds: ?paged=N
        print(f"  Fetching: {name} ({max_pages} Seiten)")

        all_entries = []
        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                page_url = url
            else:
                # Wenn URL bereits einen Query-String hat, mit & anhängen, sonst mit ?
                sep = "&" if "?" in url else "?"
                page_url = f"{url}{sep}paged={page_num}"
            try:
                req = urllib.request.Request(page_url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 AI-Tageszeitung/1.0",
                    "Accept": "application/rss+xml, application/xml, text/xml, */*",
                })
                response = urllib.request.urlopen(req, timeout=20, context=ctx)
                raw = response.read()
                d = feedparser.parse(raw)
                if len(d.entries) == 0:
                    if d.bozo and page_num == 1:
                        print(f"    WARNUNG: {d.bozo_exception}")
                    break  # Keine weiteren Seiten
                all_entries.extend(d.entries)
                if page_num == 1:
                    print(f"    -> {len(d.entries)} Einträge (Seite 1)")
            except Exception as e:
                if page_num == 1:
                    print(f"    FEHLER: {e}")
                break  # Bei Fehler auf höheren Seiten abbrechen

        if max_pages > 1 and len(all_entries) > 0:
            print(f"    -> {len(all_entries)} Einträge gesamt ({max_pages} Seiten)")
        elif max_pages == 1 and len(all_entries) == 0:
            continue

        for entry in all_entries:
            aid = article_id(entry)
            if aid in all_articles:
                existing = all_articles[aid]
                new_kommunen = classify_article(
                    entry.get("title", ""), entry.get("summary", ""), coverage, keywords
                )
                for k in new_kommunen:
                    if k not in existing["kommunen"]:
                        existing["kommunen"].append(k)
                continue

            title = entry.get("title", "Ohne Titel")
            summary = strip_html(entry.get("summary", ""))
            link = entry.get("link", "")
            published = entry.get("published", "")

            all_articles[aid] = {
                "id": aid,
                "title": title,
                "summary": summary[:400],
                "link": link,
                "published": published,
                "source": name,
                "kommunen": classify_article(title, summary, coverage, keywords),
                "fetched": datetime.now().isoformat(),
            }
            new_count += 1

    # Speichere je Kommune
    for slug in all_slugs:
        arts = sorted(
            [a for a in all_articles.values() if slug in a["kommunen"]],
            key=lambda x: x.get("published", ""), reverse=True
        )
        outdir = data_dir / slug
        outdir.mkdir(exist_ok=True)
        (outdir / "articles.json").write_text(json.dumps(arts, ensure_ascii=False, indent=2))
        print(f"  {slug}: {len(arts)} Artikel")

    all_list = sorted(all_articles.values(), key=lambda x: x.get("published", ""), reverse=True)
    (data_dir / "all_articles.json").write_text(json.dumps(all_list, ensure_ascii=False, indent=2))

    config["last_updated"] = datetime.now().isoformat()
    feeds_file.write_text(json.dumps(config, ensure_ascii=False, indent=2))

    print(f"  Gesamt: {len(all_list)} Artikel ({new_count} neu)")

if __name__ == "__main__":
    for slug, cfg in KREISE.items():
        fetch_kreis(slug, cfg)
