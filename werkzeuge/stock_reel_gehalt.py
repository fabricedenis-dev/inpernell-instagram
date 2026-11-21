#!/usr/bin/env python3
"""Reel „Do's & Don'ts: Die Gehaltsfrage“ mit echten Menschen aus freien Stock-Clips (Mixkit) und Bibliotheksstimmen
(ElevenLabs). Während gesprochen wird, zeigt das Bild bevorzugt Zuhörer, Hände oder Maschinen (keine Lippen, die
nicht passen). Untertitel Wort für Wort, Standbild mit rotem X, Michael spricht die Tipps.
Aufruf: python werkzeuge/stock_reel_gehalt.py <ordner mit Mixkit-Clips <id>-720.mp4 bzw. <id>.mp4>
-> vorschau/reichweite/stock_reel_gehalt.mp4
Hinweis: realistische KI-Stimmen -> vor Veröffentlichung KI-Hinweis setzen. Mixkit-Lizenz je Clip prüfen."""
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
import reel_design as rd  # noqa: E402
import topjob_video as tv  # noqa: E402
from bild import NAVY, ORANGE, WEISS, font, wrap  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
CLIPS = sys.argv[1] if len(sys.argv) > 1 else "."
ZIEL = os.path.join(HIER, "vorschau", "reichweite", "stock_reel_gehalt.mp4")
CACHE = os.path.join(HIER, "vorschau", "reichweite", "ton")
MUSIK = os.path.join(HIER, "assets", "musik", "carefree_kevin_macleod.mp3")
ROT, GRUEN = (226, 60, 60), (34, 170, 96)
KARTE = (0, 400, W, 1360)          # Videofläche (x0, y0, x1, y1)
STIMMEN = {"personalerin": "zKHQdbB8oaQ7roNTiDTK",   # Laura – Sharp and Professional
           "bewerber": "aTTiK3YzK3dXETpuDE2h",       # Ben – Effortless and Casual
           "coach": "IWm8DnJ4NGjFI7QAM5lM",          # Stephan – Warm and Friendly
           "michael": "87AwpS6yC86wa2WglbsK"}
ROLLE = {"personalerin": "PERSONALERIN", "bewerber": "BEWERBER", "coach": "COACH", "michael": "SO GEHT'S"}

# Szenen: Art, Sprecher, Text, Pause vor/nach, Bildfolge [(clip-id, start im Clip, Anteil der Szene, Fokus x 0..1)]
ABLAUF = [
    ("frage", "personalerin", "[professional] Was stellst du dir beim Gehalt vor?", 0.8, 0.4,
     [(5799, 1.0, 1.0, 0.42)]),
    ("dont", "bewerber", "[hesitant] Äh, so 20 Euro die Stunde wären okay.", 0.5, 0.4,
     [(6052, 9.0, 1.0, 0.62)]),
    ("freeze", None, None, 0.0, 2.6, []),
    ("rat", "coach", "[calm] Stopp. Verkauf dich nicht unter Wert. Begründe deinen Wunsch.", 0.4, 0.5,
     [(6022, 2.5, 1.0, 0.42)]),
    ("do", "bewerber", "[confident] Mit 3 Jahren Erfahrung an der 5-Achs-Fräse stelle ich mir 30 Euro pro Stunde vor.",
     0.5, 1.6, [(2244, 2.0, 0.5, 0.5), (5660, 4.0, 0.5, 0.3)]),
    ("tipps", "michael", "[warm] Drei Tipps. Recherchiere vorher, was in deinem Beruf üblich ist. Nenne eine "
     "konkrete Zahl. Und begründe sie mit deiner Erfahrung. Verkauf dich nicht unter Wert.", 0.5, 2.0,
     [(46755, 3.0, 1.0, 0.45)]),
]
TIPPS = ("Vorher recherchieren, was in deinem Beruf üblich ist.", "Eine konkrete Zahl nennen.",
         "Mit deiner Erfahrung begründen.")


