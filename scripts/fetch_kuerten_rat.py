#!/usr/bin/env python3
"""Sitzungstermine der Gemeinde Kürten aus SessionNet laden."""
import html
import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from config import BASE

PORTAL = "https://sessionnet.owl-it.de/kuerten/bi/"
JAHR_URL = PORTAL + "si0046.asp?__cselect=81920&__cfid=65536&__canz=12&__cmonat=1"
OUT = BASE / "rheinisch-bergischer-kreis" / "kuerten-rat.json"
FASSUNGEN = Path(__file__).resolve().parent / "kuerten_rat_fassungen.json"
UA = "Mozilla/5.0 (compatible; AI-Tageszeitung/1.0; +https://dna-dieter.github.io/ai-tageszeitung/)"


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": UA})
    with urlopen(request, timeout=40) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "latin-1"
    return raw.decode(charset, errors="replace")


def clean(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_sitzungen(page: str) -> list:
    sitzungen = []
    for row in re.findall(r"<tr[\s\S]*?</tr>", page, re.I):
        cells = re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", row, re.I)
        if len(cells) < 2:
            continue
        datum_text = clean(cells[0])
        match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", datum_text)
        if not match:
            continue
        datum = date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
        body = clean(cells[1])
        zeit = re.search(
            r"^(?P<name>.+?)\s+(?P<zeit>\d{1,2}:\d{2})(?:\s*-\s*\d{1,2}:\d{2})?\s*Uhr\s*(?P<ort>.*)$",
            body,
        )
        if zeit:
            gremium, uhrzeit, ort = zeit.group("name"), zeit.group("zeit"), zeit.group("ort")
        else:
            gremium, uhrzeit, ort = body, "", ""
        dokumente = []
        for href, label in re.findall(r'href="([^"]+)"[^>]*>([\s\S]*?)</a>', cells[-1], re.I):
            name = clean(label)
            if "getfile.asp" not in href or not name:
                continue
            dokumente.append({"art": name, "url": html.unescape(PORTAL + href.lstrip("/"))})
        sitzungen.append({
            "datum": datum.isoformat(),
            "gremium": gremium,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "ist_rat": gremium == "Rat",
            "dokumente": dokumente,
        })
    sitzungen.sort(key=lambda item: (item["datum"], item["uhrzeit"], item["gremium"]))
    return sitzungen


def niederschrift_id(sitzung: dict) -> str:
    for dokument in sitzung.get("dokumente") or []:
        if "Niederschrift" in dokument.get("art", ""):
            match = re.search(r"[?&]id=(\d+)", dokument.get("url", ""))
            if match:
                return match.group(1)
    return ""


def main():
    fassungen = {}
    if FASSUNGEN.exists():
        fassungen = json.loads(FASSUNGEN.read_text())
    try:
        sitzungen = parse_sitzungen(fetch(JAHR_URL))
    except Exception as exc:
        print(f"  Kürten-Rat: SessionNet nicht erreichbar ({exc})")
        return
    if not sitzungen:
        print("  Kürten-Rat: keine Sitzungen gelesen, vorhandene Datei bleibt")
        return
    heute = date.today().isoformat()
    kommende = [item for item in sitzungen if item["datum"] >= heute]
    mit_protokoll = [
        item for item in sitzungen
        if item["ist_rat"] and niederschrift_id(item) in fassungen
    ]
    letzte = mit_protokoll[-1] if mit_protokoll else None
    naechster_rat = next((item for item in kommende if item["ist_rat"]), None)
    payload = {
        "quelle": "https://www.kuerten.de/sitzungen/",
        "portal": PORTAL + "info.asp",
        "aktualisiert": datetime.now().isoformat(timespec="seconds"),
        "kommende": kommende,
        "naechster_rat": naechster_rat,
        "letzte_ratssitzung": None,
    }
    if letzte:
        datei = niederschrift_id(letzte)
        pdf = next(
            dokument["url"] for dokument in letzte["dokumente"]
            if "Niederschrift" in dokument["art"]
        )
        fassung = fassungen[datei]
        payload["letzte_ratssitzung"] = {
            "datum": letzte["datum"],
            "uhrzeit": letzte["uhrzeit"],
            "ort": letzte["ort"] or fassung.get("ort", ""),
            "pdf": pdf,
            "titel": fassung["titel"],
            "punkte": fassung["punkte"],
        }
    if OUT.exists():
        try:
            alt = json.loads(OUT.read_text())
            if {k: v for k, v in alt.items() if k != "aktualisiert"} == {k: v for k, v in payload.items() if k != "aktualisiert"}:
                payload["aktualisiert"] = alt.get("aktualisiert", payload["aktualisiert"])
        except Exception:
            pass
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"  Kürten-Rat: {len(kommende)} kommende Sitzungen")


if __name__ == "__main__":
    main()
