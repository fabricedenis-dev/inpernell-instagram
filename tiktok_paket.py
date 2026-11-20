#!/usr/bin/env python3
"""Inpernell – TikTok-Paket: fertige Videos, Beschreibungstexte und Plan-Bild zum Hochladen in TikTok Studio.

TikTok erlaubt kein eigenes Upload-Werkzeug für das eigene Konto; deshalb plant der Inhaber die Videos selbst in
TikTok Studio (Hochladen -> Planen). Dieses Skript liefert alles dafür.

Anpassungen für TikTok:
  * nur eigene Musik (Firmenkonten: keine fremde Musik außer Commercial Music Library) – das Game-Reel bekommt
    deshalb statt "Vice Police" den eigenen Track "Neon Nights"
  * Stellen-Video ("Job der Woche") mit Musik statt stiller Tonspur
  * kurze Beschreibung mit Suchbegriffen, offener Frage und 3–5 Hashtags

Aufruf: python tiktok_paket.py  ->  tiktok/<start>_bis_<ende>/ (Videos nicht im Repository, siehe .gitignore)
"""
import json
import os
import re
import subprocess
import sys
from datetime import date, timedelta

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

START = date(2026, 11, 23)
TAGE = 30
# Termine: Mo 18:00, Mi 18:00, Fr 17:00 (Abendstunden; nach 4 Wochen anhand der TikTok-Analyse anpassen)
PLAN = [
    ("2026-11-23", "18:00", "game", None),
    ("2026-11-25", "18:00", "reel", "2026-11-18-gehalts-check-1"),
    ("2026-11-27", "17:00", "job", 1),
    ("2026-11-30", "18:00", "reel", "2026-11-19-jobmarkt-region-1"),
    ("2026-12-02", "18:00", "reel", "2026-11-22-mythos-arbeitsrecht-1"),
    ("2026-12-04", "17:00", "job", 2),
    ("2026-12-07", "18:00", "reel", "2026-11-24-zeitarbeit-direktvermittlung"),
    ("2026-12-09", "18:00", "reel", "2026-11-26-lebenslauf-1"),
    ("2026-12-11", "17:00", "folgt", "Job der Woche (Stelle wird kurz vorher gewählt)"),
    ("2026-12-14", "18:00", "reel", "2026-11-29-medizintechnik-tuttlingen"),
    ("2026-12-16", "18:00", "folgt", "Neues Reel aus der Wochenplanung"),
    ("2026-12-18", "17:00", "folgt", "Job der Woche (Stelle wird kurz vorher gewählt)"),
]
GRUND_TAGS = ["#jobtok", "#jobsuche", "#schwarzwald"]


def _hashtags(ig_caption, extra=()):
    themen = [t for t in re.findall(r"#\w+", ig_caption) if t.lower() not in ("#topjobdestages", "#gaming")]
    tags = list(GRUND_TAGS) + list(extra)
    for t in themen:
        if len(tags) >= 5:
            break
        if t.lower() not in (x.lower() for x in tags):
            tags.append(t)
    return " ".join(tags[:5])


def tiktok_text(ig_caption, extra_tags=()):
    """Kurzfassung des Instagram-Bildtexts: Suchzeile, Kernpunkte (alle ❌/✅-Punkte), offene Frage, Hashtags."""
    zeilen = [z.strip() for z in ig_caption.split("\n")]
    zeilen = [z for z in zeilen if z and not z.startswith("#") and not z.startswith("Musik:")
              and "Link in der Bio" not in z and "Top Jobs aus der Region" not in z]
    suchzeile = zeilen[0]
    frage = next((z for z in zeilen[1:] if "?" in z and "❌" not in z), "")
    vergleiche = [z for z in zeilen[1:] if "❌" in z]
    punkte = vergleiche or [z for z in zeilen[1:] if z != frage][:3]
    teile = [suchzeile, ""] + punkte + (["", frage] if frage else [])
    teile += ["", "Top Jobs aus der Region: Link im Profil.", "", _hashtags(ig_caption, extra_tags)]
    return "\n".join(teile).strip() + "\n"


