#!/usr/bin/env python3
"""Animiertes Meme-Video „Jensen nach 11 Tagen zurück“ im flachen Cartoon-Stil (privater Account, Satire).
Figuren bewegen sich (Wippen, Blinzeln, Mund im Takt der Stimme, Jubel-Arme, Controller), Stimmen aus der
ElevenLabs-Bibliothek (keine Nachahmung), Sprechblasen Wort für Wort, Meme-Sounds, Musik „Fluffing a Duck“
(Kevin MacLeod, CC BY 4.0).
Aufruf: python werkzeuge/meme_huang_flat_video.py  ->  vorschau/memes/meme_huang_flat.mp4"""
import math
import os
import random
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import flat_cartoon as fc  # noqa: E402
import meme_huang_video as mh  # noqa: E402
import topjob_video as tv  # noqa: E402
from bild import font  # noqa: E402

W, H, FPS, SR = fc.W, fc.H, 30, 48000
ZIEL = os.path.join(HIER, "vorschau", "memes", "meme_huang_flat.mp4")
CACHE = os.path.join(HIER, "vorschau", "memes", "ton")
MUSIK = os.path.join(HIER, "assets", "musik", "fluffing_a_duck_kevin_macleod.mp3")
STIMME = {"chef": "IWm8DnJ4NGjFI7QAM5lM", "jensen": "gGjaVIGkCSfKUIBYtNT2"}   # Stephan, Marc (Bibliothek)

# Szenen: (Ort, Oben-Text, [(Sprecher, Text, Pause davor)], Nachlauf, Einstellungen)
SZENEN = [
    ("buero", "POV: Jensen nach 11 Tagen Pause zurück bei Nvidia",
     [("chef", "[cheerful] Willkommen zurück! Was hast du gemacht?", 0.6)], 0.4, dict(jensen="jubel")),
    ("buero", None, [("jensen", "[serious] Reflektiert. An mir gearbeitet. Viel nachgedacht.", 0.3)], 0.5,
     dict(jensen="seriös")),
    ("sofa", "Was er wirklich gemacht hat:", [], 2.4, dict(tv=("GTA VI", "Tag 1"))),
    ("sofa", "Was er wirklich gemacht hat:", [("jensen", "[excited] Ja! 100 Prozent!", 0.6)], 0.8,
     dict(tv=("Tag 11", "100 % abgeschlossen"), jubel=True)),
    ("buero", None, [("chef", "[curious] Und? Hast du was gelernt?", 0.3),
                     ("jensen", "[proud] Ja. Fluchtwagen fahren ist auch Führungserfahrung.", 0.4)], 0.6,
     dict(jensen="stolz")),
    ("buero", None, [("chef", "[stunned] Okay. Du bist eingestellt.", 0.7)], 1.8, dict(jensen="zeigen", ende=True)),
]

_FIG = {}


def fig(**kw):
    key = tuple(sorted(kw.items()))
    if key not in _FIG:
        _FIG[key] = fc.figur(**kw)
    return _FIG[key]


HG = {"buero": fc.hintergrund_buero(), "sofa": fc.hintergrund_wohnzimmer()}


