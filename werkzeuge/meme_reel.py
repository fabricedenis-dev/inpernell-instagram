#!/usr/bin/env python3
"""Meme-Reels „Erwartung vs. Realität“ mit freien Stock-Clips (Mixkit), Inpernell-Stil.
Teil 1: Clip mit fröhlicher Musik, Etikett springt rein. Harter Schnitt mit Schallplatten-Kratzer,
Teil 2: zweiter Clip, langsamer Zoom, Trauer-Posaune. Logo unten links (Variante B).
Aufruf: python werkzeuge/meme_reel.py <ordner mit <id>.mp4> [nr ...]  ->  vorschau/reichweite/meme_<nr>.mp4"""
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
import reel_design as rd  # noqa: E402
from bild import NAVY, ORANGE, WEISS, font  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
ORDNER = sys.argv[1] if len(sys.argv) > 1 else "."
MUSIK = os.path.join(HIER, "assets", "musik", "monkeys_spinning_monkeys_kevin_macleod.mp3")

# Nr: (Etikett, Zeilen Teil 1, Clip 1, Start, Dauer, Fokus, Zeilen Teil 2, Clip 2, Start, Dauer, Fokus)
MEMES = {
    1: ("Bewerber", ("Laut Lebenslauf:", "belastbar & dynamisch"), 50080, 1.0, 3.6, 0.47,
        ("Am ersten Montag", "um 7:58 Uhr"), 33743, 4.0, 5.0, 0.5),
    2: ("Das Team", ("Laut Stellenanzeige:", "jung & dynamisch"), 51295, 3.0, 3.6, 0.45,
        ("In echt", "am Montagmorgen"), 4607, 11.0, 5.0, 0.6),
    3: ("Bewerber", ("Tag 1 nach", "„Wir melden uns“"), 47985, 4.0, 3.6, 0.42,
        ("Tag 21 nach", "„Wir melden uns“"), 11281, 10.0, 5.0, 0.62),
}


