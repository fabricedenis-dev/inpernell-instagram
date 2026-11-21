#!/usr/bin/env python3
"""Beispiel-Meme mit KI-Darstellung der Inhaber: „Was Bewerber erwarten“ (grauer Büro-Stock-Clip, Fahrstuhlmusik)
vs. „Was sie bekommen“ (GTA-Poster der Inhaber, Synthwave). KI-Hinweis beim Posten Pflicht (siehe CLAUDE.md).
Aufruf: python werkzeuge/meme_inhaber.py <ordner mit Mixkit-Clip 4607.mp4>  ->  vorschau/reichweite/meme_inhaber.mp4"""
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageEnhance

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import meme_reel as mr  # noqa: E402

W, H, FPS, SR = mr.W, mr.H, mr.FPS, mr.SR
mr.ORDNER = sys.argv[1] if len(sys.argv) > 1 else "."
ZIEL = os.path.join(HIER, "vorschau", "reichweite", "meme_inhaber.mp4")
FAHRSTUHL = os.path.join(HIER, "assets", "musik", "local_forecast_elevator_kevin_macleod.mp3")
SYNTH = os.path.join(HIER, "assets", "musik", "vice_police_tausdei.mp3")
D1, D2 = 3.8, 5.6


def poster_frames(dauer):
    q = Image.open(os.path.join(HIER, "assets", "team", "vorlage_poster.png")).convert("RGB")
    s = max(W / q.width, H / q.height) * 1.12
    q = q.resize((int(q.width * s), int(q.height * s)), Image.LANCZOS)
    out = []
    n = int(round(dauer * FPS))
    for i in range(n):
        p = i / max(1, n - 1)
        z = 1.12 - 0.12 * mr.glatt(p)                       # fährt langsam heraus: erst Gesichter, dann alles
        cw, ch = int(W * z / 1.12 * q.width / (W * 1.0) * (W / q.width)), int(H * z / 1.12 * q.height / (H * 1.0) * (H / q.height))
        cw, ch = int(q.width * z / 1.12), int(q.height * z / 1.12)
        cw, ch = min(cw, q.width), min(ch, q.height)
        x = (q.width - cw) // 2
        y = int((q.height - ch) * (0.35 + 0.15 * p))
        im = q.crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
        if i < 4:                                           # kurzer Blitz beim Schnitt
            im = ImageEnhance.Brightness(im).enhance(1.8 - i * 0.2)
        out.append(im)
    return out


def lade(pfad, start, n):
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(start), "-i", pfad, "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "pipe:1"], capture_output=True, check=True).stdout
    m = np.frombuffer(roh, np.int16).astype(np.float32)[:n] / 32768
    m = np.pad(m, (0, n - len(m)))
    return m / max(1e-6, float(np.sqrt(np.mean(m ** 2)))) * 0.22


def ton():
    n1, n2 = int(D1 * SR), int(D2 * SR)
    a = lade(FAHRSTUHL, 2.0, n1)
    a[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
    a[-int(0.1 * SR):] *= np.linspace(1, 0, int(0.1 * SR))
    teil2_basis = mr.ton(0.5, D2)[int(0.5 * SR):]           # nur den Schallplatten-Kratzer aus meme_reel nutzen
    kratz = teil2_basis[:int(0.4 * SR)]
    b = lade(SYNTH, 4.406, n2) * 1.2
    b[:int(0.25 * SR)] *= np.linspace(0, 1, int(0.25 * SR))
    b[-int(0.8 * SR):] *= np.linspace(1, 0, int(0.8 * SR))
    b[:len(kratz)] += kratz * 0.9
    mix = np.concatenate([a, b])
    return mix / max(1e-6, np.abs(mix).max()) * 0.9


def main():
    a = mr.frames(4607, 11.0, D1, 0.6)
    b = poster_frames(D2)
    wav = os.path.join(tempfile.mkdtemp(), "t.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((ton() * 32767).astype(np.int16).tobytes())
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                          "-movflags", "+faststart", ZIEL], stdin=subprocess.PIPE)
    for i, im in enumerate(a):
        p.stdin.write(mr.beschriften(im, "Personalvermittler", ("Was Bewerber", "erwarten"), i / FPS).tobytes())
    for i, im in enumerate(b):
        p.stdin.write(mr.beschriften(im, "", ("Was sie", "bekommen"), 0.3 + i / FPS).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg-Fehler")
    print(ZIEL, D1 + D2, "s")


if __name__ == "__main__":
    main()