def clip_pfad(cid):
    for n in (f"{cid}_1080.mp4", f"{cid}-720.mp4", f"{cid}.mp4"):
        p = os.path.join(CLIPS, n)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            return p
    raise FileNotFoundError(cid)


def clip_frames(cid, start, dauer, fokus):
    """Liefert Einzelbilder (PIL) in Kartengröße, Ausschnitt nach Fokus."""
    bw, bh = KARTE[2] - KARTE[0], KARTE[3] - KARTE[1]
    p = clip_pfad(cid)
    sw, sh = (int(x) for x in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                               "stream=width,height", "-of", "csv=p=0", p],
                                              capture_output=True, text=True).stdout.strip().split(","))
    s = max(bw / sw, bh / sh)
    nw, nh = int(sw * s) // 2 * 2 + 2, int(sh * s) // 2 * 2 + 2
    x = int((nw - bw) * fokus)
    n = max(1, int(round(dauer * FPS)))
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(start), "-i", p, "-t", str(dauer + 0.5),
                          "-vf", f"fps={FPS},scale={nw}:{nh}:flags=lanczos,crop={bw}:{bh}:{x}:{(nh - bh) // 2},"
                                 "unsharp=5:5:0.6", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
                         capture_output=True, check=True).stdout
    groesse = bw * bh * 3
    bilder = [Image.frombytes("RGB", (bw, bh), roh[i * groesse:(i + 1) * groesse]) for i in range(len(roh) // groesse)]
    while len(bilder) < n:                       # Clip zu kurz: letztes Bild halten
        bilder.append(bilder[-1])
    return bilder[:n]


def grund():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)], fill=(int(12 + 16 * t), int(28 + 24 * t), int(60 + 34 * t)))
    return img


HG = grund()


def glatt(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def kopf(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 215, W - 60, 375], radius=24, fill=WEISS)
    d.text((95, 237), "DO'S & DON'TS IM VORSTELLUNGSGESPRÄCH", font=font("h800", 30), fill=ORANGE)
    d.text((95, 282), "Die Gehaltsfrage", font=font("h800", 60), fill=NAVY)


def untertitel(img, rolle, text, n_gesprochen, aktiv):
    d = ImageDraw.Draw(img)
    f = font("h800", 54)
    zeilen = wrap(d, text, f, W - 140)
    y0 = KARTE[3] - 40 - len(zeilen) * 66
    d.rounded_rectangle([60, y0 - 64, 60 + d.textlength(rolle, font=font("h800", 28)) + 40, y0 - 14], radius=14,
                        fill=ORANGE)
    d.text((80, y0 - 39), rolle, font=font("h800", 28), fill=NAVY, anchor="lm")
    idx, y = 0, y0
    for z in zeilen:
        x = 70
        for wort in z.split():
            if idx < n_gesprochen:
                d.text((x, y), wort, font=f, fill=ORANGE if idx == aktiv else WEISS, stroke_width=7,
                       stroke_fill=(0, 0, 0))
            x += d.textlength(wort + " ", font=f)
            idx += 1
        y += 66


