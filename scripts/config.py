"""
Zentrale Konfiguration aller Kreise für die AI Tageszeitung.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

KREISE = {
    "rheinisch-bergischer-kreis": {
        "name": "Rheinisch-Bergischer Kreis",
        "short": "Rhein-Berg",
        "docs_slug": "",  # Root-Level in docs/
        "kommunen": {
            "bergisch-gladbach": "Bergisch Gladbach",
            "burscheid": "Burscheid",
            "kuerten": "Kürten",
            "leichlingen": "Leichlingen",
            "odenthal": "Odenthal",
            "overath": "Overath",
            "roesrath": "Rösrath",
            "wermelskirchen": "Wermelskirchen",
        },
        "keywords": {
            "bergisch-gladbach": [
                "bergisch gladbach", "bensberg", "refrath", "paffrath", "gronau",
                "schildgen", "frankenforst", "moitzfeld", "herkenrath"
            ],
            "burscheid": ["burscheid", "=hilgen"],
            "kuerten": ["kürten", "kuerten", "bechen", "dürscheid", "=olpe", "biesfeld"],
            "leichlingen": ["leichlingen", "witzhelden"],
            "odenthal": ["odenthal", "=altenberg", "altenberger dom", "blecher"],
            "overath": ["overath", "marialinden", "steinenbrück", "heiligenhaus"],
            "roesrath": ["rösrath", "roesrath", "hoffnungsthal", "forsbach"],
            "wermelskirchen": ["wermelskirchen", "dhünn", "dabringhausen"],
        },
    },
    "oberbergischer-kreis": {
        "name": "Oberbergischer Kreis",
        "short": "Oberberg",
        "docs_slug": "oberberg",  # docs/oberberg/
        "kommunen": {
            "bergneustadt": "Bergneustadt",
            "engelskirchen": "Engelskirchen",
            "gummersbach": "Gummersbach",
            "hueckeswagen": "Hückeswagen",
            "lindlar": "Lindlar",
            "marienheide": "Marienheide",
            "morsbach": "Morsbach",
            "nuembrecht": "Nümbrecht",
            "radevormwald": "Radevormwald",
            "reichshof": "Reichshof",
            "waldbroel": "Waldbröl",
            "wiehl": "Wiehl",
            "wipperfuerth": "Wipperfürth",
        },
        "keywords": {
            "bergneustadt": ["bergneustadt"],
            "engelskirchen": ["engelskirchen", "ründeroth", "loope"],
            "gummersbach": ["gummersbach", "dieringhausen", "niederseßmar"],
            "hueckeswagen": ["hückeswagen", "hueckeswagen"],
            "lindlar": ["lindlar", "frielingsdorf", "=linde"],
            "marienheide": ["marienheide", "müllenbach", "gimborn"],
            "morsbach": ["morsbach", "holpe", "lichtenberg"],
            "nuembrecht": ["nümbrecht", "nuembrecht", "marienberghausen"],
            "radevormwald": ["radevormwald"],
            "reichshof": ["reichshof", "eckenhagen", "denklingen", "wildbergerhütte"],
            "waldbroel": ["waldbröl", "waldbroel"],
            "wiehl": ["wiehl", "bielstein", "drabenderhöhe", "oberwiehl"],
            "wipperfuerth": ["wipperfürth", "wipperfuerth"],
        },
    },
    # Köln: eigener Bereich, eigene Datenablage. Keine Gemeinde-Schlagwörter,
    # damit nichts in RBK/OBK einsortiert wird (jeder Bereich wird getrennt verarbeitet).
    "koeln": {
        "name": "Köln",
        "short": "Köln",
        "docs_slug": "koeln",  # docs/koeln/
        "kommunen": {},
        "keywords": {},
    },
    # Rhein-Berg Vereine & Bürgerstimmen: eigener Bereich neben Rhein-Berg, getrennt von den
    # normalen RBK-Feeds. Keine Gemeinde-Schlagwörter, damit nichts in RBK-Gemeinden einsortiert wird.
    "rhein-berg-buergerstimmen": {
        "name": "Rhein-Berg Vereine & Bürgerstimmen",
        "short": "Bürgerstimmen",
        "docs_slug": "buergerstimmen",  # docs/buergerstimmen/
        "kommunen": {},
        "keywords": {},
    },
}
