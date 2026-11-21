#!/usr/bin/env python3
"""Vertonte Fassung der Vorschau „Do's & Don'ts: Die Gehaltsfrage“: drei Sprecher aus der ElevenLabs-Bibliothek
(keine geklonten Stimmen) auf den Website-Porträts, Sprechblasen Wort für Wort synchron zur Stimme, Michael spricht
die Tipps. Achtung: Fremde Stimmen auf echten Fotos gelten als realistisch veränderter Ton – vor einer
Veröffentlichung KI-Hinweis setzen (Instagram „KI-Info“ + Bildtext).
Aufruf: python werkzeuge/demo_dosdonts_vertont.py  ->  vorschau/reichweite/demo_gehalt_vertont.mp4"""
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import demo_dosdonts as dd  # noqa: E402
import topjob_video as tv  # noqa: E402
from bild import NAVY, ORANGE, WEISS, font, wrap  # noqa: E402

W, H, FPS, SR = dd.W, dd.H, dd.FPS, dd.SR
ZIEL = os.path.join(HIER, "vorschau", "reichweite", "demo_gehalt_vertont.mp4")
CACHE = os.path.join(HIER, "vorschau", "reichweite", "ton")
STIMMEN = {"fabrice": "gGjaVIGkCSfKUIBYtNT2",     # Marc – Pleasant and Interesting
           "pascal": "aTTiK3YzK3dXETpuDE2h",      # Ben – Effortless and Casual
           "waldemar": "IWm8DnJ4NGjFI7QAM5lM",    # Stephan – Warm and Friendly
           "michael": "87AwpS6yC86wa2WglbsK"}     # Michael – Inpernell-Sprecher

# (Art, Sprecher, gesprochener Text mit Regieanweisung, Pause davor, Pause danach)
ABLAUF = [
    ("frage", "fabrice", "[curious] Was stellst du dir beim Gehalt vor?", 0.7, 0.5),
    ("dont", "pascal", "[hesitant] Äh, so 20 Euro die Stunde wären okay.", 0.6, 0.3),
    ("freeze", None, None, 0.0, 2.6),
    ("rat", "waldemar", "[calm] Stopp. Verkauf dich nicht unter Wert. Begründe deinen Wunsch.", 0.6, 0.5),
    ("do", "pascal", "[confident] Mit 3 Jahren Erfahrung an der 5-Achs-Fräse stelle ich mir 30 Euro pro Stunde vor.",
     0.7, 1.6),
    ("tipps", "michael", "[warm] Drei Tipps. Recherchiere vorher, was in deinem Beruf üblich ist. Nenne eine "
     "konkrete Zahl. Und begründe sie mit deiner Erfahrung. Verkauf dich nicht unter Wert.", 0.5, 2.0),
]
TIPPS = ("Vorher recherchieren, was in deinem Beruf üblich ist.", "Eine konkrete Zahl nennen.",
         "Mit deiner Erfahrung begründen.")


def sprechen(wer, text):
    tv.STIMME = STIMMEN[wer]
    ton, woerter, zeiten, quote = tv.sprich_abschnitt(text, CACHE)
    return ton, woerter, zeiten


def bauen():
    szenen, t = [], 0.0
    for art, wer, text, vor, nach in ABLAUF:
        if text:
            ton, woerter, zeiten = sprechen(wer, text)
            dauer = vor + len(ton) / SR + nach
        else:
            ton, woerter, zeiten, dauer = None, [], [], nach
        szenen.append(dict(art=art, wer=wer, start=t, ende=t + dauer, vor=vor, ton=ton, woerter=woerter,
                           zeiten=zeiten, text=tv.anzeige_text(text) if text else ""))
        t += dauer
    return szenen


def gesprochen(sz, rel):
    """Anzahl der Wörter, die schon gesprochen wurden (für die Sprechblase)."""
    r = rel - sz["vor"]
    if r < 0:
        return 0
    return sum(1 for a, b in sz["zeiten"] if a <= r + 0.05) or (1 if r > 0 else 0)


