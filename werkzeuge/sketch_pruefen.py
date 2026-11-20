"""Prüft ein Zeichentrick-Video: Lippen-Synchronität (offener Mund vs. Sprachpegel je Bild), Untertitel-Timing
(orange markiertes Wort vs. erkannte Wortzeiten), Tonlage/Lautstärke je Satz, Pausen. Aufruf: python sketch_pruefen.py video.mp4"""
import subprocess
import sys

import numpy as np

V = sys.argv[1]
FPS, SR, W, H = 30, 16000, 270, 480


def bilder():
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", V, "-vf", f"scale={W}:{H}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(roh, np.uint8).reshape(-1, H, W, 3)


def ton():
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", V, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(roh, np.int16).astype(np.float32) / 32768


b, a = bilder(), ton()
n = len(b)
# Mund offen = dunkelrote Mundfläche (90,30,40) sichtbar
import json, os
mund = np.array(json.load(open(V + ".mund.json")))[:len(b)] if os.path.exists(V + ".mund.json") else np.zeros(len(b))
b = b[:len(mund)]
# orange markiertes Wort sichtbar (Untertitel-Bereich)
orange = np.array([((f[150:260, :, 0] > 200) & (np.abs(f[150:260, :, 1].astype(int) - 120) < 45) & (f[150:260, :, 2] < 80)).sum()
                   for f in b])
rms = np.array([np.sqrt(np.mean(a[int(i / FPS * SR):int((i + 1) / FPS * SR)] ** 2) + 1e-12) for i in range(n)])
db = 20 * np.log10(rms)
sprache = db > -38
# Lippen: in Sprachbildern soll der Mund regelmäßig offen sein, in Pausen geschlossen
in_sprache = mund[sprache].mean() if sprache.any() else 0
in_pause = mund[~sprache].mean() if (~sprache).any() else 0
print(f"Bilder: {n}, Dauer {n / FPS:.1f} s")
print(f"Lippen: Mund offen in {in_sprache:.0%} der Sprachbilder (Soll ca. 50–75 %), in {in_pause:.0%} der Pausen (Soll < 5 %)")
# Versatz: Kreuzkorrelation Mund vs. Sprachpegel
best = max(range(-6, 7), key=lambda k: np.corrcoef(np.roll(mund.astype(float), k), sprache.astype(float))[0, 1])
print(f"Lippen-Versatz: {best / FPS * 1000:+.0f} ms (0 = synchron; positiv = Mund zu spät)")
# Pausen / Sätze
seg, an = [], None
for i, s in enumerate(sprache):
    if s and an is None:
        an = i
    if (not s or i == n - 1) and an is not None:
        if i - an > 4:
            seg.append((an, i))
        an = None
# kurze Lücken (< 0,25 s) zusammenfassen
satz = []
for s0, s1 in seg:
    if satz and s0 - satz[-1][1] < 8:
        satz[-1] = (satz[-1][0], s1)
    else:
        satz.append((s0, s1))
try:
    import librosa
    print("Sätze (Start–Ende, Pause davor, Lautstärke, Tonhöhe Median/Spanne):")
    vorher = 0
    for s0, s1 in satz:
        x = a[int(s0 / FPS * SR):int(s1 / FPS * SR)]
        f0, vf, _ = librosa.pyin(x, fmin=60, fmax=400, sr=SR, frame_length=1024)
        f0 = f0[~np.isnan(f0)]
        med = np.median(f0) if len(f0) else 0
        spanne = 12 * np.log2(np.percentile(f0, 90) / np.percentile(f0, 10)) if len(f0) > 5 else 0
        laut = 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
        print(f"  {s0 / FPS:5.2f}–{s1 / FPS:5.2f} s | Pause {max(0, s0 - vorher) / FPS:4.2f} s | {laut:5.1f} dB | "
              f"{med:5.0f} Hz | {spanne:4.1f} Halbtöne")
        vorher = s1
except Exception as e:
    print("Tonhöhe nicht messbar:", e)
# Untertitel: Wechsel des orangen Worts vs. Wortanfänge aus der Spracherkennung
from faster_whisper import WhisperModel
segs, _ = WhisperModel("small", device="cpu", compute_type="int8").transcribe(a, language="de", word_timestamps=True)
segs = list(segs)
starts = [w.start for s in segs for w in s.words]
wechsel = [i / FPS for i in range(1, n) if abs(int(orange[i]) - int(orange[i - 1])) > 25 and orange[i] > 0]
abw = [min(abs(t - s) for s in starts) for t in wechsel] if starts and wechsel else []
if abw:
    print(f"Untertitel: {len(wechsel)} Wortwechsel, Abweichung zum gesprochenen Wort Median {np.median(abw) * 1000:.0f} ms, "
          f"max {max(abw) * 1000:.0f} ms")
print("Gesprochen:", " ".join(s.text.strip() for s in segs))
