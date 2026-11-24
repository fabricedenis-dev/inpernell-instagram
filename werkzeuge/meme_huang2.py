#!/usr/bin/env python3
"""Meme-Video 2 „Huang ist zurück“ für den PRIVATEN Account (Stand 24.11.2026, Satire).
Fakten: Rücktritt 12.11.2026, Wiedereinsetzung 23.11.2026 (Nvidia-Pressemitteilung bei der SEC); GTA VI erschien am
19.11.2026. Formate nach Recherche: „Schlagzeile + ‚Jensen:‘“ und „aktualisierter Lebenslauf“ (eigenes Design).
Fotos: Anderseidesvik, CC BY 4.0, Wikimedia Commons. Musik: „Vice Police“ von Tausdei (CC BY 3.0).
Aufruf: python werkzeuge/meme_huang2.py <ordner mit NN.jpg>  ->  vorschau/memes/meme_huang2.mp4"""
import os
import random
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import meme_huang_video as mh  # noqa: E402
from bild import font, wrap  # noqa: E402

W, H, FPS, SR = mh.W, mh.H, mh.FPS, mh.SR
mh.ORDNER = sys.argv[1] if len(sys.argv) > 1 else "."
ZIEL = os.path.join(HIER, "vorschau", "memes", "meme_huang2.mp4")
MUSIK = os.path.join(HIER, "assets", "musik", "vice_police_tausdei.mp3")
NACHWEIS = "Fotos: Anderseidesvik, CC BY 4.0, Wikimedia Commons · Satire"
BLAU = (10, 102, 194)

EINTRAEGE = [
    ("Gründer und CEO", "1993 – 11/2026 · 33 Jahre"),
    ("Sabbatical: GTA 6 durchgespielt", "11/2026 · 11 Tage · 100 %"),
    ("CEO (wieder)", "seit 23.11.2026"),
]
SZENEN = [("eil", 2.4), ("jensen", 2.6), ("lebenslauf", 5.4), ("pointe", 3.6)]


def glatt(p):
    return mh.glatt(p)