def frame(szenen, t):
    sz = next((s for s in szenen if s["start"] <= t < s["ende"]), szenen[-1])
    rel = t - sz["start"]
    img = dd.HG.copy()
    art = sz["art"]
    if art != "tipps":
        dd.kopfzeile(img)
    if art in ("frage", "dont", "rat", "do"):
        wer = sz["wer"]
        dd.fotokarte(img, wer, rel, rein=1.0 if art in ("frage", "do") else rel / 0.5)
        if art == "do":
            img = dd.etikett(img, "DO", dd.GRUEN, rel)
        n = gesprochen(sz, rel)
        if n:
            dd.blase(img, sz["text"], n / len(sz["text"].split()))
        if art == "do" and rel > sz["ende"] - sz["start"] - 1.6:
            d = ImageDraw.Draw(img)
            d.rounded_rectangle([360, 1405, W - 60, 1495], radius=20, fill=dd.GRUEN)
            d.text((690, 1450), "Konkret, begründet, selbstbewusst", font=font("h800", 36), fill=WEISS, anchor="mm")
    elif art == "freeze":
        vor = szenen[1]
        dd.fotokarte(img, "pascal", 3.8, grau=True)
        dd.blase(img, vor["text"], 1.0, farbe=(210, 210, 210))
        dd.rotes_x(img, rel / 0.8)
        img = dd.etikett(img, "DON'T", dd.ROT, rel)
        if rel > 0.9:
            d = ImageDraw.Draw(img)
            d.rounded_rectangle([360, 1405, W - 60, 1495], radius=20, fill=(0, 0, 0))
            d.text((690, 1450), "Unsicher, zu niedrig, unbegründet", font=font("h800", 36), fill=WEISS, anchor="mm")
    else:
        d = ImageDraw.Draw(img)
        d.text((W // 2, 450), "SO GEHT'S", font=font("h800", 50), fill=ORANGE, anchor="mm")
        # Tipp erscheint, wenn Michael den passenden Satz beginnt (Wortanfänge: „Recherchiere“, „Nenne“, „Und“)
        r = rel - sz["vor"]
        starts = []
        for wort, (a, b) in zip(sz["woerter"], sz["zeiten"]):
            if wort.strip(".,").lower() in ("recherchiere", "nenne", "und") and len(starts) < 3:
                starts.append(a)
        y = 540
        for i, txt in enumerate(TIPPS):
            if i >= len(starts) or r < starts[i] - 0.1:
                break
            q = dd.glatt((r - starts[i] + 0.1) / 0.35)
            x = 90 - int((1 - q) * 60)
            d.ellipse([x, y, x + 72, y + 72], fill=ORANGE)
            d.text((x + 36, y + 36), str(i + 1), font=font("h800", 42), fill=NAVY, anchor="mm")
            yy = y
            for z in wrap(d, txt, font("h700", 48), W - 300):
                d.text((x + 105, yy), z, font=font("h700", 48), fill=WEISS)
                yy += 60
            y = yy + 50
        schluss = next((a for wort, (a, b) in zip(sz["woerter"], sz["zeiten"]) if wort.lower() == "verkauf"), 99)
        if r > schluss - 0.1:
            d.text((W // 2, 1300), "Verkauf dich nicht unter Wert.", font=font("h800", 56), fill=WEISS, anchor="mm")
        rgba = img.convert("RGBA")
        dd.rd.sticker(rgba, "BEISPIELZAHLEN", (W // 2 - 170, 1150), winkel=-3, fuell=(255, 196, 64),
                      schrift=NAVY, groesse=30)
        img = rgba.convert("RGB")
    rgba = img.convert("RGBA")
    dd.rd.logo_marke(rgba)
    return rgba.convert("RGB")


def tonspur(szenen, n):
    mix = np.zeros(n, np.float32)
    rng = np.random.default_rng(3)

    def setze(sig, sek, g=1.0):
        i = int(sek * SR)
        sig = sig[: max(0, n - i)]
        mix[i:i + len(sig)] += sig * g

    def wusch(d=0.35):
        from scipy.signal import butter, lfilter
        t = np.arange(int(d * SR)) / SR
        b, a = butter(2, [700 / (SR / 2), 5000 / (SR / 2)], "band")
        return (lfilter(b, a, rng.standard_normal(len(t))) * np.sin(np.pi * t / d) ** 2 * 0.5).astype(np.float32)

    t_ = np.arange(int(0.45 * SR)) / SR
    summer = np.sign(np.sin(2 * np.pi * 140 * t_)) * 0.18 * np.minimum(1, (0.45 - t_) * 20)
    t_ = np.arange(int(0.9 * SR)) / SR
    ding = (np.sin(2 * np.pi * 1320 * t_) + 0.4 * np.sin(2 * np.pi * 2653 * t_)) * np.exp(-t_ * 5) * 0.4
    pegel = np.full(n, 0.5, np.float32)
    for sz in szenen:
        if sz["ton"] is not None:
            a = sz["start"] + sz["vor"]
            setze(sz["ton"], a, 0.95)
            pegel[int(a * SR) - int(0.2 * SR):int(a * SR) + len(sz["ton"])] = 0.14
        if sz["art"] in ("dont", "rat", "tipps"):
            setze(wusch(), sz["start"], 0.6)
        if sz["art"] == "freeze":
            setze(summer, sz["start"] + 0.1)
            pegel[int(sz["start"] * SR):int(sz["ende"] * SR)] = 0.05
        if sz["art"] == "do":
            setze(ding, sz["start"] + 0.15)
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", dd.MUSIK, "-f", "s16le", "-ac", "1", "-ar", str(SR),
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
    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, "t.wav")
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
    import vollstaendig
    vollstaendig.pruefe(ZIEL, [s["text"] for s in szenen if s["text"]], streng=True)


if __name__ == "__main__":
    main()
