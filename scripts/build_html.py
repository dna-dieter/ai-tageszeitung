#!/usr/bin/env python3
"""
Baut alle HTML-Seiten für GitHub Pages aus den articles.json-Dateien.
Arbeitet alle Kreise aus config.py ab.
"""
import json
import re
from pathlib import Path
from datetime import datetime
from collections import OrderedDict
from email.utils import parsedate_to_datetime
import html as htmlmod

from config import BASE, KREISE

DOCS = BASE / "docs"
TIMESTAMP = datetime.now().strftime("%d.%m.%Y, %H:%M")
GITHUB_ACTIONS = "https://github.com/dna-dieter/ai-tageszeitung/actions/workflows/update.yml"

MONATE_DE = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April",
    5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
    9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
}

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
header { background: var(--rbk-blau); color: white; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
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
nav .sep { color: #ccc; padding: 5px 2px; font-family: sans-serif; font-size: 0.82rem; }
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
.btn-refresh { display: inline-flex; align-items: center; gap: 5px; font-family: sans-serif; font-size: 0.78rem; padding: 5px 14px; background: #2ECC71; color: white; border: none; border-radius: 4px; text-decoration: none; cursor: pointer; transition: background 0.2s; margin-top: 4px; }
.btn-refresh:hover { background: #27AE60; color: white; }
.kreis-nav { background: var(--rbk-blau); padding: 6px 24px; display: flex; gap: 12px; }
.kreis-nav a { font-family: sans-serif; font-size: 0.85rem; color: rgba(255,255,255,0.7); text-decoration: none; padding: 4px 10px; border-radius: 4px; }
.kreis-nav a:hover, .kreis-nav a.active { color: white; background: rgba(255,255,255,0.15); }
@media (max-width: 768px) { .grid { grid-template-columns: 1fr; } header h1 { font-size: 1.3rem; } }
"""

# --- Helpers ---

def strip_tags(text):
    clean = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', clean).strip()

def parse_pub_date(raw):
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', raw)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass
    return None

def group_by_month(articles):
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
    sorted_keys = sorted(grouped.keys(), reverse=True)
    result = OrderedDict()
    for key in sorted_keys:
        result[key] = sorted(grouped[key], key=lambda x: x["_dt"], reverse=True)
    if undated:
        result[("ohne", "datum")] = undated
    return result

def month_label(key):
    if key == ("ohne", "datum"):
        return "Ohne Datum"
    return f"{MONATE_DE.get(key[1], key[1])} {key[0]}"

def artikel_html(a, show_kommune=True, kommune_map=None):
    title = htmlmod.escape(a.get("title", "Ohne Titel"))
    teaser = htmlmod.escape(strip_tags(a.get("summary", ""))[:250])
    link = htmlmod.escape(a.get("link", "#"))
    source = htmlmod.escape(a.get("source", ""))
    published = a.get("published", "")[:25]
    if show_kommune and kommune_map:
        kommunen = ", ".join(kommune_map.get(k, k) for k in a.get("kommunen", []))
        tag = f'<div class="tag">{htmlmod.escape(kommunen)}</div>'
    else:
        tag = ""
    return f"""<div class="artikel">
  {tag}
  <h2><a href="{link}" target="_blank" rel="noopener">{title}</a></h2>
  <div class="teaser">{teaser}</div>
  <div class="info">{published} · {source}</div>
</div>"""

def grouped_cards(articles, max_items=None, show_kommune=True, kommune_map=None):
    if not articles:
        return '<div class="empty">Noch keine Artikel vorhanden.</div>'
    groups = group_by_month(articles)
    parts = []
    shown = 0
    for key, arts in groups.items():
        if max_items and shown >= max_items:
            break
        parts.append(f'<div class="monat-gruppe">')
        parts.append(f'<h2 class="monat-header">{month_label(key)} <span class="monat-count">{len(arts)}</span></h2>')
        for a in arts:
            if max_items and shown >= max_items:
                break
            parts.append(artikel_html(a, show_kommune=show_kommune, kommune_map=kommune_map))
            shown += 1
        parts.append('</div>')
    return "\n".join(parts)

def load_articles(data_dir, slug):
    f = data_dir / slug / "articles.json"
    if f.exists():
        return json.loads(f.read_text())
    return []

def count_articles(data_dir, slug):
    return len(load_articles(data_dir, slug))

def kreis_nav_html(active_slug=None):
    """Navigation zwischen den Kreisen."""
    links = []
    for ks, kcfg in KREISE.items():
        ds = kcfg["docs_slug"]
        href = f"/{ds}/" if ds else "/"
        href = f"{'oberberg/' if ds else ''}index.html"
        cls = ' class="active"' if ks == active_slug else ''
        links.append(f'<a href="/{href}"{cls}>{kcfg["short"]}</a>')
    return "\n".join(links)

def header_html(title, subtitle, article_count=None, kreis_slug=None):
    count_text = f"{article_count} Artikel" if article_count else "Stündlich aktualisiert"
    return f"""<div class="kreis-nav">
  <a href="/ai-tageszeitung/">Rhein-Berg</a>
  <a href="/ai-tageszeitung/oberberg/">Oberberg</a>
</div>
<header>
  <div>
    <h1>{title}</h1>
    <div class="sub">{subtitle}</div>
  </div>
  <div class="meta">
    <div><span class="live-dot"></span>{count_text}</div>
    <div>{TIMESTAMP}</div>
    <a href="{GITHUB_ACTIONS}" target="_blank" rel="noopener" class="btn-refresh">&#x21bb; Jetzt aktualisieren</a>
  </div>
</header>"""

# --- Build Functions ---

def build_kreis_index(kreis_slug, kreis_cfg):
    data_dir = BASE / kreis_slug
    kommunen = kreis_cfg["kommunen"]
    docs_slug = kreis_cfg["docs_slug"]
    docs_dir = DOCS / docs_slug if docs_slug else DOCS
    docs_dir.mkdir(parents=True, exist_ok=True)

    all_file = data_dir / "all_articles.json"
    articles = json.loads(all_file.read_text()) if all_file.exists() else []

    ticker = " · ".join(htmlmod.escape(a["title"][:60]) for a in articles[:3]) or "Keine aktuellen Meldungen"

    # Kommune-Navigation
    nav_links = [f'<a href="index.html" class="active">Alle</a>']
    for s, n in kommunen.items():
        nav_links.append(f'<a href="{s}/index.html">{n}</a>')

    # Sidebar
    sidebar_items = "".join(
        f'<li><a href="{s}/index.html">{n} <span class="badge">{count_articles(data_dir, s)}</span></a></li>'
        for s, n in kommunen.items()
    )

    page = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Tageszeitung — {kreis_cfg['name']}</title>
<style>{CSS}</style>
</head>
<body>
{header_html("AI TAGESZEITUNG", kreis_cfg['name'])}
<div class="ticker"><b>AKTUELL:</b> {ticker}</div>
<nav>{"".join(nav_links)}</nav>
<main>
<div class="grid">
  <div>{grouped_cards(articles, max_items=50, kommune_map=kommunen)}</div>
  <div>
    <div class="sidebar-box">
      <h3>Kommunen</h3>
      <ul class="k-links">{sidebar_items}</ul>
    </div>
  </div>
</div>
</main>
<footer>
  AI Tageszeitung · {kreis_cfg['name']} · Aktualisiert: {TIMESTAMP}<br>
  <a href="{GITHUB_ACTIONS}">GitHub</a>
</footer>
</body></html>"""

    (docs_dir / "index.html").write_text(page)
    print(f"  {docs_dir.relative_to(DOCS)}/index.html: {len(articles)} Artikel")

def build_kommune_page(kreis_slug, kreis_cfg, kommune_slug, kommune_name):
    data_dir = BASE / kreis_slug
    kommunen = kreis_cfg["kommunen"]
    docs_slug = kreis_cfg["docs_slug"]
    docs_dir = DOCS / docs_slug if docs_slug else DOCS
    kommune_dir = docs_dir / kommune_slug
    kommune_dir.mkdir(parents=True, exist_ok=True)

    articles = load_articles(data_dir, kommune_slug)
    kreisweite = load_articles(data_dir, "kreisweite-nachrichten")

    # Navigation
    nav_links = [f'<a href="../index.html">Alle</a>']
    for s, n in kommunen.items():
        cls = ' class="active"' if s == kommune_slug else ''
        nav_links.append(f'<a href="../{s}/index.html"{cls}>{n}</a>')

    # Sidebar
    sidebar_items = "".join(
        f'<li><a href="../{s}/index.html">{n} <span class="badge">{count_articles(data_dir, s)}</span></a></li>'
        for s, n in kommunen.items()
    )

    kreisweite_links = "".join(
        f'<div style="font-size:0.85rem; margin:4px 0;"><a href="{htmlmod.escape(a.get("link","#"))}" target="_blank" style="color:var(--text); text-decoration:none;">{htmlmod.escape(a["title"][:55])}</a></div>'
        for a in kreisweite[:5]
    )

    page = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{kommune_name} — AI Tageszeitung</title>
<style>{CSS}</style>
</head>
<body>
{header_html(kommune_name, f"AI Tageszeitung · {kreis_cfg['name']}", len(articles))}
<nav>{"".join(nav_links)}</nav>
<main>
<div class="grid">
  <div>{grouped_cards(articles, kommune_map=kommunen, show_kommune=False)}</div>
  <div>
    <div class="sidebar-box">
      <h3>Alle Kommunen</h3>
      <ul class="k-links">{sidebar_items}</ul>
    </div>
    <div class="sidebar-box">
      <h3>Kreisweite Nachrichten</h3>
      {kreisweite_links}
    </div>
  </div>
</div>
</main>
<footer>
  <a href="../index.html">Startseite</a> · {kommune_name} · Aktualisiert: {TIMESTAMP}<br>
  <a href="{GITHUB_ACTIONS}">GitHub</a>
</footer>
</body></html>"""

    (kommune_dir / "index.html").write_text(page)
    print(f"  {kommune_dir.relative_to(DOCS)}/index.html: {len(articles)} Artikel")

if __name__ == "__main__":
    for kreis_slug, kreis_cfg in KREISE.items():
        print(f"\n=== {kreis_cfg['name']} ===")
        build_kreis_index(kreis_slug, kreis_cfg)
        for ks, kn in kreis_cfg["kommunen"].items():
            build_kommune_page(kreis_slug, kreis_cfg, ks, kn)
    print("\nFertig!")
