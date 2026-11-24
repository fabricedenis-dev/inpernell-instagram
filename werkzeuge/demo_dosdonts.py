#!/usr/bin/env python3
"""Vorschau-Reel „Do's & Don'ts: Die Gehaltsfrage“ aus den Website-Porträts (ohne KI-Stimmen, ohne KI-Gesichter):
Kamerafahrt auf den Fotos, Sprechblasen Wort für Wort, Standbild grau mit rotem X, DO/DON'T, Musik und Effekte.
Aufruf: python werkzeuge/demo_dosdonts.py  ->  vorschau/reichweite/demo_gehalt.mp4"""
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
from bild import NAVY, ORANGE, WEISS, font, wrap  # noqa: E402
import reel_design as rd  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
ROT, GRUEN = (226, 60, 60), (34, 170, 96)
ZIEL = os.path.join(HIER, "vorschau", "reichweite", "demo_gehalt.mp4")
MUSIK = os.path.join(HIER, "assets", "musik", "carefree_kevin_macleod.mp3")


def foto(name):
    im = Image.open(os.path.join(HIER, "assets", "team", f"foto_{name}.jpg")).convert("RGB")
    im = im.resize((1200, 1200), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    return im


FOTOS = {n: foto(n) for n in ("fabrice", "pascal", "waldemar")}
NAMEN = {"fabrice": "Fabrice", "pascal": "Pascal", "waldemar": "Waldemar"}
ROLLE = {"fabrice": "fragt als Personaler", "pascal": "antwortet als Bewerber", "waldemar": "zeigt, wie es besser geht"}

# (Start, Ende, Art, Daten)
SZENEN = [
    (0.0, 3.6, "frage", dict(wer="fabrice", text="Was stellst du dir beim Gehalt vor?")),
    (3.6, 7.4, "dont", dict(wer="pascal", text="Äh … so 20 Euro die Stunde wären okay.")),
    (7.4, 10.0, "freeze", dict(wer="pascal", text="Äh … so 20 Euro die Stunde wären okay.")),
    (10.0, 13.6, "rat", dict(wer="waldemar", text="Stopp. Verkauf dich nicht unter Wert. Begründe deinen Wunsch.")),
    (13.6, 19.4, "do", dict(wer="pascal", text="Mit 3 Jahren Erfahrung an der 5-Achs-Fräse stelle ich mir 30 Euro pro Stunde vor.")),
    (19.4, 25.0, "tipps", {}),
]
DAUER = SZENEN[-1][1]


def glatt(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def hintergrund():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)], fill=(int(12 + 16 * t), int(28 + 24 * t), int(60 + 34 * t)))
    return img


HG = hintergrund()


def kopfzeile(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 215, W - 60, 375], radius=24, fill=WEISS)
    d.text((95, 237), "DO'S & DON'TS IM VORSTELLUNGSGESPRÄCH", font=font("h800", 30), fill=ORANGE)
    d.text((95, 282), "Die Gehaltsfrage", font=font("h800", 60), fill=NAVY)


def fotokarte(img, wer, t_rel, grau=False, rein=1.0):
    """Porträt als große Karte mit langsamer Kamerafahrt (Ken Burns)."""
    z = 1.0 + 0.10 * t_rel / 6.0
    q = FOTOS[wer]
    s = int(1200 / z)
    off = (1200 - s) // 2
    ausschnitt = q.crop((off, off - int(40 * t_rel / 6), off + s, off + s - int(40 * t_rel / 6))).resize((900, 900), Image.LANCZOS)
    if grau:
        ausschnitt = ImageEnhance.Brightness(ImageOps.grayscale(ausschnitt).convert("RGB")).enhance(0.8)
    maske = Image.new("L", (900, 900), 0)
    ImageDraw.Draw(maske).rounded_rectangle([0, 0, 899, 899], radius=40, fill=255)
    x = 90 + int((1 - glatt(rein)) * 1100) if rein < 1 else 90
    img.paste(ausschnitt, (x, 420), maske)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x + 30, 1250, x + 30 + d.textlength(NAMEN[wer], font=font("h800", 40)) + 50, 1316],
                        radius=18, fill=ORANGE)
    d.text((x + 55, 1283), NAMEN[wer], font=font("h800", 40), fill=NAVY, anchor="lm")
    d.text((x + 30, 1336), ROLLE[wer], font=font("t400", 34), fill=(200, 212, 232))


