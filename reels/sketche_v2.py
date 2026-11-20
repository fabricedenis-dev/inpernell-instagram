#!/usr/bin/env python3
"""Comic-Sketche im neuen Format (Wiedererkennung, Pointe mit Stille davor, Ba-dum-tss, Michael im Abschluss,
Meme-Musik von Kevin MacLeod, CC BY 4.0). Schreibt die Sketch-Termine in reels/warteschlange.json neu.
Neue Sketche bleiben gesperrt (freigegeben: false), bis der Inhaber sie freigibt."""
import json
import os
import sys

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
import zeichentrick_video as zv  # noqa: E402

M = "assets/musik/"


def L(wer, text, sprich, augen="normal", ruhe="neutral", arm="tisch", **kw):
    return dict(wer=wer, text=text, sprich=sprich, augen=augen, ruhe=ruhe, arm=arm, **kw)


def cap(zeile1, frage, musik):
    return (f"{zeile1}\n\nEin Zeichentrick-Sketch von Inpernell, deiner Personalvermittlung im Schwarzwald. "
            f"Direktvermittlung in Festanstellung, für dich kostenlos.\n\n{frage}\n\nTop Jobs aus der Region: Link in der Bio."
            f"\n\nMusik: {musik} von Kevin MacLeod (incompetech.com), CC BY 4.0"
            "\n\n#jobwechsel #bewerbung #arbeitsleben #schwarzwald #personalvermittlung")


POINTE = dict(sfx_vor="grillen", vor=1.3, pointe=True, sfx_nach="badumtss", nach=1.8)

gleitzeit = json.load(open(os.path.join(HIER, "reels", "sketch_gleitzeit.json"), encoding="utf-8"))

