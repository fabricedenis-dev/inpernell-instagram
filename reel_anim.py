"""Inpernell – animierte Reels aus den Folien von reel_design.py, im Takt der eigenen Musik (musik.py).

Jede Folie wird schrittweise gezeichnet (Baustein für Baustein). Aus dem Unterschied zweier Schritte entsteht
die Ebene eines Bausteins, die dann mit einem Effekt erscheint: Punch (kurz größer), Pop, von unten, von links/
rechts, Wischen (z. B. Durchstreichen, Balken). Szenen und Effekte liegen auf den Schlägen der Musik.
"""
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw

import reel_design as rd
from bild import ORANGE
from musik import erzeuge_track

W, H, FPS = rd.W, rd.H, 30


def _ease(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def _ueber(p):
    """Leichtes Überschwingen (Pop/Punch)."""
    p = min(1.0, max(0.0, p))
    c = 1.7
    return 1 + (c + 1) * (p - 1) ** 3 + c * (p - 1) ** 2


def _ebenen(fn, kwargs, schritte):
    """Grundbild und je Baustein eine RGBA-Ebene mit echter, weicher Transparenz.
    Jeder Baustein wird allein auf Schwarz und auf Weiß gezeichnet; aus beiden Bildern ergeben sich
    Deckkraft und Farbe exakt (keine harten, pixeligen Kanten)."""
    grund = fn(**kwargs, bis=0, mit_kopf=False).convert("RGBA")
    ebenen = []
    for k in range(1, schritte + 1):
        s = np.asarray(fn(**kwargs, nur=k, mit_kopf=False, basis="schwarz").convert("RGB")).astype(np.float32)
        w = np.asarray(fn(**kwargs, nur=k, mit_kopf=False, basis="weiss").convert("RGB")).astype(np.float32)
        alpha = np.clip(255.0 - (w - s).mean(axis=2), 0, 255)
        farbe = np.where(alpha[..., None] > 0, s * 255.0 / np.maximum(alpha[..., None], 1), 0)
        rgba = np.dstack([np.clip(farbe, 0, 255), alpha]).astype(np.uint8)
        ebene = Image.fromarray(rgba, "RGBA")
        box = ebene.getbbox()
        if not box:
            ebenen.append(None)
            continue
        ebenen.append((ebene.crop(box), box))
    return grund, ebenen


def _zeige(frame, ebene, effekt, p):
    if ebene is None or p <= 0:
        return
    img, (x0, y0, x1, y1) = ebene
    if p >= 1:
        frame.alpha_composite(img, (x0, y0))
        return
    w, h = img.size
    a = _ease(p / 0.6)
    if effekt in ("punch", "pop"):
        s = (1.25 - 0.25 * _ueber(p)) if effekt == "punch" else (0.4 + 0.6 * _ueber(p))
        s = max(0.05, s)
        neu = img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
        x, y = int(x0 + w / 2 - neu.width / 2), int(y0 + h / 2 - neu.height / 2)
        img, x0, y0 = neu, x, y
    elif effekt == "hoch":
        y0 += int((1 - _ease(p)) * 60)
    elif effekt == "links":
        x0 -= int((1 - _ease(p)) * 120)
    elif effekt == "rechts":
        x0 += int((1 - _ease(p)) * 120)
    elif effekt == "wisch":
        breite = max(1, int(w * _ease(p)))
        img = img.crop((0, 0, breite, h))
        a = 1.0
    if a < 1:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    frame.alpha_composite(img, (max(-img.width + 1, x0), y0))


def _fortschritt(frame, szene, anzahl, p):
    d = ImageDraw.Draw(frame)
    lg = Image.open(os.path.join(rd.HIER, "assets", "logo.png")).convert("RGBA")
    frame.alpha_composite(lg, (rd.M - 10, 96))
    luecke, y = 10, 210
    breite = (W - rd.M - rd.R - luecke * (anzahl - 1)) / anzahl
    for i in range(anzahl):
        x0 = rd.M + i * (breite + luecke)
        d.rounded_rectangle([x0, y, x0 + breite, y + 8], radius=4, fill=(88, 104, 136))
        f = 1.0 if i < szene else (p if i == szene else 0)
        if f > 0:
            d.rounded_rectangle([x0, y, x0 + max(8, breite * f), y + 8], radius=4, fill=ORANGE)


def erzeuge_reel(szenen, ziel, bpm=118, variante=0, titelbild=None):
    """szenen: Liste von dicts {fn, kwargs, takte, effekte: [(effekt, schlag), …]}"""
    schlag = 60.0 / bpm
    anzahl = len(szenen)
    dauern = [s["takte"] * 4 * schlag for s in szenen]
    gesamt = sum(dauern)
    ton = ziel + ".musik.wav"
    erzeuge_track(gesamt, ton, bpm=bpm, variante=variante)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", ton, "-map", "0:v", "-map", "1:a", "-shortest",
           "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-g", "60", "-maxrate", "9M", "-bufsize", "18M",
           "-profile:v", "high", "-tune", "film",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", ziel]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    titel = None
    for si, sz in enumerate(szenen):
        kw = dict(sz["kwargs"], szene=si, anzahl=anzahl)
        grund, ebenen = _ebenen(sz["fn"], kw, len(sz["effekte"]))
        dauer = dauern[si]
        for i in range(int(round(dauer * FPS))):
            t = i / FPS
            # langsamer Zoom auf das Grundbild + kurzer "Punch" beim Szenenwechsel
            z = 1.0 + 0.025 * (t / dauer) + 0.04 * (1 - _ease(t / 0.3))
            cw, ch = int(W / z), int(H / z)
            x, y = (W - cw) // 2, (H - ch) // 2
            frame = grund.crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
            for (effekt, takt_schlag), ebene in zip(sz["effekte"], ebenen):
                dauer_eff = 0.7 if effekt == "wisch" else 0.4
                _zeige(frame, ebene, effekt, (t - takt_schlag * schlag) / dauer_eff)
            _fortschritt(frame, si, anzahl, t / dauer)
            if si == 0 and titel is None and t >= 2.6:
                titel = frame.copy()
            proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg konnte das Reel nicht erzeugen.")
    os.remove(ton)
    if titelbild and titel is not None:
        titel.convert("RGB").save(titelbild, "JPEG", quality=90)
    return ziel


def gehalt_beispiel(ziel, titelbild=None):
    """Beispiel: 3 Fehler in der Gehaltsverhandlung (6 Szenen, 32 Sekunden)."""
    k = "personal"
    szenen = [
        {"fn": rd.folie_hook, "takte": 2,
         "kwargs": dict(kat=k, rubrik="Gehalts-Check", zeilen=["3 Fehler,", "die dich", "Geld kosten"],
                        markiert={"geld", "kosten"}, unterzeile="in der Gehaltsverhandlung"),
         "effekte": [("pop", 1.5), ("punch", -0.4), ("punch", 0.5), ("punch", 1.0), ("hoch", 2.5), ("hoch", 4)]},
    ]
    for nr, fehler, besser, detail in [
        (1, "Ohne eigene Zahl ins Gespräch", "Marktgehalt vorher checken",
         "Zum Beispiel im Entgeltatlas der Arbeitsagentur."),
        (2, "Nur übers Gehalt reden", "Das ganze Paket verhandeln",
         "Homeoffice, Weiterbildung und Urlaubstage zählen auch."),
        (3, "Sofort zusagen", "Einen Tag Bedenkzeit nehmen", "Das ist normal und wirkt professionell."),
    ]:
        szenen.append({"fn": rd.folie_vergleich, "takte": 3,
                       "kwargs": dict(kat=k, nr=nr, fehler=fehler, besser=besser, detail=detail),
                       "effekte": [("punch", 0), ("links", 1), ("wisch", 3), ("hoch", 5), ("hoch", 7)]})
    szenen.append({"fn": rd.folie_formulierung, "takte": 3,
                   "kwargs": dict(kat=k, ueberschrift="Und so nennst du deine Zahl",
                                  frage="Was stellen Sie sich beim Gehalt vor?",
                                  antwort="Mit meiner Erfahrung sehe ich mich bei 62.000 bis 66.000 Euro im Jahr.",
                                  tipp="Spanne nennen, Untergrenze realistisch"),
                   "effekte": [("pop", 0), ("hoch", 1), ("links", 2.5), ("rechts", 5), ("pop", 8)]})
    szenen.append({"fn": rd.folie_ende, "takte": 2,
                   "kwargs": dict(kat=k, titel_zeilen=["Speicher", "dir das ab"], markiert={"speicher"},
                                  zusatz="Und schick's an jemanden, der bald verhandelt."),
                   "effekte": [("pop", 0), ("punch", 1), ("hoch", 2.5), ("hoch", 4)]})
    return erzeuge_reel(szenen, ziel, variante=0, titelbild=titelbild)