def frames(cid, start, dauer, fokus, zoom_ende=1.0):
    p = os.path.join(ORDNER, f"{cid}.mp4")
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(start), "-i", p, "-t", str(dauer + 0.3),
                          "-vf", f"fps={FPS},scale=-2:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "pipe:1"], capture_output=True, check=True).stdout
    sw = int(round(1280 * H / 720 / 2) * 2)
    g = sw * H * 3
    n = int(round(dauer * FPS))
    out = []
    for i in range(min(n, len(roh) // g)):
        im = Image.frombytes("RGB", (sw, H), roh[i * g:(i + 1) * g])
        z = 1.0 + (zoom_ende - 1.0) * i / max(1, n - 1)
        cw, ch = int(W / z), int(H / z)
        x = int((sw - cw) * fokus)
        out.append(im.crop((x, (H - ch) // 2, x + cw, (H - ch) // 2 + ch)).resize((W, H), Image.BILINEAR))
    while len(out) < n:
        out.append(out[-1])
    return out


def glatt(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def beschriften(im, oben, zeilen, t):
    img = im.convert("RGBA")
    s = 1.0 + 0.35 * (1 - glatt(t / 0.25))                  # Etikett springt rein
    if t > 0.0:
        f = font("h800", int(110 * s))
        sch = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sch).text((W // 2 + 4, 486), oben, font=f, fill=(0, 0, 0, 170), anchor="mm")
        img.alpha_composite(sch.filter(ImageFilter.GaussianBlur(6)))
        ImageDraw.Draw(img).text((W // 2, 480), oben, font=f, fill=WEISS, anchor="mm")
    d = ImageDraw.Draw(img)
    y = 1150
    for k, z in enumerate(zeilen):
        q = glatt((t - 0.25 - k * 0.15) / 0.25)
        if q <= 0:
            continue
        f = font("h800", 66)
        b = d.textlength(z, font=f)
        x = 100 - int((1 - q) * 120)
        d.rectangle([x, y, x + b + 40, y + 90], fill=WEISS)
        d.text((x + 20, y + 45), z, font=f, fill=NAVY, anchor="lm")
        y += 104
    if t > 0.25:
        d.rectangle([70, 1150, 84, 1150 + 2 * 104 - 14], fill=ORANGE)
    rd.logo_marke(img)
    return img.convert("RGB")


def ton(t1, t2):
    n1, n2 = int(t1 * SR), int(t2 * SR)
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", MUSIK, "-f", "s16le", "-ac", "1", "-ar", str(SR),
                          "pipe:1"], capture_output=True, check=True).stdout
    m = np.frombuffer(roh, np.int16).astype(np.float32)[:n1] / 32768
    m = m / max(1e-6, float(np.sqrt(np.mean(m ** 2)))) * 0.22
    m[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
    teil1 = m.copy()
    rng = np.random.default_rng(1)
    # Schallplatten-Kratzer: Rauschen mit fallender Tonhöhe
    from scipy.signal import butter, lfilter
    d = 0.35
    tt = np.arange(int(d * SR)) / SR
    kratz = np.zeros(len(tt), np.float32)
    for k in range(6):
        f0 = 1800 - k * 250
        b, a = butter(2, [max(100, f0 - 300) / (SR / 2), (f0 + 300) / (SR / 2)], "band")
        kratz += lfilter(b, a, rng.standard_normal(len(tt))).astype(np.float32) * (np.abs(np.sin(np.pi * tt * 14)) > 0.5)
    kratz *= np.exp(-tt * 4) * 0.5
    teil1[-int(0.12 * SR):] *= np.linspace(1, 0, int(0.12 * SR))
    # Trauer-Posaune: vier fallende Töne, der letzte lang mit Vibrato
    noten = [(392, 0.38), (370, 0.38), (349, 0.38), (330, 1.3)]
    pos = []
    for i, (f, dauer) in enumerate(noten):
        t = np.arange(int(dauer * SR)) / SR
        vib = 1 + (0.012 * np.sin(2 * np.pi * 5.5 * t) if i == 3 else 0)
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        sig = sum(np.sin(k * ph) / k for k in range(1, 9))
        hk = np.minimum(1, t / 0.04) * np.minimum(1, (dauer - t) / 0.08)
        pos.append((sig * hk * 0.12).astype(np.float32))
    pos = np.concatenate(pos)
    teil2 = np.zeros(n2, np.float32)
    teil2[:len(kratz)] += kratz
    i0 = int(0.5 * SR)
    teil2[i0:i0 + len(pos)] += pos[: n2 - i0]
    mix = np.concatenate([teil1, teil2])
    return mix / max(1e-6, np.abs(mix).max()) * 0.9


def erzeuge(nr):
    oben, z1, c1, s1, d1, f1, z2, c2, s2, d2, f2 = MEMES[nr]
    a = frames(c1, s1, d1, f1)
    b = frames(c2, s2, d2, f2, zoom_ende=1.12)
    ziel = os.path.join(HIER, "vorschau", "reichweite", f"meme_{nr}.mp4")
    wav = os.path.join(tempfile.mkdtemp(), "t.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((ton(d1, d2) * 32767).astype(np.int16).tobytes())
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                          "-movflags", "+faststart", ziel], stdin=subprocess.PIPE)
    for i, im in enumerate(a):
        p.stdin.write(beschriften(im, oben, z1, i / FPS).tobytes())
    for i, im in enumerate(b):
        p.stdin.write(beschriften(im, oben, z2, 0.3 + i / FPS).tobytes())   # Teil 2: Beschriftung sofort da
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg-Fehler")
    print(ziel, round(d1 + d2, 1), "s")


if __name__ == "__main__":
    for nr in [int(x) for x in sys.argv[2:]] or sorted(MEMES):
        erzeuge(nr)
