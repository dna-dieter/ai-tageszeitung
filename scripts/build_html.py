#!/usr/bin/env python3
"""
Baut alle HTML-Seiten für GitHub Pages aus den articles.json-Dateien.
Arbeitet alle Kreise aus config.py ab.
"""
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo
import html as htmlmod

from config import BASE, KREISE

DOCS = BASE / "docs"
BERLIN = ZoneInfo("Europe/Berlin")
def _letzter_stand():
    """Zeitpunkt des letzten Laufs mit neuen Inhalten (last_updated aus feeds.json),
    damit die Seiten ohne neue Artikel unverändert bleiben."""
    werte = []
    for slug in KREISE:
        f = BASE / slug / "feeds.json"
        try:
            wert = datetime.fromisoformat(json.loads(f.read_text())["last_updated"])
            if wert.tzinfo is not None:
                wert = wert.astimezone(BERLIN).replace(tzinfo=None)
            werte.append(wert)
        except Exception:
            pass
    return max(werte) if werte else datetime.now()

TIMESTAMP = _letzter_stand().strftime("%d.%m.%Y, %H:%M Uhr")
GITHUB_ACTIONS = "https://github.com/dna-dieter/ai-tageszeitung/actions/workflows/update.yml"
SITE = "/ai-tageszeitung"
ANBIETER = "Dieter Nadolski"
ANBIETER_MAIL = "info-zeitung@nadolski.de"
ANBIETER_ANSCHRIFT = "Stockbergergasse 21, 51515 Kürten"
ANBIETER_ANSCHRIFT_HTML = "Stockbergergasse 21<br>51515 Kürten"
LEGAL_LINKS = (
    f'<a href="{SITE}/impressum/">Impressum</a> · '
    f'<a href="{SITE}/rechtliches/">Rechtliche Hinweise</a> · '
    f'<a href="{SITE}/rechtliches/#datenschutz">Datenschutz</a>'
)
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
.artikel .tag.bericht { color: var(--rbk-blau); margin-left: 8px; }
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
.legal { max-width: 720px; }
.legal h2 { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 1.15rem; color: var(--rbk-blau); margin: 22px 0 8px; }
.legal p, .legal li { margin: 0 0 10px; }
.legal ul { padding-left: 1.2rem; }
.legal .hinweis { background: #fff8e6; border-left: 4px solid var(--rbk-rot); padding: 10px 14px; margin-bottom: 16px; }
.empty { text-align: center; padding: 40px; color: #999; font-size: 1.1rem; }
.rat-block { margin: 4px 0 26px; }
.rat-block h2 { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 1.15rem; color: var(--rbk-blau); margin: 0 0 10px; }
.rat-hero { background: white; border-left: 4px solid var(--rbk-rot); border-radius: 6px; padding: 16px 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.rat-hero .wann { font-family: sans-serif; font-size: 0.78rem; font-weight: 700; color: var(--rbk-rot); letter-spacing: 0.04em; text-transform: uppercase; }
.rat-hero h3 { font-size: 1.25rem; margin: 4px 0; }
.rat-liste { list-style: none; }
.rat-liste li { background: white; border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.rat-liste .wann { font-family: sans-serif; font-size: 0.82rem; color: var(--rbk-blau); font-weight: 700; }
.rat-liste .ort { font-family: sans-serif; font-size: 0.8rem; color: #666; }
.rat-quelle { font-family: sans-serif; font-size: 0.8rem; color: #666; margin-top: 8px; }
.monat-gruppe { margin-bottom: 8px; }
.monat-header { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 1.05rem; color: var(--rbk-blau); border-bottom: 2px solid var(--rbk-blau); padding: 8px 0 5px 0; margin: 18px 0 10px 0; display: flex; align-items: center; gap: 8px; }
.monat-header:first-child { margin-top: 0; }
.monat-count { background: var(--rbk-blau); color: white; font-size: 0.72rem; padding: 1px 8px; border-radius: 10px; font-weight: 400; }
.btn-refresh { display: inline-flex; align-items: center; gap: 5px; font-family: sans-serif; font-size: 0.78rem; padding: 5px 14px; background: #2ECC71; color: white; border: none; border-radius: 4px; text-decoration: none; cursor: pointer; transition: background 0.2s; margin-top: 4px; }
.btn-refresh[hidden], .refresh-status[hidden] { display: none; }
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
  // Button nur für Betreiber: sichtbar mit ?admin in der Adresse (wird gemerkt), ?admin=aus blendet ihn wieder aus.
  try {
    const p = new URLSearchParams(location.search);
    if (p.has('admin')) {
      if (p.get('admin') === 'aus') localStorage.removeItem('ai_tz_admin');
      else localStorage.setItem('ai_tz_admin', '1');
    }
    if (localStorage.getItem('ai_tz_admin') === '1') {
      const b = document.getElementById('btn-refresh');
      if (b) b.hidden = false;
    }
  } catch (e) {}
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
    clean = re.sub(r'<[^>]+>', '', text or "")
    clean = htmlmod.unescape(clean)
    return re.sub(r'\s+', ' ', clean).strip()

def parse_pub_date(raw):
    if not raw:
        return None
    dt = None
    try:
        dt = parsedate_to_datetime(raw)
    except Exception:
        dt = None
    if dt is None:
        m = re.match(r'(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?', raw)
        if m:
            try:
                dt = datetime(
                    int(m.group(1)), int(m.group(2)), int(m.group(3)),
                    int(m.group(4) or 0), int(m.group(5) or 0), int(m.group(6) or 0),
                )
            except Exception:
                dt = None
    if dt is not None and dt.tzinfo is not None:
        dt = dt.astimezone(BERLIN).replace(tzinfo=None)
    return dt

def sicherer_link(url, ersatz="#"):
    """Nur http(s)-Links zulassen; alles andere (javascript:, data: …) wird zu '#'."""
    url = (url or "").strip()
    if re.match(r"https?://", url, re.I):
        return htmlmod.escape(url)
    return ersatz

def datum_de(raw):
    """Einheitliches Anzeigeformat in Ortszeit Berlin: 22.10.2026, 14:30 Uhr (ohne Uhrzeit, wenn keine angegeben)."""
    dt = parse_pub_date(raw)
    if dt is None:
        return htmlmod.escape((raw or "")[:25])
    hat_zeit = bool(re.search(r"\d{1,2}:\d{2}", raw))
    return dt.strftime("%d.%m.%Y, %H:%M Uhr") if hat_zeit else dt.strftime("%d.%m.%Y")

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
    link = sicherer_link(a.get("link"))
    source = htmlmod.escape(a.get("source", ""))
    published = datum_de(a.get("published", ""))
    tags = []
    if show_kommune and kommune_map:
        kommunen = ", ".join(kommune_map.get(k, k) for k in a.get("kommunen", []))
        tags.append(f'<span class="tag">{htmlmod.escape(kommunen)}</span>')
    source_key = a.get("source", "").lower()
    if "bürgerportal" in source_key or source_key.endswith("politik") or source_key.endswith("kultur"):
        tags.append('<span class="tag bericht">Bericht</span>')
    tag = f'<div class="tagline">{"".join(tags)}</div>' if tags else ""
    if a.get("_auch"):
        source += " · auch bei " + htmlmod.escape(", ".join(a["_auch"]))
    if a.get("_weitere"):
        source += f" · {a['_weitere']} ältere Ausgaben im Archiv"
    return f"""<div class="artikel">
  {tag}
  <h2><a href="{link}" target="_blank" rel="noopener">{title}</a></h2>
  <div class="teaser">{teaser}</div>
  <div class="info">{published} · {source}</div>
</div>"""

# Wiederkehrende Rubriken: in der Anzeige nur die neueste Ausgabe zeigen.
RUBRIKEN = (
    "das gl-wort",
    "öffentliche bekanntmachung",
    "amtliche bekanntmachung",
    "stellen- und ausbildungsangebote",
    "pressemitteilung des oberbergischen kreises",
)

def _titel_norm(title):
    return re.sub(r"\s+", " ", strip_tags(title or "")).strip().lower()

def zusammenfassen(articles):
    """Nur für die Anzeige: gleiche Überschrift aus mehreren Quellen (innerhalb von 3 Tagen)
    als eine Karte mit „auch bei …“, wiederkehrende Rubriken nur in der neuesten Ausgabe.
    Die Daten bleiben unverändert."""
    arts = sorted(articles, key=lambda a: parse_pub_date(a.get("published", "")) or datetime.min, reverse=True)
    out, by_title, rubrik_karte = [], {}, {}
    for a in arts:
        t = _titel_norm(a.get("title"))
        dt = parse_pub_date(a.get("published", ""))
        rubrik = next((r for r in RUBRIKEN if t.startswith(r)), None)
        if rubrik:
            if rubrik in rubrik_karte:
                rubrik_karte[rubrik]["_weitere"] = rubrik_karte[rubrik].get("_weitere", 0) + 1
                continue
            karte = dict(a)
            rubrik_karte[rubrik] = karte
            out.append(karte)
            continue
        kern = re.sub(r"^(pol|fw)-[a-z]+:\s*", "", t)
        kern = re.sub(r"^[\wäöüß/\- ]{3,30}:\s*", "", kern)
        kern = re.sub(r"[^\wäöüß ]", "", kern).strip()
        t = kern if len(kern) > 25 else t
        frueher = by_title.get(t)
        if frueher is not None and frueher.get("source") != a.get("source"):
            fdt = parse_pub_date(frueher.get("published", ""))
            if dt and fdt and abs((fdt - dt).days) <= 3:
                auch = frueher.setdefault("_auch", [])
                if a.get("source") and a.get("source") not in auch:
                    auch.append(a.get("source"))
                continue
        karte = dict(a)
        by_title[t] = karte
        out.append(karte)
    return out

def grouped_cards(articles, max_items=None, show_kommune=True, kommune_map=None, zusammen=True):
    if not articles:
        return '<div class="empty">Noch keine Artikel vorhanden.</div>'
    if zusammen:
        articles = zusammenfassen(articles)
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

def header_html(title, subtitle, article_count=None, kreis_slug=None, active_section=None):
    count_text = f"{article_count} Artikel" if article_count else "Stündlich aktualisiert"
    cls_rbk = ' class="active"' if active_section == "rbk" else ''
    cls_ob  = ' class="active"' if active_section == "oberberg" else ''
    cls_evt = ' class="active"' if active_section == "veranstaltungen" else ''
    cls_koe = ' class="active"' if active_section == "koeln" else ''
    cls_bst = ' class="active"' if active_section == "buergerstimmen" else ''
    return f"""<div class="kreis-nav">
  <a href="/ai-tageszeitung/"{cls_rbk}>Rhein-Berg</a>
  <a href="/ai-tageszeitung/buergerstimmen/"{cls_bst}>Rhein-Berg Vereine &amp; Bürgerstimmen</a>
  <a href="/ai-tageszeitung/oberberg/"{cls_ob}>Oberberg</a>
  <a href="/ai-tageszeitung/koeln/"{cls_koe}>Köln</a>
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
    <button type="button" onclick="triggerRefresh()" class="btn-refresh" id="btn-refresh" hidden>&#x21bb; Jetzt aktualisieren</button>
    <div class="refresh-status" id="refresh-status"></div>
  </div>
</header>"""

def kommune_nav(kommunen, prefix, kreis_slug, active_slug=None):
    parts = []
    for slug, name in kommunen.items():
        cls = ' class="active"' if slug == active_slug else ''
        parts.append(f'<a href="{prefix}{slug}/index.html"{cls}>{htmlmod.escape(name)}</a>')
        if kreis_slug == "rheinisch-bergischer-kreis" and slug == "kuerten":
            rat_cls = ' class="active"' if active_slug == "kuerten-rat" else ''
            parts.append(f'<a href="{prefix}kuerten-rat/index.html"{rat_cls}>Kürten-Rat</a>')
    return "".join(parts)

def kommune_sidebar(kommunen, data_dir, prefix, kreis_slug):
    parts = []
    for slug, name in kommunen.items():
        parts.append(
            f'<li><a href="{prefix}{slug}/index.html">{htmlmod.escape(name)} '
            f'<span class="badge">{count_articles(data_dir, slug)}</span></a></li>'
        )
        if kreis_slug == "rheinisch-bergischer-kreis" and slug == "kuerten":
            parts.append(f'<li><a href="{prefix}kuerten-rat/index.html">Kürten-Rat</a></li>')
    return "".join(parts)

def rat_datum(iso_datum: str) -> str:
    moment = datetime.strptime(iso_datum, "%Y-%m-%d")
    wochentage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    return f"{wochentage[moment.weekday()]}, {moment.day}. {MONATE_DE[moment.month]} {moment.year}"

# --- Build Functions ---

# Statischer Kasten für "Rhein-Berg Vereine & Bürgerstimmen": nur bestätigte Links laut
# rbk_social_2026-10-23.md. Einfache Links, keine Embeds, kein Tracking, keine Inhalte aus den Gruppen.
BUERGERSTIMMEN_LINKS = [
    ("Leichlingen Info & offenes Forum (Facebook-Gruppe)", "https://www.facebook.com/groups/Die.Leichlinger/"),
    ("Wermelskirchen – das Original! (Facebook-Gruppe)", "https://www.facebook.com/groups/wermelskirchen/"),
    ("Du bist aus Wermelskirchen (Facebook-Gruppe)", "https://www.facebook.com/groups/251860244925508/"),
    ("NETT-WERK Bergisch Gladbach (Facebook-Gruppe)", "https://www.facebook.com/groups/484180354933947/"),
    ("ForumWk auf WhatsApp (Kanal, Ankündigung)", "https://forumwk.de/2025/11/08/neu-forumwk-jetzt-auch-auf-whatsapp/"),
]

def weiterfuehrende_links_html(kreis_slug):
    if kreis_slug != "rhein-berg-buergerstimmen":
        return ""
    items = "".join(
        f'<li><a href="{htmlmod.escape(u)}" target="_blank" rel="noopener nofollow">{htmlmod.escape(t)}</a></li>'
        for t, u in BUERGERSTIMMEN_LINKS
    )
    return f"""<div class="sidebar-box">
      <h3>Weiterführende Links – lokale Gruppen &amp; Kanäle</h3>
      <ul class="k-links">{items}</ul>
      <p style="font-family:sans-serif; font-size:0.78rem; color:#666; margin-top:8px; line-height:1.4;">Datenschutz: Das sind reine externe Links. Es gibt keine eingebetteten Inhalte, keine Like- oder Teilen-Knöpfe und kein Tracking. Erst beim Anklicken wird die Seite des Drittanbieters geöffnet: bei den Facebook-Gruppen direkt Facebook (Meta), beim WhatsApp-Eintrag zunächst eine Ankündigung auf forumwk.de, von der aus man zum WhatsApp-Kanal (Meta) weitergehen kann. Ab dann gelten die Datenschutzbestimmungen der jeweils aufgerufenen Seite, also von Meta bei Facebook und WhatsApp und von forumwk.de bei der Ankündigung, auch wenn man dort nicht angemeldet ist. Mehr in den <a href="/ai-tageszeitung/rechtliches/">Rechtlichen Hinweisen</a>.</p>
    </div>"""

def build_kreis_index(kreis_slug, kreis_cfg):
    data_dir = BASE / kreis_slug
    kommunen = kreis_cfg["kommunen"]
    docs_slug = kreis_cfg["docs_slug"]
    docs_dir = DOCS / docs_slug if docs_slug else DOCS
    docs_dir.mkdir(parents=True, exist_ok=True)

    all_file = data_dir / "all_articles.json"
    articles = json.loads(all_file.read_text()) if all_file.exists() else []
    articles.sort(key=lambda a: parse_pub_date(a.get("published", "")) or datetime.min, reverse=True)

    ticker = " · ".join(htmlmod.escape(a["title"][:60]) for a in articles[:3]) or "Keine aktuellen Meldungen"

    # Kommune-Navigation
    nav_links = ['<a href="index.html" class="active">Alle</a>', kommune_nav(kommunen, "", kreis_slug)]

    # Sidebar
    sidebar_items = kommune_sidebar(kommunen, data_dir, "", kreis_slug)
    # Kreisweite Nachrichten als eigene Kategorie
    kreis_count = count_articles(data_dir, "kreisweite-nachrichten")
    sidebar_items += f'<li style="border-top:1px solid #eee; padding-top:6px; margin-top:6px;"><a href="kreisweite/index.html"><b>{"Alle Köln-Nachrichten" if kreis_slug == "koeln" else ("Alle Beiträge" if kreis_slug == "rhein-berg-buergerstimmen" else "Kreisweite Nachrichten")}</b> <span class="badge">{kreis_count}</span></a></li>'
    if kreis_slug == "rheinisch-bergischer-kreis":
        bst_count = count_articles(BASE / "rhein-berg-buergerstimmen", "kreisweite-nachrichten")
        sidebar_items += f'<li><a href="buergerstimmen/index.html"><b>Rhein-Berg Vereine &amp; Bürgerstimmen</b> <span class="badge">{bst_count}</span></a></li>'

    # Quellen aus feeds.json laden
    feeds_file = data_dir / "feeds.json"
    quellen_html = ""
    if feeds_file.exists():
        feeds_cfg = json.loads(feeds_file.read_text())
        type_icons = {"polizei": "🚔", "feuerwehr": "🚒", "tageszeitung": "📰",
                      "lokalnachrichten": "🌐", "radio": "📻", "verwaltung": "🏛️",
                      "buergerportal": "👥", "verein": "🤝"}
        grenze = datetime.now() - timedelta(days=30)
        aktiv = {
            a.get("source") for a in articles
            if (parse_pub_date(a.get("published", "")) or datetime.min) >= grenze
        }
        seen = set()
        items = []
        for f in feeds_cfg.get("feeds", []):
            name = f["name"]
            if name in seen or name not in aktiv:
                continue
            seen.add(name)
            icon = type_icons.get(f.get("type", ""), "📰")
            items.append(f'<li style="margin:3px 0;">{icon} {htmlmod.escape(name)}</li>')
        quellen_html = f"""<div class="sidebar-box">
      <h3>Quellen (letzte 30 Tage)</h3>
      <ul style="list-style:none; font-size:0.82rem; font-family:sans-serif; color:#555;">{"".join(items)}</ul>
    </div>"""

    active = {"rheinisch-bergischer-kreis": "rbk", "koeln": "koeln", "rhein-berg-buergerstimmen": "buergerstimmen"}.get(kreis_slug, "oberberg")
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
    {weiterfuehrende_links_html(kreis_slug)}
  </div>
</div>
</main>
<footer>
  AI Tageszeitung · {kreis_cfg['name']} · Aktualisiert: {TIMESTAMP}<br>
  {LEGAL_LINKS}<br>
  <a href="{GITHUB_ACTIONS}">GitHub</a>
</footer>
{REFRESH_JS}
</body></html>"""

    (docs_dir / "index.html").write_text(page)
    print(f"  {docs_dir.relative_to(DOCS)}/index.html: {len(articles)} Artikel")

def teile_aktuell_archiv(articles, mindestens=100, tage=90):
    """Aktuell = die 100 neuesten Artikel, mindestens aber alle der letzten 90 Tage; Rest ins Archiv (nur Anzeige, Daten bleiben)."""
    articles = sorted(articles, key=lambda a: parse_pub_date(a.get("published", "")) or datetime.min, reverse=True)
    grenze = datetime.now() - timedelta(days=tage)
    n_frisch = sum(1 for a in articles if (parse_pub_date(a.get("published", "")) or datetime.min) >= grenze)
    n = max(mindestens, n_frisch)
    return articles[:n], articles[n:]

def archiv_hinweis(anzahl):
    if not anzahl:
        return ""
    return (f'<div class="empty" style="margin-top:12px;"><a href="archiv/index.html">'
            f'Archiv: {anzahl} ältere Artikel ansehen &rarr;</a></div>')

def build_archiv_page(ziel_dir, titel, kreis_cfg, kommunen, articles, show_kommune):
    archiv_dir = ziel_dir / "archiv"
    archiv_dir.mkdir(parents=True, exist_ok=True)
    page = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{htmlmod.escape(titel)} – Archiv — AI Tageszeitung</title>
<style>{CSS}</style>
</head>
<body>
{header_html(f"{titel} – Archiv", f"AI Tageszeitung · {kreis_cfg['name']}", len(articles))}
<nav><a href="../index.html">&larr; Zurück zu {htmlmod.escape(titel)}</a></nav>
<main>
  <div>{grouped_cards(articles, kommune_map=kommunen, show_kommune=show_kommune) if articles else '<div class="empty">Keine älteren Artikel.</div>'}</div>
</main>
<footer>
  <a href="../index.html">{htmlmod.escape(titel)}</a> · Archiv · Aktualisiert: {TIMESTAMP}<br>
  {LEGAL_LINKS}<br>
  <a href="{GITHUB_ACTIONS}">GitHub</a>
</footer>
{REFRESH_JS}
</body></html>"""
    (archiv_dir / "index.html").write_text(page)
    print(f"  {archiv_dir.relative_to(DOCS)}/index.html: {len(articles)} Artikel (Archiv)")

def build_kommune_page(kreis_slug, kreis_cfg, kommune_slug, kommune_name):
    data_dir = BASE / kreis_slug
    kommunen = kreis_cfg["kommunen"]
    docs_slug = kreis_cfg["docs_slug"]
    docs_dir = DOCS / docs_slug if docs_slug else DOCS
    kommune_dir = docs_dir / kommune_slug
    kommune_dir.mkdir(parents=True, exist_ok=True)

    articles = load_articles(data_dir, kommune_slug)
    aktuell, archiv = teile_aktuell_archiv(articles)
    kreisweite = load_articles(data_dir, "kreisweite-nachrichten")
    grenze = datetime.now() - timedelta(days=30)
    kreisweite_frisch = sorted(
        (a for a in kreisweite if (parse_pub_date(a.get("published", "")) or datetime.min) >= grenze),
        key=lambda a: parse_pub_date(a.get("published", "")), reverse=True,
    )

    # Navigation
    nav_links = ['<a href="../index.html">Alle</a>', kommune_nav(kommunen, "../", kreis_slug, kommune_slug)]

    # Sidebar
    sidebar_items = kommune_sidebar(kommunen, data_dir, "../", kreis_slug)
    kreis_count = count_articles(data_dir, "kreisweite-nachrichten")
    sidebar_items += f'<li style="border-top:1px solid #eee; padding-top:6px; margin-top:6px;"><a href="../kreisweite/index.html"><b>Kreisweite Nachrichten</b> <span class="badge">{kreis_count}</span></a></li>'

    kreisweite_links = "".join(
        f'<div style="font-size:0.85rem; margin:4px 0;"><a href="{sicherer_link(a.get("link"))}" target="_blank" style="color:var(--text); text-decoration:none;">{htmlmod.escape(a["title"][:55])}</a></div>'
        for a in kreisweite_frisch[:5]
    ) or '<div style="font-size:0.85rem; color:#888;">Keine kreisweiten Meldungen der letzten 30 Tage.</div>'

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
  <div>{grouped_cards(aktuell, kommune_map=kommunen, show_kommune=False)}{archiv_hinweis(len(archiv))}</div>
  <div>
    <div class="sidebar-box">
      <h3>Alle Kommunen</h3>
      <ul class="k-links">{sidebar_items}</ul>
    </div>
    {weiterfuehrende_links_html(kreis_slug)}
    <div class="sidebar-box">
      <h3>Kreisweite Nachrichten</h3>
      {kreisweite_links}
    </div>
  </div>
</div>
</main>
<footer>
  <a href="../index.html">Startseite</a> · {kommune_name} · Aktualisiert: {TIMESTAMP}<br>
  {LEGAL_LINKS}<br>
  <a href="{GITHUB_ACTIONS}">GitHub</a>
</footer>
{REFRESH_JS}
</body></html>"""

    (kommune_dir / "index.html").write_text(page)
    build_archiv_page(kommune_dir, kommune_name, kreis_cfg, kommunen, archiv, False)
    print(f"  {kommune_dir.relative_to(DOCS)}/index.html: {len(articles)} Artikel")

def build_kreisweite_page(kreis_slug, kreis_cfg):
    data_dir = BASE / kreis_slug
    kommunen = kreis_cfg["kommunen"]
    docs_slug = kreis_cfg["docs_slug"]
    docs_dir = DOCS / docs_slug if docs_slug else DOCS
    kreisweite_dir = docs_dir / "kreisweite"
    kreisweite_dir.mkdir(parents=True, exist_ok=True)

    articles = load_articles(data_dir, "kreisweite-nachrichten")
    aktuell, archiv = teile_aktuell_archiv(articles)

    nav_links = ['<a href="../index.html">Alle</a>', kommune_nav(kommunen, "../", kreis_slug)]

    sidebar_items = kommune_sidebar(kommunen, data_dir, "../", kreis_slug)

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
  <div>{grouped_cards(aktuell, kommune_map=kommunen, show_kommune=True)}{archiv_hinweis(len(archiv))}</div>
  <div>
    <div class="sidebar-box">
      <h3>Alle Kommunen</h3>
      <ul class="k-links">{sidebar_items}</ul>
    </div>
    {weiterfuehrende_links_html(kreis_slug)}
  </div>
</div>
</main>
<footer>
  <a href="../index.html">Startseite</a> · Kreisweite Nachrichten · Aktualisiert: {TIMESTAMP}<br>
  {LEGAL_LINKS}<br>
  <a href="{GITHUB_ACTIONS}">GitHub</a>
</footer>
{REFRESH_JS}
</body></html>"""

    (kreisweite_dir / "index.html").write_text(page)
    build_archiv_page(kreisweite_dir, "Kreisweite Nachrichten", kreis_cfg, kommunen, archiv, True)
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
.evt-card .evt-teaser { font-size: 0.88rem; color: #555; margin-top: 5px; line-height: 1.45; }
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
            ("📅", "Das Bergische – Termine", "https://www.dasbergische.de/aktivitaeten/veranstaltungen"),
            ("🏛️", "Bergisch Gladbach – Terminkalender", "https://www.bergischgladbach.de/termine.aspx"),
            ("🎭", "iGL Veranstaltungskalender", "https://in-gl.de/category/veranstaltungen/"),
            ("🎵", "Stadtkultur RBK", "https://www.rheinisch-bergischer-kreis.de/"),
            ("🎪", "Eventbrite Region Bergisch Gladbach", "https://www.eventbrite.de/d/germany--bergisch-gladbach/events/"),
            ("📅", "Kölner Stadtanzeiger RBK", "https://www.ksta.de/region/rhein-berg-oberberg/"),
        ],
        "oberberg": [
            ("🌐", "Oberbergischer Kreis – Aktuelles", "https://www.obk.de/"),
            ("📰", "Oberberg-Aktuell", "https://www.oberberg-aktuell.de/"),
            ("📅", "Das Bergische – Termine", "https://www.dasbergische.de/aktivitaeten/veranstaltungen"),
            ("🎭", "OBK Veranstaltungskalender", "https://www.obk.de/obk/veranstaltungen/index.shtml.de"),
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
            return (
                '<div class="hinweis">Für <b>' + htmlmod.escape(region_name) + '</b> sind aktuell keine '
                'Veranstaltungshinweise verfügbar. Nutze die Portale unten.</div>'
            )
        letzter = htmlmod.escape(events[-1].get("datum", ""))
        hinweis = str(len(events)) + ' kommende Termine bis ' + letzter
        # Hinweis, wenn weniger als 40 Termine oder der Abruf nur eine Ersatzquelle
        # mit kürzerem Zeitraum lieferte (Feld "eingeschraenkt" aus fetch_events.py).
        if len(events) < 40 or any(e.get("eingeschraenkt") for e in events):
            quellen = sorted({e.get("quelle", "") for e in events if e.get("quelle")})
            hinweis += ' · Termine eingeschränkt, Quelle: ' + htmlmod.escape(", ".join(quellen) or "unbekannt")
        parts = ['<div class="hinweis" style="background:#EAFAF1; border-color:#27AE60;">📅 '
                 + hinweis + '</div>']
        for e in events:
            datum  = htmlmod.escape(e.get("datum", ""))
            titel  = htmlmod.escape(e.get("titel", e.get("title", "Veranstaltung")))
            ort    = htmlmod.escape(e.get("ort", ""))
            link   = sicherer_link(e.get("link"))
            info   = htmlmod.escape(e.get("quelle", e.get("source", "")))
            teaser = htmlmod.escape(e.get("teaser", "")[:200])
            preis  = htmlmod.escape(e.get("preis", ""))
            card = '<div class="evt-card">\n'
            card += '  <div class="evt-datum">' + datum
            if e.get("datum_bis"):
                card += ' bis ' + htmlmod.escape(e["datum_bis"])
            if preis:
                card += ' &middot; <span style="color:#27AE60;font-weight:normal;">' + preis + '</span>'
            else:
                card += ' &middot; <span style="color:#888;font-weight:normal;">Preis k.A.</span>'
            card += '</div>\n'
            card += '  <h3><a href="' + link + '" target="_blank" rel="noopener">' + titel + '</a></h3>\n'
            if ort:
                card += '  <div class="evt-ort">&#x1F4CD; ' + ort + '</div>\n'
            if teaser:
                card += '  <div class="evt-teaser">' + teaser + '</div>\n'
            if info:
                card += '  <div class="evt-info">Quelle: ' + info + '</div>\n'
            card += '</div>'
            parts.append(card)
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

    panel_parts = []
    for slug, name, desc in regions:
        evt_content = events_html(load_events(slug), name)
        portal_content = veranstaltungen_portal_links(slug)
        panel_parts.append(
            '<div class="region-panel" data-region="' + slug + '">\n'
            '  <div style="margin: 20px 0 8px 0; font-family: sans-serif; font-size: 0.95rem; '
            'color: var(--rbk-blau); font-weight:600;">' + htmlmod.escape(desc) + '</div>\n'
            + evt_content + '\n'
            '  <div class="sidebar-box" style="margin-top:18px;">\n'
            '    <h3>Veranstaltungsportale</h3>\n'
            + portal_content + '\n'
            '  </div>\n'
            '</div>'
        )
    panels_html = "\n".join(panel_parts)

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
  {LEGAL_LINKS}<br>
  <a href="/ai-tageszeitung/">Rhein-Berg</a> ·
  <a href="/ai-tageszeitung/oberberg/">Oberberg</a>
</footer>
{VERANSTALTUNGEN_JS}
{REFRESH_JS}
</body></html>"""

    (evt_dir / "index.html").write_text(page)
    print(f"  veranstaltungen/index.html")

def build_kuerten_rat_page(kreis_cfg):
    data_dir = BASE / "rheinisch-bergischer-kreis"
    kommunen = kreis_cfg["kommunen"]
    docs_dir = DOCS / "kuerten-rat"
    docs_dir.mkdir(parents=True, exist_ok=True)
    quelle = data_dir / "kuerten-rat.json"
    daten = json.loads(quelle.read_text()) if quelle.exists() else {}

    def termin_html(sitzung, hero=False):
        wann = rat_datum(sitzung["datum"])
        if sitzung.get("uhrzeit"):
            wann += ", " + sitzung["uhrzeit"] + " Uhr"
        ort = htmlmod.escape(sitzung.get("ort") or "Ort noch nicht genannt")
        name = htmlmod.escape(sitzung.get("gremium") or "Sitzung")
        if hero:
            hinweis = (
                '<p class="rat-quelle">Die Einladung liegt noch nicht vor. '
                'Sie erscheint im Ratsinformationssystem, sobald die Gemeinde sie freigibt.</p>'
                if not sitzung.get("dokumente") else ""
            )
            return (
                '<div class="rat-hero">'
                f'<div class="wann">{htmlmod.escape(wann)}</div>'
                f'<h3>{name}</h3>'
                f'<div class="ort">{ort}</div>'
                f'{hinweis}'
                '</div>'
            )
        return (
            '<li>'
            f'<div class="wann">{htmlmod.escape(wann)}</div>'
            f'<div><b>{name}</b><div class="ort">{ort}</div></div>'
            '</li>'
        )

    rat = daten.get("naechster_rat")
    hero = termin_html(rat, hero=True) if rat else '<p class="empty">Kein weiterer Ratstermin im Kalender.</p>'
    weitere = [
        termin_html(sitzung)
        for sitzung in daten.get("kommende") or []
        if not sitzung.get("ist_rat")
    ]
    liste = '<ul class="rat-liste">' + "".join(weitere) + '</ul>' if weitere else '<p class="empty">Keine weiteren Sitzungen im Kalender.</p>'

    letzte = daten.get("letzte_ratssitzung") or {}
    punkte = letzte.get("punkte") or []
    beschluesse = "".join(
        '<div class="artikel">'
        '<div class="tag">Beschluss</div>'
        f'<h2>{htmlmod.escape(punkt["titel"])}</h2>'
        f'<div class="teaser">{htmlmod.escape(punkt["text"])}</div>'
        '</div>'
        for punkt in punkte
    )
    if letzte:
        protokoll = (
            f'<div class="rat-block"><h2>{htmlmod.escape(letzte["titel"])}</h2>'
            f'{beschluesse}'
            '<p class="rat-quelle">Gekürzt aus der öffentlichen Niederschrift. '
            'Eröffnung, Entschuldigungen und die Genehmigung der vorigen Niederschrift sind weggelassen. '
            f'<a href="{sicherer_link(letzte["pdf"])}" target="_blank" rel="noopener">Niederschrift als PDF</a>'
            '</p></div>'
        )
    else:
        protokoll = '<p class="empty">Für die letzte Ratssitzung liegt noch keine kurze Fassung vor.</p>'

    portal = sicherer_link(daten.get("portal"), "https://www.kuerten.de/sitzungen/")
    nav = '<a href="../index.html">Alle</a>' + kommune_nav(kommunen, "../", "rheinisch-bergischer-kreis", "kuerten-rat")
    page = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kürten-Rat — AI Tageszeitung</title>
<style>{CSS}</style>
</head>
<body>
{header_html("Kürten-Rat", "AI Tageszeitung · Rheinisch-Bergischer Kreis", active_section="rbk")}
<nav>{nav}</nav>
<main>
<div class="rat-block">
  <h2>Nächste Ratssitzung</h2>
  {hero}
</div>
<div class="rat-block">
  <h2>Weitere Sitzungen</h2>
  {liste}
  <p class="rat-quelle">Termine aus dem Ratsinformationssystem der Gemeinde Kürten.
  <a href="{portal}" target="_blank" rel="noopener">SessionNet öffnen</a></p>
</div>
{protokoll}
</main>
<footer>
  <a href="../index.html">Startseite</a> · Kürten-Rat · Aktualisiert: {TIMESTAMP}<br>
  {LEGAL_LINKS}<br>
  <a href="{GITHUB_ACTIONS}">GitHub</a>
</footer>
{REFRESH_JS}
</body></html>"""
    (docs_dir / "index.html").write_text(page)
    print("  kuerten-rat/index.html")

def legal_page(filename, title, body):
    page = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — AI Tageszeitung</title>
<style>{CSS}</style>
</head>
<body>
{header_html("AI TAGESZEITUNG", title)}
<main>
<div class="legal">
{body}
</div>
</main>
<footer>
  AI Tageszeitung · {title}<br>
  {LEGAL_LINKS}
</footer>
{REFRESH_JS}
</body></html>"""
    target = DOCS / filename / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page)
    print(f"  {filename}/index.html")

def build_legal_pages():
    impressum = f"""
<h2>Anbieter</h2>
<p>{ANBIETER}<br>
{ANBIETER_ANSCHRIFT_HTML}</p>
<p>E-Mail: <a href="mailto:{ANBIETER_MAIL}">{ANBIETER_MAIL}</a></p>
<h2>Verantwortlich für den Inhalt</h2>
<p>{ANBIETER}<br>
{ANBIETER_ANSCHRIFT_HTML}</p>
<p>Verantwortlich im Sinne von § 18 Abs. 2 Medienstaatsvertrag.</p>
<p>Das Angebot wird privat betrieben, ohne Gewerbe, Handelsregistereintrag und Umsatzsteuer-ID.</p>
"""
    rechtliches = f"""
<h2>Was diese Seite zeigt</h2>
<p>Die AI Tageszeitung ist ein privates Angebot von Dieter Nadolski. Sie stellt automatisch und stündlich Meldungen aus dem Rheinisch-Bergischen Kreis, dem Oberbergischen Kreis und der Stadt Köln zusammen. Dazu kommen ein eigener Bereich „Rhein-Berg Vereine &amp; Bürgerstimmen“, ein Veranstaltungskalender und die Seite „Kürten-Rat“ mit Terminen und Beschlüssen aus dem Ratsinformationssystem der Gemeinde Kürten. Zu jeder Meldung stehen die Überschrift, die Quelle, das Datum, ein kurzer Auszug von höchstens 250 Zeichen und ein Link auf den Originalbeitrag. Die Zuordnung zu Gemeinden geschieht automatisch und kann irren.</p>
<p>Die Formulierungen gehören den genannten Redaktionen und Pressestellen. Die Seite ersetzt den Originalbericht nicht und gibt fremde Texte nicht als eigene Recherche aus.</p>
<h2>Quellen</h2>
<p>Die Quelle steht an jedem Beitrag. Dazu gehören unter anderem das Bürgerportal in-gl.de, GL Aktuell, der Kölner Stadt-Anzeiger, NEWS-on-Tour Oberberg, Oberberg Nachrichten, der Remscheider General-Anzeiger, die Rheinische Post (Leichlingen), Oberberg-Aktuell, die Rheinischen Anzeigenblätter (Rhein-Berg und Oberberg), die Rheinisch-Bergische Wirtschaftsförderung, Polizei und Feuerwehr über das Presseportal sowie weitere lokale Angebote.</p>
<p>Offizielle Mitteilungen kommen unter anderem von Bergisch Gladbach, Burscheid, Engelskirchen, Hückeswagen, Morsbach, Nümbrecht, Radevormwald, Waldbröl, Wiehl und Wipperfürth. Die Meldungen der Stadt Wiehl werden derzeit ohne Datum übernommen und erscheinen deshalb nicht in der Quellenliste der letzten 30 Tage. Für Köln werden die Pressemeldungen der Stadt Köln und Meldungen des Kölner Stadt-Anzeigers (je Abruf höchstens die 30 neuesten) übernommen. Köln-Meldungen erscheinen nur im Köln-Bereich.</p>
<p>Der Bereich „Rhein-Berg Vereine &amp; Bürgerstimmen“ zeigt Beiträge von Vereinen und Bürgerportalen, zum Beispiel Forum Wermelskirchen, Leichlingen Magazin, Bergischer Geschichtsverein Rhein-Berg und Heimat- und Bürgerverein Overath.</p>
<p>Dieselbe Meldung aus mehreren Quellen wird nach Möglichkeit nur einmal gezeigt.</p>
<h2>Veranstaltungen</h2>
<p>Termine für Rhein-Berg und Oberberg kommen aus dem Kalender von Das Bergische, Termine für Köln aus dem offenen Veranstaltungsdatensatz der Stadt Köln (Open Data, <a href="https://www.offenedaten-koeln.de/dataset/veranstaltungen-der-stadt-koeln" target="_blank" rel="noopener">offenedaten-koeln.de</a>, Datenlizenz Deutschland – Zero – Version 2.0, <a href="https://www.govdata.de/dl-de/zero-2-0" target="_blank" rel="noopener">govdata.de/dl-de/zero-2-0</a>). Angezeigt werden Titel, Zeitpunkt, Ort, eine kurze Beschreibung von höchstens 200 Zeichen und ein Link. Ein Teil der Links führt auf die Übersichtsseite des Kalenders, wenn dort keine eigene Detailadresse hinterlegt ist.</p>
<h2 id="datenschutz">Datenschutz</h2>
<p>Verantwortlicher: {ANBIETER}, {ANBIETER_ANSCHRIFT}, <a href="mailto:{ANBIETER_MAIL}">{ANBIETER_MAIL}</a>.</p>
<p>Die Seiten liegen als feste HTML-Dateien auf GitHub Pages. Der Betreiber setzt keine eigenen Cookies und keine Reichweitenmessung ein. Beim Aufruf verarbeitet der Hoster GitHub die üblichen Verbindungsdaten, insbesondere IP-Adresse, Zeitpunkt und Browsertyp, in seinen Serverprotokollen.</p>
<p>Für Besucherinnen und Besucher gibt es keinen Aktualisierungsknopf; die Seite aktualisiert sich stündlich von selbst. Nur der Betreiber kann über eine eigene Admin-Adresse einen Knopf „Jetzt aktualisieren“ einblenden. Dieser Knopf fragt nach einem GitHub-Token. Der Token bleibt im Browser der Person, die ihn eingibt, und wird nur an die GitHub-API gesendet, um den Aktualisierungslauf zu starten. Er wird nicht an den Betreiber dieser Seite übertragen.</p>
<p>Links auf Meldungen und Veranstaltungen führen auf die Seiten der jeweiligen Quelle. Dort gilt deren Datenschutzhinweis.</p>
<p>Im Bereich „Rhein-Berg Vereine &amp; Bürgerstimmen“ stehen außerdem Links zu Facebook-Gruppen und zu einem WhatsApp-Kanal. Das sind reine externe Links: Es gibt keine eingebetteten Inhalte, keine Like- oder Teilen-Knöpfe und kein Tracking. Erst beim Anklicken wird die Seite des Drittanbieters geöffnet: bei den Facebook-Gruppen direkt Facebook (Meta), beim WhatsApp-Eintrag zunächst eine Ankündigung auf forumwk.de, von der aus man zum WhatsApp-Kanal (Meta) weitergehen kann. Ab dann gelten die Datenschutzbestimmungen der jeweils aufgerufenen Seite, also von Meta bei Facebook und WhatsApp und von forumwk.de bei der Ankündigung, auch wenn man dort nicht angemeldet ist.</p>
<p>Auskunft, Berichtigung und Löschung können über die genannte E-Mail verlangt werden. Beschwerden nimmt die Landesbeauftragte für Datenschutz und Informationsfreiheit Nordrhein-Westfalen entgegen.</p>
<p><i>Stand dieser Hinweise: 23. Oktober 2026.</i></p>
"""
    legal_page("impressum", "Impressum", impressum)
    legal_page("rechtliches", "Rechtliche Hinweise", rechtliches)

if __name__ == "__main__":
    for kreis_slug, kreis_cfg in KREISE.items():
        print(f"\n=== {kreis_cfg['name']} ===")
        build_kreis_index(kreis_slug, kreis_cfg)
        for ks, kn in kreis_cfg["kommunen"].items():
            build_kommune_page(kreis_slug, kreis_cfg, ks, kn)
        build_kreisweite_page(kreis_slug, kreis_cfg)
        if kreis_slug == "rheinisch-bergischer-kreis":
            build_kuerten_rat_page(kreis_cfg)
    print("\n=== Veranstaltungen ===")
    build_veranstaltungen_page()
    print("\n=== Impressum und Rechtliches ===")
    build_legal_pages()
    print("\nFertig!")