def etikett(img, text, farbe, p):
    d = ImageDraw.Draw(img)
    s = 1.5 - 0.5 * glatt(p * 3)
    f = font("h800", int(70 * s))
    b = d.textlength(text, font=f) + 70
    hh = int(110 * s)
    d.rounded_rectangle([(W - b) / 2, 430, (W + b) / 2, 430 + hh], radius=24, fill=farbe)
    d.text((W // 2, 430 + hh // 2), text, font=f, fill=WEISS, anchor="mm")


def bauen():
    szenen, t = [], 0.0
    for art, wer, text, vor, nach, folge in ABLAUF:
        if text:
            tv.STIMME = STIMMEN[wer]
            ton, woerter, zeiten, _q = tv.sprich_abschnitt(text, CACHE)
            dauer = vor + len(ton) / SR + nach
        else:
            ton, woerter, zeiten, dauer = None, [], [], nach
        bilder = []
        for cid, st, anteil, fokus in folge:
            bilder += clip_frames(cid, st, dauer * anteil, fokus)
        szenen.append(dict(art=art, wer=wer, start=t, ende=t + dauer, vor=vor, ton=ton, woerter=woerter,
                           zeiten=zeiten, text=tv.anzeige_text(text) if text else "", bilder=bilder))
        t += dauer
    return szenen


def frame(szenen, t):
    i = next((k for k, s in enumerate(szenen) if s["start"] <= t < s["ende"]), len(szenen) - 1)
    sz = szenen[i]
    rel = t - sz["start"]
    img = HG.copy()
    if sz["art"] == "freeze":
        vor = szenen[i - 1]
        b = vor["bilder"][-1]
        b = ImageEnhance.Brightness(ImageOps.grayscale(b).convert("RGB")).enhance(0.8)
    else:
        b = sz["bilder"][min(len(sz["bilder"]) - 1, int(rel * FPS))]
        if sz["art"] == "tipps":
            b = ImageEnhance.Brightness(b).enhance(0.45)
    img.paste(b, (KARTE[0], KARTE[1]))
    if sz["art"] != "tipps":
        kopf(img)
    d = ImageDraw.Draw(img)
    r = rel - sz["vor"]
    if sz["art"] in ("frage", "dont", "rat", "do") and r > -0.05:
        n = sum(1 for a, _ in sz["zeiten"] if a <= r + 0.05)
        aktiv = max([k for k, (a, e) in enumerate(sz["zeiten"]) if a <= r] or [-1])
        if r > len(sz["ton"]) / SR:
            aktiv = -1
        untertitel(img, ROLLE[sz["wer"]], sz["text"], max(n, 1), aktiv)
    if sz["art"] == "freeze":
        vor = szenen[i - 1]
        untertitel(img, ROLLE["bewerber"], vor["text"], 99, -1)
        p1, p2 = glatt(rel / 0.4), glatt((rel - 0.4) / 0.4)
        a, e = (120, 470), (960, 1300)
        d.line([a, (a[0] + (e[0] - a[0]) * p1, a[1] + (e[1] - a[1]) * p1)], fill=ROT, width=30)
        if p2 > 0:
            a, e = (960, 470), (120, 1300)
            d.line([a, (a[0] + (e[0] - a[0]) * p2, a[1] + (e[1] - a[1]) * p2)], fill=ROT, width=30)
        etikett(img, "DON'T", ROT, rel)
        if rel > 0.9:
            d.rounded_rectangle([360, 1400, W - 60, 1490], radius=20, fill=(0, 0, 0))
            d.text((690, 1445), "Unsicher, zu niedrig, unbegründet", font=font("h800", 36), fill=WEISS, anchor="mm")
    if sz["art"] == "do":
        etikett(img, "DO", GRUEN, rel)
        if rel > sz["ende"] - sz["start"] - 1.6:
            d.rounded_rectangle([360, 1400, W - 60, 1490], radius=20, fill=GRUEN)
            d.text((690, 1445), "Konkret, begründet, selbstbewusst", font=font("h800", 36), fill=WEISS, anchor="mm")
    if sz["art"] == "tipps":
        d.text((W // 2, 480), "SO GEHT'S", font=font("h800", 52), fill=ORANGE, anchor="mm")
        starts = [a for w, (a, _) in zip(sz["woerter"], sz["zeiten"])
                  if w.strip(".,").lower() in ("recherchiere", "nenne", "und")][:3]
        y = 570
        for k, txt in enumerate(TIPPS):
            if k >= len(starts) or r < starts[k] - 0.1:
                break
            q = glatt((r - starts[k] + 0.1) / 0.35)
            x = 90 - int((1 - q) * 60)
            d.ellipse([x, y, x + 72, y + 72], fill=ORANGE)
            d.text((x + 36, y + 36), str(k + 1), font=font("h800", 42), fill=NAVY, anchor="mm")
            yy = y
            for z in wrap(d, txt, font("h700", 50), W - 300):
                d.text((x + 105, yy), z, font=font("h700", 50), fill=WEISS)
                yy += 62
            y = yy + 46
        schluss = next((a for w, (a, _) in zip(sz["woerter"], sz["zeiten"]) if w.lower() == "verkauf"), 99)
        if r > schluss - 0.1:
            d.text((W // 2, 1240), "Verkauf dich nicht unter Wert.", font=font("h800", 58), fill=WEISS, anchor="mm")
        rgba = img.convert("RGBA")
        rd.sticker(rgba, "BEISPIELZAHLEN", (W // 2 - 170, 1100), winkel=-3, fuell=(255, 196, 64), schrift=NAVY,
                   groesse=30)
        img = rgba.convert("RGB")
    rgba = img.convert("RGBA")
    rd.logo_marke(rgba)
    return rgba.convert("RGB")


def tonspur(szenen, n):
    mix = np.zeros(n, np.float32)
    rng = np.random.default_rng(3)

    def setze(sig, sek, g=1.0):
        i = int(sek * SR)
        sig = sig[: max(0, n - i)]
        mix[i:i + len(sig)] += sig * g

    from scipy.signal import butter, lfilter
    t_ = np.arange(int(0.35 * SR)) / SR
    b_, a_ = butter(2, [700 / (SR / 2), 5000 / (SR / 2)], "band")
    wusch = (lfilter(b_, a_, rng.standard_normal(len(t_))) * np.sin(np.pi * t_ / 0.35) ** 2 * 0.5).astype(np.float32)
    t_ = np.arange(int(0.45 * SR)) / SR
    summer = np.sign(np.sin(2 * np.pi * 140 * t_)) * 0.18 * np.minimum(1, (0.45 - t_) * 20)
    t_ = np.arange(int(0.9 * SR)) / SR
    ding = (np.sin(2 * np.pi * 1320 * t_) + 0.4 * np.sin(2 * np.pi * 2653 * t_)) * np.exp(-t_ * 5) * 0.4
    pegel = np.full(n, 0.5, np.float32)
    for sz in szenen:
        if sz["ton"] is not None:
            a = sz["start"] + sz["vor"]
            setze(sz["ton"], a, 0.95)
            pegel[max(0, int((a - 0.2) * SR)):int(a * SR) + len(sz["ton"])] = 0.14
        if sz["art"] in ("dont", "rat", "tipps"):
            setze(wusch, sz["start"], 0.6)
        if sz["art"] == "freeze":
            setze(summer, sz["start"] + 0.1)
            pegel[int(sz["start"] * SR):int(sz["ende"] * SR)] = 0.05
        if sz["art"] == "do":
            setze(ding, sz["start"] + 0.15)
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", MUSIK, "-f", "s16le", "-ac", "1", "-ar", str(SR),
                          "pipe:1"], capture_output=True, check=True).stdout
    m = np.frombuffer(roh, np.int16).astype(np.float32)[:n] / 32768
    m = np.pad(m, (0, n - len(m)))
    m = m / max(1e-6, float(np.sqrt(np.mean(m ** 2)))) * 0.2
    k = int(0.25 * SR)
    pegel = np.convolve(pegel, np.ones(k) / k, mode="same")
    m[-int(1.5 * SR):] *= np.linspace(1, 0, int(1.5 * SR))
    mix += m * pegel
    return mix / max(1e-6, np.abs(mix).max()) * 0.9


def main():
    szenen = bauen()
    dauer = szenen[-1]["ende"]
    n = int(dauer * SR)
    wav = os.path.join(tempfile.mkdtemp(), "t.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((tonspur(szenen, n) * 32767).astype(np.int16).tobytes())
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                          "-movflags", "+faststart", ZIEL], stdin=subprocess.PIPE)
    for k in range(int(dauer * FPS)):
        p.stdin.write(frame(szenen, k / FPS).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg-Fehler")
    print(ZIEL, round(dauer, 1), "s")
    sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
    import vollstaendig
    vollstaendig.pruefe(ZIEL, [s["text"] for s in szenen if s["text"]], streng=True)


if __name__ == "__main__":
    main()
