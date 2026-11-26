#!/usr/bin/env python3
"""Sketch „Gleitzeit im Schwarzwald“ im Strichmännchen-Meme-Stil (Inpernell-Account).
Aufbau wie bei erfolgreichen Meme-Cartoons: POV-Zeile, Dialog, der sich Satz für Satz steigert,
Pointe mit Schnitt in die Wirklichkeit, dann Abschluss mit Logo.
Hintergründe: lokale Bild-KI (assets/sketche), Figuren als Vektor (werkzeuge/strichmann.py),
Stimmen aus der ElevenLabs-Bibliothek (Rupert, Timo; keine Nachahmung),
Musik „Monkeys Spinning Monkeys“ (Kevin MacLeod, CC BY 4.0).
Aufruf: python werkzeuge/sketch_gleitzeit_strich.py [ziel.mp4]"""
import math
import os
import random
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import flat_cartoon as fc  # noqa: E402
import reel_design as rd  # noqa: E402
import strichmann as sm  # noqa: E402
import topjob_video as tv  # noqa: E402
from bild import NAVY, NAVY_HELL, ORANGE, font  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
ASSETS = os.path.join(HIER, "assets", "sketche")
ZIEL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HIER, "vorschau", "sketche", "gleitzeit_strich.mp4")
CACHE = os.path.join(HIER, "vorschau", "memes", "ton")
MUSIK = os.path.join(HIER, "assets", "musik", "monkeys_spinning_monkeys_kevin_macleod.mp3")
STIMME = {"personaler": "89gcX1AeMGgcsN8ypHLu", "bewerber": "JNpQqni9iUx1Jxy9h0P1"}   # Rupert, Timo
P_X, B_X, FUSS, GR = 290, 790, 1790, 1.2
POV = "POV: Der Personaler verkauft dir Gleitzeit"

# (Ort, Oben-Text, [(Sprecher, Sprechtext, Anzeige, Pause davor)], Nachlauf, Art)
SZENEN = [
    ("buero", POV, [("personaler", "[proud] Und das Beste: Bei uns hast du Gleitzeit!", None, 0.5),
                    ("bewerber", "[excited] Nice! Dann fang ich um zehn an.", None, 0.25)], 0.3, "angebot"),
    ("buero", POV, [("personaler", "[matter-of-fact] Kernzeit ist von sieben bis achtzehn Uhr.",
                     "Kernzeit ist von 7 bis 18 Uhr.", 0.3),
                    ("bewerber", "[confused] Und was genau gleitet da?", None, 0.5)], 0.3, "kernzeit"),
    ("buero", POV, [("personaler", "[cheerful] Na, du. Eine Stunde über die B fünfhundert. Im Januar.",
                     "Na, du. Eine Stunde über die B 500. Im Januar.", 0.3)], 0.5, "pointe"),
    ("winter", "Am nächsten Morgen, 6:48 Uhr:", [("bewerber", "[deadpan] Aha. Deshalb Gleitzeit.", None, 2.0)],
     1.6, "winter"),
    ("abspann", None, [], 3.2, "abspann"),
]

_CACHE = {}


def ebene(x, y, **kw):
    key = (x, y, tuple(sorted((k, str(v)) for k, v in kw.items())))
    if key not in _CACHE:
        e = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sm.figur(e, x, y, **kw)
        _CACHE[key] = e
    return _CACHE[key]


def setze_ebene(img, e, dx=0, dy=0):
    if dx == 0 and dy == 0:
        img.alpha_composite(e)
    else:
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tmp.paste(e, (dx, dy), e)
        img.alpha_composite(tmp)


def hg(name):
    return Image.open(os.path.join(ASSETS, name + ".png")).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")


BUERO = hg("bg_buero")
WINTER = hg("bg_winter")


