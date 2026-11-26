#!/usr/bin/env python3
"""Flacher 2D-Cartoon-Stil (wie verbreitete Meme-Animationen): großer runder Kopf, dicke Konturen, große Augen,
dünne Gliedmaßen, flache Farben. Doppelt aufgelöst gezeichnet, dann verkleinert.
figur(...) liefert RGBA; hintergrund_*(...) liefert RGB 1080 x 1920."""
import math

from PIL import Image, ImageDraw

K = 2
W, H = 1080, 1920
L = (20, 20, 24)                 # Konturfarbe
HAUT = (241, 205, 170)


def _b(x0, y0, x1, y1):
    return [x0 * K, y0 * K, x1 * K, y1 * K]


def _p(*xy):
    return [(x * K, y * K) for x, y in zip(xy[0::2], xy[1::2])]


def _linie(d, pts, farbe=L, breite=14):
    d.line(_p(*pts), fill=farbe, width=breite * K, joint="curve")
    for x, y in zip(pts[0::2], pts[1::2]):
        r = breite * K / 2
        d.ellipse([x * K - r, y * K - r, x * K + r, y * K + r], fill=farbe)


def figur(haar="huang", brille=True, jacke="leder", gesicht="laecheln", pose="steht", arm="unten", w=520, h=1040,
          mund_offen=False, blinzeln=False):
    img = Image.new("RGBA", (w * K, h * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    kopf_r = 150
    ky = 230
    sitzt = pose == "sitzt"
    # --- Körper (Oberteil)
    t0, t1 = ky + kopf_r - 10, ky + kopf_r + (250 if not sitzt else 220)
    farben = {"leder": (34, 34, 38), "anzug": (52, 70, 110), "hoodie": (90, 110, 150), "bluse": (230, 120, 140)}
    oberteil = farben.get(jacke, jacke)
    d.rounded_rectangle(_b(cx - 115, t0, cx + 115, t1), radius=60 * K, fill=oberteil, outline=L, width=7 * K)
    if jacke == "leder":
        d.polygon(_p(cx - 45, t0 + 4, cx + 45, t0 + 4, cx, t0 + 150), fill=(16, 16, 18))          # schwarzes T-Shirt
        for s in (-1, 1):
            d.polygon(_p(cx + s * 45, t0 + 4, cx + s * 100, t0 + 30, cx + s * 30, t0 + 170), fill=(58, 58, 64),
                      outline=L, width=4 * K)                                                   # Revers
            d.line(_p(cx + s * 78, t0 + 70, cx + s * 85, t1 - 30), fill=(110, 110, 120), width=5 * K)   # Glanz
        d.line(_p(cx + 20, t0 + 150, cx + 20, t1 - 10), fill=(170, 170, 180), width=3 * K)           # Reißverschluss
    elif jacke == "anzug":
        d.polygon(_p(cx - 35, t0 + 4, cx + 35, t0 + 4, cx, t0 + 120), fill=(245, 245, 245))
        d.polygon(_p(cx - 10, t0 + 20, cx + 10, t0 + 20, cx + 14, t0 + 120, cx, t0 + 140, cx - 14, t0 + 120),
                  fill=(200, 50, 50))
    elif jacke == "hoodie":
        for s in (-1, 1):
            d.line(_p(cx + s * 25, t0 + 30, cx + s * 30, t0 + 120), fill=(240, 240, 240), width=5 * K)
    # Beine (dünne Striche, Cartoon-Stil)
    if not sitzt:
        for s in (-1, 1):
            _linie(d, (cx + s * 45, t1 - 10, cx + s * 55, h - 70), L, 16)
            d.ellipse(_b(cx + s * 55 - 42, h - 92, cx + s * 55 + 42, h - 52), fill=L)
    else:
        for s in (-1, 1):
            _linie(d, (cx + s * 45, t1 - 10, cx + s * 70, t1 + 90, cx + s * 70, t1 + 230), L, 16)
            d.ellipse(_b(cx + s * 70 - 40, t1 + 215, cx + s * 70 + 40, t1 + 250), fill=L)
    # Arme
    if arm == "unten":
        for s in (-1, 1):
            _linie(d, (cx + s * 110, t0 + 50, cx + s * 150, t0 + 200), L, 14)
            d.ellipse(_b(cx + s * 150 - 22, t0 + 186, cx + s * 150 + 22, t0 + 230), fill=HAUT, outline=L, width=5 * K)
    elif arm == "controller":
        for s in (-1, 1):
            _linie(d, (cx + s * 110, t0 + 50, cx + s * 85, t0 + 170), L, 14)
        d.rounded_rectangle(_b(cx - 95, t0 + 150, cx + 95, t0 + 205), radius=26 * K, fill=(60, 60, 70), outline=L, width=5 * K)
        for bx, col in ((48, (230, 70, 70)), (68, (70, 190, 100))):
            d.ellipse(_b(cx + bx - 8, t0 + 168, cx + bx + 8, t0 + 184), fill=col)
        d.ellipse(_b(cx - 70, t0 + 164, cx - 44, t0 + 190), fill=(30, 30, 34))
    elif arm in ("jubel", "jubel2"):
        hoch = -80 if arm == "jubel" else -20
        weit = 190 if arm == "jubel" else 215
        for s in (-1, 1):
            _linie(d, (cx + s * 110, t0 + 50, cx + s * weit, t0 + hoch), L, 14)
            d.ellipse(_b(cx + s * weit - 24, t0 + hoch - 30, cx + s * weit + 24, t0 + hoch + 18), fill=HAUT, outline=L,
                      width=5 * K)
    elif arm == "zeigen":
        _linie(d, (cx - 110, t0 + 50, cx - 150, t0 + 200), L, 14)
        d.ellipse(_b(cx - 172, t0 + 186, cx - 128, t0 + 230), fill=HAUT, outline=L, width=5 * K)
        _linie(d, (cx + 110, t0 + 50, cx + 230, t0 + 10), L, 14)
        d.ellipse(_b(cx + 210, t0 - 12, cx + 254, t0 + 32), fill=HAUT, outline=L, width=5 * K)
    # --- Kopf
    d.ellipse(_b(cx - kopf_r, ky - kopf_r, cx + kopf_r, ky + kopf_r), fill=HAUT, outline=L, width=7 * K)
    for s in (-1, 1):
        d.ellipse(_b(cx + s * kopf_r - 22, ky - 10, cx + s * kopf_r + 22, ky + 45), fill=HAUT, outline=L, width=5 * K)
    if haar == "huang":                                     # graues, voluminöses, nach hinten gekämmtes Haar
        grau, hell = (178, 180, 186), (214, 216, 222)
        d.chord(_b(cx - kopf_r - 8, ky - kopf_r - 40, cx + kopf_r + 8, ky + 40), 180, 360, fill=grau, outline=L,
                width=7 * K)
        d.polygon(_p(cx - kopf_r - 6, ky - 20, cx - kopf_r + 30, ky - 120, cx - 20, ky - kopf_r - 60, cx + 90,
                     ky - kopf_r - 50, cx + kopf_r + 14, ky - 90, cx + kopf_r + 6, ky - 20, cx + 40, ky - 95, cx - 60,
                     ky - 90), fill=grau, outline=L, width=6 * K)
        for i in range(5):
            x = cx - 90 + i * 45
            d.arc(_b(x - 40, ky - kopf_r - 40, x + 120, ky - 40), 205, 290, fill=hell, width=7 * K)
    elif haar == "kurz_braun":
        d.chord(_b(cx - kopf_r - 4, ky - kopf_r - 20, cx + kopf_r + 4, ky + 10), 180, 360, fill=(110, 70, 40), outline=L,
                width=7 * K)
    elif haar == "glatze":
        d.arc(_b(cx - kopf_r + 10, ky - 60, cx - 60, ky + 40), 150, 230, fill=(150, 150, 150), width=10 * K)
        d.arc(_b(cx + 60, ky - 60, cx + kopf_r - 10, ky + 40), 310, 30, fill=(150, 150, 150), width=10 * K)
    elif haar == "lang_blond":
        d.chord(_b(cx - kopf_r - 15, ky - kopf_r - 20, cx + kopf_r + 15, ky + 60), 180, 360, fill=(240, 200, 90),
                outline=L, width=7 * K)
        for s in (-1, 1):
            d.rounded_rectangle(_b(cx + s * kopf_r - 30, ky - 30, cx + s * kopf_r + 30, ky + 200), radius=25 * K,
                                fill=(240, 200, 90), outline=L, width=6 * K)
    # Augen (groß, weiß, kleine Pupillen)
    for s in (-1, 1):
        ax = cx + s * 55
        if gesicht == "geschlossen" or blinzeln:
            d.arc(_b(ax - 32, ky - 5, ax + 32, ky + 35), 200, 340, fill=L, width=8 * K)
            continue
        gr = 40 if gesicht == "schock" else 34
        d.ellipse(_b(ax - gr, ky - gr + 10, ax + gr, ky + gr + 10), fill=(255, 255, 255), outline=L, width=6 * K)
        pr = 9 if gesicht == "schock" else 13
        px = ax + (6 if gesicht == "seitenblick" else 0)
        d.ellipse(_b(px - pr, ky + 10 - pr, px + pr, ky + 10 + pr), fill=L)
    if brille:
        for s in (-1, 1):
            ax = cx + s * 55
            d.rounded_rectangle(_b(ax - 46, ky - 26, ax + 46, ky + 46), radius=14 * K, outline=L, width=6 * K)
        d.line(_p(cx - 9, ky + 2, cx + 9, ky + 2), fill=L, width=6 * K)
    # Augenbrauen
    for s in (-1, 1):
        ax = cx + s * 55
        if gesicht == "boese":
            d.line(_p(ax - 34, ky - 50 + (0 if s < 0 else 14), ax + 34, ky - 50 + (14 if s < 0 else 0)), fill=L, width=9 * K)
        elif gesicht in ("schock", "fragend"):
            d.arc(_b(ax - 34, ky - 75, ax + 34, ky - 35), 200, 340, fill=L, width=8 * K)
        else:
            d.line(_p(ax - 30, ky - 46, ax + 30, ky - 50), fill=L, width=8 * K)
    # Mund
    my = ky + 85
    if mund_offen:
        d.ellipse(_b(cx - 40, my - 22, cx + 40, my + 46), fill=(120, 30, 40), outline=L, width=6 * K)
        d.chord(_b(cx - 26, my + 12, cx + 26, my + 42), 180, 360, fill=(220, 90, 100))
    elif gesicht in ("laecheln", "geschlossen", "seitenblick"):
        d.chord(_b(cx - 55, my - 30, cx + 55, my + 38), 0, 180, fill=(120, 30, 40), outline=L, width=6 * K)
        d.chord(_b(cx - 46, my - 24, cx + 46, my + 6), 0, 180, fill=(255, 255, 255))
    elif gesicht == "schock":
        d.ellipse(_b(cx - 26, my - 12, cx + 26, my + 40), fill=(120, 30, 40), outline=L, width=6 * K)
    elif gesicht == "fragend":
        d.line(_p(cx - 32, my + 8, cx + 32, my - 4), fill=L, width=8 * K)
    else:
        d.line(_p(cx - 32, my + 4, cx + 32, my + 4), fill=L, width=8 * K)
    return img.resize((w, h), Image.LANCZOS)


# ---------------------------------------------------------------- Hintergründe
def hintergrund_buero():
    img = Image.new("RGB", (W * K, H * K), (210, 228, 240))
    d = ImageDraw.Draw(img)
    d.rectangle(_b(0, 1250, W, H), fill=(196, 170, 140))                         # Boden
    d.line(_p(0, 1250, W, 1250), fill=L, width=6 * K)
    d.rectangle(_b(80, 420, 520, 820), fill=(170, 210, 240), outline=L, width=8 * K)   # Fenster
    d.line(_p(300, 420, 300, 820), fill=L, width=6 * K)
    d.line(_p(80, 620, 520, 620), fill=L, width=6 * K)
    for x, hh in ((110, 120), (180, 200), (250, 150), (350, 230), (430, 170)):     # Skyline
        d.rectangle(_b(x, 820 - hh, x + 55, 818), fill=(130, 150, 180))
    d.rectangle(_b(640, 470, 960, 760), fill=(236, 236, 236), outline=L, width=7 * K)   # Whiteboard
    for i, hh in enumerate((90, 150, 210, 260)):                                      # steigender Chart
        d.rectangle(_b(690 + i * 62, 720 - hh, 730 + i * 62, 720), fill=(118, 185, 0))
    d.line(_p(690, 690, 760, 640, 820, 590, 900, 500), fill=L, width=6 * K)
    return img.resize((W, H), Image.LANCZOS)


def hintergrund_wohnzimmer():
    img = Image.new("RGB", (W * K, H * K), (60, 52, 90))
    d = ImageDraw.Draw(img)
    d.rectangle(_b(0, 1250, W, H), fill=(110, 80, 70))
    d.line(_p(0, 1250, W, 1250), fill=L, width=6 * K)
    d.rectangle(_b(720, 380, 980, 640), fill=(30, 36, 80), outline=L, width=8 * K)        # Fenster, Nacht
    d.ellipse(_b(880, 420, 940, 480), fill=(240, 236, 200))
    for x, y in ((760, 430), (800, 520), (930, 560), (850, 600)):
        d.ellipse(_b(x - 4, y - 4, x + 4, y + 4), fill=(255, 255, 255))
    d.rounded_rectangle(_b(120, 1180, 960, 1450), radius=40 * K, fill=(150, 60, 60), outline=L, width=8 * K)  # Sofa
    d.rounded_rectangle(_b(120, 1060, 960, 1220), radius=40 * K, fill=(170, 70, 70), outline=L, width=8 * K)
    for x in (150, 300, 760):                                                         # Pizzakartons
        d.polygon(_p(x, 1560, x + 160, 1560, x + 180, 1600, x + 20, 1600), fill=(230, 200, 150), outline=L)
    return img.resize((W, H), Image.LANCZOS)


def fernseher(img, zeilen, x=140, y=380, w=520, h=330, glow=(90, 200, 255)):
    from bild import font
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=(16, 18, 30), outline=L, width=10)
    d.rectangle([x + w // 2 - 30, y + h, x + w // 2 + 30, y + h + 50], fill=L)
    yy = y + 40
    for t, col in zeilen:
        d.text((x + w // 2, yy), t, font=font("h800", 44), fill=col, anchor="ma")
        yy += 64


def text_oben(img, text, y=230):
    """Weißer Textkasten oben (Meme-Stil), schwarze fette Schrift, mittig."""
    from bild import font, wrap
    d = ImageDraw.Draw(img)
    f = font("h800", 56)
    zeilen = wrap(d, text, f, W - 200)
    h = 40 + len(zeilen) * 68
    d.rounded_rectangle([60, y, W - 60, y + h], radius=18, fill=(255, 255, 255), outline=L, width=5)
    for i, z in enumerate(zeilen):
        d.text((W // 2, y + 22 + i * 68), z, font=f, fill=L, anchor="ma")
    return y + h


def blase(img, text, x, y, w=560, rechts=False):
    from bild import font, wrap
    d = ImageDraw.Draw(img)
    f = font("h800", 46)
    zeilen = wrap(d, text, f, w - 50)
    h = 34 + len(zeilen) * 56
    d.rounded_rectangle([x, y, x + w, y + h], radius=28, fill=(255, 255, 255), outline=L, width=6)
    sx = x + w - 110 if rechts else x + 70
    d.polygon([(sx, y + h - 4), (sx + 46, y + h - 4), (sx + (40 if rechts else 6), y + h + 56)], fill=(255, 255, 255),
              outline=L)
    d.line([(sx + 4, y + h - 3), (sx + 42, y + h - 3)], fill=(255, 255, 255), width=8)
    for i, z in enumerate(zeilen):
        d.text((x + 26, y + 18 + i * 56), z, font=f, fill=L)