def nachweis(img):
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 430, W, H - 390], fill=(0, 0, 0))
    d.text((W // 2, H - 410), NACHWEIS, font=font("t400", 24), fill=(230, 230, 230), anchor="mm")


def satire(img, y=240):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([W - 210, y, W - 40, y + 50], radius=12, fill=(226, 60, 60))
    d.text((W - 125, y + 25), "SATIRE", font=font("h800", 28), fill=(255, 255, 255), anchor="mm")


def eil(t):
    img = Image.new("RGB", (W, H), (12, 12, 16))
    d = ImageDraw.Draw(img)
    blink = int(t * 4) % 2 == 0
    d.rounded_rectangle([70, 520, 470, 600], radius=10, fill=(226, 40, 40) if blink else (170, 30, 30))
    d.text((270, 560), "EILMELDUNG", font=font("h800", 46), fill=(255, 255, 255), anchor="mm")
    q = glatt((t - 0.15) / 0.3)
    y = 660
    for z in ("Nvidia holt", "Jensen Huang", "als CEO zurück"):
        d.text((70 - int((1 - q) * 80), y), z, font=font("h800", 96), fill=(255, 255, 255))
        y += 112
    d.text((70, y + 30), "Pressemitteilung vom 23.11.2026, nach Rücktritt am 12.11.", font=font("t400", 34),
           fill=(170, 170, 180))
    satire(img)
    nachweis(img)
    return img


def jensen(t):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((70, 250), "Jensen:", font=font("h800", 96), fill=(10, 10, 10))
    stoss = 1.0 + 0.14 * (1 - glatt(t / 0.2))
    bild = mh.ausschnitt(2, 0.6, 0.42, W, H - 420, (1.0 + 0.10 * t / 2.6) * stoss)
    img.paste(bild, (0, 420))
    satire(img, 450)
    nachweis(img)
    return img


def lebenslauf(t):
    img = Image.new("RGB", (W, H), (243, 242, 239))
    d = ImageDraw.Draw(img)
    d.text((70, 230), "Sein Lebenslauf, aktualisiert:", font=font("h800", 54), fill=(10, 10, 10))
    d.rounded_rectangle([50, 330, W - 50, 1400], radius=24, fill=(255, 255, 255), outline=(220, 220, 220), width=3)
    d.rectangle([50, 330, W - 50, 470], fill=(160, 180, 200))
    av = mh.ausschnitt(0, 0.5, 0.2, 220, 220, 1.0) if os.path.exists(os.path.join(mh.ORDNER, "00.jpg")) else \
        mh.ausschnitt(9, 0.5, 0.25, 220, 220, 1.6)
    m = Image.new("L", (220, 220), 0)
    ImageDraw.Draw(m).ellipse([0, 0, 219, 219], fill=255)
    d.ellipse([84, 364, 316, 596], fill=(255, 255, 255))
    img.paste(av, (90, 370), m)
    d.text((90, 610), "Jensen Huang", font=font("h800", 56), fill=(20, 20, 20))
    d.text((90, 680), "CEO · Lederjacken-Enthusiast · Kalifornien", font=font("t400", 34), fill=(90, 90, 90))
    d.line([(90, 750), (W - 90, 750)], fill=(225, 225, 225), width=3)
    d.text((90, 775), "Berufserfahrung", font=font("h800", 40), fill=(20, 20, 20))
    y = 850
    for i, (titel, zeit) in enumerate(EINTRAEGE):
        ein = 0.4 + i * 1.3
        q = glatt((t - ein) / 0.25)
        if q <= 0:
            break
        hl = i == 1
        if hl:
            d.rounded_rectangle([75, y - 16, W - 75, y + 150], radius=14, fill=(255, 241, 204))
        x = 90 + int((1 - q) * 60)
        d.rounded_rectangle([x, y, x + 80, y + 80], radius=12, fill=BLAU if not hl else (255, 170, 40))
        d.text((x + 40, y + 40), "6" if hl else "N", font=font("h800", 44), fill=(255, 255, 255), anchor="mm")
        for k, z in enumerate(wrap(d, titel, font("h800", 40), W - 330)):
            d.text((x + 110, y + k * 48), z, font=font("h800", 40), fill=(20, 20, 20))
        d.text((x + 110, y + 50 + 48 * (len(wrap(d, titel, font("h800", 40), W - 330)) - 1)), zeit,
               font=font("t400", 32), fill=(100, 100, 100))
        y += 180
    satire(img, 360)
    nachweis(img)
    return img


def pointe(t):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = font("h800", 58)
    y = 230
    for z in wrap(d, "Und du machst dir Sorgen um 3 Monate Lücke im Lebenslauf?", f, W - 140):
        d.text((70, y), z, font=f, fill=(10, 10, 10))
        y += 70
    oben = max(560, y + 40)
    dx = dy = 0
    if t < 0.45:
        r = random.Random(int(t * 1000))
        dx, dy = r.randint(-20, 20), r.randint(-14, 14)
    bild = mh.ausschnitt(3, 0.5, 0.45, W, H - oben, 1.0 + 0.12 * glatt(t / 3.6))
    img.paste(bild, (dx, oben + dy))
    satire(img, oben + 30)
    nachweis(img)
    return img


def tonspur(starts, gesamt):
    n = int(gesamt * SR)
    mix = np.zeros(n, np.float32)

    def setze(sig, sek, g=1.0):
        i = int(sek * SR)
        sig = sig[: max(0, n - i)]
        mix[i:i + len(sig)] += sig * g

    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", "4.406", "-i", MUSIK, "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "pipe:1"], capture_output=True, check=True).stdout
    m = np.frombuffer(roh, np.int16).astype(np.float32) / 32768
    m = m / max(1e-6, float(np.sqrt(np.mean(m ** 2)))) * 0.22
    m = np.pad(m, (0, max(0, n - len(m))))[:n]
    pegel = np.full(n, 0.9, np.float32)
    st = dict(zip([s[0] for s in SZENEN], starts))
    pegel[: int(st["jensen"] * SR)] = 0.0                       # Eilmeldung: nur Nachrichten-Ton
    t = np.arange(int(0.18 * SR)) / SR
    piep = (np.sin(2 * np.pi * 880 * t) * 0.25).astype(np.float32)
    for k in range(3):
        setze(piep, 0.1 + k * 0.3)
    setze(mh.boom(), st["jensen"], 0.9)                         # „Jensen:“ + Musik setzt ein
    for i in range(len(EINTRAEGE)):
        setze(mh.ding() * (1.6 if i == 1 else 0.7), st["lebenslauf"] + 0.4 + i * 1.3)
    setze(mh.kratzer(), st["pointe"], 0.9)
    pegel[int(st["pointe"] * SR):int((st["pointe"] + 0.5) * SR)] = 0.0
    setze(mh.boom(), st["pointe"] + 0.4, 0.8)
    k = int(0.05 * SR)
    pegel = np.convolve(pegel, np.ones(k) / k, mode="same")
    m[-int(1.2 * SR):] *= np.linspace(1, 0, int(1.2 * SR))
    mix += m * pegel
    return mix / max(1e-6, np.abs(mix).max()) * 0.9


def main():
    starts, t = [], 0.0
    for _, dauer in SZENEN:
        starts.append(t)
        t += dauer
    gesamt = t
    wav = os.path.join(tempfile.mkdtemp(), "t.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((tonspur(starts, gesamt) * 32767).astype(np.int16).tobytes())
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                          "-movflags", "+faststart", ZIEL], stdin=subprocess.PIPE)
    fn = {"eil": eil, "jensen": jensen, "lebenslauf": lebenslauf, "pointe": pointe}
    for k in range(int(gesamt * FPS)):
        zeit = k / FPS
        i = max(j for j, s in enumerate(starts) if s <= zeit)
        p.stdin.write(fn[SZENEN[i][0]](zeit - starts[i]).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg-Fehler")
    print(ZIEL, round(gesamt, 1), "s")


if __name__ == "__main__":
    main()
