#!/usr/bin/env python3
"""Zeichentrick-Sketch als Video: KI-Stimmen (Azure, kostenloser Tarif), Mund nach Lautstärke, Blinzeln,
Schnitt je Sprecher, mitlaufende Untertitel (aktuelles Wort orange), Zoom auf die Pointe, leise eigene Musik.
Aufruf: python zeichentrick_video.py ziel.mp4"""
import os
import random
import subprocess
import sys
import tempfile
import urllib.request
import wave
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageDraw

import zeichentrick as z
from bild import ORANGE, WEISS, font, wrap

W, H, FPS, SR = z.W, z.H, 30, 48000
TITEL = "Wie es sich anfühlt, als Gen Z einen Job zu suchen"
STIMMEN = {  # eigene Auswahl aus Azure-Standardstimmen, keine nachgeahmten Personen
    "personaler": dict(stimme="de-DE-ConradNeural", tempo="-4%", tonhoehe="-4%"),
    "genz": dict(stimme="de-DE-FlorianMultilingualNeural", tempo="-12%", tonhoehe="-2%"),
}
DIALOG = [
    dict(wer="personaler", text="Warum möchtest du bei uns arbeiten?", augen="normal", ruhe="neutral", arm="tisch"),
    dict(wer="genz", text="Ehrlich gesagt? Ich möchte gar nicht arbeiten.", augen="muede", ruhe="neutral", arm="handy"),
    dict(wer="personaler", text="Und warum hast du dich dann beworben?", augen="gross", ruhe="schief", arm="tisch"),
    dict(wer="genz", text="Weil man Miete leider nicht kündigen kann wie ein Abo.", augen="normal", ruhe="grinsen",
         arm="achselzucken", pointe=True),
]
VOR, NACH, ABSPANN = 0.35, 0.45, 3.0


def sprechen(text, ziel, stimme, tempo, tonhoehe):
    ssml = ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="de-DE">'
            f'<voice name="{stimme}"><prosody rate="{tempo}" pitch="{tonhoehe}">{escape(text)}</prosody></voice></speak>')
    req = urllib.request.Request(
        "https://germanywestcentral.tts.speech.microsoft.com/cognitiveservices/v1", data=ssml.encode("utf-8"),
        headers={"Ocp-Apim-Subscription-Key": os.environ.get("AZURE_SPEECH_KEY", "proxy-injected"),
                 "Content-Type": "application/ssml+xml", "User-Agent": "inpernell-reels",
                 "X-Microsoft-OutputFormat": "riff-48khz-16bit-mono-pcm"})
    with urllib.request.urlopen(req, timeout=60) as r, open(ziel, "wb") as f:
        f.write(r.read())
    with wave.open(ziel) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def szene(e, offen, augen, zoom=1.0, worte_bis=None, aktiv=None):
    genz = e["wer"] == "genz"
    img = z.hintergrund("hocker" if genz else "buero")
    z.figur(img, 500 if genz else 640, 1560, e["wer"], augen=augen,
            mund="offen" if offen else e["ruhe"], arm=e["arm"], sitzt=True)
    if zoom != 1.0:   # langsamer Zoom auf das Gesicht (Pointe)
        cw, ch = int(W / zoom), int(H / zoom)
        x, y = int(500 - cw / 2), int(1020 - ch * 0.45)
        x, y = max(0, min(W - cw, x)), max(0, min(H - ch, y))
        img = img.crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
    z.titel(img, TITEL)
    # Untertitel: ganze Zeile, gesprochenes Wort orange
    d = ImageDraw.Draw(img)
    f = font("h800", 56)
    worte = e["text"].split()
    zeilen, akt = [], []
    for wort in worte:
        probe = " ".join(akt + [wort])
        if akt and d.textlength(probe, font=f) > W - 220:
            zeilen.append(akt); akt = [wort]
        else:
            akt.append(wort)
    zeilen.append(akt)
    idx = 0
    for zi, zeile in enumerate(zeilen):
        breite = d.textlength(" ".join(zeile), font=f)
        x = (W - breite) / 2
        for wort in zeile:
            farbe = ORANGE if aktiv == idx else WEISS
            if worte_bis is None or idx <= worte_bis:
                d.text((x, 640 + zi * 72), wort, font=f, fill=farbe, stroke_width=8, stroke_fill=z.STRICH)
            x += d.textlength(wort + " ", font=f)
            idx += 1
    return img


