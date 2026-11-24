#!/usr/bin/env python3
"""Inpernell – Auswertung der Instagram-Zahlen (läuft täglich im Workflow, kostet keine Claude-Tokens).

Liest die Rohdaten von statistik.py (JSON), führt den Verlauf je Beitrag (Werte nach Tag 1, Tag 3, Tag 7) und
schreibt eine einseitige Zusammenfassung plus Grafik. Die Montags-Aufgabe liest nur die Zusammenfassung.
Freigabe des Inhabers (Variante a): Zusammenfassung und Verlauf offen im Repository, Rohdaten verschlüsselt.

Aufruf: python auswertung.py rohdaten.json
Ergebnis: data/statistik/zusammenfassung.md, verlauf.json, wochenbild.png; Exit-Code 3 bei Warnungen."""
import csv
import json
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.abspath(__file__))
ORDNER = os.path.join(HIER, "data", "statistik")
BERLIN = ZoneInfo("Europe/Berlin")
TAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
KENNZAHLEN = ["reach", "views", "likes", "comments", "saved", "shares", "ig_reels_avg_watch_time"]
# Kategorie-Farben (geprüft mit dem Palette-Validator; Legende + Tabelle wegen geringem Kontrast von Grün/Gelb)
FARBE = {"Top Job": (42, 120, 214), "Reel": (235, 104, 52), "Sketch": (27, 175, 122), "Sonstiges": (237, 161, 0)}
# Geplante Uhrzeiten (Pünktlichkeit)
TOPJOB_ZEIT = (18, 50)
REEL_ZEIT = {1: (7, 30), 3: (7, 30), 6: (17, 0)}


def _csv(name):
    p = os.path.join(HIER, "data", name)
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter=";")) if os.path.exists(p) else []


def kategorien():
    kat = {}
    for z in _csv("protokoll.csv"):
        if z.get("media_id") and not z["media_id"].startswith("geloescht"):
            kat[z["media_id"]] = ("Top Job", None)
    warte = {r["id"]: r for r in json.load(open(os.path.join(HIER, "reels", "warteschlange.json"), encoding="utf-8"))}
    for z in _csv("reels.csv"):
        r = warte.get(z["reel_id"], {})
        art = "Sketch" if "sketch" in z["reel_id"] else ("Sonstiges" if r.get("zeit") else "Reel")
        kat[z["media_id"]] = (art, r.get("zeit"))
    return kat


def _zahl(x):
    return x if isinstance(x, (int, float)) else None


