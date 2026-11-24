#!/usr/bin/env python3
"""Meme-Video „Jensen zockt GTA 6“ für den PRIVATEN Account des Inhabers (keine Inpernell-Werbung).
Fotos: Wikimedia Commons, Anderseidesvik, CC BY 4.0 (Nennung im Bild). Satire. Musik: „Fluffing a Duck“ von
Kevin MacLeod (CC BY 4.0, Nennung im Bildtext). Meme-Schnitt: harte Schnitte, Zoom-Stöße, Boom, Kratzer, Wackeln,
Abschluss-Parodie „Mission bestanden“.
Aufruf: python werkzeuge/meme_huang_video.py <ordner mit NN.jpg>  ->  vorschau/memes/meme_huang.mp4"""
import math
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
from bild import font, wrap  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
ORDNER = sys.argv[1] if len(sys.argv) > 1 else "."
ZIEL = os.path.join(HIER, "vorschau", "memes", "meme_huang.mp4")
MUSIK = os.path.join(HIER, "assets", "musik", "fluffing_a_duck_kevin_macleod.mp3")
NACHWEIS = "Fotos: Anderseidesvik, CC BY 4.0, Wikimedia Commons · Satire"

# (Foto, Fokus x, Fokus y, Text, Dauer, Effekt)
SZENEN = [
    (9, 0.5, 0.33, "Nvidia zu Jensen: „Wir holen dich nicht zurück.“", 2.6, "boom"),
    (3, 0.5, 0.45, "Jensen: „Kein Problem. Ich hab eh noch GTA 6 zu zocken.“", 2.8, "normal"),
    (2, 0.6, 0.45, "Zwei Wochen später: 100 % durchgespielt.", 2.4, "ding"),
    (10, 0.5, 0.3, "Und jetzt hat er nichts mehr zu tun.", 2.6, "stille"),
    (22, 0.45, 0.5, "Also: „Ich wäre dann wieder da.“", 2.4, "normal"),
    (6, 0.5, 0.38, "Lücke im Lebenslauf? „GTA 6. Teamfähig, stressresistent, fahre Fluchtwagen.“", 3.4, "kratzer"),
    (3, 0.5, 0.45, "", 3.0, "mission"),
]
_FOTO = {}


def foto(nr):
    if nr not in _FOTO:
        _FOTO[nr] = Image.open(os.path.join(ORDNER, f"{nr:02d}.jpg")).convert("RGB")
    return _FOTO[nr]


def ausschnitt(nr, fx, fy, w, h, zoom):
    im = foto(nr)
    s = max(w / im.width, h / im.height) * zoom
    cw, ch = w / s, h / s
    x = (im.width - cw) * fx
    y = (im.height - ch) * fy
    return im.resize((w, h), Image.LANCZOS, box=(x, y, x + cw, y + ch))


def text_oben(img, text):
    d = ImageDraw.Draw(img)
    f = font("h800", 60)
    y = 230
    for z in wrap(d, text, f, W - 140):
        d.text((70, y), z, font=f, fill=(10, 10, 10))
        y += 72
    return max(560, y + 40)


