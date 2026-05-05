#!/usr/bin/env python3
"""
Baut alle HTML-Seiten für GitHub Pages aus den articles.json-Dateien.
Erzeugt: docs/index.html, docs/<kommune>/index.html
"""
import json
from pathlib import Path
from datetime import datetime
import html as htmlmod

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "rheinisch-bergischer-kreis"
DOCS = BASE / "docs"

KOMMUNEN = {
    "bergisch-gladbach": "Bergisch Gladbach",
    "burscheid": "Burscheid",
    "kuerten": "Kürten",
    "leichlingen": "Leichlingen",
    "odenthal": "Odenthal",
    "overath": "Overath",
    "roesrath": "Rösrath",
    "wermelskirchen": "Wermelskirchen",
}

TIMESTAMP = datetime.now().strftime("%d.%m.%Y, %H:%M")

CSS = """
:root {
  --rbk-blau: #1B3A5C;
  --rbk-rot: #C0392B;
  --rbk-grau: #F5F5F5;
  --akzent: #2980B9;
  --text: #2C3E50;
  --bg: #FAFAFA;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Georgia, 'Times New Roman', serif; color: var(--text); background: var(--bg); line-height: 1.6; }
header { background: var(--rbk-blau); color: white; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; }
header h1 { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 1.8rem; letter-spacing: 2px; font-weight: 800; }
header .sub { font-size: 0.9rem; opacity: 0.85; }
header .meta { font-size: 0.8rem; text-align: right; opacity: 0.9; }
.live-dot { display: inline-block; width: 8px; height: 8px; background: #2ECC71; border-radius: 50%; margin-right: 4px; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
.ticker { background: var(--rbk-rot); color: white; padding: 7px 24px; font-size: 0.85rem; font-family: sans-serif; }
.ticker b { margin-right: 8px; }
nav { background: white; border-bottom: 2px solid var(--rbk-blau); padding: 8px 24px; display: flex; flex-wrap: wrap; gap: 3px; }
nav a { font-family: sans-serif; font-size: 0.82rem; padding: 5px 12px; text-decoration: none; color: var(--rbk-blau); border-radius: 4px; transition: all 0.2s; }
nav a:hover, nav a.active { background: var(--rbk-blau); color: white; }
main { max-width: 1200px; margin: 20px auto; padding: 0 16px; }
.grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
.artikel { background: white; border-radius: 6px; padding: 16px 18px; border-left: 4px solid var(--akzent); box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 14px; transition: box-shadow 0.2s; }
.artikel:hover { box-shadow: 0 3px 12px rgba(0,0,0,0.12); }
.artikel .tag { font-family: sans-serif; font-size: 0.72rem; font-weight: 700; color: var(--rbk-rot); text-transform: uppercase; letter-spacing: 1px; }
.artikel h2 { font-size: 1.15rem; margin: 4px 0; line-height: 1.3; }
.artikel h2 a { color: var(--text); text-decoration: none; }
.artikel h2 a:hover { color: var(--akzent); }
.artikel .teaser { font-size: 0.9rem; color: #555; margin: 6px 0; }
.artikel .info { font-family: sans-serif; font-size: 0.75rem; color: #888; }
.sidebar-box { background: white; border-radius: 6px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 14px; }
.sidebar-box h3 { font-family: sans-serif; font-size: 0.85rem; color: var(--rbk-blau); border-bottom: 2px solid var(--rbk-blau); padding-bottom: 5px; margin-bottom: 10px; }
.k-links { list-style: none; }
.k-links li { margin: 6px 0; }
.k-links a { font-family: sans-serif; font-size: 0.85rem; color: var(--text); text-decoration: none; display: flex; justify-content: space-between; }
.k-links a:hover { color: var(--akzent); }
.badge { background: var(--rbk-grau); padding: 1px 8px; border-radius: 10px; font-size: 0.75rem; }
footer { background: var(--rbk-blau); color: white; text-align: center; padding: 16px; margin-top: 30px; font-size: 0.8rem; font-family: sans-serif; }
footer a { color: #85C1E9; }
.empty { text-align: center; padding: 40px; color: #999; font-size: 1.1rem; }
.monat-gruppe { margin-bottom: 8px; }
.monat-header { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 1.05rem; color: var(--rbk-blau); border-bottom: 2px solid var(--rbk-blau); padding: 8px 0 5px 0; margin: 18px 0 10px 0; display: flex; align-items: center; gap: 8px; }
.monat-header:first-child { margin-top: 0; }
.monat-count { background: var(--rbk-blau); color: white; font-size: 0.72rem; padding: 1px 8px; border-radius: 10px; font-weight: 400; }
.btn-refresh { display: inline-flex; align-items: center; gap: 5px; font-family: sans-serif; font-size: 0.78rem; padding: 5px 14px; background: #2ECC71; color: white; border: none; border-radius: 4px; text-decoration: none; cursor: pointer; transition: background 0.2s; }
.btn-refresh:hover { background: #27AE60; color: white; }
@media (max-width: 768px) { .grid { grid-template-columns: 1fr; } header h1 { font-size: 1.3rem; } }
"""

