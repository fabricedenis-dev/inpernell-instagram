"""Zeichentrick im Comic-Stil (Version 2): doppelt aufgelöst gezeichnet und herunterskaliert (glatte Linien),
Cel-Shading, ausdrucksstarke Augen/Brauen, echte Arme mit Ärmeln und Händen, ausgestaltetes Büro, Comic-Effekte.
Gleiche Schnittstelle wie zeichentrick.py: hintergrund(), figur(), titel(), abspann(); dazu effekte()."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw

from bild import KNOPFTEXT, NAVY, ORANGE, WEISS, font, wrap

W, H = 1080, 1920
K = 2                                   # Zeichen-Auflösung (Supersampling)
HIER = os.path.dirname(os.path.abspath(__file__))
STRICH = (22, 20, 28)
HAUT, HAUT_S = (240, 196, 150), (214, 160, 118)
_CACHE = {}


def _p(*xy):
    return [(x * K, y * K) for x, y in zip(xy[0::2], xy[1::2])] if len(xy) > 2 else (xy[0] * K, xy[1] * K)


def _box(x0, y0, x1, y1):
    return [x0 * K, y0 * K, x1 * K, y1 * K]


def _linie(d, punkte, farbe, breite, rand=True):
    """Dicke Linie mit Comic-Kontur und runden Gelenken (Arme, Beine)."""
    pts = [(x * K, y * K) for x, y in punkte]
    if rand:
        d.line(pts, fill=STRICH, width=int((breite + 10) * K), joint="curve")
        for x, y in pts:
            r = (breite + 10) * K / 2
            d.ellipse([x - r, y - r, x + r, y + r], fill=STRICH)
    d.line(pts, fill=farbe, width=int(breite * K), joint="curve")
    for x, y in pts:
        r = breite * K / 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=farbe)


def _verlauf(w, h, oben, unten):
    y = np.linspace(0, 1, h)[:, None, None]
    a = np.array(oben, float)[None, None, :] * (1 - y) + np.array(unten, float)[None, None, :] * y
    return Image.fromarray(np.repeat(a, w, axis=1).astype(np.uint8))


# ---------------------------------------------------------------- Raum

def hintergrund(stuhl=None):
    """Büro im Comic-Stil (doppelt aufgelöst). stuhl: "buero" (Schreibtisch + Bürostuhl) oder "hocker"."""
    if stuhl in _CACHE:
        return _CACHE[stuhl].copy()
    img = _verlauf(W * K, H * K, (238, 229, 216), (214, 203, 190))
    d = ImageDraw.Draw(img)
    # Comic-Rasterpunkte oben an der Wand
    for y in range(0, 1100, 26):
        for x in range((y // 26 % 2) * 13, W, 26):
            r = 2.6 * (1 - y / 1100)
            if r > 0.4:
                d.ellipse(_box(x - r, y - r, x + r, y + r), fill=(226, 214, 200))
    # Fenster mit Skyline
    fx0, fy0, fx1, fy1 = 70, 520, 470, 990
    img.paste(_verlauf((fx1 - fx0) * K, (fy1 - fy0) * K, (126, 186, 236), (252, 214, 176)), (fx0 * K, fy0 * K))
    rnd = np.random.default_rng(4)
    x = fx0
    while x < fx1 - 30:
        bw, bh = rnd.integers(34, 70), rnd.integers(90, 300)
        bw = min(bw, fx1 - x)
        d.rectangle(_box(x, fy1 - bh, x + bw, fy1), fill=(98, 112, 150))
        for wy in range(int(fy1 - bh + 14), fy1 - 10, 26):
            for wx in range(int(x + 8), int(x + bw - 8), 16):
                if rnd.random() < 0.45:
                    d.rectangle(_box(wx, wy, wx + 6, wy + 10), fill=(255, 232, 160))
        x += bw + rnd.integers(2, 10)
    d.rectangle(_box(fx0, fy0, fx1, fy1), outline=STRICH, width=10 * K)
    d.line(_p((fx0 + fx1) / 2, fy0, (fx0 + fx1) / 2, fy1), fill=STRICH, width=8 * K)
    d.line(_p(fx0, (fy0 + fy1) / 2, fx1, (fy0 + fy1) / 2), fill=STRICH, width=8 * K)
    d.rectangle(_box(fx0 - 16, fy1, fx1 + 16, fy1 + 22), fill=(250, 246, 240), outline=STRICH, width=5 * K)
    # Poster "TEAMGEIST" (Büro-Ironie)
    px0, py0, px1, py1 = 700, 540, 980, 860
    d.rectangle(_box(px0 + 10, py0 + 12, px1 + 10, py1 + 12), fill=(190, 178, 164))
    d.rectangle(_box(px0, py0, px1, py1), fill=NAVY, outline=STRICH, width=6 * K)
    d.polygon(_p(px0 + 30, py1 - 110, px0 + 120, py0 + 90, px0 + 170, py0 + 150, px0 + 210, py0 + 110, px1 - 30, py1 - 110),
              fill=(70, 110, 170))
    d.polygon(_p(px0 + 92, py0 + 130, px0 + 120, py0 + 90, px0 + 146, py0 + 126), fill=WEISS)
    d.text(_p((px0 + px1) / 2, py1 - 70), "TEAMGEIST", font=font("h800", 34 * K), fill=ORANGE, anchor="mm")
    # Boden mit Dielen
    boden = 1250
    img.paste(_verlauf(W * K, (H - boden) * K, (186, 150, 116), (150, 116, 88)), (0, boden * K))
    d.line(_p(0, boden, W, boden), fill=STRICH, width=6 * K)
    for i in range(-8, 9):
        d.line(_p(W / 2 + i * 70, boden, W / 2 + i * 260, H), fill=(140, 106, 80), width=3 * K)
    # Pflanze
    d.polygon(_p(900, 1180, 1030, 1180, 1012, 1330, 918, 1330), fill=(200, 96, 70), outline=STRICH)
    d.line(_p(900, 1180, 1030, 1180, 1012, 1330, 918, 1330, 900, 1180), fill=STRICH, width=6 * K)
    for w_, l_ in ((-60, 190), (-25, 230), (10, 250), (45, 220), (80, 170), (-90, 140), (110, 130)):
        a = math.radians(w_ - 90)
        bx, by = 965, 1180
        ex, ey = bx + math.cos(a) * l_, by + math.sin(a) * l_
        nx, ny = -math.sin(a) * 26, math.cos(a) * 26
        mx, my = (bx + ex) / 2, (by + ey) / 2
        d.polygon(_p(bx, by, mx + nx, my + ny, ex, ey, mx - nx, my - ny), fill=(64, 150, 92), outline=STRICH)
        d.line(_p(bx, by, ex, ey), fill=(44, 110, 66), width=3 * K)
    if stuhl == "buero":
        # Bürostuhl (Lehne hinter der Figur)
        d.rounded_rectangle(_box(560, 980, 860, 1360), radius=70 * K, fill=(52, 56, 66), outline=STRICH, width=8 * K)
        d.rounded_rectangle(_box(590, 1010, 690, 1320), radius=50 * K, fill=(68, 72, 84))
        d.rectangle(_box(696, 1360, 724, 1490), fill=(60, 62, 70), outline=STRICH, width=5 * K)
        d.line(_p(600, 1500, 820, 1500), fill=STRICH, width=18 * K)
        for x in (600, 710, 820):
            d.ellipse(_box(x - 20, 1494, x + 20, 1534), fill=(40, 40, 46), outline=STRICH, width=4 * K)
    if stuhl == "hocker":
        d.ellipse(_box(380, 1395, 700, 1450), fill=(110, 124, 120), outline=STRICH, width=6 * K)
        d.rectangle(_box(526, 1440, 554, 1560), fill=(90, 100, 96), outline=STRICH, width=5 * K)
        d.ellipse(_box(430, 1545, 650, 1590), fill=(90, 100, 96), outline=STRICH, width=5 * K)
    _CACHE[stuhl] = img
    return img.copy()


# ---------------------------------------------------------------- Figuren

def _kopf(img, cx, cy, r, art, augen, mund, brauen):
    d = ImageDraw.Draw(img)
    # Kopfform mit Cel-Schatten (rechte Seite)
    maske = Image.new("L", img.size)
    ImageDraw.Draw(maske).ellipse(_box(cx - r, cy - r, cx + r, cy + r), fill=255)
    schatten = Image.new("L", img.size)
    ImageDraw.Draw(schatten).ellipse(_box(cx - r - 28, cy - r - 10, cx + r - 30, cy + r - 6), fill=255)
    d.ellipse(_box(cx - r, cy - r, cx + r, cy + r), fill=HAUT_S)
    img.paste(Image.new("RGB", img.size, HAUT), (0, 0), Image.fromarray(np.minimum(np.array(maske), np.array(schatten))))
    d.ellipse(_box(cx - r, cy - r, cx + r, cy + r), outline=STRICH, width=7 * K)
    # Ohren
    for s in (-1, 1):
        ox = cx + s * (r - 4)
        d.ellipse(_box(ox - 18, cy - 2, ox + 18, cy + 40), fill=HAUT if s < 0 else HAUT_S, outline=STRICH, width=5 * K)
    if art == "genz":
        braun, licht = (92, 60, 40), (140, 98, 66)
        d.chord(_box(cx - r - 12, cy - r - 24, cx + r + 12, cy + r * 0.45), 180, 360, fill=braun, outline=STRICH, width=6 * K)
        for s in (-1, 1):
            d.polygon(_p(cx + s * 6, cy - r + 4, cx + s * (r + 12), cy - r * 0.05, cx + s * (r * 0.78), cy - r * 0.62),
                      fill=braun, outline=STRICH)
        for i in range(4):
            x = cx - r * 0.6 + i * r * 0.38
            d.arc(_box(x - 30, cy - r - 10, x + 30, cy - r * 0.4), 200, 300, fill=licht, width=5 * K)
        d.line(_p(cx, cy - r - 18, cx, cy - r * 0.55), fill=(60, 38, 24), width=4 * K)
        d.ellipse(_box(cx - r - 20, cy + 8, cx - r + 4, cy + 34), fill=WEISS, outline=STRICH, width=4 * K)     # AirPod
    else:
        grau = (168, 164, 158)
        for s in (-1, 1):        # schmaler Haarkranz über den Ohren, hinter der Brille
            x0 = cx + s * r * 0.98
            d.pieslice(_box(x0 - 30, cy - r * 0.42, x0 + 30, cy + r * 0.12), 90 if s < 0 else 270, 270 if s < 0 else 90,
                       fill=grau, outline=STRICH, width=4 * K)
        d.arc(_box(cx - r * 0.55, cy - r * 0.88, cx - r * 0.05, cy - r * 0.45), 200, 320, fill=(255, 236, 214), width=9 * K)
    # Augen
    ey, iris = cy - r * 0.04, (96, 70, 52) if art == "genz" else (86, 120, 150)
    for s in (-1, 1):
        ex, er = cx + s * r * 0.36, r * 0.26
        if augen == "zu":
            d.arc(_box(ex - er, ey - er * 0.4, ex + er, ey + er * 0.9), 15, 165, fill=STRICH, width=6 * K)
            continue
        groesse = 1.15 if augen == "gross" else 1.0
        d.ellipse(_box(ex - er * groesse, ey - er * groesse, ex + er * groesse, ey + er * groesse), fill=WEISS,
                  outline=STRICH, width=5 * K)
        py = ey - er * 0.55 if augen == "genervt" else ey + er * 0.05
        pr = er * (0.42 if augen == "gross" else 0.55)
        d.ellipse(_box(ex - pr, py - pr, ex + pr, py + pr), fill=iris)
        d.ellipse(_box(ex - pr * 0.5, py - pr * 0.5, ex + pr * 0.5, py + pr * 0.5), fill=STRICH)
        d.ellipse(_box(ex + pr * 0.15, py - pr * 0.6, ex + pr * 0.5, py - pr * 0.25), fill=WEISS)
        if augen == "muede":     # schweres Oberlid
            d.chord(_box(ex - er - 2, ey - er - 2, ex + er + 2, ey + er + 2), 180, 360, fill=HAUT_S, outline=STRICH, width=5 * K)
        d.arc(_box(ex - er, ey + er * 0.35, ex + er, ey + er * 1.45), 25, 155, fill=(176, 120, 96), width=4 * K)    # Augenringe
        if art != "genz":       # Brille mit Glanz
            d.ellipse(_box(ex - er - 12, ey - er - 12, ex + er + 12, ey + er + 12), outline=STRICH, width=7 * K)
            d.line(_p(ex - er * 0.6, ey - er * 0.7, ex - er * 0.1, ey - er * 0.95), fill=WEISS, width=5 * K)
    if art != "genz":
        d.line(_p(cx - r * 0.36 + r * 0.26 + 12, ey, cx + r * 0.36 - r * 0.26 - 12, ey), fill=STRICH, width=7 * K)
    # Augenbrauen
    for s in (-1, 1):
        ex = cx + s * r * 0.36
        y0 = ey - r * 0.42
        hub = {"hoch": -24, "skeptisch": -22 if s > 0 else 2, "gelangweilt": 8, "sorge": -10}.get(brauen, 0)
        neig = {"sorge": 10 * s, "boese": -12 * s, "gelangweilt": 0}.get(brauen, 0)
        farbe = (70, 46, 32) if art == "genz" else (120, 116, 110)
        d.line(_p(ex - 26, y0 + hub + neig, ex + 26, y0 + hub - neig), fill=farbe, width=9 * K)
    # Nase
    d.arc(_box(cx - 12, cy + r * 0.12, cx + 14, cy + r * 0.36), 300, 100, fill=STRICH, width=4 * K)
    my = cy + r * 0.52
    if art != "genz":         # Schnauzer
        d.chord(_box(cx - 50, my - 30, cx + 50, my + 12), 180, 360, fill=(120, 88, 66), outline=STRICH, width=4 * K)
    if mund == "offen":
        d.chord(_box(cx - 24, my - 12, cx + 24, my + 30), 0, 180, fill=(110, 34, 44), outline=STRICH, width=4 * K)
        d.chord(_box(cx - 14, my + 8, cx + 14, my + 28), 180, 360, fill=(230, 120, 130))
        d.rectangle(_box(cx - 18, my - 10, cx + 18, my - 2), fill=WEISS)
    elif mund == "grinsen":
        d.chord(_box(cx - 40, my - 22, cx + 40, my + 30), 0, 180, fill=WEISS, outline=STRICH, width=5 * K)
        d.line(_p(cx - 34, my + 4, cx + 34, my + 4), fill=(200, 196, 196), width=3 * K)
    elif mund == "schief":
        d.line(_p(cx - 26, my + 8, cx + 24, my - 6), fill=STRICH, width=6 * K)
        d.arc(_box(cx + 14, my - 14, cx + 34, my + 4), 270, 30, fill=STRICH, width=5 * K)
    else:
        d.arc(_box(cx - 24, my - 6, cx + 24, my + 14), 200, 340, fill=STRICH, width=6 * K)


def tisch_vorn(img, cx, oben=1290):
    """Schreibtisch vor dem Personaler: Platte (Draufsicht leicht schräg) + Front bis zum Boden, Laptop, Kaffeetasse."""
    d = ImageDraw.Draw(img)
    x0, x1 = cx - 380, min(W + 40, cx + 400)
    d.polygon(_p(x0 + 30, oben, x1 - 30, oben, x1, oben + 50, x0, oben + 50), fill=(204, 158, 110))
    d.line(_p(x0 + 30, oben, x1 - 30, oben, x1, oben + 50, x0, oben + 50, x0 + 30, oben), fill=STRICH, width=7 * K)
    d.rectangle(_box(x0, oben + 50, x1, oben + 84), fill=(170, 126, 86), outline=STRICH, width=6 * K)
    d.rectangle(_box(x0 + 20, oben + 84, x1 - 20, 1600), fill=(186, 140, 96), outline=STRICH, width=7 * K)
    d.rectangle(_box(x0 + 20, oben + 84, x0 + 70, 1600), fill=(160, 118, 80))
    d.line(_p(x0 + 60, oben + 250, x1 - 60, oben + 250), fill=(156, 114, 78), width=5 * K)       # Schubladen-Fuge
    d.rounded_rectangle(_box(cx - 40, oben + 160, cx + 40, oben + 180), radius=8 * K, fill=(120, 90, 60))
    # Laptop (von hinten) links, Tasse rechts
    lx = cx - 330
    d.polygon(_p(lx, oben + 26, lx + 190, oben + 26, lx + 176, oben - 120, lx + 14, oben - 120), fill=(176, 182, 196))
    d.line(_p(lx, oben + 26, lx + 190, oben + 26, lx + 176, oben - 120, lx + 14, oben - 120, lx, oben + 26), fill=STRICH,
           width=6 * K)
    d.ellipse(_box(lx + 82, oben - 64, lx + 108, oben - 38), fill=WEISS)
    tx = cx + 250
    d.rounded_rectangle(_box(tx, oben - 40, tx + 54, oben + 24), radius=8 * K, fill=WEISS, outline=STRICH, width=5 * K)
    d.text(_p(tx + 27, oben - 8), "BOSS", font=font("h800", 14 * K), fill=ORANGE, anchor="mm")
    d.arc(_box(tx + 42, oben - 28, tx + 76, oben + 6), 270, 90, fill=STRICH, width=5 * K)
    for sx in (tx + 16, tx + 38):
        d.arc(_box(sx - 8, oben - 100, sx + 8, oben - 56), 100, 260, fill=(170, 160, 150), width=3 * K)


def _hand(d, x, y, links=True):
    d.ellipse(_box(x - 26, y - 24, x + 26, y + 26), fill=HAUT, outline=STRICH, width=5 * K)
    tx = x + (20 if links else -20)
    d.ellipse(_box(tx - 12, y - 22, tx + 12, y + 2), fill=HAUT, outline=STRICH, width=4 * K)


def figur(img, cx, fuss, art, augen="normal", mund="neutral", arm="unten", sitzt=True, kopf_dy=0, brauen=None):
    """Zeichnet auf das doppelt aufgelöste Bild aus hintergrund(). Gibt img zurück."""
    d = ImageDraw.Draw(img, "RGBA")
    r = 122
    huefte = fuss - (175 if sitzt else 330)
    schulter = huefte - 270
    kopf_y = schulter - r + 14 + kopf_dy
    genz = art == "genz"
    stoff, stoff_s = ((174, 156, 216), (140, 122, 190)) if genz else ((112, 118, 128), (84, 90, 100))
    hose = (62, 86, 140) if genz else (64, 66, 76)
    brauen = brauen or {"muede": "gelangweilt", "gross": "hoch", "genervt": "skeptisch"}.get(augen, "neutral")
    # Bodenschatten
    d.ellipse(_box(cx - 170, fuss - 18, cx + 190, fuss + 26), fill=(60, 40, 30, 70))
    # Beine (sitzend, Knie leicht auseinander)
    for s in (-1, 1):
        _linie(d, [(cx + s * 40, huefte), (cx + s * 70, huefte + 40), (cx + s * 74, fuss - 20)], hose, 46)
        sx = cx + s * 74
        d.rounded_rectangle(_box(sx - 40, fuss - 34, sx + 50, fuss + 6), radius=16 * K,
                            fill=WEISS if genz else (40, 32, 30), outline=STRICH, width=5 * K)
        if genz:
            d.line(_p(sx - 30, fuss - 6, sx + 40, fuss - 6), fill=ORANGE, width=6 * K)
    # Rumpf
    if genz:   # weiter Hoodie
        d.polygon(_p(cx - 92, schulter, cx + 92, schulter, cx + 118, huefte + 10, cx - 118, huefte + 10), fill=stoff)
        d.polygon(_p(cx + 20, schulter, cx + 92, schulter, cx + 118, huefte + 10, cx + 40, huefte + 10), fill=stoff_s)
        d.line(_p(cx - 92, schulter, cx - 118, huefte + 10, cx + 118, huefte + 10, cx + 92, schulter), fill=STRICH, width=7 * K)
        d.chord(_box(cx - 80, schulter - 40, cx + 80, schulter + 50), 180, 360, fill=stoff_s, outline=STRICH, width=6 * K)  # Kapuze
        d.rounded_rectangle(_box(cx - 66, huefte - 120, cx + 66, huefte - 44), radius=18 * K, outline=STRICH, width=5 * K)
        for s in (-1, 1):
            d.line(_p(cx + s * 22, schulter + 10, cx + s * 26, schulter + 100), fill=WEISS, width=6 * K)
            d.ellipse(_box(cx + s * 26 - 7, schulter + 96, cx + s * 26 + 7, schulter + 110), fill=WEISS)
        d.arc(_box(cx - 80, huefte - 30, cx - 20, huefte + 20), 200, 330, fill=stoff_s, width=4 * K)
    else:      # Anzug
        d.polygon(_p(cx - 86, schulter, cx + 86, schulter, cx + 102, huefte + 10, cx - 102, huefte + 10), fill=stoff)
        d.polygon(_p(cx + 16, schulter, cx + 86, schulter, cx + 102, huefte + 10, cx + 30, huefte + 10), fill=stoff_s)
        d.polygon(_p(cx - 34, schulter, cx + 34, schulter, cx, schulter + 120), fill=WEISS)
        d.polygon(_p(cx - 12, schulter + 18, cx + 12, schulter + 18, cx + 16, schulter + 150, cx, schulter + 172,
                     cx - 16, schulter + 150), fill=(184, 44, 54), outline=STRICH)
        for s in (-1, 1):
            d.line(_p(cx + s * 34, schulter, cx + s * 8, schulter + 150), fill=STRICH, width=5 * K)
        d.line(_p(cx - 86, schulter, cx - 102, huefte + 10, cx + 102, huefte + 10, cx + 86, schulter), fill=STRICH, width=7 * K)
    # Hals
    d.rectangle(_box(cx - 26, schulter - 30, cx + 26, schulter + 6), fill=HAUT_S)
    _kopf(img, cx, kopf_y, r, art, augen, mund, brauen)
    d = ImageDraw.Draw(img, "RGBA")
    # Arme (Ärmel) + Hände
    li, re = (cx - 86, schulter + 30), (cx + 86, schulter + 30)
    if arm == "achselzucken":
        wege = [[li, (cx - 170, schulter + 150), (cx - 230, schulter + 40)], [re, (cx + 170, schulter + 150), (cx + 230, schulter + 40)]]
    elif arm == "handy":
        wege = [[li, (cx - 110, schulter + 170), (cx - 30, schulter + 150)], [re, (cx + 110, schulter + 170), (cx + 30, schulter + 150)]]
    elif arm == "tisch":       # Unterarme liegen auf der Tischplatte
        wege = [[li, (cx - 150, schulter + 120), (cx - 90, 1296)], [re, (cx + 150, schulter + 120), (cx + 90, 1296)]]
    elif arm == "tisch_hoch":  # Hände gefaltet, nach vorn gebeugt (verzweifelt-hoffnungsvoll)
        wege = [[li, (cx - 140, schulter + 110), (cx - 26, schulter + 130)], [re, (cx + 140, schulter + 110), (cx + 26, schulter + 130)]]
    elif arm == "zeigen":
        wege = [[li, (cx - 110, huefte - 30)], [re, (cx + 150, schulter + 20), (cx + 210, schulter - 90)]]
    else:
        wege = [[li, (cx - 120, huefte - 20)], [re, (cx + 120, huefte - 20)]]
    if arm in ("tisch", "tisch_hoch"):
        tisch_vorn(img, cx)
        d = ImageDraw.Draw(img, "RGBA")
    for i, weg in enumerate(wege):
        _linie(d, weg, stoff if i == 0 else stoff_s, 40)
        _hand(d, *weg[-1], links=i == 0)
    if arm == "handy":
        d.rounded_rectangle(_box(cx - 34, schulter + 90, cx + 34, schulter + 176), radius=10 * K, fill=(30, 30, 38),
                            outline=STRICH, width=5 * K)
        d.rectangle(_box(cx - 26, schulter + 98, cx + 26, schulter + 166), fill=(120, 200, 240))
        d.polygon(_p(cx - 26, schulter + 98, cx - 60, kopf_y + 40, cx + 60, kopf_y + 40, cx + 26, schulter + 98),
                  fill=(140, 220, 255, 40))                           # Bildschirm-Licht im Gesicht
    return img


# ---------------------------------------------------------------- Comic-Effekte, Titel, Abspann

def effekte(img, art, cx, kopf_y):
    """art: "speedlines" (Strahlen hinter dem Kopf), "schweiss" (Schweißtropfen), "fragezeichen"."""
    d = ImageDraw.Draw(img, "RGBA")
    if art == "speedlines":
        for i in range(36):
            a = i * math.pi * 2 / 36
            r0, r1 = 220, 900
            d.polygon(_p(cx + math.cos(a) * r0, kopf_y + math.sin(a) * r0,
                         cx + math.cos(a + 0.03) * r1, kopf_y + math.sin(a + 0.03) * r1,
                         cx + math.cos(a - 0.03) * r1, kopf_y + math.sin(a - 0.03) * r1), fill=(255, 255, 255, 120))
    elif art == "schweiss":
        x, y = cx + 120, kopf_y - 70
        d.polygon(_p(x, y - 40, x + 22, y + 6, x - 22, y + 6), fill=(140, 200, 250), outline=STRICH)
        d.ellipse(_box(x - 22, y - 16, x + 22, y + 28), fill=(140, 200, 250), outline=STRICH, width=4 * K)
        d.ellipse(_box(x - 8, y - 6, x + 2, y + 6), fill=WEISS)
    elif art == "fragezeichen":
        d.text(_p(cx + 150, kopf_y - 170), "?", font=font("h800", 120 * K), fill=ORANGE, stroke_width=6 * K,
               stroke_fill=STRICH, anchor="mm")
    return img


def fertig(img):
    """Doppelt aufgelöstes Bild auf Videogröße bringen."""
    return img.resize((W, H), Image.LANCZOS)


def titel(img, text):
    d = ImageDraw.Draw(img)
    f = font("h800", 58)
    zeilen = wrap(d, text.upper(), f, W - 240)
    h = 40 + len(zeilen) * 66
    d.rounded_rectangle([98, 268, W - 82, 268 + h], radius=24, fill=STRICH)
    d.rounded_rectangle([90, 258, W - 90, 258 + h], radius=24, fill=WEISS, outline=STRICH, width=6)
    for i, z in enumerate(zeilen):
        d.text((W // 2, 278 + i * 66), z, font=f, fill=STRICH, anchor="ma")
    return img


def abspann(text, knopf):
    img = fertig(hintergrund())
    schleier = Image.new("RGB", (W, H), NAVY)
    img = Image.blend(img, schleier, 0.82)
    d = ImageDraw.Draw(img)
    for i, z in enumerate(wrap(d, text, font("h800", 70), W - 200)):
        d.text((W // 2, 520 + i * 84), z, font=font("h800", 70), fill=WEISS, anchor="ma", stroke_width=6, stroke_fill=STRICH)
    fk = font("h800", 46)
    kw = d.textlength(knopf, font=fk)
    d.rounded_rectangle([W / 2 - kw / 2 - 50, 900, W / 2 + kw / 2 + 50, 994], radius=47, fill=ORANGE, outline=STRICH, width=6)
    d.text((W // 2, 947), knopf, font=fk, fill=KNOPFTEXT, anchor="mm")
    lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
    lg = lg.resize((480, int(lg.height * 480 / lg.width)), Image.LANCZOS)
    img.paste(lg, ((W - lg.width) // 2, 1060), lg)
    d.text((W // 2, 1060 + lg.height + 30), "DIREKTVERMITTLUNG", font=font("h700", 30), fill=(255, 214, 180), anchor="ma")
    return img


def abspann_ebenen(text, knopf):
    """Abschluss in Ebenen für eine ruhige Animation: Hintergrund (Büro unter Navy-Schleier), Text, Knopf, Logo."""
    hg = Image.blend(fertig(hintergrund()), Image.new("RGB", (W, H), NAVY), 0.82).convert("RGBA")
    leer = lambda: Image.new("RGBA", (W, H), (0, 0, 0, 0))
    t, k, l = leer(), leer(), leer()
    d = ImageDraw.Draw(t)
    zeilen = wrap(d, text, font("h800", 70), W - 200)
    for i, z in enumerate(zeilen):
        d.text((W // 2, 470 + i * 84), z, font=font("h800", 70), fill=WEISS, anchor="ma", stroke_width=6, stroke_fill=STRICH)
    y = 470 + len(zeilen) * 84 + 60
    d = ImageDraw.Draw(k)
    fk = font("h800", 46)
    kw = d.textlength(knopf, font=fk)
    d.rounded_rectangle([W / 2 - kw / 2 - 50, y, W / 2 + kw / 2 + 50, y + 94], radius=47, fill=ORANGE, outline=STRICH, width=6)
    d.text((W // 2, y + 47), knopf, font=fk, fill=KNOPFTEXT, anchor="mm")
    lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
    lg = lg.resize((480, int(lg.height * 480 / lg.width)), Image.LANCZOS)
    ly = y + 170
    l.alpha_composite(lg, ((W - lg.width) // 2, ly))
    ImageDraw.Draw(l).text((W // 2, ly + lg.height + 30), "DIREKTVERMITTLUNG", font=font("h700", 30),
                           fill=(255, 214, 180), anchor="ma")
    return hg, [t, k, l]
