#!/usr/bin/env python3
"""
RSS-Feed-Fetcher für die AI Tageszeitung.
Arbeitet alle Kreise aus config.py ab.
Behält bestehende Artikel, fügt nur neue hinzu.
"""
import html
import json
import hashlib
import re
import subprocess
import sys
import ssl
import urllib.request
from datetime import datetime
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlparse

try:
    import feedparser
except ImportError:
    print("feedparser nicht installiert. Bitte: pip install feedparser")
    sys.exit(1)

from config import BASE, KREISE

def strip_html(text: str) -> str:
    clean = re.sub(r'<[^>]+>', '', text or "")
    clean = html.unescape(clean)
    return re.sub(r'\s+', ' ', clean).strip()

def article_id(entry) -> str:
    raw = entry.get("link", "") + entry.get("title", "")
    return hashlib.md5(raw.encode()).hexdigest()[:12]

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Wörter, die in fast jeder Lokalüberschrift stehen und keine Geschichte identifizieren.
STOPWORDS = {
    "bergisch", "gladbach", "stadt", "staedte", "kreis", "rhein", "neue", "neuer",
    "neues", "neuen", "woche", "wochen", "polizei", "einbruch", "einbrecher",
    "zeugen", "nach", "beim", "heute", "gestern", "morgen",
}