SKETCHE = [
    dict(id="2026-11-25-sketch-genz-wlan", datum="2026-11-25", zeit="12:00", thema="Sketch: Gen Z sucht einen Job",
         caption=cap("Wie es sich anfühlt, als Gen Z einen Job zu suchen 😅",
                     "Was war die ehrlichste Antwort, die du je im Vorstellungsgespräch gegeben hast?",
                     "Monkeys Spinning Monkeys"),
         sketch=dict(titel=zv.TITEL, dialog=zv.DIALOG, abspann=zv.ABSPANN_TEXT,
                     musik_datei=M + "monkeys_spinning_monkeys_kevin_macleod.mp3")),
    dict(id="2026-11-28-sketch-gleitzeit", datum="2026-11-28", zeit="11:00", thema="Sketch: Gleitzeit im Schwarzwald",
         caption=cap("Pendeln im Schwarzwald-Winter: Wenn der Recruiter Gleitzeit verspricht ❄️",
                     "Wie lang ist dein Arbeitsweg im Winter?", "Fluffing a Duck"),
         sketch=gleitzeit),
    dict(id="2026-12-02-sketch-runde-6", datum="2026-12-02", zeit="12:00", thema="Sketch: Runde 6",
         caption=cap("Bewerbungsgespräch Runde 6: Wenn das Auswahlverfahren kein Ende nimmt 😅",
                     "Wie viele Gesprächsrunden hattest du schon für einen einzigen Job?", "Sneaky Snitch"),
         sketch=dict(titel="Wenn das Bewerbungsgespräch in Runde 6 geht",
                     musik_datei=M + "sneaky_snitch_kevin_macleod.mp3",
                     abspann="Keine Lust auf Runde 6? Unsere Top Jobs aus der Region findest du hier.",
                     dialog=[
                         L("personaler", "Glückwunsch! Du bist in Runde 6!",
                           "[excited] Glückwunsch! Du bist in Runde sechs!", augen="gross", ruhe="grinsen",
                           arm="tisch_hoch", tag="RUNDE 6"),
                         L("genz", "Nach Telefoninterview, Fallstudie, Teamessen und Assessment-Center?",
                           "[exhausted] Nach Telefoninterview, Fallstudie, Teamessen und Assessment-Center?",
                           augen="muede", arm="handy", tag="RUNDE 1 BIS 5"),
                         L("personaler", "Leider haben wir die Stelle intern besetzt.",
                           "[apologetic] Leider haben wir die Stelle intern besetzt.", brauen="sorge"),
                         L("genz", "Mit wem?", "[shocked] Mit wem?", augen="gross", ruhe="schief", arm="achselzucken",
                           brauen="skeptisch", fx="fragezeichen"),
                         L("personaler", "Mit dem aus Runde 3. Der hat dich interviewt.",
                           "[awkward] Mit dem aus Runde drei. [pause] Der hat dich interviewt.", ruhe="schief",
                           fx="schweiss", **POINTE),
                     ])),
    dict(id="2026-12-05-sketch-laptop", datum="2026-12-05", zeit="11:00", thema="Sketch: Laptop kommt Montag",
         caption=cap("Erster Arbeitstag ohne Laptop: Onboarding, wie es jeder kennt 💻",
                     "Was war das Chaotischste an deinem ersten Arbeitstag?", "Carefree"),
         sketch=dict(titel="Erster Arbeitstag. Wo ist mein Laptop?",
                     musik_datei=M + "carefree_kevin_macleod.mp3",
                     abspann="Dein nächster Job startet hoffentlich mit Laptop. Top Jobs aus der Region findest du bei uns.",
                     dialog=[
                         L("genz", "Erster Tag! Wo ist mein Laptop?", "[excited] Erster Tag! Wo ist mein Laptop?",
                           augen="gross", ruhe="grinsen", arm="achselzucken", tag="TAG 1"),
                         L("personaler", "Kommt Montag.", "[cheerful] Kommt Montag.", ruhe="grinsen"),
                         L("genz", "Und? Mein Laptop?", "[impatient] Und? Mein Laptop?", augen="muede", arm="handy",
                           tag="TAG 8"),
                         L("personaler", "Kommt Montag.", "[cheerful] Kommt Montag.", ruhe="grinsen"),
                         L("genz", "Laptop? Kommt Montag.", "[deadpan] [cheerful] Laptop? Kommt Montag.",
                           augen="genervt", ruhe="grinsen", arm="tisch", tag="TAG 61: ER ZUM NEUEN", **POINTE),
                     ])),
    dict(id="2026-12-09-sketch-bewerbung-1995", datum="2026-12-09", zeit="12:00", thema="Sketch: Bewerbung 1995 vs. heute",
         caption=cap("Bewerbung 1995 vs. heute: Was hat sich wirklich verändert? 📮",
                     "Wie lange hast du schon mal auf eine Antwort auf deine Bewerbung gewartet?",
                     "Local Forecast - Elevator"),
         sketch=dict(titel="Bewerbung 1995 vs. heute",
                     musik_datei=M + "local_forecast_elevator_kevin_macleod.mp3",
                     abspann="Bewerben geht heute auch einfacher. Schreib uns einfach eine Nachricht.",
                     dialog=[
                         L("personaler", "Mappe, Passfoto, Briefmarke. Fertig.",
                           "[proud] Mappe, Passfoto, Briefmarke. Fertig.", ruhe="grinsen", sepia=True, tag="1995"),
                         L("genz", "45 Minuten Portal. Lebenslauf hochgeladen.",
                           "[tired] Fünfundvierzig Minuten Portal. Lebenslauf hochgeladen.", augen="muede", arm="handy",
                           tag="HEUTE"),
                         L("genz", "Und dann: Bitte alle Daten noch mal manuell eingeben.",
                           "[outraged] Und dann: Bitte alle Daten noch mal manuell eingeben.", augen="gross",
                           ruhe="schief", arm="handy", brauen="skeptisch", tag="HEUTE"),
                         L("personaler", "Und wann kam die Antwort?", "[curious] Und wann kam die Antwort?",
                           sepia=True, tag="1995"),
                         L("genz", "Nach drei Wochen. Wie bei dir. Nur automatisch.",
                           "[deadpan] Nach drei Wochen. Wie bei dir. [pause] Nur automatisch.", augen="genervt",
                           ruhe="schief", arm="achselzucken", tag="HEUTE", **POINTE),
                     ])),
]

if __name__ == "__main__":
    pfad = os.path.join(HIER, "reels", "warteschlange.json")
    q = json.load(open(pfad, encoding="utf-8"))
    alt = {r["id"]: r for r in q if "sketch" in r["id"]}
    q = [r for r in q if "sketch" not in r["id"]]
    for s in SKETCHE:
        s["freigegeben"] = bool(alt.get(s["id"], {}).get("freigegeben", False))   # Freigabe bleibt nur beim WLAN-Sketch
        s["fertig_video"] = f"reels/fertig/{s['id']}.mp4"
        s["fertig_titelbild"] = f"reels/fertig/{s['id']}.jpg"
        q.append(s)
    q.sort(key=lambda r: (r.get("datum", ""), r.get("zeit", "")))
    json.dump(q, open(pfad, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("geschrieben:", [s["id"] for s in SKETCHE])
