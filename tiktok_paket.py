#!/usr/bin/env python3
"""Inpernell – TikTok-Paket: fertige Videos, Beschreibungstexte, Plan-Bild und Anleitung für TikTok Studio.

TikTok erlaubt kein eigenes Upload-Werkzeug für das eigene Konto; der Inhaber plant die Videos selbst in TikTok Studio.
Inhalte (Stand: vertonte Fassungen):
  * Reels aus reels/warteschlange.json (Sprecher Michael Danisch, Untertitel) – fertig_video
  * Comic-Sketche aus der Warteschlange – fertig_video (nicht freigegebene sind im Plan markiert)
  * "Job der Woche": Stelle mit Michael-Stimme (topjob_video.py), eigene Texte unten
  * Game-Reel mit eigener Musik statt "Vice Police" (TikTok-Firmenkonten: keine fremde Musik)

Aufruf: python tiktok_paket.py  ->  tiktok/<start>_bis_<ende>/ + ZIP (Videos nicht im Repository)
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

START = date(2026, 11, 23)
TAGE = 30
GRUND_TAGS = ["#jobtok", "#jobsuche", "#schwarzwald"]

# (Datum, Uhrzeit, Art, Bezug). Art: game | reel | sketch | job | folgt
PLAN = [
    ("2026-11-23", "18:00", "game", "2026-11-19-game-release"),
    ("2026-11-25", "18:00", "sketch", "2026-11-25-sketch-genz-wlan"),
    ("2026-11-27", "17:00", "job", "2833534"),
    ("2026-11-29", "18:00", "reel", "2026-11-22-mythos-arbeitsrecht-1"),
    ("2026-11-30", "18:00", "reel", "2026-11-24-zeitarbeit-direktvermittlung"),
    ("2026-12-02", "18:00", "sketch", "2026-12-02-sketch-staerken"),
    ("2026-12-04", "17:00", "job", "2771089"),
    ("2026-12-06", "18:00", "reel", "2026-11-26-lebenslauf-1"),
    ("2026-12-07", "18:00", "sketch", "2026-11-28-sketch-bewerbung-1995"),
    ("2026-12-09", "18:00", "sketch", "2026-12-09-sketch-gehalt"),
    ("2026-12-11", "17:00", "reel", "2026-11-29-medizintechnik-tuttlingen"),
    ("2026-12-13", "18:00", "sketch", "2026-12-05-sketch-faxgeraet"),
    ("2026-12-16", "18:00", "folgt", "Neues Reel aus der Wochenplanung"),
    ("2026-12-18", "17:00", "folgt", "Job der Woche (Stelle wird kurz vorher gewählt)"),
]

JOB_TEXTE = {
    "2833534": {
        "einstieg": dict(
            sprich="[confident] Lust auf Software, die Elektronik testet? Dein Job der Woche: Softwareentwickler für "
                   "Testsysteme in Villingen-Schwenningen, mit 70.000 bis 80.000 Euro im Jahr.",
            titel=["Software-", "entwickler"], untertitel="Testsysteme und Automatisierung (m/w/d)",
            chips=["70.000 – 80.000 € / Jahr", "Hybrid / Homeoffice"], badge="JOB DER WOCHE",
            ausloeser=["Lust", "Software", "Job", "Softwareentwickler", "Villingen", "70.000"]),
        "aufgaben": dict(
            sprich="Du entwickelst Software für automatisierte Testanlagen, programmierst Testabläufe und bindest "
                   "Messtechnik und Roboter ein.",
            punkte=[("Software für Testanlagen", "von der Konzeption bis zur Inbetriebnahme"),
                    ("Testabläufe programmieren", "für Komponenten, Baugruppen und Geräte"),
                    ("Messtechnik & Roboter", "Steuerungen und Automatisierung einbinden")],
            ausloeser=["Du", "entwickelst", "programmierst", "bindest"]),
        "profil": dict(
            sprich="Mitbringen solltest du ein Studium oder eine Ausbildung, idealerweise Erfahrung mit C, C++ "
                   "oder Python und gutes Deutsch und Englisch.",
            punkte=[("Studium oder Ausbildung", "z. B. Informatik, Elektrotechnik, Mechatronik"),
                    ("C, C++ oder Python", "Erfahrung wünschenswert, SQL ein Plus"),
                    ("Deutsch und Englisch", "gute Kenntnisse in beiden Sprachen")],
            ausloeser=["Mitbringen", "Studium", "idealerweise", "gutes"]),
        "vorteile": dict(
            sprich="Und das Beste: Wir vermitteln dich direkt in eine Festanstellung beim Arbeitgeber. Keine "
                   "Zeitarbeit, Homeoffice möglich, und für dich kostenlos.",
            punkte=["Festanstellung beim Arbeitgeber", "Keine Zeitarbeit", "Hybrid / Homeoffice möglich",
                    "Für dich kostenlos"],
            ausloeser=["Beste", "direkt", "Keine", "Homeoffice", "kostenlos"]),
        "ende": dict(
            sprich="[warm] Klingt nach dir? Dann bewirb dich über den Link in der Bio oder schreib uns einfach "
                   "eine DM.",
            ausloeser=["Klingt", "bewirb", "Link", "DM"]),
    },
    "2771089": {
        "einstieg": dict(
            sprich="[confident] Du kannst CNC-Drehmaschinen im Schlaf rüsten? Dein Job der Woche: Zerspanungsmechaniker "
                   "in Titisee, mit 50.000 bis 60.000 Euro im Jahr.",
            titel=["Zerspanungs-", "mechaniker"], untertitel="CNC-Drehen (m/w/d)",
            chips=["50.000 – 60.000 € / Jahr", "Vollzeit · 40 h"], badge="JOB DER WOCHE",
            ausloeser=["Du", "CNC", "Job", "Zerspanungsmechaniker", "Titisee", "50.000"]),
        "aufgaben": dict(
            sprich="Du rüstest, richtest ein und programmierst CNC-Drehmaschinen, fährst Neu- und Serienteile ein und "
                   "behebst Störungen selbstständig.",
            punkte=[("CNC-Drehmaschinen", "rüsten, einrichten und programmieren"),
                    ("Neu- und Serienteile", "einfahren, optimieren und betreuen"),
                    ("Störungen beheben", "selbstständig analysieren und lösen")],
            ausloeser=["Du", "rüstest", "fährst", "behebst"]),
        "profil": dict(
            sprich="Mitbringen solltest du eine Ausbildung als Zerspanungsmechaniker oder Industriemechaniker, "
                   "Qualitätsbewusstsein und die Bereitschaft zur Schichtarbeit.",
            punkte=[("Abgeschlossene Ausbildung", "Zerspanung, Industriemechanik o. Ä."),
                    ("Qualitätsbewusstsein", "sorgfältig mit Produkten und Prozessen"),
                    ("Schichtarbeit", "Flexibilität und Bereitschaft")],
            ausloeser=["Mitbringen", "Ausbildung", "Qualitätsbewusstsein", "Bereitschaft"]),
        "vorteile": dict(
            sprich="Und das Beste: Wir vermitteln dich direkt in eine Festanstellung beim Arbeitgeber. Keine "
                   "Zeitarbeit, und für dich kostenlos.",
            punkte=["Festanstellung beim Arbeitgeber", "Keine Zeitarbeit", "Für dich kostenlos"],
            ausloeser=["Beste", "direkt", "Keine", "kostenlos"]),
        "ende": dict(
            sprich="[warm] Klingt nach dir? Dann bewirb dich über den Link in der Bio oder schreib uns einfach "
                   "eine DM.",
            ausloeser=["Klingt", "bewirb", "Link", "DM"]),
    },
}


def _hashtags(caption, extra=()):
    themen = [t for t in re.findall(r"#\w+", caption) if t.lower() not in ("#topjobdestages", "#gaming")]
    tags = list(GRUND_TAGS) + list(extra)
    for t in themen:
        if len(tags) >= 5:
            break
        if t.lower() not in (x.lower() for x in tags):
            tags.append(t)
    return " ".join(tags[:5])


def tiktok_text(ig_caption, extra_tags=()):
    zeilen = [z.strip() for z in ig_caption.split("\n")]
    zeilen = [z for z in zeilen if z and not z.startswith("#") and not z.startswith("Musik:")
              and "Link in der Bio" not in z and "Top Jobs aus der Region" not in z]
    frage = next((z for z in zeilen[1:] if "?" in z and "❌" not in z), "")
    vergleiche = [z for z in zeilen[1:] if "❌" in z]
    punkte = vergleiche or [z for z in zeilen[1:] if z != frage][:3]
    teile = [zeilen[0], ""] + punkte + (["", frage] if frage else [])
    teile += ["", "Top Jobs aus der Region: Link im Profil.", "", _hashtags(ig_caption, extra_tags)]
    return "\n".join(teile).strip() + "\n"


GAME_TEXT = """Personalvermittlung im Game-Modus: Mission Traumjob im Schwarzwald 🎮🌴

