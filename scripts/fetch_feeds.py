#!/usr/bin/env python3
"""
RSS-Feed-Fetcher für die AI Tageszeitung Rheinisch-Bergischer Kreis.
Liest feeds.json, holt alle RSS-Feeds, ordnet Artikel den Kommunen zu,
speichert sie als JSON-Dateien je Kommune.
"""
import json
import hashlib
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import feedparser
except ImportError:
    print("feedparser nicht installiert. Bitte: pip install feedparser")
    sys.exit(1)

BASE = Path(__file__).resolve().parent.parent / "rheinisch-bergischer-kreis"
FEEDS_JSON = BASE / "feeds.json"

KOMMUNEN_KEYWORDS = {
    "bergisch-gladbach": [
        "bergisch gladbach", "bensberg", "refrath", "paffrath", "gronau",
        "hand", "schildgen", "frankenforst", "moitzfeld", "herkenrath"
    ],
    "burscheid": ["burscheid", "hilgen"],
    "kuerten": ["kürten", "kuerten", "bechen", "dürscheid", "olpe", "biesfeld"],
    "leichlingen": ["leichlingen", "witzhelden"],
    "odenthal": ["odenthal", "altenberg", "blecher"],
    "overath": ["overath", "marialinden", "steinenbrück", "heiligenhaus"],
    "roesrath": ["rösrath", "roesrath", "hoffnungsthal", "forsbach"],
    "wermelskirchen": ["wermelskirchen", "dhünn", "dabringhausen"],
}

def classify_article(title: str, summary: str) -> list[str]:
    """Ordnet einen Artikel einer oder mehreren Kommunen zu."""
    text = (title + " " + summary).lower()
    matches = []
    for slug, keywords in KOMMUNEN_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                matches.append(slug)
                break
    return matches if matches else ["kreisweite-nachrichten"]

def article_id(entry) -> str:
    """Erzeugt eine stabile ID für Deduplizierung."""
    raw = entry.get("link", "") + entry.get("title", "")
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def fetch_all():
    config = json.loads(FEEDS_JSON.read_text())
    all_articles = {}  # id -> article dict

    for feed_cfg in config["feeds"]:
        url = feed_cfg["url"]
        name = feed_cfg["name"]
        print(f"Fetching: {name} ({url})")

        try:
            d = feedparser.parse(url)
            print(f"  -> {len(d.entries)} Einträge")
        except Exception as e:
            print(f"  FEHLER: {e}")
            continue

        for entry in d.entries:
            aid = article_id(entry)
            if aid in all_articles:
                continue

            title = entry.get("title", "Ohne Titel")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            published = entry.get("published", "")

            kommunen = classify_article(title, summary)

            all_articles[aid] = {
                "id": aid,
                "title": title,
                "summary": summary[:500],
                "link": link,
                "published": published,
                "source": name,
                "kommunen": kommunen,
                "fetched": datetime.now().isoformat(),
            }

    # Speichere je Kommune
    for slug in list(KOMMUNEN_KEYWORDS.keys()) + ["kreisweite-nachrichten"]:
        kommune_articles = [
            a for a in all_articles.values() if slug in a["kommunen"]
        ]
        kommune_articles.sort(key=lambda x: x.get("published", ""), reverse=True)

        outdir = BASE / slug
        outdir.mkdir(exist_ok=True)
        outfile = outdir / "articles.json"
        outfile.write_text(json.dumps(kommune_articles, ensure_ascii=False, indent=2))
        print(f"{slug}: {len(kommune_articles)} Artikel")

    # Gesamtübersicht
    all_list = sorted(all_articles.values(), key=lambda x: x.get("published", ""), reverse=True)
    (BASE / "all_articles.json").write_text(json.dumps(all_list, ensure_ascii=False, indent=2))
    print(f"\nGesamt: {len(all_list)} Artikel")

if __name__ == "__main__":
    fetch_all()
