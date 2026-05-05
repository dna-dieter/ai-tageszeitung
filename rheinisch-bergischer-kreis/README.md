# AI Tageszeitung — Rheinisch-Bergischer Kreis

Kontinuierlich aktualisierte Online-Tageszeitung für den Rheinisch-Bergischen Kreis.
Gesetzt mit LaTeX, publiziert via GitHub Pages.

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

## Architektur

```
rheinisch-bergischer-kreis/
├── feeds.json              # RSS-Feed-Konfiguration
├── templates/              # LaTeX-Templates
│   ├── titelseite.tex      # Kreisweite Titelseite
│   ├── kommune-seite.tex   # Erste Seite je Kommune
│   └── artikel-detail.tex  # Einzelartikel
├── output/                 # Generierte PDFs + HTML
├── assets/                 # Bilder, Logos, Karten
└── <gemeinde>/             # Artikel-Daten je Gemeinde
```

## Aktualisierungs-Zyklus

- RSS-Feeds werden alle 15 Minuten abgefragt
- Neue Artikel werden automatisch kategorisiert (Kommune, Thema)
- LaTeX-Kompilierung bei neuen Artikeln
- GitHub Pages Deployment via GitHub Actions