def glatt(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def mission(img, t):
    """GTA-artige Parodie-Einblendung (eigene Schrift, kein Logo)."""
    d = ImageDraw.Draw(img)
    q = glatt(t / 0.35)
    groesse = int(118 * (1.3 - 0.3 * q))
    f = font("h800", groesse)
    y = 760
    for zeile, farbe in (("MISSION", (255, 196, 40)), ("BESTANDEN", (255, 196, 40))):
        d.text((W // 2, y), zeile, font=f, fill=farbe, anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0))
        y += int(groesse * 1.05)
    if t > 0.7:
        d.text((W // 2, y + 40), "Comeback +", font=font("h800", 64), fill=(255, 255, 255), anchor="mm",
               stroke_width=7, stroke_fill=(0, 0, 0))


def frame(i, t, sz):
    nr, fx, fy, text, dauer, eff = sz
    img = Image.new("RGB", (W, H), (255, 255, 255))
    if eff == "mission":
        zoom = 1.05 + 0.08 * t / dauer
        bild = ausschnitt(nr, fx, fy, W, H, zoom)
        bild = ImageEnhance.Color(bild).enhance(0.35)
        bild = ImageEnhance.Brightness(bild).enhance(0.8)
        img.paste(bild, (0, 0))
        mission(img, t)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([W - 210, 240, W - 40, 290], radius=12, fill=(226, 60, 60))
        d.text((W - 125, 265), "SATIRE", font=font("h800", 28), fill=(255, 255, 255), anchor="mm")
    else:
        oben = text_oben(img, text)
        stoss = 1.0 + 0.10 * (1 - glatt(t / 0.22))                # Zoom-Stoß beim Schnitt
        if eff == "stille":
            zoom = 1.0 + 0.45 * glatt(t / dauer)                    # langsamer, unangenehmer Zoom aufs Gesicht
        else:
            zoom = 1.0 + 0.06 * t / dauer
        bild = ausschnitt(nr, fx, fy, W, H - oben, zoom * stoss)
        dx = dy = 0
        if eff == "kratzer" and t < 0.5:                             # Wackeln beim Höhepunkt
            r = random.Random(int(t * 1000))
            dx, dy = r.randint(-22, 22), r.randint(-16, 16)
        img.paste(bild, (dx, oben + dy))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([W - 210, oben + 30, W - 40, oben + 80], radius=12, fill=(226, 60, 60))
        d.text((W - 125, oben + 55), "SATIRE", font=font("h800", 28), fill=(255, 255, 255), anchor="mm")
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 430, W, H - 390], fill=(0, 0, 0))
    d.text((W // 2, H - 410), NACHWEIS, font=font("t400", 24), fill=(230, 230, 230), anchor="mm")
    return img


# ---------------------------------------------------------------- Ton
def _t(d):
    return np.arange(int(d * SR)) / SR


def boom():
    t = _t(1.2)
    f = 60 * np.exp(-t * 2.5) + 38
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    klick = np.random.default_rng(1).standard_normal(len(t)) * np.exp(-t * 60) * 0.4
    return ((sig + klick) * 0.9).astype(np.float32)


def ding():
    t = _t(1.0)
    return ((np.sin(2 * np.pi * 1568 * t) + 0.5 * np.sin(2 * np.pi * 2093 * t)) * np.exp(-t * 4) * 0.35).astype(np.float32)


def kratzer():
    from scipy.signal import butter, lfilter
    t = _t(0.45)
    rng = np.random.default_rng(2)
    out = np.zeros(len(t), np.float32)
    for k in range(6):
        f0 = 2000 - k * 280
        b, a = butter(2, [max(100, f0 - 300) / (SR / 2), (f0 + 300) / (SR / 2)], "band")
        out += lfilter(b, a, rng.standard_normal(len(t))).astype(np.float32) * (np.abs(np.sin(np.pi * t * 12)) > 0.45)
    return out * np.exp(-t * 3) * 0.6


def grillen(d):
    out = np.zeros(int(d * SR), np.float32)
    tz = _t(0.03)
    zirp = np.sin(2 * np.pi * 4600 * tz) * np.sin(np.pi * tz / 0.03)
    for k in np.arange(0.3, d - 0.2, 0.5):
        for j in range(3):
            i = int((k + j * 0.055) * SR)
            out[i:i + len(zirp)] += zirp[: len(out) - i]
    return out * 0.15


def jingle():
    """Kurzer Erfolgs-Akkord (eigene Synthese)."""
    out = np.zeros(int(2.4 * SR), np.float32)
    for k, (f, st) in enumerate(((392, 0.0), (494, 0.12), (587, 0.24), (784, 0.36))):
        t = _t(2.0 - st)
        ton = sum(np.sign(np.sin(2 * np.pi * f * h * t)) / (h * 3) for h in (1, 2)) * np.exp(-t * 1.6) * 0.18
        i = int(st * SR)
        out[i:i + len(ton)] += ton.astype(np.float32)
    return out


def tonspur(starts, gesamt):
    n = int(gesamt * SR)
    mix = np.zeros(n, np.float32)

    def setze(sig, sek, g=1.0):
        i = int(sek * SR)
        sig = sig[: max(0, n - i)]
        mix[i:i + len(sig)] += sig * g

    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", MUSIK, "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"],
                         capture_output=True, check=True).stdout
    m = np.frombuffer(roh, np.int16).astype(np.float32) / 32768
    m = m / max(1e-6, float(np.sqrt(np.mean(m ** 2)))) * 0.2
    m = np.pad(m, (0, max(0, n - len(m))))[:n]
    pegel = np.full(n, 0.9, np.float32)
    for (st, sz) in zip(starts, SZENEN):
        eff, dauer = sz[5], sz[4]
        a, e = int(st * SR), int((st + dauer) * SR)
        if eff == "boom":
            setze(boom(), st, 0.9)
        if eff == "ding":
            setze(ding(), st + 0.1)
        if eff == "stille":
            pegel[a:e] = 0.0
            setze(grillen(dauer), st)
        if eff == "kratzer":
            setze(kratzer(), st, 0.9)
            setze(boom(), st + 0.35, 0.8)
        if eff == "mission":
            pegel[a:] = 0.0
            setze(jingle(), st + 0.05, 1.0)
    k = int(0.06 * SR)
    pegel = np.convolve(pegel, np.ones(k) / k, mode="same")
    mix += m * pegel
    return mix / max(1e-6, np.abs(mix).max()) * 0.9


def main():
    starts, t = [], 0.0
    for sz in SZENEN:
        starts.append(t)
        t += sz[4]
    gesamt = t
    wav = os.path.join(tempfile.mkdtemp(), "t.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((tonspur(starts, gesamt) * 32767).astype(np.int16).tobytes())
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                          "-movflags", "+faststart", ZIEL], stdin=subprocess.PIPE)
    for k in range(int(gesamt * FPS)):
        zeit = k / FPS
        i = max(j for j, s in enumerate(starts) if s <= zeit)
        p.stdin.write(frame(i, zeit - starts[i], SZENEN[i]).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg-Fehler")
    print(ZIEL, round(gesamt, 1), "s")


if __name__ == "__main__":
    main()
