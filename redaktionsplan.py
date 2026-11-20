#!/usr/bin/env python3
"""Inpernell – Redaktionsplan als Bild (Inpernell-Stil).

Zeigt die laufende und die nächste Woche: täglich den Top Job des Tages (18:50), die Reels aus
reels/warteschlange.json (Di/Do 07:30, So 17:00, Sonder-Reels mit eigener Uhrzeit) mit Vorschaubild,
den Montagstermin für neue Reel-Themen und den Status (veröffentlicht / geplant / gesperrt).

Aufruf: python redaktionsplan.py [JJJJ-MM-TT Starttag, Standard heute] [Tage, Standard 14]  ->  vorschau/redaktionsplan.png
"""
import csv
import json
import os
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw

from bild import HELL, NAVY, ORANGE, WEISS, font, wrap

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HIER, "vorschau", "redaktionsplan.png")
B = 1200
NAVY2, LINIE, GRUEN, GRAU = (18, 40, 78), (52, 74, 112), (52, 199, 123), (140, 152, 176)
TAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
REEL_ZEIT = {1: "07:30", 3: "07:30", 6: "17:00"}


def _csv(pfad):
    if not os.path.exists(pfad):
        return []
    with open(pfad, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _reel_titel(r):
    if r.get("sketch") or (r.get("thema") or "").startswith("Sketch"):
        return r.get("thema", "Comic-Sketch")
    for s in r.get("szenen", []):
        if s["typ"] == "hook":
            text = ""
            for z in s["zeilen"]:
                if text.endswith("-"):          # Silbentrennung der Folie wieder zusammenziehen
                    text = text[:-1] + z
                else:
                    text += (" " if text else "") + z
            return text
    return r.get("caption", "").split("\n")[0].split(":")[0]


def _vorschau(r):
    """Titelbild des Reels: veröffentlichtes/fertiges Bild, sonst die erste Folie neu zeichnen."""
    for pfad in (os.path.join(HIER, "docs", "reels", r["id"] + ".jpg"),
                 os.path.join(HIER, r.get("fertig_titelbild", "") or "-")):
        if os.path.exists(pfad):
            return Image.open(pfad).convert("RGB")
    try:
        import reel_anim
        import reel_design as rd
        s = reel_anim._szene(r["szenen"][0], r.get("kategorie", "personal"))
        return s["fn"](**s["kwargs"], szene=0, anzahl=len(r["szenen"])).convert("RGB")
    except Exception:
        return Image.new("RGB", (1080, 1920), NAVY2)


def eintraege(start, tage):
    reels = json.load(open(os.path.join(HIER, "reels", "warteschlange.json"), encoding="utf-8"))
    raus = {z["reel_id"]: z for z in _csv(os.path.join(HIER, "data", "reels.csv"))}
    posts = {}
    for z in _csv(os.path.join(HIER, "data", "protokoll.csv")):
        if z.get("media_id") and not z["media_id"].startswith("geloescht"):
            posts[z["datum"]] = z
    plan = []
    for i in range(tage):
        tag = start + timedelta(days=i)
        iso = tag.isoformat()
        e = {"tag": tag, "punkte": []}
        for r in reels:
            if r.get("datum") != iso:
                continue
            zeit = r.get("zeit") or REEL_ZEIT.get(tag.weekday(), "07:30")
            if r["id"] in raus:
                status = "veröffentlicht"
            elif r.get("zeit") and not r.get("freigegeben"):
                status = "wartet auf Freigabe"
            else:
                status = "geplant"
            e["punkte"].append({"art": "reel", "zeit": zeit, "titel": _reel_titel(r), "status": status, "reel": r})
        if tag.weekday() in REEL_ZEIT and not any(p["art"] == "reel" and not p["reel"].get("zeit") for p in e["punkte"]):
            e["punkte"].append({"art": "offen", "zeit": REEL_ZEIT[tag.weekday()], "titel": "Reel-Thema folgt (Montags-Aufgabe)",
                                "status": "geplant"})
        if tag.weekday() == 0:
            e["punkte"].append({"art": "aufgabe", "zeit": "10:13", "titel": "Neue Reel-Themen für die Folgewoche",
                                "status": "geplant"})
        ov = os.path.join(HIER, "overrides", iso + ".json")
        if iso in posts:
            e["punkte"].append({"art": "job", "zeit": "18:50", "titel": posts[iso]["titel"], "status": "veröffentlicht"})
        elif os.path.exists(ov):
            e["punkte"].append({"art": "job", "zeit": "18:50", "titel": json.load(open(ov, encoding="utf-8"))["titel"],
                                "status": "geplant"})
        else:
            e["punkte"].append({"art": "job", "zeit": "18:50", "titel": "Stelle wird um 16:07 ausgewählt",
                                "status": "geplant"})
        e["punkte"].sort(key=lambda p: p["zeit"])
        plan.append(e)
    return plan


def zeichne(plan, heute, ziel=ZIEL):
    zeilen_h = []
    for e in plan:
        h = 30
        for p in e["punkte"]:
            h += 196 if p["art"] == "reel" else 128
        zeilen_h.append(max(h, 120))
    kopf = 250
    H = kopf + sum(zeilen_h) + 60 * (1 + sum(1 for e in plan[1:] if e["tag"].weekday() == 0)) + 120
    img = Image.new("RGB", (B, H), NAVY)
    d = ImageDraw.Draw(img)
    d.text((60, 60), "REDAKTIONSPLAN", font=font("h800", 70), fill=WEISS)
    von, bis = plan[0]["tag"], plan[-1]["tag"]
    d.text((60, 150), f"Instagram @inpernell.personalvermittlung · {von:%d.%m.} bis {bis:%d.%m.%Y}",
           font=font("t400", 32), fill=HELL)
    lg = os.path.join(HIER, "assets", "logo.png")
    if os.path.exists(lg):
        l = Image.open(lg).convert("RGBA")
        img.paste(l, (B - 60 - l.width, 70), l)
    y = kopf
    for i, (e, h) in enumerate(zip(plan, zeilen_h)):
        if i == 0 or e["tag"].weekday() == 0:
            d.text((60, y + 8), f"KW {e['tag'].isocalendar()[1]}", font=font("h800", 34), fill=ORANGE)
            y += 60
        tag = e["tag"]
        vergangen, ist_heute = tag < heute, tag == heute
        fl = NAVY2 if not ist_heute else (40, 60, 104)
        d.rounded_rectangle([40, y, B - 40, y + h - 16], radius=22, fill=fl,
                            outline=ORANGE if ist_heute else LINIE, width=4 if ist_heute else 2)
        d.text((70, y + 26), TAGE[tag.weekday()], font=font("h800", 44), fill=ORANGE if ist_heute else WEISS)
        d.text((70, y + 82), f"{tag:%d.%m.}", font=font("t400", 30), fill=HELL)
        if ist_heute:
            d.rounded_rectangle([66, y + 128, 166, y + 164], radius=18, fill=ORANGE)
            d.text((116, y + 146), "HEUTE", font=font("h800", 20), fill=NAVY, anchor="mm")
        py = y + 20
        for p in e["punkte"]:
            x0 = 210
            farbe = {"reel": ORANGE, "offen": ORANGE, "job": (70, 150, 230), "aufgabe": GRAU}[p["art"]]
            label = {"reel": "REEL", "offen": "REEL", "job": "TOP JOB + STORY", "aufgabe": "CLAUDE-AUFGABE"}[p["art"]]
            if p["art"] == "reel":
                th = _vorschau(p["reel"]).resize((96, 170), Image.LANCZOS)
                img.paste(th, (x0, py))
                d.rectangle([x0, py, x0 + 96, py + 170], outline=LINIE, width=2)
                tx = x0 + 120
            else:
                tx = x0
            d.text((tx, py + 4), f"{p['zeit']}  {label}", font=font("h800", 26), fill=farbe)
            zz = wrap(d, p["titel"], font("h700", 32), B - 80 - tx - 40)
            for k, z in enumerate(zz):
                d.text((tx, py + 42 + k * 38), z, font=font("h700", 32), fill=WEISS)
            st = p["status"]
            if vergangen and st == "geplant":
                st = "nicht erschienen"
            sf = {"veröffentlicht": GRUEN, "geplant": GRAU, "wartet auf Freigabe": ORANGE,
                  "nicht erschienen": (226, 75, 74)}[st]
            sy = py + 42 + len(zz) * 38 + 6
            d.ellipse([tx, sy + 8, tx + 16, sy + 24], fill=sf)
            d.text((tx + 26, sy), st, font=font("t400", 26), fill=sf)
            py += 196 if p["art"] == "reel" else 128
        y += h
    d.text((60, H - 70), f"Stand: {datetime.now(ZoneInfo('Europe/Berlin')):%d.%m.%Y %H:%M} Uhr · Reels Di/Do 07:30, "
                         "So 17:00 · Top Job täglich 18:50", font=font("t400", 24), fill=GRAU)
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    img.save(ziel, optimize=True)
    return ziel


if __name__ == "__main__":
    heute = datetime.now(ZoneInfo("Europe/Berlin")).date()
    start = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else heute
    tage = int(sys.argv[2]) if len(sys.argv) > 2 else 14
    print(zeichne(eintraege(start, tage), heute))