Ganz Deutschland zockt gerade. Wir haben trotzdem offen und vermitteln weiter: Festanstellung direkt beim Arbeitgeber, für dich kostenlos.

Die Crew: Fabrice (Industrie und IT), Pascal (Bank und Finanzen), Waldemar (Maschinenbau).

Welche Mission würdest du in deinem Job als Nächstes freischalten?

Top Jobs aus der Region: Link im Profil.

#jobtok #jobsuche #schwarzwald #personalvermittlung #gaming
"""


def main():
    ende = START + timedelta(days=TAGE - 1)
    ordner = os.path.join(HIER, "tiktok", f"{START:%Y-%m-%d}_bis_{ende:%Y-%m-%d}")
    if os.path.isdir(ordner):
        shutil.rmtree(ordner)
    os.makedirs(ordner)
    q = {r["id"]: r for r in json.load(open(os.path.join(HIER, "reels", "warteschlange.json"), encoding="utf-8"))}
    eintraege = []
    for nr, (tag, zeit, art, ref) in enumerate(PLAN, 1):
        name = f"{nr:02d}_{tag}"
        video = os.path.join(ordner, name + ".mp4")
        bild = video.replace(".mp4", ".jpg")
        e = {"nr": nr, "datum": tag, "zeit": zeit, "art": art, "datei": os.path.basename(video), "hinweis": ""}
        if art == "folgt":
            e["titel"] = ref
            eintraege.append(e)
            continue
        if art == "game":
            import game_reel as g
            g.MUSIK_DATEI, g.MUSIK, g.BPM = None, "neon_nights", 112
            g.SCHLAG = 60.0 / g.BPM
            g.erzeuge(video, bild)
            e["titel"] = "Personalvermittlung im Game-Modus"
            text = GAME_TEXT
        elif art in ("reel", "sketch"):
            r = q[ref]
            if not r.get("fertig_video") or not os.path.exists(os.path.join(HIER, r["fertig_video"])):
                raise RuntimeError(f"{ref}: fertiges Video fehlt (reel_vertont.py / zeichentrick_video.py)")
            shutil.copyfile(os.path.join(HIER, r["fertig_video"]), video)
            shutil.copyfile(os.path.join(HIER, r["fertig_titelbild"]), bild)
            e["titel"] = (r.get("thema") or r["caption"].split("\n")[0]).replace("Sketch: ", "Sketch: ")
            if art == "reel":
                hook = next(s for s in r["szenen"] if s["typ"] == "hook")
                titel = ""
                for z in hook["zeilen"]:
                    titel = titel[:-1] + z if titel.endswith("-") else (titel + " " + z).strip()
                e["titel"] = titel
            if art == "sketch" and not r.get("freigegeben"):
                e["hinweis"] = "erst nach Freigabe posten"
            text = tiktok_text(r["caption"], ["#comedy"] if art == "sketch" else ())
        else:   # job
            import agent
            import topjob_video as tv
            s = next(x for x in agent.stellen_laden() if str(x["id"]) == ref)
            tv.erzeuge(s, video, JOB_TEXTE[ref])
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "2.5", "-i", video, "-frames:v", "1", "-q:v", "2",
                            bild], check=True)
            post = agent.aus_stelle(s, date.fromisoformat(tag).strftime("%d.%m.%Y"))
            e["titel"] = "Job der Woche: " + post["titel"]
            ort = post.get("ort", "")
            eckdaten = [z for z in post["caption"].split("\n") if z[:1] in ("💶", "🕒", "🏠", "📍")]
            text = (f"Job der Woche: {post['titel']} in {ort}\n\n" + "\n".join(eckdaten)
                    + "\n\nDirektvermittlung: Du wirst direkt beim Arbeitgeber angestellt, keine Zeitarbeit, "
                      "für dich kostenlos.\n\nWäre das was für dich oder für jemanden, den du kennst?"
                    + "\n\nBewerben: Link im Profil.\n\n"
                    + _hashtags(post["caption"], [f"#jobs{re.sub(r'[^A-Za-zÄÖÜäöüß]', '', ort).lower()}"] if ort else [])
                    + "\n")
        with open(os.path.join(ordner, name + ".txt"), "w", encoding="utf-8") as f:
            f.write(f"Veröffentlichen am {date.fromisoformat(tag):%d.%m.%Y} um {zeit} Uhr"
                    + (f" ({e['hinweis']})" if e["hinweis"] else "") + "\n\n" + text)
        eintraege.append(e)
        print(name, e["titel"])
    plan_bild(eintraege, ordner)
    anleitung(eintraege, ordner)
    zip_pfad = os.path.join(HIER, "tiktok", f"TikTok-Paket_{START:%Y-%m-%d}_bis_{ende:%Y-%m-%d}")
    shutil.make_archive(zip_pfad, "zip", os.path.dirname(ordner), os.path.basename(ordner))
    print(ordner, zip_pfad + ".zip")


def plan_bild(eintraege, ordner):
    from bild import HELL, NAVY, ORANGE, WEISS, font, wrap
    B, zeile = 1200, 230
    img = Image.new("RGB", (B, 260 + zeile * len(eintraege) + 80), NAVY)
    d = ImageDraw.Draw(img)
    d.text((60, 60), "TIKTOK-PLAN", font=font("h800", 70), fill=WEISS)
    d.text((60, 150), f"{START:%d.%m.} bis {START + timedelta(days=TAGE - 1):%d.%m.%Y} · in TikTok Studio planen",
           font=font("t400", 30), fill=HELL)
    tage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    y = 250
    farben = {"game": ORANGE, "reel": ORANGE, "sketch": (236, 120, 190), "job": (70, 150, 230), "folgt": (140, 152, 176)}
    labels = {"game": "SONDER-VIDEO", "reel": "VIDEO MIT SPRECHER", "sketch": "COMIC-SKETCH", "job": "JOB DER WOCHE",
              "folgt": "WIRD NACHGELIEFERT"}
    for e in eintraege:
        tag = date.fromisoformat(e["datum"])
        d.rounded_rectangle([40, y, B - 40, y + zeile - 20], radius=22, fill=(18, 40, 78), outline=(52, 74, 112), width=2)
        d.text((70, y + 30), f"{tage[tag.weekday()]} {tag:%d.%m.}", font=font("h800", 40), fill=WEISS)
        d.text((70, y + 90), f"{e['zeit']} Uhr", font=font("t400", 30), fill=HELL)
        bild = os.path.join(ordner, e["datei"].replace(".mp4", ".jpg"))
        x = 300
        if os.path.exists(bild):
            img.paste(Image.open(bild).convert("RGB").resize((106, 188), Image.LANCZOS), (x, y + 10))
        else:
            d.rounded_rectangle([x, y + 10, x + 106, y + 198], radius=10, outline=(140, 152, 176), width=2)
            d.text((x + 53, y + 104), "folgt", font=font("h700", 24), fill=(140, 152, 176), anchor="mm")
        d.text((x + 140, y + 30), f"{e['nr']:02d} · {labels[e['art']]}", font=font("h800", 26), fill=farben[e["art"]])
        zeilen = wrap(d, e["titel"], font("h700", 34), B - 80 - x - 160)[:2]
        for k, z in enumerate(zeilen):
            d.text((x + 140, y + 72 + k * 42), z, font=font("h700", 34), fill=WEISS)
        if e["hinweis"]:
            hy = y + 72 + len(zeilen) * 42 + 4
            d.ellipse([x + 140, hy + 9, x + 156, hy + 25], fill=ORANGE)
            d.text((x + 166, hy), e["hinweis"], font=font("t400", 26), fill=ORANGE)
        y += zeile
    img.save(os.path.join(ordner, "00_tiktok-plan.png"), optimize=True)


def anleitung(eintraege, ordner):
    zeilen = ["# TikTok-Plan: so planst du die Videos ein", "",
              "1. Am Computer tiktok.com/tiktokstudio/upload öffnen und mit dem Inpernell-Konto anmelden.",
              "2. Video mit der Nummer aus der Liste auswählen.",
              "3. Beschreibung aus der gleichnamigen .txt-Datei einfügen (ohne die erste Zeile mit dem Termin).",
              "4. Titelbild: das Bild mit der gleichen Nummer.",
              "5. Unter „Wann posten“ auf „Planen“ stellen, Datum und Uhrzeit aus der Liste eintragen.",
              "6. „Planen“ klicken.", "",
              "Hinweise: Alle Videos haben bereits Ton (Sprecher bzw. eigene Musik): in TikTok keine Musik hinzufügen. "
              "Sketche mit dem Vermerk „erst nach Freigabe posten“ sind noch nicht freigegeben.", "",
              "| Nr. | Termin | Inhalt | Datei |", "|---|---|---|---|"]
    for e in eintraege:
        datei = e["datei"] if e["art"] != "folgt" else "wird nachgeliefert"
        hinweis = f" ({e['hinweis']})" if e["hinweis"] else ""
        zeilen.append(f"| {e['nr']:02d} | {date.fromisoformat(e['datum']):%d.%m.} {e['zeit']} | {e['titel']}{hinweis} | {datei} |")
    zeilen += ["", "## Beschreibungen zum Kopieren", ""]
    for e in eintraege:
        txt = os.path.join(ordner, e["datei"].replace(".mp4", ".txt"))
        if e["art"] != "folgt" and os.path.exists(txt):
            inhalt = open(txt, encoding="utf-8").read().split("\n", 2)[2].strip()
            zeilen += [f"### {e['nr']:02d} · {date.fromisoformat(e['datum']):%d.%m.} {e['zeit']} · {e['titel']}", "",
                       "```", inhalt, "```", ""]
    with open(os.path.join(ordner, "ANLEITUNG.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen) + "\n")


if __name__ == "__main__":
    main()