def satire(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([W - 210, 1440, W - 40, 1490], radius=12, fill=(226, 60, 60))
    d.text((W - 125, 1465), "SATIRE", font=font("h800", 28), fill=(255, 255, 255), anchor="mm")


def bauen():
    szenen, t = [], 0.0
    for ort, oben, saetze, nach, opt in SZENEN:
        teile, rel = [], 0.0
        for wer, text, vor in saetze:
            tv.STIMME = STIMME[wer]
            ton, woerter, zeiten, _q = tv.sprich_abschnitt(text, CACHE)
            rel += vor
            teile.append(dict(wer=wer, text=tv.anzeige_text(text), ton=ton, zeiten=zeiten, start=rel))
            rel += len(ton) / SR
        dauer = rel + nach
        szenen.append(dict(ort=ort, oben=oben, teile=teile, start=t, dauer=dauer, opt=opt))
        t += dauer
    return szenen, t


def spricht(sz, rel):
    """(Sprecher, Mund offen?) zum Zeitpunkt rel."""
    for tl in sz["teile"]:
        r = rel - tl["start"]
        if 0 <= r < len(tl["ton"]) / SR:
            i = int(r * SR)
            rms = float(np.sqrt(np.mean(tl["ton"][i:i + SR // FPS] ** 2) + 1e-9))
            return tl["wer"], rms > 0.03 and int(r * FPS) % 4 != 3
    return None, False


def blasen(img, sz, rel):
    """Sprechblase des aktuellen bzw. letzten Satzes, Wort für Wort."""
    y = fc.text_oben(img, sz["oben"]) + 40 if sz["oben"] else 260
    sichtbar = [tl for tl in sz["teile"] if rel >= tl["start"] - 0.05]
    for k, tl in enumerate(sichtbar[-2:]):
        r = rel - tl["start"]
        n = sum(1 for a, _ in tl["zeiten"] if a <= r + 0.05)
        worte = tl["text"].split()
        if n <= 0:
            continue
        teil = " ".join(worte[:n])
        if tl["wer"] == "chef":
            fc.blase(img, teil, 60, y, w=560)
        else:
            fc.blase(img, teil, 440, y + (0 if k == 0 and len(sichtbar) == 1 else 260), w=580, rechts=True)


def frame(sz, rel, k, blinz):
    img = HG[sz["ort"]].copy()
    opt = sz["opt"]
    wer, offen = spricht(sz, rel)
    wippen = int(6 * math.sin(k * 0.25))
    if sz["ort"] == "buero":
        chef_g = "schock" if opt.get("ende") and rel > 0.6 else ("fragend" if not opt.get("jensen") == "jubel" else "laecheln")
        c = fig(haar="glatze", brille=False, jacke="anzug", gesicht=chef_g, mund_offen=(wer == "chef" and offen),
                blinzeln=(k in blinz and chef_g != "schock"))
        jarm, jges = "unten", "laecheln"
        if opt.get("jensen") == "jubel":
            jarm = "jubel" if (k // 6) % 2 == 0 else "jubel2"
        elif opt.get("jensen") == "seriös":
            jges = "geschlossen"
        elif opt.get("jensen") == "stolz":
            jges = "seitenblick"
        elif opt.get("jensen") == "zeigen":
            jarm = "zeigen"
        j = fig(gesicht=jges, arm=jarm, mund_offen=(wer == "jensen" and offen),
                blinzeln=(k in blinz and jges not in ("geschlossen",)))
        img.paste(c, (30, 720 + wippen), c)
        img.paste(j, (540, 720 - wippen), j)
    else:
        jub = opt.get("jubel") and rel > 0.4
        arm = ("jubel" if (k // 5) % 2 == 0 else "jubel2") if jub else "controller"
        j = fig(jacke="hoodie", pose="sitzt", gesicht="laecheln" if jub else "seitenblick", arm=arm,
                mund_offen=(wer == "jensen" and offen), blinzeln=(k in blinz))
        dx = random.Random(k).randint(-4, 4) if arm == "controller" else 0      # hektisches Drücken
        img.paste(j, (280 + dx, 840 + (abs(wippen) if jub else 0)), j)
        t1, t2 = opt["tv"]
        farbe = (120, 230, 120) if "100" in t2 else (255, 255, 255)
        fc.fernseher(img, [(t1, (255, 200, 60)), (t2, farbe)], y=560)
        if random.Random(k // 3).random() < 0.3:                                  # Bildschirm flackert
            d = ImageDraw.Draw(img)
            d.rectangle([150, 570, 650, 880], outline=(90, 200, 255), width=4)
    if sz["opt"].get("ende") and rel > 0.7:                                       # Zoom auf Jensens Grinsen
        z = 1 + 0.35 * min(1, (rel - 0.7) / 0.5)
        cw, ch = int(W / z), int(H / z)
        x0, y0 = min(W - cw, int(800 - cw / 2)), max(0, int(900 - ch / 2))
        img = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
    blasen(img, sz, rel)                                                          # nach dem Zoom: immer lesbar
    satire(img)
    return img


def tonspur(szenen, gesamt):
    n = int(gesamt * SR)
    mix = np.zeros(n, np.float32)

    def setze(sig, sek, g=1.0):
        i = int(sek * SR)
        sig = sig[: max(0, n - i)]
        mix[i:i + len(sig)] += sig * g

    pegel = np.full(n, 0.5, np.float32)
    for i, sz in enumerate(szenen):
        for tl in sz["teile"]:
            a = sz["start"] + tl["start"]
            setze(tl["ton"], a, 0.95)
            pegel[max(0, int((a - 0.2) * SR)):int(a * SR) + len(tl["ton"])] = 0.12
        if i == 2:                                                       # Schnitt zur Wahrheit: Kratzer, Musik weg
            setze(mh.kratzer(), sz["start"], 0.9)
            pegel[int(sz["start"] * SR):int((sz["start"] + 0.6) * SR)] = 0.0
            t = np.arange(int(0.05 * SR)) / SR
            klick = (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90) * 0.25).astype(np.float32)
            for k in np.arange(0.8, sz["dauer"] - 0.1, 0.17):            # Controller-Klicks
                setze(klick, sz["start"] + k)
        if i == 3:
            setze(mh.ding(), sz["start"] + 0.3, 1.2)
        if i == 5:
            setze(mh.boom(), sz["start"] + 0.7, 1.0)
            pegel[int((sz["start"] + 0.6) * SR):] = 0.0
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", MUSIK, "-f", "s16le", "-ac", "1", "-ar", str(SR),
                          "pipe:1"], capture_output=True, check=True).stdout
    m = np.frombuffer(roh, np.int16).astype(np.float32) / 32768
    m = m / max(1e-6, float(np.sqrt(np.mean(m ** 2)))) * 0.2
    m = np.pad(m, (0, max(0, n - len(m))))[:n]
    k = int(0.15 * SR)
    pegel = np.convolve(pegel, np.ones(k) / k, mode="same")
    mix += m * pegel
    return mix / max(1e-6, np.abs(mix).max()) * 0.9


def main():
    szenen, gesamt = bauen()
    r = random.Random(4)
    blinz = set()
    for k in range(int(gesamt * FPS)):
        if r.random() < 0.015:
            blinz.update(range(k, k + 4))
    wav = os.path.join(tempfile.mkdtemp(), "t.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((tonspur(szenen, gesamt) * 32767).astype(np.int16).tobytes())
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                          "-movflags", "+faststart", ZIEL], stdin=subprocess.PIPE)
    for k in range(int(gesamt * FPS)):
        zeit = k / FPS
        sz = next((s for s in szenen if s["start"] <= zeit < s["start"] + s["dauer"]), szenen[-1])
        p.stdin.write(frame(sz, zeit - sz["start"], k, blinz).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg-Fehler")
    print(ZIEL, round(gesamt, 1), "s")
    import vollstaendig
    vollstaendig.pruefe(ZIEL, [tl["text"] for s in szenen for tl in s["teile"]], streng=True)


if __name__ == "__main__":
    main()
