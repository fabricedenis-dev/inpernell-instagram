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

import zeichentrick_comic as z
from bild import ORANGE, WEISS, font, wrap

W, H, FPS, SR = z.W, z.H, 30, 48000
TITEL = "Wie es sich anfühlt, als Gen Z einen Job zu suchen"
# Stimmen: ElevenLabs (Starter-Abo mit gewerblicher Lizenz), Stimmen aus der Bibliothek, die die Sprecher selbst
# dort anbieten. Schlüssel liegt als Netzwerk-Geheimnis in der Umgebung (nicht im Repository).
STIMMEN = {
    "personaler": dict(eleven="89gcX1AeMGgcsN8ypHLu"),     # Rupert – Proper & At Your Service (steif, förmlich)
    "genz": dict(eleven="JNpQqni9iUx1Jxy9h0P1"),           # Timo – Confident and Mild (jung, lässig)
}
_MODELL = {}
DIALOG = [
    dict(wer="personaler", text="Warum möchtest du bei uns arbeiten?", sprich="[curious] Warum möchtest du bei uns arbeiten?",
         augen="normal", ruhe="neutral", arm="tisch"),
    dict(wer="genz", text="Ehrlich? Ich will gar nicht arbeiten.",
         sprich="[sighs] [bored] Ehrlich? Ich will gar nicht arbeiten.", augen="muede", ruhe="neutral", arm="handy"),
    dict(wer="personaler", text="Und warum hast du dich dann beworben?",
         sprich="[confused] Und warum hast du dich dann beworben?", augen="gross", ruhe="schief", arm="tisch",
         brauen="skeptisch"),
    dict(wer="genz", text="Meine Mutter will sonst das WLAN-Passwort ändern.",
         sprich="[deadpan] Meine Mutter will sonst das WLAN-Passwort ändern.", augen="muede", ruhe="neutral", arm="handy",
         fx="schweiss",
         vor=0.6),
    dict(wer="personaler", text="Wann kannst du anfangen?", sprich="[desperate] [hopeful] Wann kannst du anfangen?",
         augen="gross", ruhe="grinsen", arm="tisch_hoch", brauen="sorge", fx="speedlines", sfx_vor="grillen", vor=1.3, pointe=True),
    dict(wer="genz", text="Remote?", sprich="[unimpressed] Remote?", augen="genervt", ruhe="schief", arm="achselzucken", fx="fragezeichen", sfx_nach="badumtss",
         vor=0.35, nach=1.3),
]
ABSPANN_TEXT = "Fachkräftemangel ist real. Wir finden die, die wirklich wollen."
VOR, NACH, ABSPANN = 0.35, 0.45, 3.0
UEBERGANG = 0.9           # weiche Überblendung von der letzten Szene in den Abschluss
ABSPANN_VOR, ABSPANN_NACH = 0.5, 2.2   # Pause vor der Sprecherstimme im Abschluss, Standzeit danach


def _asr():
    if "asr" not in _MODELL:
        from faster_whisper import WhisperModel
        _MODELL["asr"] = WhisperModel("small", device="cpu", compute_type="int8")
    return _MODELL["asr"]


def _sprechen_einmal(e, st):
    """Spricht den Satz (ElevenLabs v3, mit Regieanweisungen) und ermittelt Wortzeiten per Spracherkennung;
    schneidet nach dem letzten erkannten Wort ab. Gibt (Ton 48 kHz, Wortzeiten) zurück."""
    import json
    body = json.dumps({"text": e.get("sprich", e["text"]), "model_id": "eleven_v3", "language_code": "de"}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{st['eleven']}?output_format=mp3_44100_128", data=body,
        headers={"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "proxy-injected"), "Content-Type": "application/json",
                 "Accept": "audio/mpeg"})
    import hashlib
    cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vorschau", "comic", "ton")
    os.makedirs(cache, exist_ok=True)
    cpfad = os.path.join(cache, hashlib.sha1((st["eleven"] + "|" + e.get("sprich", e["text"]) + "|" + str(_VERSUCH[0])).encode()).hexdigest()[:16] + ".mp3")
    if os.path.exists(cpfad):
        mp3 = open(cpfad, "rb").read()
    else:
        with urllib.request.urlopen(req, timeout=120) as r:
            mp3 = r.read()
        open(cpfad, "wb").write(mp3)
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


_VERSUCH = [0]


