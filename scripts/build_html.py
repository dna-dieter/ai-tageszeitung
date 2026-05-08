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
GITHUB_REPO = "dna-dieter/ai-tageszeitung"
GITHUB_WORKFLOW_FILE = "update.yml"

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
.btn-refresh:disabled, .btn-refresh.loading { background: #95A5A6; cursor: wait; opacity: 0.8; }
.btn-refresh .spinner { display: inline-block; width: 10px; height: 10px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.refresh-status { font-size: 0.72rem; color: rgba(255,255,255,0.85); margin-top: 4px; min-height: 14px; font-family: sans-serif; }
.kreis-nav { background: var(--rbk-blau); padding: 6px 24px; display: flex; gap: 12px; }
.kreis-nav a { font-family: sans-serif; font-size: 0.85rem; color: rgba(255,255,255,0.7); text-decoration: none; padding: 4px 10px; border-radius: 4px; }
.kreis-nav a:hover, .kreis-nav a.active { color: white; background: rgba(255,255,255,0.15); }
@media (max-width: 768px) { .grid { grid-template-columns: 1fr; } header h1 { font-size: 1.3rem; } }
"""

REFRESH_JS = """
<script>
(function() {
  const REPO = 'dna-dieter/ai-tageszeitung';
  const WORKFLOW = 'update.yml';
  const TOKEN_KEY = 'ai_tz_github_token';
  const API = 'https://api.github.com';

  function getToken() {
    let t = localStorage.getItem(TOKEN_KEY);
    if (!t) {
      t = prompt(
        'Einmaliger Setup: Bitte GitHub Personal Access Token eingeben.\\n\\n' +
        'Der Token braucht Berechtigung "Actions: Read and write" auf diesem Repo.\\n' +
        'Der Token wird nur lokal in deinem Browser gespeichert.'
      );
      if (t) {
        t = t.trim();
        localStorage.setItem(TOKEN_KEY, t);
      }
    }
    return t;
  }

  function setStatus(msg) {
    const el = document.getElementById('refresh-status');
    if (el) el.textContent = msg;
  }

  function setButton(loading, label) {
    const btn = document.getElementById('btn-refresh');
    if (!btn) return;
    btn.disabled = loading;
    btn.classList.toggle('loading', loading);
    btn.innerHTML = loading
      ? '<span class="spinner"></span> ' + (label || 'Aktualisiere...')
      : '\\u21bb ' + (label || 'Jetzt aktualisieren');
  }

  async function gh(path, opts) {
    const token = getToken();
    if (!token) throw new Error('Kein Token');
    const res = await fetch(API + path, Object.assign({
      headers: {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer ' + token,
        'X-GitHub-Api-Version': '2022-11-28'
      }
    }, opts || {}));
    return res;
  }

  async function triggerWorkflow() {
    const res = await gh('/repos/' + REPO + '/actions/workflows/' + WORKFLOW + '/dispatches', {
      method: 'POST',
      headers: {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer ' + getToken(),
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ref: 'main' })
    });
    if (res.status === 401 || res.status === 403) {
      localStorage.removeItem(TOKEN_KEY);
      throw new Error('Token ungültig oder abgelaufen (gelöscht, bitte neu eingeben)');
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error('Trigger fehlgeschlagen: ' + res.status + ' ' + text.slice(0, 120));
    }
  }

  async function findRun(triggeredAt) {
    const res = await gh('/repos/' + REPO + '/actions/workflows/' + WORKFLOW + '/runs?per_page=5&event=workflow_dispatch');
    if (!res.ok) return null;
    const data = await res.json();
    const runs = data.workflow_runs || [];
    for (const r of runs) {
      const created = new Date(r.created_at).getTime();
      if (created >= triggeredAt - 10000) return r;
    }
    return null;
  }

  async function waitForCompletion(triggeredAt) {
    const deadline = Date.now() + 6 * 60 * 1000; // max 6 min
    let run = null;
    // find the run (kann ein paar Sekunden dauern)
    while (!run && Date.now() < deadline) {
      await new Promise(r => setTimeout(r, 3000));
      run = await findRun(triggeredAt);
      if (!run) setStatus('Starte Workflow...');
    }
    if (!run) throw new Error('Workflow-Lauf nicht gefunden');

    while (Date.now() < deadline) {
      const res = await gh('/repos/' + REPO + '/actions/runs/' + run.id);
      if (!res.ok) break;
      const r = await res.json();
      setStatus('Status: ' + (r.status || '?') + (r.conclusion ? ' (' + r.conclusion + ')' : ''));
      if (r.status === 'completed') return r;
      await new Promise(res => setTimeout(res, 5000));
    }
    throw new Error('Timeout beim Warten');
  }

  window.triggerRefresh = async function() {
    try {
      const token = getToken();
      if (!token) return;
      setButton(true, 'Starte...');
      setStatus('Sende Trigger an GitHub...');
      const t0 = Date.now();
      await triggerWorkflow();
      setStatus('Workflow gestartet, warte auf Abschluss...');
      const run = await waitForCompletion(t0);
      if (run.conclusion === 'success') {
        setStatus('Fertig! Lade Seite neu...');
        // Kurz warten bis GitHub Pages deployed hat
        setTimeout(() => location.reload(), 30000);
        setStatus('Fertig! Seite lädt in 30s neu (GitHub Pages Deploy)...');
      } else {
        setButton(false);
        setStatus('Fehlgeschlagen: ' + run.conclusion);
      }
    } catch (e) {
      setButton(false);
      setStatus('Fehler: ' + e.message);
    }
  };
})();
</script>
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

def header_html(title, subtitle, article_count=None, kreis_slug=None, active_section=None):
    count_text = f"{article_count} Artikel" if article_count else "Stündlich aktualisiert"
    cls_rbk = ' class="active"' if active_section == "rbk" else ''
    cls_ob  = ' class="active"' if active_section == "oberberg" else ''
    cls_evt = ' class="active"' if active_section == "veranstaltungen" else ''
    return f"""<div class="kreis-nav">
  <a href="/ai-tageszeitung/"{cls_rbk}>Rhein-Berg</a>
  <a href="/ai-tageszeitung/oberberg/"{cls_ob}>Oberberg</a>
  <a href="/ai-tageszeitung/veranstaltungen/"{cls_evt}>📅 Veranstaltungen</a>
</div>
<header>
  <div>
    <h1>{title}</h1>
    <div class="sub">{subtitle}</div>
  </div>
  <div class="meta">
    <div><span class="live-dot"></span>{count_text}</div>
    <div>{TIMESTAMP}</div>
    <button type="button" onclick="triggerRefresh()" class="btn-refresh" id="btn-refresh">&#x21bb; Jetzt aktualisieren</button>
    <div class="refresh-status" id="refresh-status"></div>
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
    # Kreisweite Nachrichten als eigene Kategorie
    kreis_count = count_articles(data_dir, "kreisweite-nachrichten")
    sidebar_items += f'<li style="border-top:1px solid #eee; padding-top:6px; margin-top:6px;"><a href="kreisweite/index.html"><b>Kreisweite Nachrichten</b> <span class="badge">{kreis_count}</span></a></li>'

    # Quellen aus feeds.json laden
    feeds_file = data_dir / "feeds.json"
    quellen_html = ""
    if feeds_file.exists():
        feeds_cfg = json.loads(feeds_file.read_text())
        type_icons = {"polizei": "🚔", "feuerwehr": "🚒", "tageszeitung": "📰",
                      "lokalnachrichten": "🌐", "radio": "📻", "verwaltung": "🏛️",
                      "buergerportal": "👥"}
        seen = set()
        items = []
        for f in feeds_cfg.get("feeds", []):
            name = f["name"]
            if name in seen:
                continue
            seen.add(name)
            icon = type_icons.get(f.get("type", ""), "📰")
            items.append(f'<li style="margin:3px 0;">{icon} {htmlmod.escape(name)}</li>')
        quellen_html = f"""<div class="sidebar-box">
      <h3>Quellen</h3>
      <ul style="list-style:none; font-size:0.82rem; font-family:sans-serif; color:#555;">{"".join(items)}</ul>
    </div>"""

    active = "rbk" if kreis_slug == "rheinisch-bergischer-kreis" else "oberberg"
    page = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Tageszeitung — {kreis_cfg['name']}</title>
<style>{CSS}</style>
</head>
<body>
{header_html("AI TAGESZEITUNG", kreis_cfg['name'], active_section=active)}
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
    {quellen_html}
  </div>
</div>
</main>
<footer>
  AI Tageszeitung · {kreis_cfg['name']} · Aktualisiert: {TIMESTAMP}<br>
  <a href="{GITHUB_ACTIONS}">GitHub</a>
</footer>
{REFRESH_JS}
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
    kreis_count = count_articles(data_dir, "kreisweite-nachrichten")
    sidebar_items += f'<li style="border-top:1px solid #eee; padding-top:6px; margin-top:6px;"><a href="../kreisweite/index.html"><b>Kreisweite Nachrichten</b> <span class="badge">{kreis_count}</span></a></li>'

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
{REFRESH_JS}
</body></html>"""

    (kommune_dir / "index.html").write_text(page)
    print(f"  {kommune_dir.relative_to(DOCS)}/index.html: {len(articles)} Artikel")

def build_kreisweite_page(kreis_slug, kreis_cfg):
    data_dir = BASE / kreis_slug
    kommunen = kreis_cfg["kommunen"]
    docs_slug = kreis_cfg["docs_slug"]
    docs_dir = DOCS / docs_slug if docs_slug else DOCS
    kreisweite_dir = docs_dir / "kreisweite"
    kreisweite_dir.mkdir(parents=True, exist_ok=True)

    articles = load_articles(data_dir, "kreisweite-nachrichten")

    nav_links = [f'<a href="../index.html">Alle</a>']
    for s, n in kommunen.items():
        nav_links.append(f'<a href="../{s}/index.html">{n}</a>')

    sidebar_items = "".join(
        f'<li><a href="../{s}/index.html">{n} <span class="badge">{count_articles(data_dir, s)}</span></a></li>'
        for s, n in kommunen.items()
    )

    page = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kreisweite Nachrichten — AI Tageszeitung</title>
<style>{CSS}</style>
</head>
<body>
{header_html("Kreisweite Nachrichten", f"AI Tageszeitung · {kreis_cfg['name']}", len(articles))}
<nav>{"".join(nav_links)}</nav>
<main>
<div class="grid">
  <div>{grouped_cards(articles, kommune_map=kommunen, show_kommune=True)}</div>
  <div>
    <div class="sidebar-box">
      <h3>Alle Kommunen</h3>
      <ul class="k-links">{sidebar_items}</ul>
    </div>
  </div>
</div>
</main>
<footer>
  <a href="../index.html">Startseite</a> · Kreisweite Nachrichten · Aktualisiert: {TIMESTAMP}<br>
  <a href="{GITHUB_ACTIONS}">GitHub</a>
</footer>
{REFRESH_JS}
</body></html>"""

    (kreisweite_dir / "index.html").write_text(page)
    print(f"  {kreisweite_dir.relative_to(DOCS)}/index.html: {len(articles)} Artikel")

VERANSTALTUNGEN_CSS_EXTRA = """
.region-tabs { display: flex; gap: 0; background: white; border-bottom: 2px solid var(--rbk-blau); padding: 0 24px; }
.region-tab { font-family: sans-serif; font-size: 0.88rem; padding: 10px 20px; cursor: pointer; border: none; background: none; color: var(--rbk-blau); border-bottom: 3px solid transparent; margin-bottom: -2px; transition: all 0.2s; font-weight: 600; }
.region-tab:hover { background: var(--rbk-grau); }
.region-tab.active { border-bottom-color: var(--rbk-rot); color: var(--rbk-rot); }
.region-panel { display: none; }
.region-panel.active { display: block; }
.evt-card { background: white; border-radius: 6px; padding: 14px 18px; border-left: 4px solid #8E44AD; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 12px; }
.evt-card:hover { box-shadow: 0 3px 12px rgba(0,0,0,0.12); }
.evt-card .evt-datum { font-family: sans-serif; font-size: 0.78rem; font-weight: 700; color: #8E44AD; text-transform: uppercase; letter-spacing: 1px; }
.evt-card h3 { font-size: 1.05rem; margin: 4px 0; line-height: 1.3; }
.evt-card h3 a { color: var(--text); text-decoration: none; }
.evt-card h3 a:hover { color: var(--akzent); }
.evt-card .evt-ort { font-family: sans-serif; font-size: 0.82rem; color: #666; margin-top: 4px; }
.evt-card .evt-info { font-family: sans-serif; font-size: 0.75rem; color: #888; margin-top: 5px; }
.portal-links { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }
.portal-link { background: white; border-radius: 6px; padding: 12px 14px; text-decoration: none; color: var(--text); border: 1px solid #e0e0e0; font-family: sans-serif; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; transition: all 0.2s; }
.portal-link:hover { border-color: var(--akzent); color: var(--akzent); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.portal-link .icon { font-size: 1.2rem; }
.hinweis { background: #EBF5FB; border-left: 4px solid var(--akzent); padding: 12px 16px; border-radius: 4px; font-family: sans-serif; font-size: 0.85rem; color: #555; margin-bottom: 16px; }
@media (max-width: 600px) { .portal-links { grid-template-columns: 1fr; } .region-tab { padding: 8px 12px; font-size: 0.8rem; } }
"""

VERANSTALTUNGEN_JS = """
<script>
function switchRegion(slug) {
  document.querySelectorAll('.region-tab').forEach(t => t.classList.toggle('active', t.dataset.region === slug));
  document.querySelectorAll('.region-panel').forEach(p => p.classList.toggle('active', p.dataset.region === slug));
  localStorage.setItem('evt_region', slug);
}
(function() {
  const saved = localStorage.getItem('evt_region') || 'rbk';
  switchRegion(saved);
})();
</script>
"""

def veranstaltungen_portal_links(region):
    portale = {
        "koeln": [
            ("🎭", "Köln.de Veranstaltungen", "https://www.koeln.de/veranstaltungen/"),
            ("🎵", "KölnTicket", "https://www.koelnticket.de/veranstaltungen/"),
            ("🏛️", "Kölner Philharmonie", "https://www.koelner-philharmonie.de/"),
            ("🎪", "Eventim Köln", "https://www.eventim.de/city/koeln-218/"),
            ("🌐", "Köln-Events", "https://www.koeln-events.de/"),
            ("🎨", "Museen Köln", "https://www.museenkoeln.de/"),
        ],
        "rbk": [
            ("🌐", "RGA Veranstaltungen", "https://www.rga.de/veranstaltungen/"),
            ("🏛️", "Bergisch Gladbach – Veranstaltungen", "https://www.bergischgladbach.de/veranstaltungen.aspx"),
            ("🎭", "iGL Veranstaltungskalender", "https://in-gl.de/category/veranstaltungen/"),
            ("🎵", "Stadtkultur RBK", "https://www.rheinisch-bergischer-kreis.de/"),
            ("🎪", "Eventbrite Region Bergisch Gladbach", "https://www.eventbrite.de/d/germany--bergisch-gladbach/events/"),
            ("📅", "Kölner Stadtanzeiger RBK", "https://www.ksta.de/region/rhein-berg-oberberg/"),
        ],
        "oberberg": [
            ("🌐", "Oberbergischer Kreis – Aktuelles", "https://www.obk.de/"),
            ("📰", "Oberberg-Aktuell", "https://www.oberberg-aktuell.de/"),
            ("🎭", "OBK Veranstaltungskalender", "https://www.obk.de/veranstaltungen/"),
            ("🎵", "Gummersbach Stadtkultur", "https://www.gummersbach.de/"),
            ("🎪", "Eventbrite Gummersbach", "https://www.eventbrite.de/d/germany--gummersbach/events/"),
            ("📅", "Lokalkompass Oberberg", "https://www.lokalkompass.de/gummersbach/"),
        ],
    }
    items = "".join(
        f'<a class="portal-link" href="{url}" target="_blank" rel="noopener"><span class="icon">{icon}</span>{name}</a>'
        for icon, name, url in portale.get(region, [])
    )
    return f'<div class="portal-links">{items}</div>'

def build_veranstaltungen_page():
    evt_dir = DOCS / "veranstaltungen"
    evt_dir.mkdir(parents=True, exist_ok=True)

    # Prüfen ob JSON-Dateien mit Veranstaltungen existieren
    def load_events(slug):
        f = evt_dir / f"{slug}.json"
        if f.exists():
            try:
                return json.loads(f.read_text())
            except Exception:
                return []
        return []

    def events_html(events, region_name):
        if not events:
            return f"""<div class="hinweis">
  Für <b>{region_name}</b> werden demnächst automatisch Veranstaltungen aus lokalen Quellen geladen.<br>
  Nutze bis dahin die direkten Links zu den Veranstaltungsportalen unten.
</div>"""
        parts = []
        for e in events[:30]:
            datum = e.get("datum", "")
            titel = htmlmod.escape(e.get("titel", e.get("title", "Veranstaltung")))
            ort   = htmlmod.escape(e.get("ort", ""))
            link  = htmlmod.escape(e.get("link", "#"))
            info  = htmlmod.escape(e.get("quelle", e.get("source", "")))
            parts.append(f"""<div class="evt-card">
  <div class="evt-datum">{htmlmod.escape(datum)}</div>
  <h3><a href="{link}" target="_blank" rel="noopener">{titel}</a></h3>
  {"<div class='evt-ort'>📍 " + ort + "</div>" if ort else ""}
  {"<div class='evt-info'>" + info + "</div>" if info else ""}
</div>""")
        return "\n".join(parts)

    regions = [
        ("koeln",    "Köln",                    "Veranstaltungen in der Domstadt"),
        ("rbk",      "Rheinisch-Bergischer Kreis","Veranstaltungen im RBK"),
        ("oberberg", "Oberbergischer Kreis",      "Veranstaltungen im Oberberg"),
    ]

    tabs_html = "".join(
        f'<button class="region-tab" data-region="{slug}" onclick="switchRegion(\'{slug}\')">{name}</button>'
        for slug, name, _ in regions
    )

    panels_html = "".join(f"""<div class="region-panel" data-region="{slug}">
  <div style="margin: 20px 0 8px 0; font-family: sans-serif; font-size: 0.95rem; color: var(--rbk-blau); font-weight:600;">{desc}</div>
  {events_html(load_events(slug), name)}
  <div class="sidebar-box" style="margin-top:18px;">
    <h3>Veranstaltungsportale</h3>
    {veranstaltungen_portal_links(slug)}
  </div>
</div>""" for slug, name, desc in regions)

    page = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Veranstaltungen — AI Tageszeitung</title>
<style>{CSS}
{VERANSTALTUNGEN_CSS_EXTRA}
</style>
</head>
<body>
{header_html("AI TAGESZEITUNG", "Veranstaltungskalender", active_section="veranstaltungen")}
<div class="region-tabs">
  {tabs_html}
</div>
<main>
  {panels_html}
</main>
<footer>
  AI Tageszeitung · Veranstaltungskalender · Aktualisiert: {TIMESTAMP}<br>
  <a href="/ai-tageszeitung/">Rhein-Berg</a> ·
  <a href="/ai-tageszeitung/oberberg/">Oberberg</a>
</footer>
{VERANSTALTUNGEN_JS}
{REFRESH_JS}
</body></html>"""

    (evt_dir / "index.html").write_text(page)
    print(f"  veranstaltungen/index.html")

if __name__ == "__main__":
    for kreis_slug, kreis_cfg in KREISE.items():
        print(f"\n=== {kreis_cfg['name']} ===")
        build_kreis_index(kreis_slug, kreis_cfg)
        for ks, kn in kreis_cfg["kommunen"].items():
            build_kommune_page(kreis_slug, kreis_cfg, ks, kn)
        build_kreisweite_page(kreis_slug, kreis_cfg)
    print("\n=== Veranstaltungen ===")
    build_veranstaltungen_page()
    print("\nFertig!")