def load_articles(kommune_slug):
    f = DATA / kommune_slug / "articles.json"
    if f.exists():
        return json.loads(f.read_text())
    return []

def count_articles(slug):
    return len(load_articles(slug))

def nav_html(active_slug=None):
    alle_href = "index.html" if active_slug is None else "../index.html"
    links = [f'<a href="{alle_href}"' + (' class="active"' if active_slug is None else '') + '>Alle</a>']
    for slug, name in KOMMUNEN.items():
        cls = ' class="active"' if slug == active_slug else ''
        prefix = "../" if active_slug else ""
        href = f"{prefix}{slug}/index.html" if active_slug != slug else "index.html"
        if active_slug is None:
            href = f"{slug}/index.html"
        links.append(f'<a href="{href}"{cls}>{name}</a>')
    return "\n".join(links)

def strip_tags(text):
    """Entfernt HTML-Tags aus Text."""
    import re
    clean = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', clean).strip()

def artikel_html(a, show_kommune=True):
    title = htmlmod.escape(a.get("title", "Ohne Titel"))
    teaser = htmlmod.escape(strip_tags(a.get("summary", ""))[:250])
    link = htmlmod.escape(a.get("link", "#"))
    source = htmlmod.escape(a.get("source", ""))
    published = a.get("published", "")[:25]
    kommunen = ", ".join(KOMMUNEN.get(k, k) for k in a.get("kommunen", []))
    tag = f'<div class="tag">{htmlmod.escape(kommunen)}</div>' if show_kommune else ""
    return f"""<div class="artikel">
  {tag}
  <h2><a href="{link}" target="_blank" rel="noopener">{title}</a></h2>
  <div class="teaser">{teaser}</div>
  <div class="info">{published} · {source}</div>
</div>"""

def sidebar_html():
    items = []
    for slug, name in KOMMUNEN.items():
        c = count_articles(slug)
        items.append(f'<li><a href="{slug}/index.html">{name} <span class="badge">{c}</span></a></li>')
    return "\n".join(items)

def build_index():
    all_file = DATA / "all_articles.json"
    articles = json.loads(all_file.read_text()) if all_file.exists() else []

    if not articles:
        artikel_cards = '<div class="empty">Noch keine Artikel geladen. Bitte RSS-Fetcher ausführen.</div>'
    else:
        groups = group_by_month(articles)
        parts = []
        shown = 0
        for key, arts in groups.items():
            if shown >= 50:
                break
            if key == ("ohne", "datum"):
                label = "Ohne Datum"
            else:
                year, month = key
                label = f"{MONATE_DE.get(month, month)} {year}"
            parts.append(f'<div class="monat-gruppe">')
            parts.append(f'<h2 class="monat-header">{label} <span class="monat-count">{len(arts)}</span></h2>')
            for a in arts:
                if shown >= 50:
                    break
                parts.append(artikel_html(a))
                shown += 1
            parts.append('</div>')
        artikel_cards = "\n".join(parts)

    # Ticker: erste 3 Artikel
    ticker_items = " · ".join(htmlmod.escape(a["title"][:60]) for a in articles[:3]) or "Keine Eilmeldungen"

    page = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Tageszeitung — Rheinisch-Bergischer Kreis</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div>
    <h1>AI TAGESZEITUNG</h1>
    <div class="sub">Rheinisch-Bergischer Kreis</div>
  </div>
  <div class="meta">
    <div><span class="live-dot"></span>Stündlich aktualisiert</div>
    <div>{TIMESTAMP}</div>
    <a href="https://github.com/dna-dieter/ai-tageszeitung/actions/workflows/update.yml" target="_blank" rel="noopener" class="btn-refresh">&#x21bb; Jetzt aktualisieren</a>
  </div>
</header>
<div class="ticker"><b>AKTUELL:</b> {ticker_items}</div>
<nav>{nav_html()}</nav>
<main>
<div class="grid">
  <div>{artikel_cards}</div>
  <div>
    <div class="sidebar-box">
      <h3>Kommunen</h3>
      <ul class="k-links">{sidebar_html()}</ul>
    </div>
    <div class="sidebar-box">
      <h3>Quellen</h3>
      <div style="font-size:0.82rem; font-family:sans-serif; color:#666;">
        Kölner Stadt-Anzeiger · Kölnische Rundschau · Radio Berg · RheinBergNews · iGL Bürgerportal · Presseportal Polizei · Kreisverwaltung RBK
      </div>
    </div>
  </div>
