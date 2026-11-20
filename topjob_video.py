#!/usr/bin/env python3
"""Inpernell – „Top Job des Tages“ als gesprochenes Reel (Vorschau, wird hier NICHT veröffentlicht).

Ablauf: Sprechertext je Abschnitt (Einstieg, Aufgaben, Profil, Vorteile, Handlungsaufruf) → ElevenLabs v3
(Stimme „Michael Danisch“, jeder Abschnitt einzeln) → Wortzeiten per faster-whisper → je Abschnitt eine Folie im
Inpernell-Reel-Stil (reel_design), deren Bausteine genau dann erscheinen, wenn sie gesprochen werden →
mitlaufende Untertitel (gesprochenes Wort orange) im freien Band über dem kleinen Logo → leise eigene Musik
(musik.erzeuge_chill) unter der Stimme → loudnorm auf −14 LUFS → H.264/AAC.

Aufruf:  python topjob_video.py [job_id]     (ohne job_id: heute bzw. zuletzt gepostete Stelle aus dem Protokoll)
Ausgabe: vorschau/topjob-video/<JJJJ-MM-TT>-<jobid>.mp4, …-kontaktbogen.jpg, …-pruefung.json
"""
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import wave

import numpy as np
from PIL import Image, ImageDraw

import agent
import kategorien
import musik
import reel_anim as ra
import reel_design as rd
from bild import HELL, KNOPFTEXT, NAVY, ORANGE, PFIRSICH, WEISS, font, gesperrt, gesperrt_breite, wrap

W, H, FPS, SR = rd.W, rd.H, 30, 48000
M = rd.M                    # linker Rand 80
RECHTS = W - rd.R           # 940: rechts davon blendet Instagram zwischen y 1000 und 1700 die Knöpfe ein
INHALT_OBEN, INHALT_UNTEN = 285, 1225          # Folieninhalt (Feed-Ausschnitt, über dem Untertitel-Band)
UT_OBEN, UT_UNTEN = 1245, 1400                 # Untertitel-Band: unter dem Inhalt, über dem Logo (y 1420)
STIMME = "87AwpS6yC86wa2WglbsK"                # ElevenLabs: Michael Danisch – Deep and Soulful
HIER = os.path.dirname(os.path.abspath(__file__))
ZIELORDNER = os.path.join(HIER, "vorschau", "topjob-video")
VOR, NACH, ABSPANN = 0.28, 0.18, 2.2           # Pause vor/nach jedem Abschnitt, Standzeit der Abschlussfolie
_MODELL = {}

