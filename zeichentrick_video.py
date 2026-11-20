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
# Stimmen: ElevenLabs (Starter-Abo mit gewerblicher Lizenz), Stimmen aus der Bibliothek, die die Sprecher selbst
# dort anbieten. Schlüssel liegt als Netzwerk-Geheimnis in der Umgebung (nicht im Repository).
STIMMEN = {
    "personaler": dict(eleven="87AwpS6yC86wa2WglbsK"),     # Michael Danisch – Deep and Soulful
    "genz": dict(eleven="raYPS0b2ZPlIzZWkcD0G"),           # Lars (jünger und höher als Michael, ca. 115 Hz)
}
_MODELL = {}
DIALOG = [
    dict(wer="personaler", text="Warum möchtest du bei uns arbeiten?", sprich="[curious] Warum möchtest du bei uns arbeiten?",
         augen="normal", ruhe="neutral", arm="tisch"),
    dict(wer="genz", text="Ehrlich? Ich will gar nicht arbeiten.",
         sprich="[sighs] [bored] Ehrlich? Ich will gar nicht arbeiten.", augen="muede", ruhe="neutral", arm="handy"),
    dict(wer="personaler", text="Und warum hast du dich dann beworben?",
         sprich="[confused] Und warum hast du dich dann beworben?", augen="gross", ruhe="schief", arm="tisch"),
    dict(wer="genz", text="Meine Mutter will sonst das WLAN-Passwort ändern.",
         sprich="[deadpan] Meine Mutter will sonst das WLAN-Passwort ändern.", augen="muede", ruhe="neutral", arm="handy",
         vor=0.6),
    dict(wer="personaler", text="Wann kannst du anfangen?", sprich="[desperate] [hopeful] Wann kannst du anfangen?",
         augen="gross", ruhe="grinsen", arm="tisch", vor=1.3, pointe=True),
    dict(wer="genz", text="Remote?", sprich="[unimpressed] Remote?", augen="genervt", ruhe="schief", arm="achselzucken",
         vor=0.35, nach=1.3),
]
ABSPANN_TEXT = "Fachkräftemangel ist real. Wir finden die, die wirklich wollen."
VOR, NACH, ABSPANN = 0.35, 0.45, 3.0


def _asr():
    if "asr" not in _MODELL:
        from faster_whisper import WhisperModel
        _MODELL["asr"] = WhisperModel("small", device="cpu", compute_type="int8")
    return _MODELL["asr"]


def sprechen(e, st):
    """Spricht den Satz (ElevenLabs v3, mit Regieanweisungen) und ermittelt Wortzeiten per Spracherkennung;
    schneidet nach dem letzten erkannten Wort ab. Gibt (Ton 48 kHz, Wortzeiten) zurück."""
    import json
    body = json.dumps({"text": e.get("sprich", e["text"]), "model_id": "eleven_v3", "language_code": "de"}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{st['eleven']}?output_format=mp3_44100_128", data=body,
        headers={"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "proxy-injected"), "Content-Type": "application/json",
                 "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=120) as r:
        mp3 = r.read()
    dek = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"],
                         input=mp3, capture_output=True, check=True).stdout
    ton = np.frombuffer(dek, np.int16).astype(np.float32) / 32768
    a16 = np.interp(np.arange(int(len(ton) * 16000 / SR)) * SR / 16000, np.arange(len(ton)), ton).astype(np.float32)
    segs, _ = _asr().transcribe(a16, language="de", word_timestamps=True)
    woerter = [w for s in segs for w in s.words]
    n = len(e["text"].split())
    if woerter:
        ton = ton[: int((woerter[min(len(woerter), n) - 1].end + 0.2) * SR)]
    print("  erkannt:", " ".join(w.word.strip() for w in woerter))
    return ton, [(w.start, w.end) for w in woerter[:n]]


def szene(e, offen, augen, zoom=1.0, worte_bis=None, aktiv=None):
    genz = e["wer"] == "genz"
    img = z.hintergrund("hocker" if genz else "buero")
    z.figur(img, 500 if genz else 640, 1560, e["wer"], augen=augen,
            mund="offen" if offen else e["ruhe"], arm=e["arm"], sitzt=True)
    if zoom != 1.0:   # langsamer Zoom auf das Gesicht (Pointe)
        cw, ch = int(W / zoom), int(H / zoom)
        x, y = int((500 if genz else 640) - cw / 2), int(1020 - ch * 0.45)
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
        ton, zeiten = sprechen(e, st)
        laut = np.where(np.abs(ton) > 0.02)[0]
        vorne = max(0, laut[0] - 800) if len(laut) else 0
        ton = ton[vorne:]
        zeiten = [(a - vorne / SR, b - vorne / SR) for a, b in zeiten]
        vor = e.get("vor", VOR)
        dauer = vor + len(ton) / SR + e.get("nach", NACH)
        takte.append(dict(e=e, start=t, ton=ton, dauer=dauer, zeiten=zeiten, vor=vor))
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
        a = int((tk["start"] + tk["vor"]) * SR)
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
    abspann = z.abspann(ABSPANN_TEXT, "Link in der Bio")
    mundlog = []
    for k in range(int(gesamt * FPS)):
        zeit = k / FPS
        tk = next((x for x in takte if x["start"] <= zeit < x["start"] + x["dauer"]), None)
        if tk is None:
            frame = abspann
        else:
            e, rel = tk["e"], zeit - tk["start"] - tk["vor"]
            sprech_dauer = len(tk["ton"]) / SR
            offen = False
            if 0 <= rel < sprech_dauer:
                i0 = int(rel * SR)
                rms = float(np.sqrt(np.mean(tk["ton"][i0:i0 + SR // FPS] ** 2) + 1e-9))
                offen = rms > 0.035 and (k % 4 < 3)
            worte = len(e["text"].split())
            aktiv = None
            if 0 <= rel < sprech_dauer:
                if len(tk["zeiten"]) == worte:      # echte Wortzeiten aus der Spracherkennung
                    aktiv = max([j for j, (a, b) in enumerate(tk["zeiten"]) if a <= rel] or [0])
                else:
                    aktiv = min(worte - 1, int(rel / max(0.1, sprech_dauer) * worte))
            augen = "zu" if k in blinzeln and e["augen"] not in ("muede",) else e["augen"]
            zoom = 1.0 + 0.12 * min(1, max(0, rel) / max(0.1, sprech_dauer)) if e.get("pointe") else 1.0
            frame = szene(e, offen, augen, zoom=zoom, aktiv=aktiv)
        mundlog.append(1 if tk is not None and offen else 0)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg-Fehler")
    import json
    json.dump(mundlog, open(ziel + ".mund.json", "w"))
    print(ziel, round(gesamt, 1), "s")


if __name__ == "__main__":
    main(sys.argv[1])
