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
                "hand", "schildgen", "frankenforst", "moitzfeld", "herkenrath"
            ],
            "burscheid": ["burscheid", "hilgen"],
            "kuerten": ["kürten", "kuerten", "bechen", "dürscheid", "olpe", "biesfeld"],
            "leichlingen": ["leichlingen", "witzhelden"],
            "odenthal": ["odenthal", "altenberg", "blecher"],
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
            "lindlar": ["lindlar", "frielingsdorf", "linde"],
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
}