# Handgeschriebene Texte je Stelle (nur Fakten aus der Anzeige). Ohne Eintrag baut texte_aus_stelle() einen
# einfachen Text direkt aus den Listenpunkten der Anzeige.
TEXTE = {
    "2833534": {
        "einstieg": dict(
            sprich="[confident] Lust auf Software, die Elektronik testet? Dein Top Job des Tages: "
                   "Softwareentwickler für Testsysteme in Villingen-Schwenningen.",
            titel=["Software-", "entwickler"], untertitel="Testsysteme und Automatisierung (m/w/d)",
            chips=["Vollzeit · 40 h", "Hybrid / Homeoffice"],
            ausloeser=["Lust", "Software", "Top", "Softwareentwickler", "Villingen", "Villingen"]),
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
}


# ---------------------------------------------------------------- Stelle und Texte

def stelle_heute():
    """Heute bzw. zuletzt gepostete Stelle (letzte Protokollzeile mit echter media_id); sonst eine mit Gehalt."""
    stellen = agent.stellen_laden()
    nach_id = {str(s.get("id")): s for s in stellen}
    for z in reversed(agent.protokoll_lesen()):
        mid = (z.get("media_id") or "").strip()
        if mid.isdigit() and z.get("job_id") in nach_id:
            return nach_id[z["job_id"]]
    mit = [s for s in stellen if gehalt_plausibel(s)]
    return (mit or stellen)[0]


def gehalt_plausibel(s):
    """Gehaltsangabe nur, wenn sie zur Periode passt (z. B. „70 – 80 € / Jahr“ ist ein Eingabefehler)."""
    g = agent.gehalt(s)
    if not g:
        return ""
    sal = s.get("salary") or {}
    try:
        wert = float(sal.get("max") or sal.get("min"))
    except (TypeError, ValueError):
        return ""
    minimum = {"year": 10000, "month": 800, "hour": 8}.get((sal.get("period") or "").lower(), 0)
    return g if wert >= minimum else ""


def _gesprochen_gehalt(g):
    """„65.000 – 80.000 € / Jahr“ → „65.000 bis 80.000 Euro im Jahr“."""
    g = g.replace(" – ", " bis ").replace(" €", " Euro")
    return g.replace(" / Jahr", " im Jahr").replace(" / Monat", " im Monat").replace(" / Stunde", " pro Stunde")


def texte_aus_stelle(s):
    """Einfacher Ersatztext direkt aus der Anzeige (vollständige Listenpunkte, nichts erfunden)."""
    j = agent.aus_stelle(s, dt.date.today().isoformat())
    titel = re.sub(r"\s*\((m|w|d)/(m|w|d)/(m|w|d)\)\s*", "", j["titel"], flags=re.I).strip()
    g = gehalt_plausibel(s)
    ort = j["ort"]
    einstieg = f"[confident] Neuer Job gesucht{' in ' + ort if ort else ''}? Dann ist das dein Top Job des Tages: {titel}"
    einstieg += (f", mit {_gesprochen_gehalt(g)}." if g else ".")
    auf = [agent.kurzpunkt(p, 40) for p in j["aufgaben"]]
    auf = [p for p in auf if p][:3]
    anf = [agent.kurzpunkt(p, 40) for p in j["anforderungen"]]
    anf = [p for p in anf if p][:3]
    liste = lambda xs: ", ".join(xs[:-1]) + " und " + xs[-1] if len(xs) > 1 else (xs[0] if xs else "")
    modell = j["fakten"][2][1]
    vorteile = ["Festanstellung beim Arbeitgeber", "Keine Zeitarbeit", "Für dich kostenlos"]
    extra = ""
    if modell != "Vor Ort":
        vorteile.insert(2, modell)
        extra = f" {modell} ist möglich."
    return {
        "einstieg": dict(sprich=einstieg, titel=wrap(ImageDraw.Draw(Image.new("RGB", (1, 1))), titel,
                                                   font("h800", 96), RECHTS - M)[:3],
                         untertitel=g or j["fakten"][1][1], chips=[j["fakten"][1][1], modell],
                         ausloeser=None),
        "aufgaben": dict(sprich=f"Deine Aufgaben: {liste(auf)}.", punkte=[(p, "") for p in auf], ausloeser=None),
        "profil": dict(sprich=f"Das bringst du mit: {liste(anf)}.", punkte=[(p, "") for p in anf], ausloeser=None),
        "vorteile": dict(sprich="Und das Beste: Wir vermitteln dich direkt an den Arbeitgeber, in Festanstellung. "
                                f"Keine Zeitarbeit.{extra} Und für dich ist das Ganze komplett kostenlos.",
                         punkte=vorteile, ausloeser=None),
        "ende": dict(sprich="[warm] Klingt nach dir? Dann bewirb dich über den Link in der Bio oder schreib uns "
                            "einfach eine DM.", ausloeser=["Klingt", "bewirb", "Link", "DM"]),
    }


def anzeige_text(sprich):
    """Regieanweisungen in eckigen Klammern entfernen (nie in die Untertitel)."""
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", "", sprich)).strip()


# ---------------------------------------------------------------- Folien (Bausteine wie in reel_design)

def _grundbild(kat, foto_hoehe, basis, variante="oben"):
    if basis in ("schwarz", "weiss"):
        return Image.new("RGBA", (W, H), (0, 0, 0, 255) if basis == "schwarz" else (255, 255, 255, 255))
    return rd.grund(kat, foto_hoehe, variante)


def _pin(d, x, y, r, farbe):
    d.ellipse([x - r, y - r, x + r, y + r], fill=farbe)
    d.polygon([(x - r * 0.82, y + r * 0.5), (x + r * 0.82, y + r * 0.5), (x, y + r * 1.9)], fill=farbe)
    d.ellipse([x - r * 0.4, y - r * 0.4, x + r * 0.4, y + r * 0.4], fill=NAVY)


def _chip(d, x, y, text, f, fuell, schrift, rand=None):
    b = d.textlength(text, font=f) + 56
    d.rounded_rectangle([x, y, x + b, y + f.size + 34], radius=(f.size + 34) // 2, fill=fuell, outline=rand,
                        width=2 if rand else 0)
    d.text((x + 28, y + 17 + f.size // 2), text, font=f, fill=schrift, anchor="lm")
    return x + b


def folie_einstieg(kat, ort, titel, untertitel, chips, bis=99, nur=None, mit_kopf=False, basis="grund"):
    g = rd.Stufe(bis, nur)
    img = _grundbild(kat, 1150, basis)
    mess = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    groesse = 132
    while groesse > 64 and any(mess.textlength(z, font=font("h800", groesse)) > RECHTS - M for z in titel):
        groesse -= 4
    f = font("h800", groesse)
    y = 560
    for zeile in titel:                                  # Titelzeilen (je ein Baustein)
        if g():
            rd.marker_text(ImageDraw.Draw(img), (M, y), [zeile], f, set())
        y += int(groesse * 1.04)
    if g():
        rd.sticker(img, "TOP JOB DES TAGES", (M - 6, 330), winkel=-4, groesse=30)
    fu = font("h700", 44)
    zeilen = wrap(mess, untertitel, fu, RECHTS - M - 40)
    y += 26
    if g():
        d = ImageDraw.Draw(img)
        for i, z in enumerate(zeilen):
            tw = d.textlength(z, font=fu)
            d.rounded_rectangle([M, y + i * 74, M + tw + 40, y + i * 74 + 64], radius=12, fill=WEISS)
            d.text((M + 20, y + i * 74 + 32), z, font=fu, fill=NAVY, anchor="lm")
    y += 74 * len(zeilen) + 34
    if g() and ort:
        d = ImageDraw.Draw(img)
        _pin(d, M + 20, y + 22, 17, ORANGE)
        d.text((M + 56, y + 26), ort, font=font("h800", 50), fill=WEISS, anchor="lm")
    y += 96
    if g():
        d = ImageDraw.Draw(img)
        x = M
        fc = font("h700", 34)
        for c in chips:
            if x + d.textlength(c, font=fc) + 56 > RECHTS:
                break
            x = _chip(d, x, y, c, fc, rd.NAVY2, WEISS, rand=PFIRSICH) + 16
    return img


def folie_liste(kat, rubrik, ueberschrift, punkte, symbol="nummer", bis=99, nur=None, mit_kopf=False, basis="grund"):
    """Überschrift + drei Glas-Karten (Stichwort groß, kurze Zeile darunter)."""
    g = rd.Stufe(bis, nur)
    img = _grundbild(kat, 700, basis)
    if g():
        rd.sticker(img, rubrik.upper(), (M - 6, 300), winkel=-3, groesse=28)
        rd.marker_text(ImageDraw.Draw(img), (M, 400), [ueberschrift], font("h800", 84), set())
    y, hoehe, luecke = 560, 196, 26
    fk, fs = font("h800", 50), font("t400", 34)
    for i, (stich, zusatz) in enumerate(punkte):
        if g():
            rd.glas(img, [M, y, RECHTS, y + hoehe], radius=30)
            d = ImageDraw.Draw(img)
            if symbol == "nummer":
                d.text((M + 36, y + hoehe // 2), f"{i + 1:02d}", font=font("h800", 64), fill=ORANGE, anchor="lm")
            else:
                rd.icon_haken(d, M + 70, y + hoehe // 2, 32, ORANGE)
            tx = M + 136
            platz = RECHTS - tx - 30
            gross = 50
            while gross > 34 and d.textlength(stich, font=font("h800", gross)) > platz:
                gross -= 2
            if zusatz:
                d.text((tx, y + 62), stich, font=font("h800", gross), fill=WEISS, anchor="lm")
                zz = wrap(d, zusatz, fs, platz)
                for k, z in enumerate(zz[:2]):
                    d.text((tx, y + 118 + k * 42), z, font=fs, fill=HELL, anchor="lm")
            else:
                d.text((tx, y + hoehe // 2), stich, font=font("h800", gross), fill=WEISS, anchor="lm")
        y += hoehe + luecke
    return img


def folie_vorteile(kat, punkte, bis=99, nur=None, mit_kopf=False, basis="grund"):
    g = rd.Stufe(bis, nur)
    img = _grundbild(kat, 700, basis)
    if g():
        rd.sticker(img, "DEINE VORTEILE", (M - 6, 300), winkel=-3, groesse=28)
        rd.marker_text(ImageDraw.Draw(img), (M, 400), ["Direkt-", "vermittlung"], font("h800", 96), {"vermittlung"})
    y = 650
    for p in punkte:
        if g():
            rd.glas(img, [M, y, RECHTS, y + 118], radius=28)
            d = ImageDraw.Draw(img)
            rd.icon_haken(d, M + 58, y + 59, 28, rd.GRUEN)
            gross = 44
            while gross > 32 and d.textlength(p, font=font("h800", gross)) > RECHTS - M - 140:
                gross -= 2
            d.text((M + 110, y + 59), p, font=font("h800", gross), fill=WEISS, anchor="lm")
        y += 136
    return img


def folie_abschluss(kat, bis=99, nur=None, mit_kopf=False, basis="grund"):
    """Große Abschlussfolie: Logo mit „Direktvermittlung“ (steht von Anfang an), Frage, Link in der Bio, DM."""
    g = rd.Stufe(bis, nur)
    img = _grundbild(kat, 900, basis, variante="unten")
    if basis == "grund":
        lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
        rd.glas(img, [M, 1010, RECHTS, 1200], radius=36)
        img.alpha_composite(lg, (M + 36, 1040))
        gesperrt(ImageDraw.Draw(img), (M + 44, 1144), "DIREKTVERMITTLUNG", font("h700", 26), PFIRSICH, 5)
    if g():
        rd.marker_text(ImageDraw.Draw(img), (M, 340), ["Klingt", "nach dir?"], font("h800", 128), {"dir"})
    if g():
        ImageDraw.Draw(img).text((M, 640), "Jetzt bewerben, kostenlos", font=font("t700", 44), fill=HELL)
    if g():
        d = ImageDraw.Draw(img)
        fk = font("h800", 48)
        kt = "Link in der Bio"
        kw = d.textlength(kt, font=fk)
        d.rounded_rectangle([M, 740, M + kw + 150, 840], radius=50, fill=ORANGE)
        d.text((M + 44, 790), kt, font=fk, fill=KNOPFTEXT, anchor="lm")
        ax = M + 44 + kw + 22
        d.line([(ax, 790), (ax + 40, 790)], fill=KNOPFTEXT, width=6)
        d.line([(ax + 24, 774), (ax + 40, 790), (ax + 24, 806)], fill=KNOPFTEXT, width=6, joint="curve")
    if g():
        d = ImageDraw.Draw(img)
        _chip(d, M, 880, "oder schreib uns eine DM", font("h700", 38), rd.NAVY2, WEISS, rand=PFIRSICH)
    return img


# ---------------------------------------------------------------- Ton: ElevenLabs + Wortzeiten

def _asr():
    if "asr" not in _MODELL:
        os.environ.setdefault("HF_HOME", "/tmp/claude-0/-home-user-inpernell-instagram/"
                                         "28eed184-8c7d-52a4-8fed-76c2bb07f7fa/scratchpad/hf")
        from faster_whisper import WhisperModel
        _MODELL["asr"] = WhisperModel("small", device="cpu", compute_type="int8")
    return _MODELL["asr"]


def eleven_mp3(text, cache):
    """Ein Abschnitt als MP3 (zwischengespeichert, damit Wiederholungen keine Zeichen kosten)."""
    os.makedirs(cache, exist_ok=True)
    pfad = os.path.join(cache, hashlib.sha1((STIMME + "|eleven_v3|" + text).encode()).hexdigest()[:16] + ".mp3")
    if not os.path.exists(pfad):
        body = json.dumps({"text": text, "model_id": "eleven_v3", "language_code": "de"}).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{STIMME}?output_format=mp3_44100_128", data=body,
            headers={"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "proxy-injected"),
                     "Content-Type": "application/json", "Accept": "audio/mpeg"})
        with urllib.request.urlopen(req, timeout=180) as r:
            daten = r.read()
        with open(pfad, "wb") as f:
            f.write(daten)
        print(f"  ElevenLabs: {len(text)} Zeichen")
    return pfad


def dekodiere(pfad, sr=SR):
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", pfad, "-f", "s16le", "-ac", "1", "-ar", str(sr),
                          "pipe:1"], capture_output=True, check=True).stdout
    return np.frombuffer(roh, np.int16).astype(np.float32) / 32768


def _norm(w):
    return re.sub(r"[^0-9a-zäöüß+]", "", w.lower())


def transkribiere(ton, sr=SR):
    a16 = ton if sr == 16000 else np.interp(np.arange(int(len(ton) * 16000 / sr)) * sr / 16000,
                                            np.arange(len(ton)), ton).astype(np.float32)
    segs, _ = _asr().transcribe(a16, language="de", word_timestamps=True, beam_size=5, vad_filter=False)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words if w.word.strip()]


def zuordnen(woerter, erkannt):
    """Ordnet jedem Wort des Skripts Start/Ende aus der Erkennung zu (difflib), Lücken werden interpoliert.
    Bindestrich-Wörter zählen als ein Wort (Erkennung liefert sie oft geteilt)."""
    a = [_norm(w) for w in woerter]
    b = [_norm(w) for w, _, _ in erkannt]
    zeiten = [None] * len(a)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for blk in sm.get_opcodes():
        tag, i1, i2, j1, j2 = blk
        if tag == "equal":
            for k in range(i2 - i1):
                zeiten[i1 + k] = (erkannt[j1 + k][1], erkannt[j1 + k][2])
        elif tag == "replace" and j2 > j1:
            # gleich viele Zeichen → anteilig verteilen (z. B. „Villingen-Schwenningen“ = „Villingen“ + „Schwenningen“)
            t0, t1 = erkannt[j1][1], erkannt[j2 - 1][2]
            laengen = [max(1, len(x)) for x in a[i1:i2]]
            ges, acc = sum(laengen), 0
            for k, ln in enumerate(laengen):
                zeiten[i1 + k] = (t0 + (t1 - t0) * acc / ges, t0 + (t1 - t0) * (acc + ln) / ges)
                acc += ln
    # Interpolation für fehlende Wörter
    for i in range(len(zeiten)):
        if zeiten[i] is None:
            vor = next((zeiten[k][1] for k in range(i - 1, -1, -1) if zeiten[k]), 0.0)
            nach = next((zeiten[k][0] for k in range(i + 1, len(zeiten)) if zeiten[k]), vor + 0.3)
            zeiten[i] = (vor, max(vor + 0.05, (vor + nach) / 2))
    treffer = sum(1 for t in sm.get_opcodes() if t[0] == "equal" for _ in range(t[2] - t[1]))
    return zeiten, treffer / max(1, len(a))


def pausen_kuerzen(ton, laenger=0.36, rest=0.26, schwelle=0.008):
    """Lange Sprechpausen (v3 setzt bei dieser Stimme sehr lange Pausen) auf `rest` Sekunden kürzen.
    Nur echte Stille wird entfernt, die Stimme selbst bleibt unverändert (kein Zeitstrecken)."""
    f = int(0.01 * SR)
    rms = np.sqrt(np.convolve(ton ** 2, np.ones(f) / f, mode="same"))
    still = rms < schwelle
    teile, i, n = [], 0, len(ton)
    x = 0
    while x < n:
        if still[x]:
            y = x
            while y < n and still[y]:
                y += 1
            if (y - x) / SR > laenger and x > 0 and y < n:
                halb = int(rest * SR / 2)
                teile.append(ton[i:x + halb])
                i = y - halb
            x = y
        else:
            x += 1
    teile.append(ton[i:])
    return np.concatenate(teile)


def sprich_abschnitt(sprich, cache):
    """MP3 holen, dekodieren, vorn/hinten sauber schneiden (nichts nach dem letzten Wort), Wortzeiten ermitteln."""
    ton = pausen_kuerzen(dekodiere(eleven_mp3(sprich, cache)))
    woerter = anzeige_text(sprich).split()
    erkannt = transkribiere(ton)
    if not erkannt:
        raise RuntimeError("Spracherkennung fand keine Wörter: " + sprich)
    zeiten, quote = zuordnen(woerter, erkannt)
    laut = np.where(np.abs(ton) > 0.015)[0]
    anfang = max(0, int(laut[0]) - int(0.04 * SR)) if len(laut) else 0
    # Ende: letztes erkanntes Wort, das zum Skript gehört, plus Ausklang bis die Stimme verklungen ist
    ende_wort = zeiten[-1][1]
    ende = int((ende_wort + 0.12) * SR)
    fenster = int(0.02 * SR)
    grenze = min(len(ton), int((ende_wort + 0.45) * SR))
    while ende + fenster < grenze and np.sqrt(np.mean(ton[ende:ende + fenster] ** 2)) > 0.01:
        ende += fenster
    ton = ton[anfang:ende].copy()
    aus = min(len(ton), int(0.06 * SR))
    ton[-aus:] *= np.linspace(1, 0, aus)
    zeiten = [(max(0.0, a - anfang / SR), max(0.0, b - anfang / SR)) for a, b in zeiten]
    print(f"  erkannt ({quote:.0%}):", " ".join(w for w, _, _ in erkannt))
    return ton, woerter, zeiten, quote


# ---------------------------------------------------------------- Untertitel

UT_FONT = 54


def ut_bloecke(woerter, maxw=RECHTS - M - 40):
    """Teilt die Wörter in Blöcke von höchstens zwei Zeilen; Satzende und Doppelpunkt beenden einen Block."""
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    f = font("h800", UT_FONT)
    bloecke, zeilen, zeile = [], [], []
    for i, w in enumerate(woerter):
        probe = " ".join(woerter[k] for k in zeile + [i])
        if zeile and d.textlength(probe, font=f) > maxw:
            zeilen.append(zeile)
            zeile = []
            if len(zeilen) == 2:
                bloecke.append(zeilen)
                zeilen = []
        zeile.append(i)
        if re.search(r"[.?!:]$", w) or (re.search(r",$", w) and len(zeilen) == 1 and len(zeile) >= 2):
            zeilen.append(zeile)
            bloecke.append(zeilen)
            zeilen, zeile = [], []
    if zeile:
        zeilen.append(zeile)
    if zeilen:
        bloecke.append(zeilen)
    return bloecke


def zeichne_untertitel(frame, woerter, block, aktiv):
    d = ImageDraw.Draw(frame)
    f = font("h800", UT_FONT)
    hoehe = 70
    gesamt_h = hoehe * len(block)
    y = UT_OBEN + (UT_UNTEN - UT_OBEN - gesamt_h) // 2
    boxen = []
    for zeile in block:
        text = " ".join(woerter[k] for k in zeile)
        tw = d.textlength(text, font=f)
        x = (M + RECHTS) / 2 - tw / 2
        boxen.append((x, y, x + tw, y + hoehe))
        for k in zeile:
            wort = woerter[k]
            d.text((x, y + hoehe / 2), wort, font=f, fill=ORANGE if k == aktiv else WEISS, anchor="lm",
                   stroke_width=7, stroke_fill=NAVY)
            x += d.textlength(wort + " ", font=f)
        y += hoehe
    return boxen


# ---------------------------------------------------------------- Video bauen

def _ausloeser_index(woerter, liste, anzahl):
    """Wortindex je Baustein: Stichwort (erste Fundstelle ab dem vorigen Auslöser), sonst gleichmäßig verteilt."""
    if not liste:
        return [round(i * (len(woerter) - 1) / max(1, anzahl)) for i in range(anzahl)]
    idx, ab = [], 0
    for st in liste[:anzahl]:
        k = next((i for i in range(ab, len(woerter)) if _norm(woerter[i]).startswith(_norm(st))), ab)
        idx.append(k)
        ab = k
    while len(idx) < anzahl:
        idx.append(idx[-1])
    return idx


def abschnitte(stelle, texte):
    kat = kategorien.erkenne(stelle.get("title"), stelle.get("category_code"))
    ort = (stelle.get("city") or stelle.get("location") or "").split(",")[0].strip()
    t = texte
    return kat, [
        dict(name="einstieg", sprich=t["einstieg"]["sprich"], fn=folie_einstieg,
             kw=dict(kat=kat, ort=ort, titel=t["einstieg"]["titel"], untertitel=t["einstieg"]["untertitel"],
                     chips=t["einstieg"]["chips"]),
             schritte=len(t["einstieg"]["titel"]) + 4, ausloeser=t["einstieg"].get("ausloeser"),
             effekte=["punch"] * len(t["einstieg"]["titel"]) + ["pop", "links", "hoch", "hoch"]),
        dict(name="aufgaben", sprich=t["aufgaben"]["sprich"], fn=folie_liste,
             kw=dict(kat=kat, rubrik="Deine Aufgaben", ueberschrift="Das machst du", punkte=t["aufgaben"]["punkte"]),
             schritte=1 + len(t["aufgaben"]["punkte"]), ausloeser=t["aufgaben"].get("ausloeser"),
             effekte=["pop"] + ["links"] * len(t["aufgaben"]["punkte"])),
        dict(name="profil", sprich=t["profil"]["sprich"], fn=folie_liste,
             kw=dict(kat=kat, rubrik="Das bringst du mit", ueberschrift="Dein Profil", punkte=t["profil"]["punkte"],
                     symbol="haken"),
             schritte=1 + len(t["profil"]["punkte"]), ausloeser=t["profil"].get("ausloeser"),
             effekte=["pop"] + ["rechts"] * len(t["profil"]["punkte"])),
        dict(name="vorteile", sprich=t["vorteile"]["sprich"], fn=folie_vorteile,
             kw=dict(kat=kat, punkte=t["vorteile"]["punkte"]),
             schritte=1 + len(t["vorteile"]["punkte"]), ausloeser=t["vorteile"].get("ausloeser"),
             effekte=["pop"] + ["punch"] * len(t["vorteile"]["punkte"])),
        dict(name="ende", sprich=t["ende"]["sprich"], fn=folie_abschluss, kw=dict(kat=kat), schritte=4,
             ausloeser=t["ende"].get("ausloeser"), effekte=["punch", "hoch", "pop", "hoch"]),
    ]


def _musik_mix(stimme, sprech_maske, sprech_ende, gesamt, tmp):
    mwav = os.path.join(tmp, "musik.wav")
    musik.erzeuge_chill(gesamt + 0.5, mwav, "palm_breeze")
    with wave.open(mwav) as w:
        kanaele = w.getnchannels()
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    m = m.reshape(-1, kanaele)
    if kanaele == 1:
        m = np.repeat(m, 2, axis=1)
    n = len(stimme)
    m = np.pad(m, ((0, max(0, n - len(m))), (0, 0)))[:n]
    m = m / max(1e-6, np.abs(m).max())
    # Lautstärke der Musik: leise unter der Stimme (Ducking), in Pausen etwas mehr, im Abspann deutlich lauter
    ziel = np.where(sprech_maske, 0.075, 0.12)
    k = int(0.25 * SR)
    huelle = np.convolve(ziel, np.ones(k) / k, mode="same")
    a = int(sprech_ende * SR)
    if a < n:
        huelle[a:] = np.linspace(huelle[a], 0.32, n - a)
    ein, aus = int(0.4 * SR), int(1.0 * SR)
    huelle[:ein] *= np.linspace(0, 1, ein)
    huelle[-aus:] *= np.linspace(1, 0, aus)
    mix = m * huelle[:, None] + stimme[:, None] * 0.9
    roh = os.path.join(tmp, "mix.wav")
    _wav_schreiben(roh, mix / max(1e-6, np.abs(mix).max()) * 0.89)
    # loudnorm in zwei Durchgängen (genauer als einfach), Ziel −14 LUFS, Spitze −1,5 dBTP
    mess = subprocess.run(["ffmpeg", "-hide_banner", "-i", roh, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(mess[mess.rindex("{"):mess.rindex("}") + 1])
    norm = os.path.join(tmp, "mix_norm.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", roh, "-af",
                    f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
                    f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:"
                    "linear=true", "-ar", str(SR), norm], check=True)
    return norm


def _wav_schreiben(pfad, x):
    x = np.clip(x, -1, 1)
    with wave.open(pfad, "wb") as w:
        w.setnchannels(2 if x.ndim == 2 else 1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def erzeuge(stelle, ziel=None, texte=None):
    """Baut das Vorschau-Video für eine Stelle (Recruitee-Angebot als dict). Gibt (Pfad, Plan) zurück."""
    jid = str(stelle.get("id"))
    texte = texte or TEXTE.get(jid) or texte_aus_stelle(stelle)
    if ziel is None:
        os.makedirs(ZIELORDNER, exist_ok=True)
        ziel = os.path.join(ZIELORDNER, f"{dt.date.today().isoformat()}-{jid}.mp4")
    cache = os.path.join(os.path.dirname(ziel), "ton")
    kat, abs_ = abschnitte(stelle, texte)
    rd.KORN = 3
    tmp = tempfile.mkdtemp()

    # 1) Ton je Abschnitt + Zeitplan
    t = 0.0
    plan = []
    for a in abs_:
        print("Abschnitt", a["name"])
        ton, woerter, zeiten, quote = sprich_abschnitt(a["sprich"], cache)
        sprech = len(ton) / SR
        dauer = VOR + sprech + (ABSPANN if a["name"] == "ende" else NACH)
        idx = _ausloeser_index(woerter, a["ausloeser"], a["schritte"])
        plan.append(dict(a, start=t, ton=ton, woerter=woerter, zeiten=zeiten, quote=quote, dauer=dauer,
                         sprech=sprech, trigger=[max(0.0, VOR + zeiten[i][0] - 0.12) for i in idx]))
        t += dauer
    gesamt = t
    sprech_ende = plan[-1]["start"] + VOR + plan[-1]["sprech"]
    n = int(round(gesamt * FPS)) * SR // FPS
    stimme = np.zeros(n, np.float32)
    maske = np.zeros(n, bool)
    for p in plan:
        a = int((p["start"] + VOR) * SR)
        stimme[a:a + len(p["ton"])] += p["ton"][: n - a]
        maske[a:a + len(p["ton"])] = True
    tonpfad = _musik_mix(stimme, maske, sprech_ende, gesamt, tmp)

    # 2) Folien vorbereiten (Grundbild + Ebenen) und Ränder prüfen
    probleme = []
    for p in plan:
        p["grund"], p["ebenen"] = ra._ebenen(p["fn"], p["kw"], p["schritte"])
        for k, e in enumerate(p["ebenen"]):
            if e is None:
                continue
            x0, y0, x1, y1 = e[1]
            if x0 < M - 20 or x1 > RECHTS + 2 or y0 < INHALT_OBEN or y1 > INHALT_UNTEN:
                probleme.append(f"{p['name']} Baustein {k + 1}: {e[1]} außerhalb des Inhaltsbereichs")
        p["bloecke"] = ut_bloecke(p["woerter"])

    # 3) Bilder rendern
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", tonpfad, "-map", "0:v", "-map", "1:a", "-shortest",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-g", "60", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", ziel]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ut_plan = []          # (Abschnitt, Wortindex, Zeitpunkt der Hervorhebung) zur Prüfung
    anzahl = len(plan)
    versatz = 0
    for si, p in enumerate(plan):
        erst = {}
        for i in range(int(round(p["dauer"] * FPS))):
            tl = i / FPS
            z = 1.0 + 0.025 * (tl / p["dauer"]) + 0.04 * (1 - ra._ease(tl / 0.3))
            cw, ch = int(W / z), int(H / z)
            x, y = (W - cw) // 2, (H - ch) // 2
            frame = p["grund"].crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
            for eff, trig, eb in zip(p["effekte"], p["trigger"], p["ebenen"]):
                ra._zeige(frame, eb, eff, (tl - trig) / (0.7 if eff == "wisch" else 0.4))
            ra._fortschritt(frame, si, anzahl, tl / p["dauer"])
            if p["fn"] is not folie_abschluss:
                rd.logo_marke(frame)
            # Untertitel: Block des aktuellen Worts, das gesprochene Wort orange
            rel = tl - VOR
            if -0.05 <= rel <= p["sprech"] + 0.3:
                aktiv = max([k for k, (a, _) in enumerate(p["zeiten"]) if a <= rel] or [0])
                block = next(b for b in p["bloecke"] if any(aktiv in zl for zl in b))
                boxen = zeichne_untertitel(frame, p["woerter"], block, aktiv if rel <= p["zeiten"][-1][1] + 0.05 else -1)
                for bx in boxen:
                    if bx[0] < M - 10 or bx[2] > RECHTS + 10:
                        probleme.append(f"Untertitel zu breit: {p['name']} {bx}")
                if aktiv not in erst and rel >= 0:
                    erst[aktiv] = p["start"] + tl
            proc.stdin.write(frame.convert("RGB").tobytes())
        for k, zeit in erst.items():
            ut_plan.append(dict(abschnitt=p["name"], nr=versatz + k, wort=p["woerter"][k], zeit=zeit))
        versatz += len(p["woerter"])
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg konnte das Video nicht erzeugen.")
    info = dict(ziel=ziel, gesamt=gesamt, probleme=sorted(set(probleme)), untertitel=ut_plan,
                text=" ".join(anzeige_text(p["sprich"]) for p in plan),
                sprich=[p["sprich"] for p in plan], abschnitte=[(p["name"], p["start"], p["dauer"]) for p in plan],
                quoten={p["name"]: p["quote"] for p in plan},
                zeichen=sum(len(p["sprich"]) for p in plan))
    return ziel, info


# ---------------------------------------------------------------- Prüfung und Kontaktbogen

def pruefen(ziel, info):
    """Dauer, Transkript-Abgleich, Untertitel-Synchronität (Median), Lautstärke, Ränder."""
    dauer = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  ziel], capture_output=True, text=True).stdout)
    ton = dekodiere(ziel, 16000)
    erkannt = transkribiere(ton, 16000)
    soll = info["text"].split()
    zeiten, quote = zuordnen(soll, erkannt)
    a = [_norm(w) for w in soll]
    b = [_norm(w) for w, _, _ in erkannt]
    aehnlich = difflib.SequenceMatcher(None, " ".join(a), " ".join(b), autojunk=False).ratio()
    letztes = erkannt[-1] if erkannt else None
    # Untertitel: Zeitpunkt der Hervorhebung vs. erkannter Wortanfang im fertigen Video
    abw = []
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    paare = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                paare[i1 + k] = erkannt[j1 + k][1]
    for u in info["untertitel"]:
        if u["nr"] in paare:
            abw.append(u["zeit"] - paare[u["nr"]])
    loud = subprocess.run(["ffmpeg", "-hide_banner", "-i", ziel, "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    i_lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud)[-1])
    ende_sprache = letztes[2] if letztes else 0
    ergebnis = dict(
        dauer_s=round(dauer, 2), dauer_ok=40 <= dauer <= 50,
        transkript=" ".join(w for w, _, _ in erkannt),
        wort_treffer=round(quote, 3), zeichen_aehnlichkeit=round(aehnlich, 3),
        letztes_wort=letztes[0] if letztes else "", letztes_wort_ende_s=round(ende_sprache, 2),
        stille_danach_s=round(dauer - ende_sprache, 2),
        ut_median_ms=round(float(np.median(np.abs(abw))) * 1000, 1) if abw else None,
        ut_mittel_signiert_ms=round(float(np.mean(abw)) * 1000, 1) if abw else None,
        ut_p90_ms=round(float(np.percentile(np.abs(abw), 90)) * 1000, 1) if abw else None,
        ut_vergleiche=len(abw), lufs=i_lufs, true_peak_dbfs=tp, raender=info["probleme"] or "ok",
        elevenlabs_zeichen=info["zeichen"])
    return ergebnis


def kontaktbogen(ziel, info, pfad, anzahl=10):
    """10 Einzelbilder (je Abschnitt zwei Zeitpunkte) in einem JPG."""
    zeiten = []
    for name, start, dauer in info["abschnitte"]:
        zeiten += [start + dauer * 0.35, start + dauer * 0.9]
    zeiten = zeiten[:anzahl]
    bw, bh, sp = 360, 640, 5
    bogen = Image.new("RGB", (sp * bw + 6 * 16, 2 * (bh + 44) + 3 * 16), (240, 238, 232))
    d = ImageDraw.Draw(bogen)
    for i, zt in enumerate(zeiten):
        roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{zt:.2f}", "-i", ziel, "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"], capture_output=True, check=True).stdout
        bild = Image.frombytes("RGB", (W, H), roh).resize((bw, bh), Image.LANCZOS)
        x = 16 + (i % sp) * (bw + 16)
        y = 16 + (i // sp) * (bh + 44 + 16)
        bogen.paste(bild, (x, y + 44))
        d.text((x, y + 8), f"{zt:5.1f} s", font=font("h700", 26), fill=NAVY)
    bogen.save(pfad, "JPEG", quality=90)
    return pfad


def main():
    if len(sys.argv) > 1:
        stelle = next(s for s in agent.stellen_laden() if str(s.get("id")) == sys.argv[1])
    else:
        stelle = stelle_heute()
    print("Stelle:", stelle.get("id"), stelle.get("title"))
    ziel, info = erzeuge(stelle)
    erg = pruefen(ziel, info)
    bogen = kontaktbogen(ziel, info, ziel[:-4] + "-kontaktbogen.jpg")
    with open(ziel[:-4] + "-pruefung.json", "w", encoding="utf-8") as f:
        json.dump(dict(erg, sprechertext=info["sprich"], abschnitte=info["abschnitte"], quoten=info["quoten"]),
                  f, ensure_ascii=False, indent=1)
    print(json.dumps(erg, ensure_ascii=False, indent=1))
    print(ziel)
    print(bogen)


if __name__ == "__main__":
    main()