GAME_TEXT = """Personalvermittlung im Game-Modus: Mission Traumjob im Schwarzwald 🎮🌴

Ganz Deutschland zockt gerade. Wir haben trotzdem offen und vermitteln weiter: Festanstellung direkt beim Arbeitgeber, für dich kostenlos.

Die Crew: Fabrice (Industrie und IT), Pascal (Bank und Finanzen), Waldemar (Maschinenbau).

Welche Mission würdest du in deinem Job als Nächstes freischalten?

Top Jobs aus der Region: Link im Profil.

#jobtok #jobsuche #schwarzwald #personalvermittlung #gaming
"""


def mit_musik(video, ziel, bpm_variante=1):
    import musik
    dauer = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", video]).decode().strip())
    wav = ziel + ".wav"
    musik.erzeuge_track(dauer, wav, variante=bpm_variante)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", ziel],
                   check=True)
    os.remove(wav)


def stellen(anzahl):
    """Stellen mit Gehaltsangabe für "Job der Woche" (nicht die zuletzt auf Instagram gezeigten)."""
    import agent
    alle = agent.stellen_laden()
    gezeigt = {z.get("job_id") for z in agent.protokoll_lesen()}
    mit_gehalt = [s for s in alle if agent.gehalt(s) and str(s.get("id")) not in gezeigt]
    rest = [s for s in alle if s not in mit_gehalt and str(s.get("id")) not in gezeigt]
    return (mit_gehalt + rest)[:anzahl]


def main():
    ende = START + timedelta(days=TAGE - 1)
    ordner = os.path.join(HIER, "tiktok", f"{START:%Y-%m-%d}_bis_{ende:%Y-%m-%d}")
    os.makedirs(ordner, exist_ok=True)
    warteschlange = {r["id"]: r for r in json.load(open(os.path.join(HIER, "reels", "warteschlange.json"),
                                                         encoding="utf-8"))}
    jobs = stellen(2)
    eintraege = []
    for nr, (tag, zeit, art, ref) in enumerate(PLAN, 1):
        name = f"{nr:02d}_{tag}"
        video = os.path.join(ordner, name + ".mp4")
        e = {"nr": nr, "datum": tag, "zeit": zeit, "art": art, "datei": os.path.basename(video)}
        if art == "game":
            import game_reel as g
            g.MUSIK_DATEI, g.MUSIK, g.BPM = None, "neon_nights", 112
            g.SCHLAG = 60.0 / g.BPM
            if not os.path.exists(video):
                g.erzeuge(video, video.replace(".mp4", ".jpg"))
            r = warteschlange["2026-11-19-game-release"]
            e["titel"] = "Personalvermittlung im Game-Modus"
            text = GAME_TEXT
        elif art == "reel":
            import reel_anim
            r = warteschlange[ref]
            if not os.path.exists(video):
                reel_anim.aus_definition(r, video, titelbild=video.replace(".mp4", ".jpg"))
            hook = next((s for s in r["szenen"] if s["typ"] == "hook"), None)
            titel = ""
            for z in (hook["zeilen"] if hook else []):
                titel = titel[:-1] + z if titel.endswith("-") else (titel + " " + z).strip()
            e["titel"] = titel or r["id"]
            text = tiktok_text(r["caption"])
        elif art == "job":
            import agent
            from bild import erzeuge_reel
            s = jobs[ref - 1]
            post = agent.aus_stelle(s, date.fromisoformat(tag).strftime("%d.%m.%Y"))
            post["badge"], post["datum"] = "JOB DER WOCHE", ""
            if not os.path.exists(video):
                roh = video.replace(".mp4", "-roh.mp4")
                erzeuge_reel(post, roh, sekunden=12, titelbild=video.replace(".mp4", ".jpg"))
                mit_musik(roh, video, bpm_variante=ref)
                os.remove(roh)
            e["titel"] = "Job der Woche: " + post["titel"]
            ort = post.get("ort", "")
            eckdaten = [z for z in post["caption"].split("\n") if z[:1] in ("💶", "🕒", "🏠", "📍")]
            text = (f"Job der Woche: {post['titel']} in {ort}\n\n" + "\n".join(eckdaten)
                    + "\n\nDirektvermittlung: Du wirst direkt beim Arbeitgeber angestellt, keine Zeitarbeit, "
                      "für dich kostenlos.\n\nWäre das was für dich oder für jemanden, den du kennst?"
                    + "\n\nBewerben: Link im Profil.\n\n"
                    + _hashtags(post["caption"], [f"#jobs{re.sub(r'[^A-Za-zÄÖÜäöüß]', '', ort).lower()}"] if ort else []) + "\n")
        else:
            e["titel"] = ref
            eintraege.append(e)
            continue
        with open(os.path.join(ordner, name + ".txt"), "w", encoding="utf-8") as f:
            f.write(f"Veröffentlichen am {date.fromisoformat(tag):%d.%m.%Y} um {zeit} Uhr\n\n" + text)
        eintraege.append(e)
        print(name, e["titel"])
    plan_bild(eintraege, ordner)
    anleitung(eintraege, ordner)
    print(ordner)