def main(ziel):
    rnd = random.Random(3)
    tmp = tempfile.mkdtemp()
    spuren, takte = [], []
    t = 0.0
    for i, e in enumerate(DIALOG):
        st = STIMMEN[e["wer"]]
        ton = sprechen(e["text"], os.path.join(tmp, f"{i}.wav"), st["stimme"], st["tempo"], st["tonhoehe"])
        # Stille am Anfang/Ende der Azure-Datei abschneiden
        laut = np.where(np.abs(ton) > 0.02)[0]
        ton = ton[max(0, laut[0] - 800):laut[-1] + 2400] if len(laut) else ton
        dauer = VOR + len(ton) / SR + NACH + (0.5 if e.get("pointe") else 0)
        takte.append(dict(e=e, start=t, ton=ton, dauer=dauer))
        t += dauer
    gesamt = t + ABSPANN
    # Tonspur: Stimmen + leise eigene Musik (im Abspann lauter)
    import musik
    mwav = os.path.join(tmp, "musik.wav")
    musik.erzeuge_chill(gesamt, mwav, "ocean_lofi")
    with wave.open(mwav) as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, 2).mean(axis=1) / 32768
    n = int(gesamt * SR)
    m = np.pad(m, (0, max(0, n - len(m))))[:n]
    pegel = np.full(n, 0.12)
    pegel[int(t * SR):] = np.linspace(0.12, 0.45, n - int(t * SR))
    mix = m * pegel
    for tk in takte:
        a = int((tk["start"] + VOR) * SR)
        mix[a:a + len(tk["ton"])] += tk["ton"] * 0.95
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.9
    tonpfad = os.path.join(tmp, "mix.wav")
    with wave.open(tonpfad, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", tonpfad, "-map", "0:v", "-map", "1:a", "-shortest", "-c:v", "libx264", "-preset", "slow",
           "-crf", "18", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
           "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-movflags", "+faststart", ziel]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    blinzeln = set()
    for k in range(int(gesamt * FPS)):
        if rnd.random() < 0.012:
            blinzeln.update(range(k, k + 4))
    abspann = z.abspann("Du willst doch arbeiten? Dann wenigstens im richtigen Job.", "Link in der Bio")
    for k in range(int(gesamt * FPS)):
        zeit = k / FPS
        tk = next((x for x in takte if x["start"] <= zeit < x["start"] + x["dauer"]), None)
        if tk is None:
            frame = abspann
        else:
            e, rel = tk["e"], zeit - tk["start"] - VOR
            sprech_dauer = len(tk["ton"]) / SR
            offen = False
            if 0 <= rel < sprech_dauer:
                i0 = int(rel * SR)
                rms = float(np.sqrt(np.mean(tk["ton"][i0:i0 + SR // FPS] ** 2) + 1e-9))
                offen = rms > 0.035 and (k % 4 < 3)
            worte = len(e["text"].split())
            aktiv = min(worte - 1, int(max(0, rel) / max(0.1, sprech_dauer) * worte)) if 0 <= rel < sprech_dauer else None
            augen = "zu" if k in blinzeln and e["augen"] not in ("muede",) else e["augen"]
            zoom = 1.0 + 0.12 * min(1, max(0, rel) / max(0.1, sprech_dauer)) if e.get("pointe") else 1.0
            frame = szene(e, offen, augen, zoom=zoom, aktiv=aktiv)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg-Fehler")
    print(ziel, round(gesamt, 1), "s")


if __name__ == "__main__":
    main(sys.argv[1])