def blase(img, text, anteil, farbe=WEISS):
    """Sprechblase mit Text Wort für Wort (anteil 0..1)."""
    d = ImageDraw.Draw(img)
    f = font("h800", 50)
    worte = text.split()
    n = max(1, int(round(len(worte) * min(1.0, anteil))))
    zeilen = wrap(d, text, f, W - 220)
    h = 50 + len(zeilen) * 62
    y0 = 1100 - h
    d.rounded_rectangle([70, y0, W - 70, y0 + h], radius=28, fill=farbe)
    d.polygon([(160, y0 + h - 2), (210, y0 + h - 2), (150, y0 + h + 50)], fill=farbe)
    gezeigt, y = 0, y0 + 25
    for z in zeilen:
        x = 110
        for wort in z.split():
            if gezeigt < n:
                d.text((x, y), wort, font=f, fill=NAVY)
            x += d.textlength(wort + " ", font=f)
            gezeigt += 1
        y += 62


def etikett(img, text, farbe, p):
    rgba = img.convert("RGBA")
    s = 1.6 - 0.6 * glatt(p * 3)
    f = font("h800", int(70 * s))
    d = ImageDraw.Draw(rgba)
    b = d.textlength(text, font=f) + 70
    hh = int(110 * s)
    d.rounded_rectangle([(W - b) / 2, 440, (W + b) / 2, 440 + hh], radius=24, fill=farbe)
    d.text((W // 2, 440 + hh // 2), text, font=f, fill=WEISS, anchor="mm")
    return rgba.convert("RGB")


def rotes_x(img, p):
    d = ImageDraw.Draw(img)
    p1, p2 = glatt(p * 2), glatt(p * 2 - 1)
    a, b = (130, 470), (950, 1280)
    d.line([a, (a[0] + (b[0] - a[0]) * p1, a[1] + (b[1] - a[1]) * p1)], fill=ROT, width=30)
    if p2 > 0:
        a, b = (950, 470), (130, 1280)
        d.line([a, (a[0] + (b[0] - a[0]) * p2, a[1] + (b[1] - a[1]) * p2)], fill=ROT, width=30)


def tipps(img, t):
    d = ImageDraw.Draw(img)
    d.text((W // 2, 450), "SO GEHT'S", font=font("h800", 50), fill=ORANGE, anchor="mm")
    y = 540
    for i, txt in enumerate(("Vorher recherchieren, was in deinem Beruf und deiner Region üblich ist.",
                             "Eine konkrete Zahl nennen, keine Spanne nach unten.",
                             "Mit Erfahrung, Maschinen und Erfolgen begründen.")):
        q = glatt((t - 0.3 - i * 0.6) / 0.4)
        if q <= 0:
            break
        x = 90 - int((1 - q) * 60)
        d.ellipse([x, y, x + 72, y + 72], fill=ORANGE)
        d.text((x + 36, y + 36), str(i + 1), font=font("h800", 42), fill=NAVY, anchor="mm")
        yy = y
        for z in wrap(d, txt, font("h700", 48), W - 300):
            d.text((x + 105, yy), z, font=font("h700", 48), fill=WEISS)
            yy += 60
        y = yy + 50
    if t > 2.4:
        d.text((W // 2, 1380), "Verkauf dich nicht unter Wert.", font=font("h800", 56), fill=WEISS, anchor="mm")


def frame(t):
    img = HG.copy()
    for a, e, art, dd in SZENEN:
        if a <= t < e:
            break
    rel = t - a
    if art != "tipps":
        kopfzeile(img)
    if art == "frage":
        fotokarte(img, "fabrice", rel)
        if rel > 0.6:
            blase(img, dd["text"], (rel - 0.6) / 1.8)
    elif art == "dont":
        fotokarte(img, "pascal", rel, rein=rel / 0.5)
        if rel > 0.7:
            blase(img, dd["text"], (rel - 0.7) / 2.0)
    elif art == "freeze":
        fotokarte(img, "pascal", 3.8, grau=True)
        blase(img, dd["text"], 1.0, farbe=(210, 210, 210))
        rotes_x(img, rel / 0.8)
        img = etikett(img, "DON'T", ROT, rel)
        if rel > 0.9:
            d = ImageDraw.Draw(img)
            d.rounded_rectangle([360, 1405, W - 60, 1495], radius=20, fill=(0, 0, 0))
            d.text((690, 1450), "Unsicher, zu niedrig, unbegründet", font=font("h800", 36), fill=WEISS, anchor="mm")
    elif art == "rat":
        fotokarte(img, "waldemar", rel, rein=rel / 0.5)
        if rel > 0.6:
            blase(img, dd["text"], (rel - 0.6) / 2.2)
    elif art == "do":
        fotokarte(img, "pascal", rel)
        img = etikett(img, "DO", GRUEN, rel)
        if rel > 0.6:
            blase(img, dd["text"], (rel - 0.6) / 3.2)
        if rel > 4.2:
            d = ImageDraw.Draw(img)
            d.rounded_rectangle([360, 1405, W - 60, 1495], radius=20, fill=GRUEN)
            d.text((690, 1450), "Konkret, begründet, selbstbewusst", font=font("h800", 36), fill=WEISS, anchor="mm")
    else:
        tipps(img, rel)
        if rel > 3.4:
            rgba = img.convert("RGBA")
            rd.sticker(rgba, "BEISPIELZAHLEN", (W // 2 - 170, 1170), winkel=-3, fuell=(255, 196, 64),
                       schrift=NAVY, groesse=30)
            img = rgba.convert("RGB")
    rgba = img.convert("RGBA")
    rd.logo_marke(rgba)
    return rgba.convert("RGB")


def ton(n):
    mix = np.zeros(n, np.float32)
    rng = np.random.default_rng(3)

    def setze(sig, sek, g=1.0):
        i = int(sek * SR)
        sig = sig[: max(0, n - i)]
        mix[i:i + len(sig)] += sig * g

    def ding(f=1320, d=0.9):
        t = np.arange(int(d * SR)) / SR
        return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t * 5) * 0.4

    def summer(d=0.45):
        t = np.arange(int(d * SR)) / SR
        return np.sign(np.sin(2 * np.pi * 140 * t)) * 0.18 * np.minimum(1, (d - t) * 20)

    def wusch(d=0.35):
        t = np.arange(int(d * SR)) / SR
        from scipy.signal import butter, lfilter
        b, a = butter(2, [700 / (SR / 2), 5000 / (SR / 2)], "band")
        return (lfilter(b, a, rng.standard_normal(len(t))) * np.sin(np.pi * t / d) ** 2 * 0.5).astype(np.float32)

    for a, e, art, _ in SZENEN:
        if art in ("dont", "rat"):
            setze(wusch(), a, 0.7)
        if art == "freeze":
            setze(summer(), a + 0.1)
        if art == "do":
            setze(ding(), a + 0.15)
        if art == "tipps":
            setze(wusch(), a, 0.6)
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", MUSIK, "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"],
                         capture_output=True, check=True).stdout
    m = np.frombuffer(roh, np.int16).astype(np.float32)[:n] / 32768
    m = np.pad(m, (0, n - len(m)))
    m = m / max(1e-6, float(np.sqrt(np.mean(m ** 2)))) * 0.2
    pegel = np.full(n, 0.55, np.float32)
    fa, fe = SZENEN[2][0], SZENEN[2][1]
    pegel[int(fa * SR):int(fe * SR)] = 0.08                      # Standbild: Musik fast weg
    k = int(0.25 * SR)
    pegel = np.convolve(pegel, np.ones(k) / k, mode="same")
    m[-int(1.5 * SR):] *= np.linspace(1, 0, int(1.5 * SR))
    mix += m * pegel
    return mix / max(1e-6, np.abs(mix).max()) * 0.9


def main():
    n = int(DAUER * SR)
    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, "t.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((ton(n) * 32767).astype(np.int16).tobytes())
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                          "-movflags", "+faststart", ZIEL], stdin=subprocess.PIPE)
    for k in range(int(DAUER * FPS)):
        p.stdin.write(frame(k / FPS).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg-Fehler")
    print(ZIEL)


if __name__ == "__main__":
    main()