def plan_bild(eintraege, ordner):
    from bild import HELL, NAVY, ORANGE, WEISS, font, wrap
    B, zeile = 1200, 230
    img = Image.new("RGB", (B, 260 + zeile * len(eintraege) + 80), NAVY)
    d = ImageDraw.Draw(img)
    d.text((60, 60), "TIKTOK-PLAN", font=font("h800", 70), fill=WEISS)
    d.text((60, 150), f"{START:%d.%m.} bis {START + timedelta(days=TAGE - 1):%d.%m.%Y} · 3 Videos pro Woche · "
                      "in TikTok Studio planen", font=font("t400", 30), fill=HELL)
    tage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    y = 250
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
        farbe = {"game": ORANGE, "reel": ORANGE, "job": (70, 150, 230), "folgt": (140, 152, 176)}[e["art"]]
        label = {"game": "SONDER-VIDEO", "reel": "VIDEO", "job": "JOB DER WOCHE", "folgt": "WIRD NACHGELIEFERT"}[e["art"]]
        d.text((x + 140, y + 30), f"{e['nr']:02d} · {label}", font=font("h800", 26), fill=farbe)
        for k, z in enumerate(wrap(d, e["titel"], font("h700", 34), B - 80 - x - 160)[:3]):
            d.text((x + 140, y + 72 + k * 42), z, font=font("h700", 34), fill=WEISS)
        y += zeile
    img.save(os.path.join(ordner, "00_tiktok-plan.png"), optimize=True)


def anleitung(eintraege, ordner):
    zeilen = ["# TikTok-Plan: so planst du die Videos ein", "",
              "1. Am Computer tiktok.com/tiktokstudio/upload öffnen und mit dem Inpernell-Konto anmelden.",
              "2. Video auswählen (Datei mit der Nummer aus der Liste unten).",
              "3. Beschreibung: den Text aus der gleichnamigen .txt-Datei einfügen (ohne die erste Zeile mit dem Termin).",
              "4. Titelbild: das Bild mit der gleichen Nummer bzw. ein Bild aus dem Video wählen.",
              "5. Unter „Wann posten“ auf „Planen“ stellen und Datum und Uhrzeit aus der Liste eintragen.",
              "6. Bei „Inhalte offenlegen“ nichts einschalten (eigene Werbung des eigenen Unternehmens ist erkennbar).",
              "7. „Planen“ klicken. Fertig.", "",
              "Hinweis: Musik ist eigene Musik, deshalb in TikTok keine weitere Musik hinzufügen.", "",
              "| Nr. | Termin | Inhalt | Datei |", "|---|---|---|---|"]
    for e in eintraege:
        datei = e["datei"] if e["art"] != "folgt" else "wird nachgeliefert"
        zeilen.append(f"| {e['nr']:02d} | {date.fromisoformat(e['datum']):%d.%m.} {e['zeit']} | {e['titel']} | {datei} |")
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