def auto_sprite():
    """Kleines rotes Auto mit dem Bewerber am Steuer (Seitenansicht), 2-fach gezeichnet und verkleinert."""
    s = 2
    sp = Image.new("RGBA", (640 * s, 380 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    K = (20, 20, 24)
    d.polygon([(150 * s, 150 * s), (210 * s, 50 * s), (430 * s, 50 * s), (500 * s, 150 * s)], fill=(190, 225, 245),
              outline=K, width=8 * s)
    kopf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sm.figur(kopf, 320, 470, groesse=0.42, **sm.BEWERBER, augen="genervt", mund="neutral", brauen=(-4, 0))
    kopf = kopf.crop((320 - 160, 470 - 470, 320 + 160, 470 - 260)).resize((320 * s, 210 * s), Image.LANCZOS)
    k2 = Image.new("RGBA", sp.size, (0, 0, 0, 0))
    k2.paste(kopf, (180 * s, -20 * s), kopf)
    maske = Image.new("L", sp.size, 0)
    ImageDraw.Draw(maske).polygon([(158 * s, 146 * s), (214 * s, 56 * s), (426 * s, 56 * s), (494 * s, 146 * s)],
                                  fill=255)
    k2.putalpha(Image.composite(k2.getchannel("A"), Image.new("L", sp.size, 0), maske))
    sp.alpha_composite(k2)
    d = ImageDraw.Draw(sp)
    d.line([(320 * s, 50 * s), (320 * s, 150 * s)], fill=K, width=8 * s)
    d.rounded_rectangle([40 * s, 140 * s, 600 * s, 290 * s], radius=50 * s, fill=(214, 46, 46), outline=K, width=8 * s)
    d.rectangle([560 * s, 180 * s, 600 * s, 215 * s], fill=(255, 230, 120), outline=K, width=4 * s)
    for x in (160, 470):
        d.ellipse([(x - 55) * s, 230 * s, (x + 55) * s, 340 * s], fill=K)
        d.ellipse([(x - 24) * s, 262 * s, (x + 24) * s, 308 * s], fill=(160, 160, 170))
    d.rectangle([40 * s, 120 * s, 600 * s, 150 * s], fill=(255, 255, 255), outline=K, width=5 * s)   # Schnee aufs Dach
    return sp.resize((640, 380), Image.LANCZOS)


AUTO = auto_sprite().resize((920, 546), Image.LANCZOS)
SCHNEE = [(random.Random(i).randint(0, W), random.Random(i * 3).randint(0, H), random.Random(i * 7).randint(4, 11))
          for i in range(140)]


def bauen():
    szenen, t = [], 0.0
    for ort, oben, saetze, nach, art in SZENEN:
        teile, rel = [], 0.0
        for wer, text, anzeige, vor in saetze:
            tv.STIMME = STIMME[wer]
            ton, woerter, zeiten, _q = tv.sprich_abschnitt(text, CACHE)
            rel += vor
            teile.append(dict(wer=wer, text=anzeige or tv.anzeige_text(text), ton=ton, zeiten=zeiten, start=rel))
            rel += len(ton) / SR
        dauer = rel + nach
        szenen.append(dict(ort=ort, oben=oben, teile=teile, start=t, dauer=dauer, art=art))
        t += dauer
    return szenen, t


def spricht(sz, rel):
    for tl in sz["teile"]:
        r = rel - tl["start"]
        if 0 <= r < len(tl["ton"]) / SR:
            i = int(r * SR)
            rms = float(np.sqrt(np.mean(tl["ton"][i:i + SR // FPS] ** 2) + 1e-9))
            return tl["wer"], rms > 0.03 and int(r * FPS) % 4 != 3
    return None, False


def worte(tl, rel):
    r = rel - tl["start"]
    w = tl["text"].split()
    n = len(tl["zeiten"])
    # Anzeige und Sprechtext können unterschiedlich viele Wörter haben: anteilig aufdecken
    k = sum(1 for a, _ in tl["zeiten"] if a <= r + 0.05)
    return " ".join(w[:round(k * len(w) / max(1, n))]) if k > 0 else ""


def buero(sz, rel, k, blinz):
    img = BUERO.copy()
    art = sz["art"]
    wer, offen = spricht(sz, rel)
    wip = int(5 * math.sin(k * 0.22))
    zweiter = sz["teile"][1]["start"] if len(sz["teile"]) > 1 else 99
    if art == "angebot":
        p = dict(mund="grinsen", brauen=(-8, 8), arm_l=(40, 60), arm_r=(40, 60))
        b = dict(mund="neutral", brauen=(0, 4)) if rel < zweiter else \
            dict(mund="lachen", brauen=(-10, 10), arm_l=(140, 160), arm_r=(15, 5), faust=(True, False))
    elif art == "kernzeit":
        p = dict(mund="laecheln", brauen=(-6, 6), arm_l=(15, 5), arm_r=(150, 175), faust=(False, False))
        b = dict(augen="gross", mund="offen", brauen=(-14, 18)) if rel < zweiter else \
            dict(augen="genervt", mund="skeptisch", brauen=(12, 0), arm_l=(70, 140), arm_r=(15, 5))
    else:
        p = dict(mund="grinsen", brauen=(-10, 10), arm_l=(15, 5), arm_r=(70, 100))
        b = dict(augen="punkt", mund="neutral", brauen=(0, 0))
    if wer == "personaler" and offen:
        p["mund"] = "offen"
    if wer == "bewerber" and offen:
        b["mund"] = "offen"
    for f in (p, b):
        if k in blinz and f.get("augen") is None:
            f["augen"] = "zu"
    setze_ebene(img, ebene(P_X, FUSS, groesse=GR, **sm.PERSONALER, **p), dy=wip)
    setze_ebene(img, ebene(B_X, FUSS, groesse=GR, spiegeln=True, **sm.BEWERBER, **b), dy=-wip)
    img = img.convert("RGB")
    if art == "pointe":                                               # langsamer Zoom auf den sprachlosen Bewerber
        z = 1 + 0.25 * min(1, rel / max(0.1, sz["dauer"]))
        cw, ch = int(W / z), int(H / z)
        x0, y0 = min(W - cw, int(B_X - cw / 2)), max(0, int(950 - ch / 2))
        img = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
    y = fc.text_oben(img, sz["oben"]) + 30
    for tl in [t for t in sz["teile"] if rel >= t["start"] - 0.05]:
        txt = worte(tl, rel)
        if tl["wer"] == "personaler":
            if txt:
                fc.blase(img, txt, 40, y, w=640)
            y += 190 if len(tl["text"]) > 26 else 130
        elif txt:
            fc.blase(img, txt, 400, y, w=640, rechts=True)
    img = img.convert("RGBA")
    rd.logo_marke(img)
    return img.convert("RGB")


def winter(sz, rel, k):
    img = WINTER.copy()
    d = ImageDraw.Draw(img)
    for (x, y, r) in SCHNEE:                                          # fallender Schnee
        yy = (y + k * (r * 1.6)) % H
        xx = (x + 30 * math.sin((k + y) * 0.03)) % W
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 255, 255, 230))
    # Auto rutscht seitlich über die glatte Straße, schlingert und landet in der Schneewehe
    p = min(1.0, rel / 2.4)
    x = -980 + (1 - (1 - p) ** 2) * 1240
    w = 10 * math.sin(rel * 5.5) if rel < 2.4 else -6
    dy = 0
    if rel > 2.4:
        x = 260 + 14 * math.sin(rel * 32) * math.exp(-(rel - 2.4) * 4)
        dy = 30
    a = AUTO.rotate(w, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(a, (int(x), 1330 - a.height // 2 + dy + 200))
    if rel > 2.4:                                                     # Schneewolke beim Einschlag
        r = int(80 + 260 * min(1, (rel - 2.4) / 0.5))
        al = int(220 * max(0, 1 - (rel - 2.4) / 1.4))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse([1080 - r, 1500 - r // 2, 1080 + r, 1500 + r // 2], fill=(255, 255, 255, al))
        img.alpha_composite(ov)
    img = img.convert("RGB")
    fc.text_oben(img, sz["oben"])
    for tl in sz["teile"]:
        txt = worte(tl, rel)
        if txt:
            fc.blase(img, txt, 360, 820, w=600, rechts=True)
    img = img.convert("RGBA")
    rd.logo_marke(img)
    return img.convert("RGB")


_ABSPANN = {}


def abspann(rel):
    if "b" not in _ABSPANN:
        img = Image.new("RGB", (W, H), NAVY)
        d = ImageDraw.Draw(img)
        for y in range(H):
            t = y / H
            d.line([(0, y), (W, y)], fill=tuple(int(NAVY_HELL[i] + (NAVY[i] - NAVY_HELL[i]) * t) for i in range(3)))
        lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
        lg = lg.resize((760, round(lg.height * 760 / lg.width)), Image.LANCZOS)
        img.paste(lg, ((W - 760) // 2, 640), lg)
        d.text((W // 2, 880), "Direktvermittlung", font=font("h800", 64), fill=ORANGE, anchor="ma")
        f = font("t400", 48)
        for i, z in enumerate(("Gute Jobs gibt es auch hier", "im Schwarzwald.", "Ganz ohne Rutschpartie.")):
            d.text((W // 2, 1060 + i * 66), z, font=f, fill=(255, 255, 255), anchor="ma")
        _ABSPANN["b"] = img
    img = _ABSPANN["b"]
    if rel < 0.3:
        return Image.blend(Image.new("RGB", (W, H), NAVY), img, rel / 0.3)
    return img


def tonspur(szenen, gesamt):
    rng = np.random.default_rng(3)
    from scipy.signal import butter, lfilter
    n = int(gesamt * SR)
    mix = np.zeros(n, np.float32)

    def setze(sig, sek, g=1.0):
        i = int(sek * SR)
        if 0 <= i < n:
            sig = sig[: n - i]
            mix[i:i + len(sig)] += sig * g

    def grillen(dauer):
        out = np.zeros(int(dauer * SR), np.float32)
        t = np.arange(int(0.03 * SR)) / SR
        zirp = np.sin(2 * np.pi * 4600 * t) * np.sin(np.pi * t / 0.03)
        for k in np.arange(0.05, dauer - 0.2, 0.45):
            for j in range(3):
                i = int((k + j * 0.055) * SR)
                out[i:i + len(zirp)] += zirp[: len(out) - i]
        return out * 0.18

    def badumtss():
        def tom(f, d=0.16):
            t = np.arange(int(d * SR)) / SR
            return np.sin(2 * np.pi * f * (1 + 0.6 * np.exp(-t * 30)) * t) * np.exp(-t * 18)
        t = np.arange(int(0.9 * SR)) / SR
        b_, a_ = butter(2, 6000 / (SR / 2), "high")
        becken = lfilter(b_, a_, rng.standard_normal(len(t))) * np.exp(-t * 4.5) * 0.9
        out = np.zeros(int(1.4 * SR), np.float32)
        for sek, sig in ((0, tom(190)), (0.17, tom(130)), (0.40, becken)):
            i = int(sek * SR)
            out[i:i + len(sig)] += sig[: len(out) - i]
        return out * 0.55

    def quietschen(d=1.6):
        t = np.arange(int(d * SR)) / SR
        f = 1700 + 500 * np.sin(2 * np.pi * 3 * t)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + 0.5 * rng.standard_normal(len(t))
        b_, a_ = butter(2, [1200 / (SR / 2), 3800 / (SR / 2)], "band")
        return (lfilter(b_, a_, s) * np.minimum(1, t * 8) * np.exp(-t * 0.8) * 0.5).astype(np.float32)

    def plumps():
        t = np.arange(int(0.6 * SR)) / SR
        b_, a_ = butter(2, 400 / (SR / 2), "low")
        return (lfilter(b_, a_, rng.standard_normal(len(t))) * np.exp(-t * 9) * 3.0).astype(np.float32)

    pegel = np.full(n, 0.5, np.float32)
    for sz in szenen:
        for tl in sz["teile"]:
            a = sz["start"] + tl["start"]
            setze(tl["ton"], a, 0.95)
            pegel[max(0, int((a - 0.3) * SR)):int(a * SR) + len(tl["ton"])] = 0.12
        if sz["art"] == "pointe":                                       # Stille + Grillen nach der Pointe
            ende = sz["start"] + sz["teile"][0]["start"] + len(sz["teile"][0]["ton"]) / SR
            pegel[int(ende * SR):int((sz["start"] + sz["dauer"]) * SR)] = 0.0
            setze(grillen(sz["dauer"] - (ende - sz["start"]) + 0.2), ende)
        if sz["art"] == "winter":
            setze(quietschen(), sz["start"] + 0.5, 0.9)
            setze(plumps(), sz["start"] + 2.4, 1.0)
            tl = sz["teile"][0]
            setze(badumtss(), sz["start"] + tl["start"] + len(tl["ton"]) / SR + 0.15, 1.0)
        if sz["art"] == "abspann":
            pegel[int(sz["start"] * SR):] = 0.55
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", MUSIK, "-f", "s16le", "-ac", "1", "-ar", str(SR),
                          "pipe:1"], capture_output=True, check=True).stdout
    m = np.frombuffer(roh, np.int16).astype(np.float32) / 32768
    m = m / max(1e-6, float(np.sqrt(np.mean(m ** 2)))) * 0.2
    m = np.pad(m, (0, max(0, n - len(m))))[:n]
    k = int(0.15 * SR)
    pegel = np.convolve(pegel, np.ones(k) / k, mode="same")
    aus = np.ones(n, np.float32)
    f = int(1.0 * SR)
    aus[-f:] = np.linspace(1, 0, f)
    mix += m * pegel * aus
    return mix / max(1e-6, np.abs(mix).max()) * 0.9


def main():
    szenen, gesamt = bauen()
    r = random.Random(4)
    blinz = set()
    for k in range(int(gesamt * FPS)):
        if r.random() < 0.015:
            blinz.update(range(k, k + 4))
    wav = os.path.join(tempfile.mkdtemp(), "t.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((tonspur(szenen, gesamt) * 32767).astype(np.int16).tobytes())
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                          "-movflags", "+faststart", ZIEL], stdin=subprocess.PIPE)
    for k in range(int(gesamt * FPS)):
        zeit = k / FPS
        sz = next((s for s in szenen if s["start"] <= zeit < s["start"] + s["dauer"]), szenen[-1])
        rel = zeit - sz["start"]
        if sz["ort"] == "buero":
            f = buero(sz, rel, k, blinz)
        elif sz["ort"] == "winter":
            f = winter(sz, rel, k)
        else:
            f = abspann(rel)
        p.stdin.write(f.tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg-Fehler")
    print(ZIEL, round(gesamt, 1), "s")
    import vollstaendig
    vollstaendig.pruefe(ZIEL, [tl["text"] for s in szenen for tl in s["teile"]], streng=True)


if __name__ == "__main__":
    main()