def main(rohpfad):
    roh = json.load(open(rohpfad, encoding="utf-8"))
    os.makedirs(ORDNER, exist_ok=True)
    vpfad = os.path.join(ORDNER, "verlauf.json")
    verlauf = json.load(open(vpfad, encoding="utf-8")) if os.path.exists(vpfad) else {"beitraege": {}, "follower": {}}
    jetzt = datetime.now(timezone.utc)
    heute = jetzt.astimezone(BERLIN).date()
    verlauf["follower"][heute.isoformat()] = (roh.get("profil") or {}).get("followers_count")
    kat = kategorien()
    insights_fehlen = False
    neu_tag1 = set()
    for b in roh.get("beitraege", []):
        t = datetime.strptime(b["zeit"], "%Y-%m-%dT%H:%M:%S%z")
        werte = {k: _zahl((b.get("insights") or {}).get(k)) for k in KENNZAHLEN}
        werte["likes"] = werte["likes"] if werte["likes"] is not None else b.get("likes")
        werte["comments"] = werte["comments"] if werte["comments"] is not None else b.get("kommentare")
        if werte["reach"] is None:
            insights_fehlen = True
        e = verlauf["beitraege"].setdefault(b["id"], {})
        art, sonderzeit = kat.get(b["id"], ("Reel" if b.get("art") == "REELS" else "Sonstiges", None))
        e.update({"zeit": t.astimezone(BERLIN).strftime("%Y-%m-%d %H:%M"), "art": art, "titel": b.get("titel", "")[:60],
                  "sonderzeit": sonderzeit, "aktuell": werte})
        alter = (jetzt - t).total_seconds() / 3600
        for stufe, ab in (("tag1", 20), ("tag3", 68), ("tag7", 164)):
            if alter >= ab and stufe not in e:
                e[stufe] = werte
                if stufe == "tag1" and alter < 72:          # nur frisch gemessene Beiträge auf Einbruch prüfen
                    neu_tag1.add(b["id"])
    warnungen = pruefen(verlauf, heute, neu_tag1)
    json.dump(verlauf, open(vpfad, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    schreiben(verlauf, heute, insights_fehlen, warnungen, roh)
    grafik(verlauf, heute)
    for w in warnungen:
        print("::warning::" + w)
    return 3 if warnungen else 0


def pruefen(verlauf, heute, neu_tag1=()):
    """Pünktlichkeit und Ausfälle des Vortags, starker Reichweiten-Einbruch."""
    w = []
    gestern = heute - timedelta(days=1)
    bt = [e for e in verlauf["beitraege"].values() if e["zeit"].startswith(gestern.isoformat())]
    tj = [e for e in bt if e["art"] == "Top Job"]
    if not tj:
        w.append(f"{gestern:%d.%m.}: kein Top Job erschienen.")
    for e in tj:
        ist = datetime.strptime(e["zeit"], "%Y-%m-%d %H:%M")
        if abs((ist.hour * 60 + ist.minute) - (TOPJOB_ZEIT[0] * 60 + TOPJOB_ZEIT[1])) > 10:
            w.append(f"{gestern:%d.%m.}: Top Job um {ist:%H:%M} statt 18:50.")
    plan = REEL_ZEIT.get(gestern.weekday())
    reels = [e for e in bt if e["art"] == "Reel"]
    if plan and not reels:
        w.append(f"{gestern:%d.%m.}: geplantes Reel ({plan[0]:02d}:{plan[1]:02d}) nicht erschienen.")
    for e in reels + [e for e in bt if e["art"] in ("Sketch", "Sonstiges") and e.get("sonderzeit")]:
        soll = e.get("sonderzeit") or (f"{plan[0]:02d}:{plan[1]:02d}" if plan else None)
        if soll:
            ist = datetime.strptime(e["zeit"], "%Y-%m-%d %H:%M")
            sh, sm = (int(x) for x in soll.split(":"))
            if abs(ist.hour * 60 + ist.minute - sh * 60 - sm) > 10:
                w.append(f"{gestern:%d.%m.}: {e['art']} um {ist:%H:%M} statt {soll}.")
    # Einbruch: Beitrag nach Tag 1 unter 30 % des Medians der letzten 10 gleichen Formats
    alle = sorted(verlauf["beitraege"].values(), key=lambda e: e["zeit"])
    for mid in neu_tag1:
        e = verlauf["beitraege"][mid]
        if e.get("warnung_einbruch"):
            continue
        mass = "reach" if e["tag1"].get("reach") is not None else "likes"
        vgl = [x["tag1"].get(mass) for x in alle if x is not e and x["art"] == e["art"] and "tag1" in x
               and x["tag1"].get(mass) is not None][-10:]
        if len(vgl) >= 4 and e["tag1"].get(mass) is not None and e["tag1"][mass] < 0.3 * statistics.median(vgl):
            w.append(f"Einbruch: „{kurz(e['titel'], 40)}“ ({e['art']}) hat nach Tag 1 nur {e['tag1'][mass]} {mass} "
                     f"(Median {statistics.median(vgl):.0f}).")
            e["warnung_einbruch"] = True
    return w


def kurz(text, n):
    """Auf ganze Wörter kürzen (nie mitten im Wort abschneiden)."""
    aus = ""
    for w in text.replace("–", " ").split():
        if len(aus) + len(w) + 1 > n:
            break
        aus = (aus + " " + w).strip()
    return aus or text[:n]


def _f(x, nach=0):
    return "–" if x is None else (f"{x:.{nach}f}" if isinstance(x, float) else str(x))


def schreiben(verlauf, heute, insights_fehlen, warnungen, roh):
    alle = sorted(verlauf["beitraege"].values(), key=lambda e: e["zeit"])
    fol = verlauf["follower"]
    f_heute = fol.get(heute.isoformat())
    f_vor7 = next((fol[d] for d in sorted(fol) if d >= (heute - timedelta(days=7)).isoformat()), None)
    z = [f"# Instagram-Auswertung, Stand {heute:%d.%m.%Y}", ""]
    z.append(f"Follower: {_f(f_heute)} (7 Tage: {'+' if f_heute and f_vor7 and f_heute >= f_vor7 else ''}"
             f"{(f_heute - f_vor7) if f_heute is not None and f_vor7 is not None else '–'})")
    if insights_fehlen:
        z.append("Hinweis: Reichweite/Aufrufe/Speichern/Teilen fehlen (Berechtigung instagram_manage_insights fehlt). "
                 "Bewertung vorerst nach Likes und Kommentaren.")
    z += ["", "## Warnungen", *(f"- {w}" for w in warnungen or ["keine"]), ""]
    z += ["## Beiträge der letzten 14 Tage (Werte aktuell)", "",
          "| Datum | Format | Titel | Likes | Komm. | Reichw. | Aufrufe | Geteilt | Gespeich. | Sehdauer s |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    grenze = (heute - timedelta(days=14)).isoformat()
    for e in reversed([e for e in alle if e["zeit"] >= grenze]):
        a = e["aktuell"]
        sd = a.get("ig_reels_avg_watch_time")
        z.append(f"| {e['zeit'][8:10]}.{e['zeit'][5:7]}. {e['zeit'][11:]} | {e['art']} | {kurz(e['titel'], 38)} | "
                 f"{_f(a.get('likes'))} | {_f(a.get('comments'))} | {_f(a.get('reach'))} | {_f(a.get('views'))} | "
                 f"{_f(a.get('shares'))} | {_f(a.get('saved'))} | {_f(sd / 1000 if sd else None, 1)} |")
    z += ["", "## Durchschnitt nach Format (letzte 30 Tage, Werte nach Tag 3 bzw. aktuell)", "",
          "| Format | Beiträge | Likes | Komm. | Reichw. | Geteilt/Reichw. | Likes/Reichw. |", "|---|---|---|---|---|---|---|"]
    g30 = (heute - timedelta(days=30)).isoformat()
    for art in ("Top Job", "Reel", "Sketch", "Sonstiges"):
        xs = [e.get("tag3", e["aktuell"]) for e in alle if e["art"] == art and e["zeit"] >= g30]
        if not xs:
            continue
        def m(k):
            v = [x.get(k) for x in xs if x.get(k) is not None]
            return statistics.mean(v) if v else None
        r = m("reach")
        z.append(f"| {art} | {len(xs)} | {_f(m('likes'), 1)} | {_f(m('comments'), 1)} | {_f(r, 0)} | "
                 f"{_f(m('shares') / r * 100 if r and m('shares') is not None else None, 1)} % | "
                 f"{_f(m('likes') / r * 100 if r and m('likes') is not None else None, 1)} % |")
    bewertet = [e for e in alle if e["zeit"] >= g30]
    def score(e):
        a = e.get("tag3", e["aktuell"])
        if a.get("reach"):
            return ((a.get("shares") or 0) * 3 + (a.get("saved") or 0) * 2 + (a.get("likes") or 0)) / a["reach"]
        return (a.get("likes") or 0) + 2 * (a.get("comments") or 0)
    bewertet.sort(key=score, reverse=True)
    z += ["", "## Beste und schwächste Beiträge (30 Tage)", ""]
    z += [f"- Top: {e['zeit'][:10]} {e['art']} – {kurz(e['titel'], 50)}" for e in bewertet[:3]]
    z += [f"- Schwach: {e['zeit'][:10]} {e['art']} – {kurz(e['titel'], 50)}" for e in bewertet[-3:][::-1]]
    z += ["", "## Wochentag (Likes im Schnitt, 30 Tage)", ""]
    tage = {}
    for e in bewertet:
        d = datetime.strptime(e["zeit"], "%Y-%m-%d %H:%M")
        tage.setdefault(TAGE[d.weekday()], []).append(e.get("tag3", e["aktuell"]).get("likes") or 0)
    z.append(" · ".join(f"{t}: {statistics.mean(tage[t]):.1f}" for t in TAGE if t in tage))
    z += ["", f"Rohdaten verschlüsselt in data/statistik/daten.enc · Abruf {roh.get('abgerufen', '')}"]
    open(os.path.join(ORDNER, "zusammenfassung.md"), "w", encoding="utf-8").write("\n".join(z) + "\n")


def grafik(verlauf, heute):
    """Balken je Beitrag der letzten 14 Tage (Reichweite, sonst Likes), Farbe = Format, mit Legende und Werten."""
    from bild import font
    grenze = (heute - timedelta(days=14)).isoformat()
    xs = sorted([e for e in verlauf["beitraege"].values() if e["zeit"] >= grenze], key=lambda e: e["zeit"])
    mass = "reach" if any(e["aktuell"].get("reach") is not None for e in xs) else "likes"
    W, zeile = 1200, 44
    H = 170 + max(1, len(xs)) * zeile + 60
    img = Image.new("RGB", (W, H), (252, 252, 251))
    d = ImageDraw.Draw(img)
    d.text((40, 30), f"{'Reichweite' if mass == 'reach' else 'Likes'} je Beitrag, letzte 14 Tage",
           font=font("h800", 34), fill=(30, 30, 30))
    x = 40
    for art, col in FARBE.items():                                   # Legende
        d.rounded_rectangle([x, 92, x + 22, 114], radius=4, fill=col)
        d.text((x + 30, 90), art, font=font("t400", 24), fill=(80, 80, 80))
        x += 60 + d.textlength(art, font=font("t400", 24))
    mx = max([e["aktuell"].get(mass) or 0 for e in xs] + [1])
    x0, x1 = 420, W - 110
    d.line([(x0, 150), (x0, 150 + len(xs) * zeile)], fill=(200, 200, 200), width=1)
    for i, e in enumerate(reversed(xs)):
        y = 150 + i * zeile
        v = e["aktuell"].get(mass) or 0
        d.text((40, y + 8), f"{e['zeit'][8:10]}.{e['zeit'][5:7]}. {kurz(e['titel'], 26)}", font=font("t400", 22),
               fill=(60, 60, 60))
        b = int((x1 - x0) * v / mx)
        if b > 0:
            d.rounded_rectangle([x0, y + 8, x0 + b, y + zeile - 8], radius=4, fill=FARBE.get(e["art"], (150, 150, 150)))
        d.text((x0 + b + 10, y + 8), str(v), font=font("t400", 22), fill=(60, 60, 60))
    d.text((40, H - 44), f"Stand {heute:%d.%m.%Y} · Werte aktuell · Quelle: Instagram-Schnittstelle",
           font=font("t400", 20), fill=(110, 110, 110))
    img.save(os.path.join(ORDNER, "wochenbild.png"), optimize=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
