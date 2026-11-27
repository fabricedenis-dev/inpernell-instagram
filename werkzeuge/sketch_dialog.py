#!/usr/bin/env python3
"""Dialog-Sketch im Stil erfolgreicher Strichmännchen-Meme-Kanäle (Analyse von @cartoonslustig, 26.11.2026):
- feste Hook-Zeile oben (weißer Kasten), die ganze Zeit sichtbar
- schneller Dialog aus kurzen Sätzen (1–2 s), alle 5–8 s eine kleine Pointe, am Ende ein Nachklapp
- Schuss/Gegenschuss: Nahaufnahme der sprechenden Figur, ab und zu beide im Bild
- Untertitel Wort für Wort in kleinen Häppchen (weiß, schwarze Kontur) unten in der Bildmitte, keine Sprechblasen
Hintergrund aus der lokalen Bild-KI, Figuren als Vektor (werkzeuge/strichmann.py), Bibliotheksstimmen.
Aufruf: python werkzeuge/sketch_dialog.py <sketch.json> [ziel.mp4]"""
import json
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
CACHE = os.path.join(HIER, "vorschau", "memes", "ton")
SUB_Y = 1290


class Sketch:
    def __init__(self, pfad):
        self.cfg = json.load(open(pfad, encoding="utf-8"))
        c = self.cfg
        self.figuren = {k: {**getattr(sm, v["typ"]), **v.get("extra", {})} for k, v in c["figuren"].items()}
        self.stimmen = {k: v["stimme"] for k, v in c["figuren"].items()}
        self.links = c["links"]
        bg = Image.open(os.path.join(HIER, c["hintergrund"])).convert("RGB").resize((W, H), Image.LANCZOS)
        self.bg = bg.convert("RGBA")
        z = 1.35                                                # Nahaufnahme: Hintergrund vergrößert, je Seite versetzt
        g = bg.resize((int(W * z), int(H * z)), Image.LANCZOS)
        oy = int((H * z - H) * 0.35)
        self.bg_nah = {"links": g.crop((0, oy, W, oy + H)).convert("RGBA"),
                       "rechts": g.crop((g.width - W, oy, g.width, oy + H)).convert("RGBA")}
        self.bg_figur = {}
        for k, v in c["figuren"].items():
            if v.get("hintergrund"):
                b = Image.open(os.path.join(HIER, v["hintergrund"])).convert("RGB")
                bw = min(b.width, int(b.height * 9 / 16))
                b = b.crop(((b.width - bw) // 2, 0, (b.width + bw) // 2, b.height)).resize((W, H), Image.LANCZOS)
                self.bg_figur[k] = b.convert("RGBA")
        self.cache = {}

    def ebene(self, wer, x, y, gr, **kw):
        spiegel = wer != self.links
        key = (wer, x, y, gr, tuple(sorted((k, str(v)) for k, v in kw.items())))
        if key not in self.cache:
            if len(self.cache) > 400:
                self.cache.clear()
            e = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sm.figur(e, x, y, groesse=gr, spiegeln=spiegel, **self.figuren[wer], **kw)
            self.cache[key] = e
        return self.cache[key]


def setze(img, e, dx=0, dy=0):
    if dx == 0 and dy == 0:
        img.alpha_composite(e)
    else:
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tmp.paste(e, (int(dx), int(dy)), e)
        img.alpha_composite(tmp)


def bauen(sk):
    zeilen, t = [], 0.6
    for z in sk.cfg["dialog"]:
        tv.STIMME = sk.stimmen[z["wer"]]
        ton, woerter, zeiten, _q = tv.sprich_abschnitt(z["sprich"], CACHE)
        t += z.get("vor", 0.12)
        anzeige = z.get("text") or tv.anzeige_text(z["sprich"])
        zeilen.append(dict(z=z, ton=ton, zeiten=zeiten, text=anzeige, start=t, ende=t + len(ton) / SR))
        t += len(ton) / SR + z.get("nach", 0.0)
    return zeilen, t + sk.cfg.get("ausklang", 1.2)


def haeppchen(zl, rel):
    """Aktuelles Untertitel-Häppchen (bis 3 Wörter) passend zur gesprochenen Stelle: Liste (Wort, stumm?)."""
    stumm = set(zl["z"].get("stumm", []))
    w = []
    for i, t in enumerate(zl["text"].split()):          # „B 500“ o. ä. zusammenhalten
        if w and len(w[-1][0]) == 1 and w[-1][0].isupper() and t[:1].isdigit():
            w[-1] = (w[-1][0] + " " + t, w[-1][1])
        else:
            w.append((t, i in stumm))
    n = max(1, len(zl["zeiten"]))
    k = sum(1 for a, _ in zl["zeiten"] if a <= rel + 0.05)
    if k <= 0:
        return []
    i = min(len(w) - 1, int((k - 1) * len(w) / n))
    g = i // 3
    return w[g * 3:g * 3 + 3]


def untertitel(img, teile):
    if not teile:
        return
    d = ImageDraw.Draw(img)
    f = font("h800", 74)
    breiten = [d.textlength(t + " ", font=f) for t, _ in teile]
    x = W // 2 - (sum(breiten) - d.textlength(" ", font=f)) / 2
    for (t, st), bw in zip(teile, breiten):
        d.text((x, SUB_Y), t, font=f, fill=(255, 70, 70) if st else (255, 255, 255), anchor="lm", stroke_width=8,
               stroke_fill=(10, 10, 14))
        x += bw


def stoerung_jetzt(zl, rel):
    for i in zl["z"].get("stumm", []):
        if i < len(zl["zeiten"]):
            a, b = zl["zeiten"][i]
            if a - 0.05 <= rel <= b + 0.1:
                return True
    return False


def stoer_bild(img, k):
    """Funkloch: Farbversatz, verschobene Streifen, Rauschen."""
    r, g, b = img.split()
    img = Image.merge("RGB", (r.transform(img.size, Image.AFFINE, (1, 0, -14, 0, 1, 0)), g,
                              b.transform(img.size, Image.AFFINE, (1, 0, 14, 0, 1, 0))))
    rr = random.Random(k)
    for _ in range(5):
        y0 = rr.randint(200, H - 200)
        h = rr.randint(20, 70)
        img.paste(img.crop((0, y0, W, y0 + h)), (rr.randint(-60, 60), y0))
    d = ImageDraw.Draw(img)
    for _ in range(900):
        x, y = rr.randint(0, W - 1), rr.randint(0, H - 1)
        c = rr.randint(150, 255)
        d.rectangle([x, y, x + 3, y + 3], fill=(c, c, c))
    return img


def sms_karte(img, text, rel):
    """Benachrichtigung wie auf dem Handy, gleitet von oben herein."""
    d = ImageDraw.Draw(img)
    y = int(420 - max(0, 1 - rel / 0.3) * 300)
    d.rounded_rectangle([70, y, W - 70, y + 300], radius=36, fill=(250, 250, 252), outline=(40, 40, 48), width=5)
    d.rounded_rectangle([100, y + 30, 160, y + 90], radius=14, fill=(60, 200, 90))
    d.text((180, y + 42), "Nachrichten · jetzt", font=font("t400", 34), fill=(90, 90, 100))
    from bild import wrap
    for i, z in enumerate(wrap(d, text, font("h800", 46), W - 220)[:3]):
        d.text((110, y + 110 + i * 56), z, font=font("h800", 46), fill=(20, 20, 26))


def mund_offen(zl, rel):
    if not (0 <= rel < len(zl["ton"]) / SR):
        return False
    i = int(rel * SR)
    rms = float(np.sqrt(np.mean(zl["ton"][i:i + SR // FPS] ** 2) + 1e-9))
    return rms > 0.03 and int(rel * FPS) % 4 != 3


def frame(sk, zeilen, zeit, k, blinz, gesamt):
    akt = None
    for zl in zeilen:
        if zeit >= zl["start"] - 0.12:
            akt = zl
    akt = akt or zeilen[0]
    z = akt["z"]
    rel = zeit - akt["start"]
    wer = z["wer"]
    anderer = next(f for f in sk.figuren if f != wer)
    einst = z.get("einst", "nah")
    wip = 4 * math.sin(k * 0.22)
    pose = dict(z.get("pose", {}))
    if mund_offen(akt, rel):
        pose["mund"] = "offen"
    if k in blinz and pose.get("augen") is None:
        pose["augen"] = "zu"
    if einst == "total" or einst == "abgang":
        img = sk.bg.copy()
        gegen = dict(z.get("gegen", {}))
        if k in blinz and gegen.get("augen") is None:
            gegen["augen"] = "zu"
        for f, p in ((wer, pose), (anderer, gegen)):
            x = 290 if f == sk.links else 790
            dx = 0
            if einst == "abgang" and f == wer and rel > len(akt["ton"]) / SR + 0.2:
                r = rel - len(akt["ton"]) / SR - 0.2
                dx = (1 if f != sk.links else -1) * (r ** 1.6) * 900
                p = {**p, "arm_l": (95, 100), "arm_r": (95, 100), "mund": "laecheln", "augen": "zu"}
            setze(img, sk.ebene(f, x, 1790, 1.2, **p), dx=dx, dy=wip if f == wer else -wip)
    else:
        seite = "links" if wer == sk.links else "rechts"
        img = (sk.bg_figur.get(wer) or sk.bg_nah[seite]).copy()
        x = 470 if wer == sk.links else 610
        setze(img, sk.ebene(wer, x, 2330, 1.85, **pose), dy=wip)
    img = img.convert("RGB")
    if z.get("zoom") and rel > 0:
        zz = 1 + 0.22 * min(1, rel / max(0.3, akt["ende"] - akt["start"] + z.get("nach", 0)))
        cw, ch = int(W / zz), int(H / zz)
        img = img.crop(((W - cw) // 2, int(760 - ch / 2) if 760 - ch / 2 > 0 else 0,
                        (W - cw) // 2 + cw, (int(760 - ch / 2) if 760 - ch / 2 > 0 else 0) + ch)).resize((W, H))
    if stoerung_jetzt(akt, rel):
        img = stoer_bild(img, k)
    fc.text_oben(img, sk.cfg["hook"], y=210)
    if z.get("sms") and rel > -z.get("vor", 0.12):
        sms_karte(img, z["sms"], rel + z.get("vor", 0.12))
    untertitel(img, haeppchen(akt, rel))
    img = img.convert("RGBA")
    rd.logo_marke(img)
    return img.convert("RGB")


_AB = {}


def abspann(sk, rel):
    if "b" not in _AB:
        img = Image.new("RGB", (W, H), NAVY)
        d = ImageDraw.Draw(img)
        for y in range(H):
            t = y / H
            d.line([(0, y), (W, y)], fill=tuple(int(NAVY_HELL[i] + (NAVY[i] - NAVY_HELL[i]) * t) for i in range(3)))
        lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
        lg = lg.resize((760, round(lg.height * 760 / lg.width)), Image.LANCZOS)
        img.paste(lg, ((W - 760) // 2, 640), lg)
        d.text((W // 2, 880), "Direktvermittlung", font=font("h800", 64), fill=ORANGE, anchor="ma")
        for i, zz in enumerate(sk.cfg["abspann"]):
            d.text((W // 2, 1060 + i * 66), zz, font=font("t400", 48), fill=(255, 255, 255), anchor="ma")
        _AB["b"] = img
    if rel < 0.3:
        return Image.blend(Image.new("RGB", (W, H), NAVY), _AB["b"], rel / 0.3)
    return _AB["b"]


def tonspur(sk, zeilen, gesamt):
    rng = np.random.default_rng(3)
    from scipy.signal import butter, lfilter
    n = int(gesamt * SR)
    mix = np.zeros(n, np.float32)

    def leg(sig, sek, g=1.0):
        i = int(sek * SR)
        if 0 <= i < n:
            sig = sig[: n - i]
            mix[i:i + len(sig)] += sig * g

    def grillen(dauer):
        out = np.zeros(int(dauer * SR), np.float32)
        t = np.arange(int(0.03 * SR)) / SR
        zirp = np.sin(2 * np.pi * 4600 * t) * np.sin(np.pi * t / 0.03)
        for kk in np.arange(0.05, dauer - 0.2, 0.45):
            for j in range(3):
                i = int((kk + j * 0.055) * SR)
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

    def wusch(d=0.5):
        t = np.arange(int(d * SR)) / SR
        b_, a_ = butter(2, [700 / (SR / 2), 4500 / (SR / 2)], "band")
        return (lfilter(b_, a_, rng.standard_normal(len(t))) * np.sin(np.pi * t / d) ** 2 * 0.6).astype(np.float32)

    def rauschen(d):
        t = np.arange(int(d * SR)) / SR
        b_, a_ = butter(2, [300 / (SR / 2), 6000 / (SR / 2)], "band")
        x = lfilter(b_, a_, rng.standard_normal(len(t))) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 23 * t)))
        return (x * 0.35).astype(np.float32)

    def tuten():
        t = np.arange(int(0.35 * SR)) / SR
        ton_ = (np.sin(2 * np.pi * 425 * t) * 0.3).astype(np.float32)
        out = np.zeros(int(1.6 * SR), np.float32)
        for k0 in (0.0, 0.55, 1.1):
            i = int(k0 * SR)
            out[i:i + len(ton_)] += ton_[: len(out) - i]
        return out

    pegel = np.full(n, 0.32, np.float32)
    for zl in zeilen:
        ton_z = zl["ton"].copy()
        for i in zl["z"].get("stumm", []):
            if i < len(zl["zeiten"]):
                a, b = zl["zeiten"][i]
                ia, ib = int(max(0, a - 0.03) * SR), int(min(len(ton_z) / SR, b + 0.08) * SR)
                ton_z[ia:ib] = rauschen((ib - ia) / SR)[: ib - ia]
        zl["ton_mix"] = ton_z
        leg(ton_z, zl["start"], 0.95)
        if zl["z"].get("tuten_nach"):
            leg(tuten(), zl["ende"] + 0.3, 0.9)
        pegel[max(0, int((zl["start"] - 0.2) * SR)):int(zl["ende"] * SR)] = 0.1
        z = zl["z"]
        if z.get("grillen_nach"):
            pegel[int(zl["ende"] * SR):int((zl["ende"] + z["grillen_nach"]) * SR)] = 0.0
            leg(grillen(z["grillen_nach"]), zl["ende"] + 0.1)
        if z.get("einst") == "abgang":
            leg(wusch(), zl["ende"] + 0.25, 0.9)
        if z.get("badumtss"):
            leg(badumtss(), zl["ende"] + z.get("badumtss", 0.2) + (0.9 if z.get("einst") == "abgang" else 0))
    ab = zeilen[-1]["ende"] + sk.cfg.get("ausklang", 1.2)
    pegel[int(ab * SR):] = 0.5
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", os.path.join(HIER, sk.cfg["musik"]), "-f", "s16le",
                          "-ac", "1", "-ar", str(SR), "pipe:1"], capture_output=True, check=True).stdout
    m = np.frombuffer(roh, np.int16).astype(np.float32) / 32768
    m = m / max(1e-6, float(np.sqrt(np.mean(m ** 2)))) * 0.2
    m = np.tile(m, int(np.ceil(n / max(1, len(m)))) + 1)[:n]
    kk = int(0.15 * SR)
    pegel = np.convolve(pegel, np.ones(kk) / kk, mode="same")
    aus = np.ones(n, np.float32)
    aus[-SR:] = np.linspace(1, 0, SR)
    mix += m * pegel * aus
    return mix / max(1e-6, np.abs(mix).max()) * 0.9


def main(pfad, ziel):
    sk = Sketch(pfad)
    zeilen, ende_dialog = bauen(sk)
    gesamt = ende_dialog + sk.cfg.get("abspann_dauer", 3.0)
    r = random.Random(4)
    blinz = set()
    for kk in range(int(gesamt * FPS)):
        if r.random() < 0.015:
            blinz.update(range(kk, kk + 4))
    wav = os.path.join(tempfile.mkdtemp(), "t.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((tonspur(sk, zeilen, gesamt) * 32767).astype(np.int16).tobytes())
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                          "-movflags", "+faststart", ziel], stdin=subprocess.PIPE)
    for kk in range(int(gesamt * FPS)):
        zeit = kk / FPS
        f = frame(sk, zeilen, zeit, kk, blinz, gesamt) if zeit < ende_dialog else abspann(sk, zeit - ende_dialog)
        p.stdin.write(f.tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg-Fehler")
    print(ziel, round(gesamt, 1), "s")
    import vollstaendig
    # Wörter im Funkloch sind absichtlich nicht zu hören
    texte = [" ".join(w for i, w in enumerate(zl["text"].split()) if i not in set(zl["z"].get("stumm", [])))
             for zl in zeilen]
    vollstaendig.pruefe(ziel, texte, streng=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else
         os.path.join(HIER, "vorschau", "sketche", os.path.basename(sys.argv[1]).replace(".json", ".mp4")))
