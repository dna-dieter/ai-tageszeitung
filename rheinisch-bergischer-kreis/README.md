# AI Tageszeitung — Rheinisch-Bergischer Kreis

Automatisch aktualisierte Online-Zeitung für den Rheinisch-Bergischen Kreis.
Ausgegeben wird nur HTML über GitHub Pages (Ordner `docs/` im Repo-Stamm).
Der Oberbergische Kreis läuft mit denselben Skripten unter `docs/oberberg/`.

## Gemeinden

| Gemeinde | Ordner | Einwohner (ca.) |
|----------|--------|-----------------|
| Bergisch Gladbach (Kreisstadt) | bergisch-gladbach/ | 112.000 |
| Burscheid | burscheid/ | 19.000 |
| Kürten | kuerten/ | 20.000 |
| Leichlingen | leichlingen/ | 28.000 |
| Odenthal | odenthal/ | 15.000 |
| Overath | overath/ | 27.000 |
| Rösrath | roesrath/ | 29.000 |
| Wermelskirchen | wermelskirchen/ | 35.000 |

Dazu `kreisweite-nachrichten/` für Meldungen ohne eindeutige Gemeinde.

## Struktur

```
rheinisch-bergischer-kreis/
├── feeds.json              # RSS-Feeds (name, url, type, coverage, verified, optional pages)
├── all_articles.json       # Gesamtarchiv des Kreises
├── <gemeinde>/articles.json
├── kreisweite-nachrichten/articles.json
├── kuerten-rat.json        # Sitzungstermine Kürten (aus SessionNet)
├── templates/              # LaTeX-Vorlagen, derzeit UNGENUTZT
├── output/, assets/, scripts/  # derzeit leer
```

Die Skripte liegen zentral in `../scripts/`:

- `config.py` – Kreise, Gemeinden, Schlagwörter für die Zuordnung
- `fetch_feeds.py` – lädt alle Feeds, ordnet Gemeinden zu, entfernt Dubletten, schreibt die JSON-Dateien
- `fetch_events.py` – Veranstaltungen (Das Bergische für RBK/Oberberg, Rausgegangen für Köln) nach `docs/veranstaltungen/*.json`
- `fetch_kuerten_rat.py` – Sitzungstermine Kürten; Kurzfassungen der Ratssitzungen kommen aus `kuerten_rat_fassungen.json`
- `build_html.py` – erzeugt alle HTML-Seiten in `docs/`

## Zuordnung zu Gemeinden

- Feeds mit `coverage: "<gemeinde>"` gehen direkt an diese Gemeinde.
- Zusätzlich werden Titel und Auszug gegen die Schlagwörter in `config.py` geprüft (Treffer nur an Wortanfängen, siehe `classify_article` in `fetch_feeds.py`).
- Ohne Treffer landet eine Meldung in `kreisweite-nachrichten`.
- Bestehende Artikel bleiben erhalten (Dedup über Link+Titel sowie über ähnliche Titel).

## Aktualisierung

GitHub Actions (`.github/workflows/update.yml`) läuft **stündlich um :05** und manuell per `workflow_dispatch`:

1. `fetch_feeds.py`
2. `fetch_events.py`
3. `fetch_kuerten_rat.py`
4. `build_html.py`
5. Commit „Auto-Update: …“ und Push, falls sich etwas geändert hat

Lokal: `cd scripts && python3 fetch_feeds.py && python3 build_html.py` (benötigt `feedparser`).

## Quellen

Siehe `feeds.json` (Stand: 21 Einträge), u. a. iGL Bürgerportal, GL Aktuell, RGA, Kölner Stadt-Anzeiger, Kölnische Rundschau, Presseportal (Polizei RBK, Feuerwehr Bergisch Gladbach), Stadt Bergisch Gladbach, Gemeinde Kürten. Einträge mit `verified: false` sind ungeprüft.
