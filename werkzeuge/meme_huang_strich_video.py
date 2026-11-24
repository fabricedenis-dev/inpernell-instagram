#!/usr/bin/env python3
"""Animiertes Meme-Video „Jensen nach 11 Tagen zurück“ im Strichmännchen-Meme-Stil (privater Account, Satire).
Gemalte Hintergründe und Spielszene aus der lokalen Bild-KI (assets/memes/huang), Figuren als Vektor
(werkzeuge/strichmann.py): Mund im Takt der Stimme, Blinzeln, Jubel-Arme, Wippen. Stimmen aus der
ElevenLabs-Bibliothek (keine Nachahmung), Sprechblasen Wort für Wort, Meme-Sounds,
Musik „Monkeys Spinning Monkeys“ (Kevin MacLeod, CC BY 4.0).
Aufruf: python werkzeuge/meme_huang_strich_video.py  ->  vorschau/memes/meme_huang_strich.mp4"""
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
import meme_huang_video as mh  # noqa: E402
import storyboard_huang_strich as sb  # noqa: E402
import strichmann as sm  # noqa: E402
import topjob_video as tv  # noqa: E402
from bild import font  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
sb.ORDNER = os.path.join(HIER, "assets", "memes", "huang")
ZIEL = os.path.join(HIER, "vorschau", "memes", "meme_huang_strich.mp4")
CACHE = os.path.join(HIER, "vorschau", "memes", "ton")
MUSIK = os.path.join(HIER, "assets", "musik", "monkeys_spinning_monkeys_kevin_macleod.mp3")
STIMME = {"chef": "IWm8DnJ4NGjFI7QAM5lM", "jensen": "gGjaVIGkCSfKUIBYtNT2"}   # Stephan, Marc (Bibliothek)
CHEF_X, JENSEN_X, FUSS, GR = 290, 790, 1790, 1.2

SZENEN = [
    ("buero", "POV: Jensen nach 11 Tagen Pause zurück bei Nvidia",
     [("chef", "[cheerful] Willkommen zurück! Was hast du gemacht?", 0.7)], 0.4, "jubel"),
    ("buero", None, [("jensen", "[serious] Reflektiert. An mir gearbeitet. Viel nachgedacht.", 0.3)], 0.5, "ernst"),
    ("sofa", "GTA VI · Tag 1", [("jensen", "[whispers] Nur noch eine Mission.", 1.0)], 0.6, "zocken"),
    ("sofa", "GTA VI · Tag 11", [("jensen", "[excited] Ja! Hundert Prozent!", 0.7)], 0.8, "geschafft"),
    ("buero", None, [("chef", "[curious] Und? Hast du was gelernt?", 0.3),
                     ("jensen", "[proud] Ja. Fluchtwagen fahren ist auch Führungserfahrung.", 0.4)], 0.6, "stolz"),
    ("buero", None, [("chef", "[stunned] Okay. Du bist eingestellt.", 0.7)], 1.8, "ende"),
]

_CACHE = {}


def ebene(x, y, **kw):
    """Figur als transparente Vollbild-Ebene, zwischengespeichert (gleiche Pose = gleiches Bild)."""
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


BUERO = sb.hg("bg_buero").convert("RGBA")


