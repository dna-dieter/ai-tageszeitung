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
from datetime import datetime
from pathlib import Path

try:
    import feedparser
    import urllib.request
    import ssl
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

ALL_SLUGS = list(KOMMUNEN_KEYWORDS.keys()) + ["kreisweite-nachrichten"]

def strip_html(text: str) -> str:
    """Entfernt HTML-Tags aus Text."""
    clean = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', clean).strip()

def classify_article(title: str, summary: str, feed_coverage: str) -> list[str]:
    """Ordnet einen Artikel Kommunen zu.

    1. Wenn der Feed eine spezifische Kommune hat (nicht kreisweite-nachrichten),
       wird diese immer zugewiesen.
    2. Zusätzlich Keyword-Matching im Text.
    """
    matches = set()

    # Feed-Coverage direkt zuweisen (wenn kommune-spezifisch)
    if feed_coverage and feed_coverage != "kreisweite-nachrichten":
        matches.add(feed_coverage)

    # Keyword-Matching
    text = (title + " " + summary).lower()
    for slug, keywords in KOMMUNEN_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                matches.add(slug)
                break

    return list(matches) if matches else ["kreisweite-nachrichten"]

def article_id(entry) -> str:
    """Erzeugt eine stabile ID für Deduplizierung."""
    raw = entry.get("link", "") + entry.get("title", "")
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def fetch_all():
    config = json.loads(FEEDS_JSON.read_text())
    all_articles = {}  # id -> article dict

    # SSL-Kontext ohne strenge Verifikation (manche lokale Seiten haben Probleme)
    ctx = ssl.create_default_context()

    for feed_cfg in config["feeds"]:
        url = feed_cfg["url"]
        name = feed_cfg["name"]
        coverage = feed_cfg.get("coverage", "kreisweite-nachrichten")
        print(f"Fetching: {name} ({url})")

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 AI-Tageszeitung/1.0",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            })
            response = urllib.request.urlopen(req, timeout=20, context=ctx)
            raw = response.read()
            d = feedparser.parse(raw)
            count = len(d.entries)
            print(f"  -> {count} Einträge")
            if count == 0 and d.bozo:
                print(f"  WARNUNG: Feed-Parse-Fehler: {d.bozo_exception}")
        except Exception as e:
            print(f"  FEHLER: {e}")
            continue

        for entry in d.entries:
            aid = article_id(entry)
            if aid in all_articles:
                # Merge: zusätzliche Kommune zuweisen
                existing = all_articles[aid]
                new_kommunen = classify_article(
                    entry.get("title", ""), entry.get("summary", ""), coverage
                )
                for k in new_kommunen:
                    if k not in existing["kommunen"]:
                        existing["kommunen"].append(k)
                continue

            title = entry.get("title", "Ohne Titel")
            summary = strip_html(entry.get("summary", ""))
            link = entry.get("link", "")
            published = entry.get("published", "")

            kommunen = classify_article(title, summary, coverage)

            all_articles[aid] = {
                "id": aid,
                "title": title,
                "summary": summary[:400],
                "link": link,
                "published": published,
                "source": name,
                "kommunen": kommunen,
                "fetched": datetime.now().isoformat(),
            }

    # Speichere je Kommune
    for slug in ALL_SLUGS:
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

    config["last_updated"] = datetime.now().isoformat()
    FEEDS_JSON.write_text(json.dumps(config, ensure_ascii=False, indent=2))

    print(f"\nGesamt: {len(all_list)} Artikel")

if __name__ == "__main__":
    fetch_all()
