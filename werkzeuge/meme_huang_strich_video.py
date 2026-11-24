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

# (Ort, Oben-Text, Schild, [(Sprecher, Text, Pause davor)], Nachlauf, Art)
SZENEN = [
    ("buero", "POV: Jensen nach 11 Tagen Pause zurück bei Nvidia", None,
     [("chef", "[cheerful] Willkommen zurück! Wie war deine Auszeit?", 0.6),
      ("jensen", "[calm] Sehr erholsam. Ich habe viel reflektiert.", 0.3)], 0.4, "start"),
    ("sofa", "Was er wirklich gemacht hat:", "GTA VI · Tag 1",
     [("jensen", "[whispers] Nur noch eine Mission.", 1.0)], 0.5, "zocken"),
    ("sofa", "Was er wirklich gemacht hat:", "GTA VI · Tag 4 · 4:00 Uhr",
     [("jensen", "[frustrated] Warum ruckelt das?!", 0.9)], 0.6, "ruckeln"),
    ("buero", None, None,
     [("chef", "[curious] Und warum bist du wirklich zurück?", 0.3),
      ("jensen", "[serious] Wir brauchen sofort eine schnellere Grafikkarte.", 0.3)], 0.9, "warum"),
    ("buero", None, None,
     [("chef", "[suspicious] Für die KI-Rechenzentren?", 0.3),
      ("jensen", "[nervous] Ja. Genau. Für die Rechenzentren.", 0.5)], 0.6, "ausrede"),
    ("sofa", "Eine Woche später:", "Neue Grafikkarte",
     [("jensen", "[satisfied] Läuft.", 1.0)], 1.8, "laeuft"),
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
def _ruckeln():
    g = sb.spielbild("spiel_1", "Auftrag: Entkomme der Polizei")
    r, gg, bb = g.split()
    g = Image.merge("RGB", (r.transform(g.size, Image.AFFINE, (1, 0, -10, 0, 1, 0)), gg,
                            bb.transform(g.size, Image.AFFINE, (1, 0, 10, 0, 1, 0))))
    d = ImageDraw.Draw(g)
    for y0 in (90, 210, 330):                                          # verschobene Bildstreifen
        streifen = g.crop((0, y0, 860, y0 + 26))
        g.paste(streifen, (34, y0 + 6))
    d.rounded_rectangle([300, 190, 560, 300], radius=16, fill=(0, 0, 0))
    d.text((430, 245), "FPS: 9", font=font("h800", 56), fill=(255, 70, 70), anchor="mm")
    return g


def _laeuft():
    g = sb.spielbild("spiel_2", "")
    d = ImageDraw.Draw(g)
    d.rounded_rectangle([20, 16, 250, 70], radius=12, fill=(0, 0, 0))
    d.text((135, 43), "240 FPS", font=font("h800", 40), fill=(110, 230, 110), anchor="mm")
    return g


SPIEL = {"zocken": sb.spielbild("spiel_1", "Auftrag: Entkomme der Polizei"), "ruckeln": _ruckeln(), "laeuft": _laeuft()}


def bauen():
    szenen, t = [], 0.0
    for ort, oben, schild, saetze, nach, art in SZENEN:
        teile, rel = [], 0.0
        for wer, text, vor in saetze:
            tv.STIMME = STIMME[wer]
            ton, woerter, zeiten, _q = tv.sprich_abschnitt(text, CACHE)
            rel += vor
            teile.append(dict(wer=wer, text=tv.anzeige_text(text), ton=ton, zeiten=zeiten, start=rel))
            rel += len(ton) / SR
        dauer = rel + nach
        szenen.append(dict(ort=ort, oben=oben, schild=schild, teile=teile, start=t, dauer=dauer, art=art))
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
    c = {"start": dict(mund="laecheln", brauen=(-6, 6), arm_l=(40, 60), arm_r=(40, 60)),
         "warum": dict(mund="skeptisch", brauen=(10, 4), blick=(1, 0)),
         "ausrede": dict(augen="genervt", mund="skeptisch", brauen=(12, 0), blick=(1, 0), arm_r=(60, 150))}[art]
    c = dict(c)
    if wer == "chef" and offen:
        c["mund"] = "offen"
    if k in blinz and c.get("augen") is None:
        c["augen"] = "zu"
    setze_ebene(img, ebene(CHEF_X, FUSS, groesse=GR, **sm.CHEF, **c), dy=wip)
    # Jensen
    j = {"start": dict(augen="zu", mund="laecheln", brauen=(-12, 4), arm_l=(10, -40), arm_r=(10, -40)),
         "warum": dict(mund="neutral", brauen=(16, 0), arm_r=(120, 170), faust=(False, True)),
         "ausrede": dict(mund="zaehne", brauen=(-14, 14), blick=(1, -1), arm_l=(10, -40), arm_r=(10, -40))}[art]
    j = dict(j)
    if art == "ausrede" and rel < sz["teile"][1]["start"]:
        j.update(mund="neutral", blick=(-1, 0), brauen=(-8, 8))
    if wer == "jensen" and offen:
        j["mund"] = "offen"
    if k in blinz and j.get("augen") is None:
        j["augen"] = "zu"
    setze_ebene(img, ebene(JENSEN_X, FUSS, groesse=GR, spiegeln=True, **sm.JENSEN, **j),
                dx=random.Random(k).randint(-2, 2) if art == "ausrede" else 0, dy=-wip)
    if art == "ausrede" and rel >= sz["teile"][1]["start"]:            # Schweißtropfen
        d = ImageDraw.Draw(img)
        yy = 620 + int((rel * 60) % 60)
        d.polygon([(915, yy), (900, yy + 34), (930, yy + 34)], fill=(120, 190, 255), outline=(20, 20, 24))
        d.ellipse([898, yy + 18, 932, yy + 52], fill=(120, 190, 255), outline=(20, 20, 24), width=3)
    img = img.convert("RGB")
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
    sp = SPIEL[art]
    z = 1 + (0.03 * math.sin(k * 0.3) if art != "ruckeln" else 0)
    sw, sh = sp.size
    cw, ch = int(sw / z), int(sh / z)
    bild = sp.crop(((sw - cw) // 2, (sh - ch) // 2, (sw + cw) // 2, (sh + ch) // 2)).resize((sw, sh))
    if art == "zocken":
        bild = bild.transform(bild.size, Image.AFFINE, (1, 0, random.Random(k).randint(-6, 6), 0, 1, 0))
    if art == "ruckeln" and (k // 4) % 3 == 0:                          # Bild hängt und springt
        bild = bild.transform(bild.size, Image.AFFINE, (1, 0, 18, 0, 1, 0))
    img.paste(bild, (110, 542))
    dx = dy = 0
    if art == "zocken":
        j = dict(arm_l=(30, 10), arm_r=(30, 10), halt="controller")
        dx = random.Random(k * 7).randint(-3, 3)
    elif art == "ruckeln":
        auf = rel > sz["teile"][0]["start"] - 0.2
        w = (k // 3) % 2 == 0
        j = dict(arm_l=(115, 150) if w else (125, 165), arm_r=(125, 165) if w else (115, 150), faust=(True, True)) \
            if auf else dict(arm_l=(30, 10), arm_r=(30, 10), halt="controller")
        dx = random.Random(k).randint(-5, 5) if auf else 0
    else:
        hoch = rel > sz["teile"][0]["start"]
        j = dict(arm_l=(30, 10), arm_r=(150, 172) if hoch else (30, 10), faust=(False, True)) if hoch else \
            dict(arm_l=(30, 10), arm_r=(30, 10), halt="controller")
    setze_ebene(img, ebene(540, 1920, groesse=0.9, bein="sitzen", ruecken=True, **sb.HOODIE, **j), dx, dy)
    img.alpha_composite(SOFA)
    img = img.convert("RGB")
    if art == "laeuft" and rel > sz["teile"][0]["start"] + 0.6:        # Zoom auf den flüssigen Bildschirm
        z = 1 + 0.3 * min(1, (rel - sz["teile"][0]["start"] - 0.6) / 0.6)
        cw, ch = int(W / z), int(H / z)
        x0, y0 = (W - cw) // 2, max(0, int(790 - ch / 2))
        img = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
    fc.text_oben(img, sz["oben"])
    d = ImageDraw.Draw(img)
    fs = font("h800", 40)
    bw = int(d.textlength(sz["schild"], font=fs)) + 60
    d.rounded_rectangle([540 - bw // 2, 400, 540 + bw // 2, 470], radius=14, fill=(20, 22, 34),
                        outline=(255, 200, 60), width=4)
    d.text((540, 435), sz["schild"], font=fs, fill=(255, 200, 60), anchor="mm")
    for tl in sz["teile"]:
        txt = worte(tl, rel)
        if txt:
            fc.blase(img, txt, 260, 1330 if art == "laeuft" else 1150, w=600, rechts=True)
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
        art = sz["art"]
        if art == "zocken":                                               # Schnitt zur Wahrheit
            setze(mh.kratzer(), sz["start"], 0.9)
            pegel[int(sz["start"] * SR):int((sz["start"] + 0.6) * SR)] = 0.0
        if art in ("zocken", "ruckeln"):
            t = np.arange(int(0.05 * SR)) / SR
            klick = (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90) * 0.25).astype(np.float32)
            for k in np.arange(0.5, sz["dauer"] - 0.1, 0.16 if art == "zocken" else 0.09):
                setze(klick, sz["start"] + k)
        if art == "ruckeln":                                              # Musik stottert
            for k in np.arange(0.0, sz["dauer"], 0.36):
                pegel[int((sz["start"] + k) * SR):int((sz["start"] + k + 0.18) * SR)] = 0.0
            t = np.arange(int(0.25 * SR)) / SR
            fehler = (np.sign(np.sin(2 * np.pi * 110 * t)) * 0.18 * np.exp(-t * 6)).astype(np.float32)
            setze(fehler, sz["start"] + 0.3)
            setze(fehler, sz["start"] + 0.65)
        if art == "warum":
            ende = sz["start"] + sz["teile"][-1]["start"] + len(sz["teile"][-1]["ton"]) / SR
            setze(mh.boom(), ende + 0.05, 1.0)
        if art == "laeuft":
            setze(mh.ding(), sz["start"] + sz["teile"][0]["start"] + 0.5, 1.2)
            pegel[int((sz["start"] + sz["teile"][0]["start"] + 0.5) * SR):] = 0.6
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