def sprechen(e, st, versuche=3):
    """Fordert neu an, wenn die Stimme Wörter auslässt (weniger als 85 % der Wörter erkannt)."""
    n = len(e["text"].split())
    beste = None
    for v in range(versuche):
        _VERSUCH[0] = v
        ton, zeiten = _sprechen_einmal(e, st)
        if beste is None or len(zeiten) > len(beste[1]):
            beste = (ton, zeiten)
        if len(zeiten) >= 0.85 * n:
            break
        print("  Wörter fehlen, neuer Versuch")
    return beste


def szene(e, offen, augen, zoom=1.0, worte_bis=None, aktiv=None, ohne_ut=False):
    genz = e["wer"] == "genz"
    img = z.hintergrund("hocker" if genz else "buero")
    cx = 540 if genz else 680
    z.figur(img, cx, 1560, e["wer"], augen=augen, mund="offen" if offen else e["ruhe"], arm=e["arm"], sitzt=True,
            brauen=e.get("brauen"))
    if e.get("fx"):
        z.effekte(img, e["fx"], cx, 1007)
    img = z.fertig(img)
    if zoom != 1.0:   # langsamer Zoom auf das Gesicht (Pointe)
        cw, ch = int(W / zoom), int(H / zoom)
        x, y = int(cx - cw / 2), int(1020 - ch * 0.45)
        x, y = max(0, min(W - cw, x)), max(0, min(H - ch, y))
        img = img.crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
    z.titel(img, TITEL)
    if e.get("tag"):          # Einordnung über dem Untertitel, z. B. „STELLENANZEIGE“ oder „ÜBERSETZUNG“
        z_ = ImageDraw.Draw(img)
        import reel_design as rd_
        rgba = img.convert("RGBA")
        rd_.sticker(rgba, e["tag"], (W // 2 - 170, 560), winkel=-3, fuell=tuple(e.get("tag_farbe", (255, 196, 64))),
                    schrift=z.STRICH, groesse=30)
        img = rgba.convert("RGB")
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
            if not ohne_ut and (worte_bis is None or idx <= worte_bis):
                d.text((x, 640 + zi * 72), wort, font=f, fill=farbe, stroke_width=8, stroke_fill=z.STRICH)
            x += d.textlength(wort + " ", font=f)
            idx += 1
    return img


_FLOCKEN = [(random.Random(11 + i).uniform(0, W), random.Random(91 + i).uniform(0, H), random.Random(7 + i).choice((3, 4, 6)))
            for i in range(260)]


def _winter_bild(ein, t):
    """Winter-Einspieler zum Zeitpunkt t: Auto gleitet langsam quer über die Straße und dreht sich, Schnee fällt."""
    hg, auto = ein
    img = hg.copy()
    p = min(1.0, t / 2.6)
    p = p * p * (3 - 2 * p)
    # Seitenansicht: Schlingern (Kippen) und eine halbe Drehung, angedeutet durch Stauchen und Spiegeln
    breite = abs(np.cos(p * np.pi))
    a2 = auto if p < 0.5 else auto.transpose(Image.FLIP_LEFT_RIGHT)
    a2 = a2.resize((max(40, int(auto.width * (0.25 + 0.75 * breite))), auto.height), Image.LANCZOS)
    r = a2.rotate(-12 * np.sin(p * np.pi * 3), resample=Image.BICUBIC, expand=True)
    cx, cy = 330 + 360 * p, 1420 + 110 * p
    img.paste(r, (int(cx - r.width / 2), int(cy - r.height / 2)), r)
    d = ImageDraw.Draw(img)
    for x, y, g in _FLOCKEN:
        yy = (y + t * 140 * g / 4) % H
        xx = (x + 25 * np.sin(t * 1.5 + y)) % W
        d.ellipse([xx - g, yy - g, xx + g, yy + g], fill=(240, 246, 255))
    return img


def main(ziel, sketch=None):
    """sketch: dict mit titel, dialog (Liste wie DIALOG), abspann. Ohne Angabe: der Gen-Z-Sketch oben."""
    global TITEL, DIALOG, ABSPANN_TEXT
    sketch = sketch or {}
    if sketch:
        TITEL, DIALOG, ABSPANN_TEXT = sketch["titel"], sketch["dialog"], sketch["abspann"]
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
    # Abschluss: Michael Danisch spricht den Abspann-Text
    import topjob_video as tv
    sprich_ab = "[warm] " + ABSPANN_TEXT + " Link in der Bio."
    ab_ton, _w, _z, _q = tv.sprich_abschnitt(sprich_ab, os.path.join(os.path.dirname(os.path.abspath(ziel)), "ton"))
    abspann_start = t
    abspann_dauer = UEBERGANG + ABSPANN_VOR + len(ab_ton) / SR + ABSPANN_NACH
    gesamt = t + abspann_dauer
    # Tonspur: Stimmen + Comedy-Effekte (Grillen in der Starr-Pause, Wusch bei der Pointe, Ba-dum-tss am Schluss);
    # Musik nur im Abspann
    import musik
    n = int(gesamt * SR)
    mix = np.zeros(n, np.float32)
    rng = np.random.default_rng(7)

    def setze(sig, sek, gain=1.0):
        i = int(sek * SR)
        if 0 <= i < n:
            sig = sig[: n - i]
            mix[i:i + len(sig)] += sig * gain

    def grillen(dauer):
        out = np.zeros(int(dauer * SR), np.float32)
        t = np.arange(int(0.03 * SR)) / SR
        zirp = np.sin(2 * np.pi * 4600 * t) * np.sin(np.pi * t / 0.03)
        for k in np.arange(0.05, dauer - 0.2, 0.45):
            for j in range(3):
                i = int((k + j * 0.055) * SR)
                out[i:i + len(zirp)] += zirp[: len(out) - i]
        return out * 0.18

    def wusch():
        t = np.arange(int(0.35 * SR)) / SR
        x = rng.standard_normal(len(t))
        from scipy.signal import butter, lfilter
        b_, a_ = butter(2, [800 / (SR / 2), 5000 / (SR / 2)], "band")
        return (lfilter(b_, a_, x) * np.sin(np.pi * t / 0.35) ** 2 * 0.5).astype(np.float32)

    def badumtss():
        def tom(f, d=0.16):
            t = np.arange(int(d * SR)) / SR
            return np.sin(2 * np.pi * f * (1 + 0.6 * np.exp(-t * 30)) * t) * np.exp(-t * 18)
        t = np.arange(int(0.9 * SR)) / SR
        from scipy.signal import butter, lfilter
        b_, a_ = butter(2, 6000 / (SR / 2), "high")
        becken = lfilter(b_, a_, rng.standard_normal(len(t))) * np.exp(-t * 4.5) * 0.9
        out = np.zeros(int(1.4 * SR), np.float32)
        for sek, sig in ((0, tom(190)), (0.17, tom(130)), (0.40, becken)):
            i = int(sek * SR)
            out[i:i + len(sig)] += sig[: len(out) - i]
        return out * 0.55

    for tk in takte:
        st = tk["start"] + tk["vor"]
        setze(tk["ton"], st, 0.95)
        if tk["e"].get("sfx_vor") == "grillen":
            setze(grillen(tk["vor"]), tk["start"])
            setze(wusch(), st - 0.15, 0.6)
        if tk["e"].get("sfx_nach") == "badumtss":
            setze(badumtss(), st + len(tk["ton"]) / SR + tk["e"].get("badumtss_nach", 0.15))
        if tk["e"].get("einspieler") == "winter":                    # Rutschgeräusch zum gleitenden Auto
            setze(wusch(), st + len(tk["ton"]) / SR + 0.3, 0.5)
    ab_sprech = abspann_start + UEBERGANG + ABSPANN_VOR
    setze(ab_ton, ab_sprech, 0.95)
    # Musik: verspielte Comedy-Untermalung, leise unter den Stimmen, in der Starr-Pause aus (Timing der Pointe),
    # nach dem Ba-dum-tss wieder da, im Abschluss etwas lauter und unter dem Sprecher geduckt
    if sketch.get("musik_datei"):          # fertiges Musikstück (Lizenz siehe assets/musik/LIZENZEN.md)
        roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(sketch.get("musik_start", 0)), "-i",
                              os.path.join(os.path.dirname(os.path.abspath(__file__)), sketch["musik_datei"]),
                              "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"], capture_output=True, check=True).stdout
        m = np.frombuffer(roh, np.int16).astype(np.float32) / 32768
        while len(m) < n:
            m = np.concatenate([m, m])
        m = m[:n] / max(1e-6, float(np.sqrt(np.mean(m[:n] ** 2)))) * 0.2      # auf festen Grundpegel bringen
        m[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
        m[-int(1.5 * SR):] *= np.linspace(1, 0, int(1.5 * SR))
    else:
        mwav = os.path.join(tmp, "musik.wav")
        musik.erzeuge_comedy(gesamt + 0.5, mwav)
        with wave.open(mwav) as w:
            m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, 2).mean(axis=1) / 32768
        m = np.pad(m, (0, max(0, n - len(m))))[:n]
    pegel = np.full(n, 0.20, np.float32)
    for tk in takte:
        a0 = int((tk["start"] + tk["vor"]) * SR)
        pegel[a0:a0 + len(tk["ton"])] = 0.11
        if tk["e"].get("sfx_vor") == "grillen":                       # Stille für die Pointe
            pegel[int(tk["start"] * SR):int((tk["start"] + tk["vor"] + len(tk["ton"]) / SR) * SR)] = 0.0
        if tk["e"].get("sfx_nach") == "badumtss":
            e0 = int((tk["start"] + tk["vor"] + len(tk["ton"]) / SR) * SR)
            pegel[e0:int(abspann_start * SR)] = 0.0
    pegel[int(abspann_start * SR):] = 0.30
    pegel[int(ab_sprech * SR):int(ab_sprech * SR) + len(ab_ton)] = 0.16
    k = int(0.2 * SR)
    pegel = np.convolve(pegel, np.ones(k) / k, mode="same")
    mix += m * pegel
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
    ab_hg, ab_ebenen = z.abspann_ebenen(ABSPANN_TEXT, "Link in der Bio")
    letztes = None
    einspieler = None
    mundlog = []
    for k in range(int(gesamt * FPS)):
        zeit = k / FPS
        tk = next((x for x in takte if x["start"] <= zeit < x["start"] + x["dauer"]), None)
        if tk is None:
            rel = zeit - abspann_start
            frame = ab_hg.copy()
            if rel < UEBERGANG and letztes is not None:             # weiche Blende: letzte Szene zoomt weg und blendet aus
                p = min(1.0, rel / UEBERGANG)
                p = p * p * (3 - 2 * p)
                zz = 1 + 0.08 * p
                cw, ch = int(W / zz), int(H / zz)
                alt = letztes.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H))
                frame = Image.blend(alt.convert("RGBA"), frame, p)
            for j, eb in enumerate(ab_ebenen):                       # Text, Knopf, Logo nacheinander sanft einblenden
                ein = UEBERGANG * 0.6 + j * 0.45
                q = min(1.0, max(0.0, (rel - ein) / 0.5))
                if q > 0:
                    q = q * q * (3 - 2 * q)
                    eb2 = eb.copy()
                    eb2.putalpha(eb.getchannel("A").point(lambda v, q=q: int(v * q)))
                    frame.alpha_composite(eb2, (0, int((1 - q) * 40)))
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
            if e.get("einspieler") and rel > sprech_dauer + 0.35:     # Sitcom-Einspieler nach der Pointe
                q = min(1.0, (rel - sprech_dauer - 0.35) / 0.25)
                te = rel - sprech_dauer - 0.35
                if e["einspieler"] == "winter":
                    if einspieler is None:
                        einspieler = z.einspieler_winter(e.get("einspieler_text", "AM NÄCHSTEN MORGEN, 6:48 UHR:"))
                    bild = _winter_bild(einspieler, te)
                else:
                    if einspieler is None:
                        einspieler = z.einspieler_alpaka(e.get("einspieler_text", "INZWISCHEN BEIM VORGÄNGER:"))
                    bild = einspieler
                zz = 1.0 + 0.04 * min(1, te / 2.5)
                cw, ch = int(W / zz), int(H / zz)
                bild = bild.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H))
                frame = Image.blend(szene(e, False, augen, zoom=zoom, aktiv=None).convert("RGB"), bild, q) if q < 1 else bild
            else:
                frame = szene(e, offen, augen, zoom=zoom, aktiv=aktiv, ohne_ut=rel < -0.05)
            letztes = frame
        mundlog.append(1 if tk is not None and offen else 0)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg-Fehler")
    import json
    json.dump(mundlog, open(ziel + ".mund.json", "w"))
    print(ziel, round(gesamt, 1), "s")


if __name__ == "__main__":
    if len(sys.argv) > 2:        # python zeichentrick_video.py ziel.mp4 <sketch-id aus reels/warteschlange.json>
        import json
        q = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "reels", "warteschlange.json"),
                           encoding="utf-8"))
        main(sys.argv[1], next(r["sketch"] for r in q if r["id"] == sys.argv[2]))
    else:
        main(sys.argv[1])
