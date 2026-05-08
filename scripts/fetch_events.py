#!/usr/bin/env python3
"""
Veranstaltungs-Extraktor für die AI Tageszeitung.

Strategie:
  RBK + Oberberg: Event-Artikel aus vorhandenen all_articles.json filtern
  Köln:           Eigene Feeds laden (in koeln/feeds.json konfiguriert)

Ergebnis: docs/veranstaltungen/{region}.json
"""
import json
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from email.utils import parsedate_to_datetime

try:
    import feedparser
except ImportError:
    print("feedparser nicht installiert. Bitte: pip install feedparser")
    sys.exit(1)

from config import BASE, KREISE

DOCS = BASE / "docs"
EVT_DIR = DOCS / "veranstaltungen"
EVT_DIR.mkdir(parents=True, exist_ok=True)

# Keywords: Artikel die dieses Wort im Titel ODER Teaser haben → Veranstaltung
EVENT_KEYWORDS = [
    "veranstaltung", "konzert", "ausstellung", "vortrag", "führung", "festival",
    "markt", "messe", "workshop", "kurs", "seminar", "treffen", "feier", "fest",
    "premiere", "lesung", "turnier", "lauf", "wanderung", "radtour",
    "tag der offenen", "infoabend", "info-abend", "informationsabend",
    "lädt ein", "findet statt", "findet am", "eingeladen", "besichtigung",
    "aufführung", "theaterst", "musikabend", "bürgerversamml", "stadtführung",
    "spaziergang", "flohhmarkt", "flohmarkt", "weihnachtsmarkt", "jahrmarkt",
    "sportveranstaltung", "vereinsfest", "sommerfest", "frühlingsfest",
    "dorfgemeinschaft", "kulturabend", "öffentliche sitzung",
]

def is_event(article: dict) -> bool:
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    return any(kw in text for kw in EVENT_KEYWORDS)

def parse_date(raw: str):
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', raw)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                            tzinfo=timezone.utc)
        except Exception:
            pass
    return None

def format_datum(dt) -> str:
    if dt is None:
        return ""
    MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
              "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    return f"{dt.day}. {MONATE[dt.month - 1]} {dt.year}"

def article_to_event(a: dict) -> dict:
    dt = parse_date(a.get("published", ""))
    return {
        "titel":  a.get("title", ""),
        "datum":  format_datum(dt),
        "datum_raw": a.get("published", ""),
        "ort":    "",
        "link":   a.get("link", "#"),
        "quelle": a.get("source", ""),
        "teaser": a.get("summary", "")[:200],
    }

def extract_from_articles(region_slug: str, all_articles_path: Path) -> list:
    if not all_articles_path.exists():
        print(f"  SKIP {region_slug}: {all_articles_path} nicht gefunden")
        return []
    articles = json.loads(all_articles_path.read_text())
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=14)
    events = []
    for a in articles:
        if not is_event(a):
            continue
        dt = parse_date(a.get("published", ""))
        # Nur aktuelle (letzte 14 Tage) oder zukünftige Artikel
        if dt and dt < cutoff:
            continue
        events.append(article_to_event(a))
    # Nach Datum sortieren, neueste zuerst
    events.sort(key=lambda x: x.get("datum_raw", ""), reverse=True)
    print(f"  {region_slug}: {len(events)} Veranstaltungsartikel (von {len(articles)} gesamt)")
    return events

def fetch_koeln() -> list:
    feeds_file = BASE / "koeln" / "feeds.json"
    if not feeds_file.exists():
        print("  köln: keine feeds.json – übersprungen")
        return []
    config = json.loads(feeds_file.read_text())
    ctx = ssl.create_default_context()
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=14)
    events = []
    seen = set()
    for feed_cfg in config.get("feeds", []):
        url  = feed_cfg["url"]
        name = feed_cfg["name"]
        print(f"  Fetching Köln: {name}")
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 AI-Tageszeitung/1.0",
                "Accept": "application/rss+xml, application/xml, */*",
            })
            resp = urllib.request.urlopen(req, timeout=20, context=ctx)
            d = feedparser.parse(resp.read())
            for entry in d.entries:
                link = entry.get("link", "")
                if link in seen:
                    continue
                seen.add(link)
                title   = entry.get("title", "")
                summary = re.sub(r'<[^>]+>', '', entry.get("summary", ""))
                text = (title + " " + summary).lower()
                if not any(kw in text for kw in EVENT_KEYWORDS):
                    continue
                published = entry.get("published", "")
                dt = parse_date(published)
                if dt and dt < cutoff:
                    continue
                events.append({
                    "titel":     title,
                    "datum":     format_datum(dt),
                    "datum_raw": published,
                    "ort":       "",
                    "link":      link,
                    "quelle":    name,
                    "teaser":    summary[:200],
                })
            print(f"    -> {len(d.entries)} Einträge gelesen")
        except Exception as e:
            print(f"    FEHLER: {e}")
    events.sort(key=lambda x: x.get("datum_raw", ""), reverse=True)
    print(f"  köln: {len(events)} Veranstaltungsartikel")
    return events

def save(slug: str, events: list):
    path = EVT_DIR / f"{slug}.json"
    path.write_text(json.dumps(events, ensure_ascii=False, indent=2))
    print(f"  -> {path.relative_to(BASE)} ({len(events)} Einträge)")

if __name__ == "__main__":
    print("\n=== Veranstaltungen: RBK ===")
    rbk = extract_from_articles("rbk", BASE / "rheinisch-bergischer-kreis" / "all_articles.json")
    save("rbk", rbk)

    print("\n=== Veranstaltungen: Oberberg ===")
    ob = extract_from_articles("oberberg", BASE / "oberbergischer-kreis" / "all_articles.json")
    save("oberberg", ob)

    print("\n=== Veranstaltungen: Köln ===")
    koeln = fetch_koeln()
    save("koeln", koeln)

    print("\nFertig!")