def wohnzimmer_hg():
    im = Image.open(os.path.join(sb.ORDNER, "bg_wohnzimmer.png")).convert("RGB")
    hh = int(im.height * 0.62)
    bw = int(hh * 9 / 16)
    img = im.crop(((im.width - bw) // 2, int(im.height * 0.03), (im.width + bw) // 2, hh)).resize((W, H), Image.LANCZOS)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([40, 470, 1040, 1100], radius=60, fill=(255, 120, 200, 60))
    img.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([88, 520, 992, 1050], radius=16, fill=(16, 16, 20), outline=(5, 5, 8), width=8)
    d.rectangle([500, 1050, 580, 1090], fill=(30, 30, 36))
    d.rounded_rectangle([380, 1086, 700, 1104], radius=8, fill=(30, 30, 36))
    return img.convert("RGBA")


WOHN = wohnzimmer_hg()
SOFA = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(SOFA)
_d.rounded_rectangle([60, 1560, 1020, 1990], radius=70, fill=(170, 40, 60), outline=(20, 20, 24), width=8)
_d.rounded_rectangle([20, 1500, 170, 1990], radius=60, fill=(150, 34, 52), outline=(20, 20, 24), width=8)
_d.rounded_rectangle([910, 1500, 1060, 1990], radius=60, fill=(150, 34, 52), outline=(20, 20, 24), width=8)
SPIEL = {1: sb.spielbild("spiel_1", "Auftrag: Entkomme der Polizei"),
         2: sb.spielbild("spiel_2", "Letzter Auftrag"),
         3: sb.spielbild("spiel_2", "Letzter Auftrag", erfuellt=True)}


def bauen():
    szenen, t = [], 0.0
    for ort, oben, saetze, nach, art in SZENEN:
        teile, rel = [], 0.0
        for wer, text, vor in saetze:
            tv.STIMME = STIMME[wer]
            ton, woerter, zeiten, _q = tv.sprich_abschnitt(text, CACHE)
            rel += vor
            teile.append(dict(wer=wer, text=tv.anzeige_text(text), ton=ton, zeiten=zeiten, start=rel))
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
    n = sum(1 for a, _ in tl["zeiten"] if a <= r + 0.05)
    return " ".join(tl["text"].split()[:n]) if n > 0 else ""


def buero(sz, rel, k, blinz):
    img = BUERO.copy()
    art = sz["art"]
    wer, offen = spricht(sz, rel)
    wip = int(5 * math.sin(k * 0.22))
    # Chef
    if art == "ende" and rel > 0.6:
        c = dict(augen="gross", mund="schock", brauen=(-14, 22))
    elif art == "jubel":
        c = dict(mund="laecheln", brauen=(-6, 6), arm_l=(40, 60), arm_r=(40, 60))
    elif art == "stolz":
        c = dict(mund="skeptisch", brauen=(10, 4), blick=(1, 0))
    else:
        c = dict(mund="neutral", brauen=(-8, 10), blick=(1, 0))
    if wer == "chef" and offen:
        c["mund"] = "offen"
    if k in blinz and c.get("augen") != "gross":
        c["augen"] = "zu"
    setze_ebene(img, ebene(CHEF_X, FUSS, groesse=GR, **sm.CHEF, **c), dy=wip)
    # Jensen
    if art == "jubel":
        hoch = (k // 6) % 2 == 0
        j = dict(mund="lachen", brauen=(-10, 10), arm_l=(140, 160) if hoch else (150, 178),
                 arm_r=(150, 178) if hoch else (140, 160), faust=(True, True))
    elif art == "ernst":
        j = dict(augen="zu", mund="laecheln", brauen=(-12, 4), arm_l=(10, -40), arm_r=(10, -40))
    elif art == "stolz":
        j = dict(augen="genervt", mund="grinsen", brauen=(-6, 0), arm_r=(60, 150), faust=(False, True))
    else:
        j = dict(augen="genervt", mund="grinsen", brauen=(-6, 0))
    if wer == "jensen" and offen:
        j["mund"] = "offen"
    if k in blinz and j.get("augen") != "zu":
        j["augen"] = "zu"
    setze_ebene(img, ebene(JENSEN_X, FUSS, groesse=GR, spiegeln=True, **sm.JENSEN, **j), dy=-wip)
    img = img.convert("RGB")
    if art == "ende" and rel > 0.7:                                    # Zoom auf Jensens Grinsen
        z = 1 + 0.45 * min(1, (rel - 0.7) / 0.5)
        cw, ch = int(W / z), int(H / z)
        x0, y0 = min(W - cw, int(JENSEN_X - cw / 2)), max(0, int(1000 - ch / 2))
        img = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
    y = fc.text_oben(img, sz["oben"]) + 30 if sz["oben"] else 200
    sichtbar = [tl for tl in sz["teile"] if rel >= tl["start"] - 0.05]
    for tl in sichtbar:
        txt = worte(tl, rel)
        if tl["wer"] == "chef":
            if txt:
                fc.blase(img, txt, 40, y, w=600)
            y += 170 if len(tl["text"]) > 22 else 130
        elif txt:
            fc.blase(img, txt, 420, y, w=620, rechts=True)
    sb.satire(img)
    return img


def sofa(sz, rel, k, blinz):
    img = WOHN.copy()
    art = sz["art"]
    if art == "zocken":
        sp = SPIEL[1]
    else:
        sp = SPIEL[3] if rel > 0.5 else SPIEL[2]
    z = 1 + 0.03 * math.sin(k * 0.3)                                     # Spiel bewegt sich
    sw, sh = sp.size
    cw, ch = int(sw / z), int(sh / z)
    bild = sp.crop(((sw - cw) // 2, (sh - ch) // 2, (sw + cw) // 2, (sh + ch) // 2)).resize((sw, sh))
    if art == "zocken":
        bild = bild.transform(bild.size, Image.AFFINE, (1, 0, random.Random(k).randint(-6, 6), 0, 1, 0))
    img.paste(bild, (110, 542))
    if art == "zocken":
        j = dict(arm_l=(30, 10), arm_r=(30, 10), halt="controller")
        dx = random.Random(k * 7).randint(-3, 3)
        dy = 0
    else:
        hoch = rel > 0.5 and (k // 5) % 2 == 0
        j = dict(arm_l=(140, 160) if hoch else (150, 178), arm_r=(150, 178) if hoch else (140, 160), faust=(True, True))
        dx, dy = 0, -abs(int(14 * math.sin(k * 0.6))) if rel > 0.5 else 0
    setze_ebene(img, ebene(540, 1920, groesse=0.9, bein="sitzen", ruecken=True, **sb.HOODIE, **j), dx, dy)
    img.alpha_composite(SOFA)
    img = img.convert("RGB")
    fc.text_oben(img, "Was er wirklich gemacht hat:")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([340, 400, 740, 470], radius=14, fill=(20, 22, 34), outline=(255, 200, 60), width=4)
    d.text((540, 435), sz["oben"], font=font("h800", 40), fill=(255, 200, 60), anchor="mm")
    for tl in sz["teile"]:
        txt = worte(tl, rel)
        if txt:
            fc.blase(img, txt, 260, 1150, w=600, rechts=True)
    sb.satire(img)
    return img


def tonspur(szenen, gesamt):
    n = int(gesamt * SR)
    mix = np.zeros(n, np.float32)

    def setze(sig, sek, g=1.0):
        i = int(sek * SR)
        sig = sig[: max(0, n - i)]
        mix[i:i + len(sig)] += sig * g

    pegel = np.full(n, 0.5, np.float32)
    for i, sz in enumerate(szenen):
        for tl in sz["teile"]:
            a = sz["start"] + tl["start"]
            setze(tl["ton"], a, 0.95)
            pegel[max(0, int((a - 0.3) * SR)):int(a * SR) + len(tl["ton"])] = 0.12
        if i == 2:                                                        # Schnitt zur Wahrheit
            setze(mh.kratzer(), sz["start"], 0.9)
            pegel[int(sz["start"] * SR):int((sz["start"] + 0.6) * SR)] = 0.0
            t = np.arange(int(0.05 * SR)) / SR
            klick = (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90) * 0.25).astype(np.float32)
            for k in np.arange(0.5, sz["dauer"] - 0.1, 0.16):             # Controller-Klicks
                setze(klick, sz["start"] + k)
        if i == 3:
            setze(mh.ding(), sz["start"] + 0.5, 1.2)
        if i == 5:
            setze(mh.boom(), sz["start"] + 0.7, 1.0)
            pegel[int((sz["start"] + 0.6) * SR):] = 0.0
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", MUSIK, "-f", "s16le", "-ac", "1", "-ar", str(SR),
                          "pipe:1"], capture_output=True, check=True).stdout
    m = np.frombuffer(roh, np.int16).astype(np.float32) / 32768
    m = m / max(1e-6, float(np.sqrt(np.mean(m ** 2)))) * 0.2
    m = np.pad(m, (0, max(0, n - len(m))))[:n]
    k = int(0.15 * SR)
    pegel = np.convolve(pegel, np.ones(k) / k, mode="same")
    mix += m * pegel
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
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                          "-movflags", "+faststart", ZIEL], stdin=subprocess.PIPE)
    for k in range(int(gesamt * FPS)):
        zeit = k / FPS
        sz = next((s for s in szenen if s["start"] <= zeit < s["start"] + s["dauer"]), szenen[-1])
        f = (buero if sz["ort"] == "buero" else sofa)(sz, zeit - sz["start"], k, blinz)
        p.stdin.write(f.tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg-Fehler")
    print(ZIEL, round(gesamt, 1), "s")
    import vollstaendig
    vollstaendig.pruefe(ZIEL, [tl["text"] for s in szenen for tl in s["teile"]], streng=True)


if __name__ == "__main__":
    main()