def fetch_bytes(url: str, ctx) -> bytes:
    """RSS laden. Manche Portale (in-gl.de) antworten Python mit 403, curl kommt durch."""
    req = urllib.request.Request(url, headers={
        "User-Agent": BROWSER_UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        "Accept-Language": "de-DE,de;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=25, context=ctx) as response:
            return response.read()
    except Exception as first_error:
        code = getattr(first_error, "code", None)
        if code not in (403, 429, 503) and "403" not in str(first_error) and "503" not in str(first_error):
            raise
        try:
            return subprocess.check_output(
                ["curl", "-fsSL", "--compressed", "-A", BROWSER_UA, "--max-time", "30", url],
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            raise first_error

BERLIN = ZoneInfo("Europe/Berlin")

def sort_key(article: dict):
    """Echtes Veröffentlichungsdatum (Ortszeit Berlin) zum Sortieren; ohne Datum ganz hinten."""
    return parse_date(article.get("published", "")) or datetime.min

def parse_date(raw: str):
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is not None:
            dt = dt.astimezone(BERLIN)
        return dt.replace(tzinfo=None)
    except Exception:
        pass
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?", raw)
    if not m:
        return None
    try:
        return datetime(
            int(m.group(1)), int(m.group(2)), int(m.group(3)),
            int(m.group(4) or 0), int(m.group(5) or 0), int(m.group(6) or 0),
        )
    except Exception:
        return None

def canonical_url(url: str) -> str:
    try:
        parts = urlparse((url or "").strip())
    except Exception:
        return (url or "").strip().lower()
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path.rstrip("/") or "/"
    return host + path

def story_slug(url: str) -> str:
    path = urlparse(url or "").path
    path = re.sub(r"/\d{4}/\d{2}/\d{2}/", "/", path)
    return path.strip("/").split("/")[-1]

def norm_text(text: str) -> str:
    text = html.unescape(text or "").lower()
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def content_tokens(title: str) -> list:
    tokens = []
    for word in norm_text(title).split():
        if len(word) < 5 or word in STOPWORDS:
            continue
        if len(word) > 6 and word.endswith("es"):
            word = word[:-2]
        elif len(word) > 5 and word.endswith("s"):
            word = word[:-1]
        tokens.append(word)
    return tokens

def source_rank(article: dict) -> int:
    source = article.get("source", "").lower()
    if "bürgerportal" in source or "buergerportal" in source:
        return 800
    if source.endswith("politik") or source.endswith("kultur"):
        return 550
    if "stadt-anzeiger" in source or source.startswith("rga"):
        return 400
    if "gl aktuell" in source:
        return 250
    if "stadt bergisch" in source:
        return 120
    if "polizei" in source or "feuerwehr" in source:
        return 0
    return 180

def article_quality(article: dict) -> tuple:
    return (source_rank(article), min(len(article.get("summary") or ""), 400))

def same_story(a: dict, b: dict) -> bool:
    if canonical_url(a.get("link", "")) == canonical_url(b.get("link", "")):
        return True
    slug_a, slug_b = story_slug(a.get("link", "")), story_slug(b.get("link", ""))
    # Dieselbe WordPress-Meldung, nur mit neuem Datum im Pfad erneut veröffentlicht.
    if len(slug_a) >= 28 and slug_a == slug_b:
        return True
    # Kurze, wiederkehrende Pfade („wort“, „wort-2“) sind Rubriken, keine Dubletten.
    if min(len(slug_a), len(slug_b)) <= 24:
        return False
    date_a, date_b = parse_date(a.get("published", "")), parse_date(b.get("published", ""))
    if date_a and date_b and abs((date_a - date_b).days) > 6:
        return False
    title_a, title_b = norm_text(a.get("title", "")), norm_text(b.get("title", ""))
    if len(title_a) < 18 or len(title_b) < 18:
        return False
    ratio = SequenceMatcher(None, title_a, title_b).ratio()
    if title_a == title_b:
        return True
    tokens_a = content_tokens(a.get("title", ""))
    tokens_b = content_tokens(b.get("title", ""))
    shared = set(tokens_a) & set(tokens_b)
    long_shared = [token for token in shared if len(token) >= 8]
    shorter = min(len(tokens_a), len(tokens_b)) or 1
    containment = len(shared) / shorter
    # Polizeimeldungen zum selben Delikttyp sind oft verschiedene Taten.
    both_blotter = all(
        any(word in (article.get("source") or "").lower() for word in ("polizei", "feuerwehr"))
        for article in (a, b)
    )
    if both_blotter:
        return ratio >= 0.93
    if ratio >= 0.88 and long_shared:
        return True
    return ratio >= 0.68 and len(long_shared) >= 2 and containment >= 0.5

def dedupe_articles(articles: dict) -> int:
    """Gleiche Geschichte aus mehreren Quellen auf den gehaltvolleren Beitrag reduzieren."""
    ids = list(articles.keys())
    parent = {aid: aid for aid in ids}

    def find(aid):
        while parent[aid] != aid:
            parent[aid] = parent[parent[aid]]
            aid = parent[aid]
        return aid

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    by_url = {}
    by_slug = {}
    for aid, article in articles.items():
        url_key = canonical_url(article.get("link", ""))
        if url_key:
            if url_key in by_url:
                union(aid, by_url[url_key])
            else:
                by_url[url_key] = aid
        slug = story_slug(article.get("link", ""))
        if len(slug) >= 28:
            if slug in by_slug:
                union(aid, by_slug[slug])
            else:
                by_slug[slug] = aid

    dated = []
    for aid, article in articles.items():
        moment = parse_date(article.get("published", ""))
        if moment:
            dated.append((moment, aid))
    dated.sort()
    for index, (moment, aid) in enumerate(dated):
        for other_moment, other in dated[index + 1:]:
            if (other_moment - moment).days > 8:
                break
            if find(aid) == find(other):
                continue
            if same_story(articles[aid], articles[other]):
                union(aid, other)

    clusters = {}
    for aid in ids:
        clusters.setdefault(find(aid), []).append(aid)

    removed = 0
    for members in clusters.values():
        if len(members) < 2:
            continue
        winner = max(members, key=lambda aid: article_quality(articles[aid]))
        kept = articles[winner]
        kommunen = list(kept.get("kommunen") or [])
        for aid in members:
            if aid == winner:
                continue
            for kommune in articles[aid].get("kommunen") or []:
                if kommune not in kommunen:
                    kommunen.append(kommune)
            del articles[aid]
            removed += 1
        kept["kommunen"] = kommunen
    return removed

_KW_CACHE = {}

def keyword_regex(kw: str):
    """Schlagwort als Regex: Treffer nur am Wortanfang (z. B. „Kürtener“ zu „kürten“).
    Beginnt das Schlagwort mit „=“, muss das ganze Wort passen (z. B. „=olpe“ trifft
    Olpe, aber nicht „Stolpersteine“ oder „Olper Straße“). \\b ist in Python
    Unicode-fähig, Umlaute und ß zählen als Buchstaben."""
    if kw not in _KW_CACHE:
        exact = kw.startswith("=")
        body = re.escape(kw[1:] if exact else kw)
        _KW_CACHE[kw] = re.compile(r"(?<!\w)" + body + (r"(?!\w)" if exact else ""))
    return _KW_CACHE[kw]

def classify_article(title: str, summary: str, feed_coverage: str, keywords: dict) -> list:
    matches = set()
    if feed_coverage and feed_coverage != "kreisweite-nachrichten":
        matches.add(feed_coverage)
    text = (title + " " + summary).lower()
    for slug, kws in keywords.items():
        for kw in kws:
            if keyword_regex(kw).search(text):
                matches.add(slug)
                break
    return list(matches) if matches else ["kreisweite-nachrichten"]

# Schlagwörter, die bis Oktober 2026 als Teilwort zählten und entfernt wurden.
LEGACY_KEYWORDS = {"bergisch-gladbach": ["hand"]}

def reclassify_all(articles: dict, feeds: list, keywords: dict) -> int:
    """Gemeinden aller Artikel neu berechnen: Feed-Herkunft + Schlagwörter.
    Feed-Herkunft = Coverage der eigenen Quelle plus aller Feeds, in denen der Artikel
    sonst noch auftauchte (Feld „feed_kommunen“). Für Altdaten ohne dieses Feld bleibt
    eine Gemeinde erhalten, wenn ein gemeindespezifischer Feed desselben Anbieters
    (z. B. „RGA …“) sie abdeckt – dieselbe Meldung steht dort oft in mehreren Ortsfeeds."""
    coverage_by_source = {f["name"]: f.get("coverage", "kreisweite-nachrichten") for f in feeds}
    anbieter_cov = {}
    for f in feeds:
        cov = f.get("coverage", "kreisweite-nachrichten")
        if cov != "kreisweite-nachrichten":
            anbieter_cov.setdefault(f["name"].split()[0], set()).add(cov)
    changed = 0
    for article in articles.values():
        source = article.get("source", "")
        own = coverage_by_source.get(source)
        neu = set(classify_article(article.get("title", ""), article.get("summary", ""), own, keywords))
        herkunft = set(article.get("feed_kommunen") or [])
        if "feed_kommunen" not in article and own and own != "kreisweite-nachrichten":
            moeglich = anbieter_cov.get(source.split()[0] if source else "", set())
            herkunft = {k for k in article.get("kommunen") or [] if k in moeglich}
        neu |= herkunft
        # Bisherige Gemeinden nur entfernen, wenn belegbar falsch: der alte Teilwort-Treffer
        # steckt im gespeicherten Text, die neue Wortgrenzen-Regel verwirft ihn. Treffer,
        # die aus dem (beim Abruf längeren) Originaltext stammen, bleiben erhalten.
        text = (article.get("title", "") + " " + article.get("summary", "")).lower()
        for k in article.get("kommunen") or []:
            if k in neu or k == "kreisweite-nachrichten":
                continue
            alt_treffer = any(kw.lstrip("=") in text for kw in keywords.get(k, []) + LEGACY_KEYWORDS.get(k, []))
            if not alt_treffer:
                neu.add(k)
        if len(neu) > 1:
            neu.discard("kreisweite-nachrichten")
        neu = sorted(neu)
        if neu != sorted(article.get("kommunen") or []):
            article["kommunen"] = neu
            changed += 1
    return changed

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
        return 0, 0

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

    failed = active = 0
    for feed_cfg in config["feeds"]:
        if feed_cfg.get("enabled") is False:
            print(f"  Übersprungen: {feed_cfg['name']}")
            continue
        active += 1
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
                raw = fetch_bytes(page_url, ctx)
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
        if len(all_entries) == 0:
            failed += 1
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
                if coverage != "kreisweite-nachrichten":
                    fk = existing.setdefault("feed_kommunen", [])
                    if coverage not in fk:
                        fk.append(coverage)
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
                "feed_kommunen": [coverage] if coverage != "kreisweite-nachrichten" else [],
            }
            new_count += 1

    # Bestand mit der aktuellen Logik neu zuordnen (Feed-Herkunft + Schlagwörter),
    # damit alte Fehlzuordnungen verschwinden. Es werden keine Artikel entfernt.
    changed = reclassify_all(all_articles, config["feeds"], keywords)
    if changed:
        print(f"  Neu zugeordnet: {changed}")

    removed = dedupe_articles(all_articles)
    if removed:
        print(f"  Duplikate entfernt: {removed}")

    # Speichere je Kommune
    for slug in all_slugs:
        arts = sorted(
            [a for a in all_articles.values() if slug in a["kommunen"]],
            key=sort_key, reverse=True
        )
        outdir = data_dir / slug
        outdir.mkdir(exist_ok=True)
        (outdir / "articles.json").write_text(json.dumps(arts, ensure_ascii=False, indent=2))
        print(f"  {slug}: {len(arts)} Artikel")

    all_list = sorted(all_articles.values(), key=sort_key, reverse=True)
    (data_dir / "all_articles.json").write_text(json.dumps(all_list, ensure_ascii=False, indent=2))

    if new_count or changed or removed or "last_updated" not in config:
        config["last_updated"] = datetime.now(BERLIN).isoformat()
    feeds_file.write_text(json.dumps(config, ensure_ascii=False, indent=2))

    print(f"  Gesamt: {len(all_list)} Artikel ({new_count} neu)")
    print(f"  Feeds ohne Antwort: {failed}/{active}")
    return failed, active

if __name__ == "__main__":
    total_failed = total_active = 0
    for slug, cfg in KREISE.items():
        f, a = fetch_kreis(slug, cfg)
        total_failed += f
        total_active += a
    if total_active and total_failed * 2 > total_active:
        print(f"FEHLER: Mehrheit der Feeds ausgefallen ({total_failed}/{total_active})")
        sys.exit(1)
