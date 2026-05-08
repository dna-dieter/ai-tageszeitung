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

RAUSGEGANGEN_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

def _rg_get(url: str, ctx) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": RAUSGEGANGEN_UA,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "de-DE,de;q=0.9",
    })
    return urllib.request.urlopen(req, timeout=15, context=ctx).read()

def scrape_rausgegangen_koeln(max_events: int = 40) -> list:
    """Scrapet rausgegangen.de/cologne/eventsbydate/ via JSON-LD."""
    ctx = ssl.create_default_context()
    events = []
    seen = set()

    # Hauptseite + alle relevanten Kategorien
    urls_to_try = [
        "https://rausgegangen.de/cologne/eventsbydate/",
        "https://rausgegangen.de/cologne/kategorie/konzerte-und-musik/",
        "https://rausgegangen.de/cologne/kategorie/feste-und-festival/",
        "https://rausgegangen.de/cologne/kategorie/markt/",
        "https://rausgegangen.de/cologne/kategorie/ausstellung/",
        "https://rausgegangen.de/cologne/kategorie/aktiv-und-kreativ/",
        "https://rausgegangen.de/cologne/kategorie/food-und-drinks/",
        "https://rausgegangen.de/cologne/kategorie/kinder-und-familien/",
        "https://rausgegangen.de/cologne/kategorie/shows-und-performances/",
        "https://rausgegangen.de/cologne/kategorie/party/",
    ]

    event_urls = []
    for page_url in urls_to_try:
        try:
            html = _rg_get(page_url, ctx).decode("utf-8", errors="replace")
            jlds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
            for jld_raw in jlds:
                try:
                    d = json.loads(jld_raw)
                    if d.get("@type") == "ItemList":
                        for item in d.get("itemListElement", []):
                            u = item.get("url", "")
                            if u and u not in seen:
                                seen.add(u)
                                event_urls.append(u)
                except Exception:
                    pass
        except Exception as e:
            print(f"    Seite {page_url}: {e}")

    print(f"  Köln: {len(event_urls)} Event-URLs gefunden, lade Details...")

    import time
    for evt_url in event_urls[:max_events]:
        try:
            html = _rg_get(evt_url, ctx).decode("utf-8", errors="replace")
            jlds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
            for jld_raw in jlds:
                try:
                    d = json.loads(jld_raw)
                    if d.get("@type") != "Event":
                        continue
                    name      = d.get("name", "")
                    desc      = re.sub(r'<[^>]+>', '', d.get("description", ""))[:220]
                    start     = d.get("startDate", "")
                    location  = d.get("location", {})
                    place     = location.get("name", "")
                    addr      = location.get("address", {})
                    ort_parts = [p for p in [place, addr.get("streetAddress",""), addr.get("addressLocality","")] if p]
                    ort       = ", ".join(ort_parts[:2])  # Name + Straße
                    offers    = d.get("offers", {})
                    price_raw = str(offers.get("price", ""))
                    price     = f"ab {float(price_raw):.0f} €" if price_raw and price_raw != "0" else "kostenlos"
                    # Datum formatieren
                    dt = None
                    if start:
                        try:
                            dt = datetime.fromisoformat(start)
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                        except Exception:
                            pass
                    events.append({
                        "titel":     name,
                        "datum":     format_datum(dt),
                        "datum_raw": start,
                        "ort":       ort,
                        "preis":     price,
                        "link":      evt_url,
                        "quelle":    "Rausgegangen Köln",
                        "teaser":    desc,
                    })
                    break
                except Exception:
                    pass
            time.sleep(0.3)  # sanftes Throttling
        except Exception as e:
            print(f"    FEHLER {evt_url}: {e}")

    events.sort(key=lambda x: x.get("datum_raw", ""))
    print(f"  Köln: {len(events)} Veranstaltungen geladen")
    return events

def fetch_koeln() -> list:
    return scrape_rausgegangen_koeln(max_events=40)

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
