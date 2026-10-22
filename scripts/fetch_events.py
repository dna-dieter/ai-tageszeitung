#!/usr/bin/env python3
"""
Veranstaltungs-Extraktor für die AI Tageszeitung.

Strategie:
  RBK + Oberberg: Terminkalender „Das Bergische“ (destination.one)
  Köln:           Rausgegangen, JSON-LD

Ergebnis: docs/veranstaltungen/{region}.json
"""
import json
import os
import re
import ssl
import sys
import urllib.parse
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

# Öffentlicher Kalender von dasbergische.de. Der Lizenzschlüssel kommt aus der
# Umgebungsvariable BERG_LICENSE (GitHub-Secret), er steht nicht im Code.
BERG_API = "https://meta.et4.de/rest.ashx/search/"
BERG_EXPERIENCE = "dasbergische-web"
BERG_LICENSE = os.environ.get("BERG_LICENSE", "").strip()
BERG_HORIZON_DAYS = 120

RBK_CITIES = [
    "Bergisch Gladbach", "Burscheid", "Kürten", "Leichlingen",
    "Odenthal", "Overath", "Rösrath", "Wermelskirchen",
]
OBERBERG_CITIES = [
    "Bergneustadt", "Engelskirchen", "Gummersbach", "Hückeswagen",
    "Lindlar", "Marienheide", "Morsbach", "Nümbrecht",
    "Radevormwald", "Reichshof", "Waldbröl", "Wiehl", "Wipperfürth",
]
WEEKDAY = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
}

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

def _parse_iso(raw: str):
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def next_occurrence(intervals: list, now: datetime, horizon: datetime):
    """Nächster Termin eines Kalendereintrags innerhalb des Horizonts."""
    best = None
    grace = now - timedelta(hours=8)
    for iv in intervals or []:
        start = _parse_iso(iv.get("start"))
        if start is None:
            continue
        repeat_until = _parse_iso(iv.get("repeatUntil")) or start
        weekdays = [WEEKDAY[d] for d in (iv.get("weekdays") or []) if d in WEEKDAY]
        weekly = weekdays and iv.get("freq") == "Weekly" and repeat_until >= grace
        candidate = None
        if weekly:
            day = max(grace.date(), start.date())
            last = min(horizon.date(), repeat_until.date())
            while day <= last:
                if day.weekday() in weekdays:
                    candidate = datetime.combine(day, start.timetz())
                    if candidate >= grace:
                        break
                    candidate = None
                day += timedelta(days=1)
        elif grace <= start <= horizon:
            candidate = start
        if candidate and (best is None or candidate < best):
            best = candidate
    return best

def _plain(item: dict) -> str:
    for text in item.get("texts") or []:
        if text.get("type") == "text/plain" and text.get("value"):
            raw = text["value"]
            break
    else:
        raw = ""
        for text in item.get("texts") or []:
            if text.get("value"):
                raw = text["value"]
                break
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw[:220]

def _price(item: dict) -> str:
    for number in item.get("numbers") or []:
        if number.get("type") != "PRICE_ADULT":
            continue
        try:
            value = float(number.get("value"))
        except (TypeError, ValueError):
            return ""
        if value <= 0:
            return "kostenlos"
        return f"ab {value:.0f} €"
    return ""

def _preis_aus(price_raw: str) -> str:
    """Preis nur angeben, wenn er belegt ist: 0 = kostenlos, fehlend = leer (Anzeige: Preis k.A.)."""
    if price_raw in ("", "None"):
        return ""
    try:
        wert = float(price_raw.replace(",", "."))
    except ValueError:
        return ""
    return "kostenlos" if wert <= 0 else f"ab {wert:.0f} €"

def _place(item: dict) -> str:
    city = item.get("city") or ""
    parts = [item.get("name") or "", item.get("street") or ""]
    tail = " ".join(p for p in [item.get("zip") or "", city] if p)
    if tail:
        parts.append(tail)
    seen = []
    for part in parts:
        part = part.strip()
        if part and part not in seen:
            seen.append(part)
    return ", ".join(seen)

def berg_item_to_event(item: dict, when: datetime) -> dict:
    web = (item.get("web") or "").strip()
    link = web if web.startswith("http") else "https://www.dasbergische.de/aktivitaeten/veranstaltungen"
    return {
        "titel": item.get("title") or "",
        "datum": format_datum(when),
        "datum_raw": when.isoformat(),
        "ort": _place(item),
        "preis": _price(item),
        "link": link,
        "quelle": "Das Bergische",
        "teaser": _plain(item),
    }

def fetch_bergische(cities: list, limit: int = 40) -> list:
    """Kommende Termine aus dem Kalender von dasbergische.de."""
    quoted = " OR ".join(f'"{city}"' for city in cities)
    query = f"(type:(Event) AND city_exact:({quoted}))"
    now = datetime.now(timezone.utc).astimezone()
    horizon = now + timedelta(days=BERG_HORIZON_DAYS)
    def stamp(moment: datetime, clock: str) -> str:
        offset = moment.strftime("%z")
        return moment.strftime(f"%Y-%m-%dT{clock}") + offset[:3] + ":" + offset[3:]

    params = {
        "experience": BERG_EXPERIENCE,
        "licensekey": BERG_LICENSE,
        "template": "ET2014A.json",
        "mkt": "de",
        "limit": "80",
        "sort": "start asc",
        "startdate": stamp(now, "00:00:00"),
        "enddate": stamp(horizon, "23:59:00"),
        "q": query,
    }
    url = BERG_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": RAUSGEGANGEN_UA,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=40) as response:
        data = json.load(response)
    events = []
    seen = set()
    for item in data.get("items") or []:
        when = next_occurrence(item.get("timeIntervals"), now, horizon)
        if when is None:
            continue
        title = (item.get("title") or "").strip()
        key = (title.lower(), item.get("city"), when.date().isoformat())
        if not title or key in seen:
            continue
        seen.add(key)
        events.append(berg_item_to_event(item, when))
    events.sort(key=lambda event: event.get("datum_raw", ""))
    print(f"  Kalender: {len(events)} Termine (API {data.get('overallcount', '?')} Treffer)")
    return events[:limit]

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
                    price     = _preis_aus(price_raw)
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

def save_or_keep(slug: str, events: list):
    """Leere Ergebnisse überschreiben einen vorhandenen Kalender nicht."""
    path = EVT_DIR / f"{slug}.json"
    if not events and path.exists():
        try:
            old = json.loads(path.read_text())
        except Exception:
            old = []
        if old:
            print(f"  -> behalte {path.name} ({len(old)} vorhandene Einträge)")
            return
    save(slug, events)

if __name__ == "__main__":
    for slug, label, cities in (("rbk", "RBK", RBK_CITIES), ("oberberg", "Oberberg", OBERBERG_CITIES)):
        print(f"\n=== Veranstaltungen: {label} ===")
        if not BERG_LICENSE:
            print(f"::warning::BERG_LICENSE nicht gesetzt - Abruf Das Bergische ({label}) übersprungen, vorhandene Daten bleiben.")
            continue
        try:
            events = fetch_bergische(cities)
        except Exception as exc:
            print(f"  FEHLER {label}: {type(exc).__name__}")
            events = []
        save_or_keep(slug, events)

    print("\n=== Veranstaltungen: Köln ===")
    try:
        koeln = fetch_koeln()
    except Exception as exc:
        print(f"  FEHLER Köln: {exc}")
        koeln = []
    save_or_keep("koeln", koeln)

    print("\nFertig!")