</div>
</main>
<footer>
  AI Tageszeitung · Rheinisch-Bergischer Kreis · Aktualisiert: {TIMESTAMP}<br>
  Automatisch aus öffentlichen RSS-Quellen · <a href="https://github.com/dna-dieter/ai-tageszeitung">GitHub</a>
</footer>
</body></html>"""

    (DOCS / "index.html").write_text(page)
    print(f"docs/index.html: {len(articles)} Artikel")

MONATE_DE = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April",
    5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
    9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
}

def parse_pub_date(raw: str):
    """Versucht ein Datum aus dem published-String zu extrahieren."""
    from email.utils import parsedate_to_datetime
    import re
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    # Fallback: ISO-Format
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', raw)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass
    return None

def group_by_month(articles):
    """Gruppiert Artikel nach (Jahr, Monat), sortiert jüngste zuerst."""
    from collections import OrderedDict
    grouped = {}
    undated = []
    for a in articles:
        dt = parse_pub_date(a.get("published", ""))
        a["_dt"] = dt
        if dt:
            key = (dt.year, dt.month)
            grouped.setdefault(key, []).append(a)
        else:
            undated.append(a)
    # Sortiere Gruppen: jüngster Monat zuerst
    sorted_keys = sorted(grouped.keys(), reverse=True)
    # Sortiere Artikel innerhalb jeder Gruppe: jüngster zuerst
    result = OrderedDict()
    for key in sorted_keys:
        arts = sorted(grouped[key], key=lambda x: x["_dt"], reverse=True)
        result[key] = arts
    if undated:
        result[("ohne", "datum")] = undated
    return result

def build_kommune(slug, name):
    articles = load_articles(slug)
    kreisweite = load_articles("kreisweite-nachrichten")

    if not articles:
        artikel_cards = f'<div class="empty">Noch keine Artikel für {name}. Die RSS-Feeds werden regelmäßig abgefragt.</div>'
    else:
        groups = group_by_month(articles)
        parts = []
        for key, arts in groups.items():
            if key == ("ohne", "datum"):
                label = "Ohne Datum"
            else:
                year, month = key
                label = f"{MONATE_DE.get(month, month)} {year}"
            parts.append(f'<div class="monat-gruppe">')
            parts.append(f'<h2 class="monat-header">{label} <span class="monat-count">{len(arts)}</span></h2>')
            for a in arts:
                parts.append(artikel_html(a, show_kommune=False))
            parts.append('</div>')
        artikel_cards = "\n".join(parts)

    # Navigation relativ
    nav_links = [f'<a href="../index.html">Alle</a>']
    for s, n in KOMMUNEN.items():
        cls = ' class="active"' if s == slug else ''
        nav_links.append(f'<a href="../{s}/index.html"{cls}>{n}</a>')

    page = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — AI Tageszeitung</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div>
    <h1>{name}</h1>
    <div class="sub">AI Tageszeitung · Rheinisch-Bergischer Kreis</div>
  </div>
  <div class="meta">
    <div><span class="live-dot"></span>{len(articles)} Artikel</div>
    <div>{TIMESTAMP}</div>
    <a href="https://github.com/dna-dieter/ai-tageszeitung/actions/workflows/update.yml" target="_blank" rel="noopener" class="btn-refresh">&#x21bb; Jetzt aktualisieren</a>
  </div>
</header>
<nav>{"".join(nav_links)}</nav>
<main>
<div class="grid">
  <div>{artikel_cards}</div>
  <div>
    <div class="sidebar-box">
      <h3>Alle Kommunen</h3>
      <ul class="k-links">
        {"".join(f'<li><a href="../{s}/index.html">{n} <span class="badge">{count_articles(s)}</span></a></li>' for s, n in KOMMUNEN.items())}
      </ul>
    </div>
    <div class="sidebar-box">
      <h3>Kreisweite Nachrichten</h3>
      {"".join(f'<div style="font-size:0.85rem; margin:4px 0;"><a href="{htmlmod.escape(a.get("link","#"))}" target="_blank" style="color:var(--text); text-decoration:none;">{htmlmod.escape(a["title"][:55])}</a></div>' for a in kreisweite[:5])}
    </div>
  </div>
</div>
</main>
<footer>
  <a href="../index.html">Startseite</a> · {name} · Aktualisiert: {TIMESTAMP}<br>
  <a href="https://github.com/dna-dieter/ai-tageszeitung">GitHub</a>
</footer>
</body></html>"""

    outdir = DOCS / slug
    outdir.mkdir(exist_ok=True)
    (outdir / "index.html").write_text(page)
    print(f"docs/{slug}/index.html: {len(articles)} Artikel")

if __name__ == "__main__":
    build_index()
    for slug, name in KOMMUNEN.items():
        build_kommune(slug, name)
    print("Fertig!")
