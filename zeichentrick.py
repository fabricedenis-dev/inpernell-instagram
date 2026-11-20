"""Zeichentrick-Sketche (Strichmännchen-Cartoon-Stil): große runde Köpfe, dünne Strich-Arme/-Beine,
Augenringe, schlichter grauer Verlauf als Hintergrund, Meme-Titel oben. Eigene Figuren, keine Kopie."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw

from bild import KNOPFTEXT, NAVY, ORANGE, WEISS, font, wrap

W, H = 1080, 1920
HIER = os.path.dirname(os.path.abspath(__file__))
STRICH = (20, 20, 24)
HAUT, HAUT_S = (232, 186, 140), (205, 156, 112)


def hintergrund(stuhl=None):
    y = np.linspace(0, 1, H)[:, None]
    farbe = (150 + 90 * y) * np.ones((1, W))
    img = Image.fromarray(np.stack([farbe, farbe + 2, farbe + 6], axis=2).clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    if stuhl == "buero":        # Bürostuhl hinter der Figur + Tischkante
        d.rounded_rectangle([600, 1020, 820, 1330], radius=60, fill=(46, 48, 54))
        d.rectangle([700, 1330, 720, 1480], fill=(60, 62, 68))
        d.line([(610, 1490), (810, 1490)], fill=(60, 62, 68), width=14)
        d.rectangle([0, 1240, 330, 1270], fill=(176, 132, 92))
        d.rectangle([30, 1270, 52, 1560], fill=(150, 110, 76))
    if stuhl == "hocker":
        d.ellipse([400, 1395, 680, 1445], fill=(120, 132, 128))
        d.rectangle([528, 1420, 552, 1560], fill=(96, 104, 100))
        d.ellipse([440, 1545, 640, 1585], fill=(96, 104, 100))
    return img


def _kopf(d, cx, cy, r, haare, augen, mund, brille=False, bart=False):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=HAUT, outline=STRICH, width=5)
    d.chord([cx - r + 6, cy - r * 0.1, cx + r - 6, cy + r - 4], 20, 160, fill=HAUT_S)      # leichter Schatten unten
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=STRICH, width=5)
    haare(d, cx, cy, r)
    ey = cy - r * 0.05
    for ex in (cx - r * 0.36, cx + r * 0.36):
        er = r * 0.27
        if augen == "muede":
            d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=WEISS, outline=STRICH, width=4)
            d.chord([ex - er, ey - er, ex + er, ey + er], 180, 360, fill=HAUT_S, outline=STRICH, width=4)  # halb geschlossen
            d.ellipse([ex - 7, ey + 2, ex + 9, ey + 18], fill=STRICH)
        elif augen == "genervt":
            d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=WEISS, outline=STRICH, width=4)
            d.ellipse([ex - 8, ey - er + 4, ex + 8, ey - er + 20], fill=STRICH)                 # Augenrollen
        elif augen == "gross":
            d.ellipse([ex - er * 1.15, ey - er * 1.15, ex + er * 1.15, ey + er * 1.15], fill=WEISS, outline=STRICH, width=4)
            d.ellipse([ex - 7, ey - 7, ex + 7, ey + 7], fill=STRICH)
        else:
            d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=WEISS, outline=STRICH, width=4)
            d.ellipse([ex - 6, ey - 2, ex + 10, ey + 14], fill=STRICH)
        d.arc([ex - er, ey + er * 0.3, ex + er, ey + er * 1.4], 20, 160, fill=(150, 110, 90), width=4)   # Augenringe
        if brille:
            d.ellipse([ex - er - 8, ey - er - 8, ex + er + 8, ey + er + 8], outline=STRICH, width=6)
    if brille:
        d.line([(cx - r * 0.36 + r * 0.27 + 8, ey), (cx + r * 0.36 - r * 0.27 - 8, ey)], fill=STRICH, width=6)
    my = cy + r * 0.5
    if bart:
        d.chord([cx - 46, my - 26, cx + 46, my + 10], 180, 360, fill=(110, 80, 60))
    if mund == "offen":
        d.ellipse([cx - 16, my - 8, cx + 16, my + 22], fill=(90, 30, 40), outline=STRICH, width=3)
    elif mund == "grinsen":
        d.chord([cx - 34, my - 16, cx + 34, my + 26], 0, 180, fill=WEISS, outline=STRICH, width=4)
    elif mund == "schief":
        d.line([(cx - 24, my + 6), (cx + 20, my - 4)], fill=STRICH, width=5)
    else:
        d.arc([cx - 22, my - 6, cx + 22, my + 14], 200, 340, fill=STRICH, width=5)


def haare_vorhang(d, cx, cy, r):
    """Mittelscheitel ("Curtains"), Gen-Z-Frisur."""
    braun = (88, 58, 38)
    d.chord([cx - r - 10, cy - r - 18, cx + r + 10, cy + r * 0.4], 180, 360, fill=braun)
    d.polygon([(cx - 4, cy - r + 6), (cx - r - 8, cy - r * 0.05), (cx - r * 0.9, cy - r * 0.55)], fill=braun)
    d.polygon([(cx + 4, cy - r + 6), (cx + r + 8, cy - r * 0.05), (cx + r * 0.9, cy - r * 0.55)], fill=braun)
    d.line([(cx, cy - r - 12), (cx, cy - r * 0.55)], fill=(60, 38, 24), width=4)


def haare_glatze(d, cx, cy, r):
    grau = (150, 146, 140)
    d.chord([cx - r - 6, cy - r * 0.3, cx - r * 0.55, cy + r * 0.3], 90, 270, fill=grau)
    d.chord([cx + r * 0.55, cy - r * 0.3, cx + r + 6, cy + r * 0.3], 270, 90, fill=grau)
    d.arc([cx - r * 0.5, cy - r * 0.85, cx - r * 0.1, cy - r * 0.55], 200, 330, fill=(250, 220, 190), width=6)  # Glanz


def figur(img, cx, fuss, art, augen="normal", mund="neutral", arm="unten", sitzt=False, handy=False):
    d = ImageDraw.Draw(img)
    r = 115
    huefte = fuss - (330 if not sitzt else 175)
    schulter = huefte - 260
    kopf_y = schulter - r + 10
    if art == "genz":
        farbe, schatten = (176, 160, 214), (146, 130, 186)        # lila Hoodie
    else:
        farbe, schatten = (110, 116, 124), (86, 92, 100)          # grauer Anzug
    # Beine (dünne Striche)
    if sitzt:
        for dx in (-30, 30):
            d.line([(cx + dx, huefte), (cx + dx + 70, huefte + 10), (cx + dx + 70, fuss)], fill=STRICH, width=9, joint="curve")
            d.ellipse([cx + dx + 50, fuss - 16, cx + dx + 110, fuss + 6], fill=STRICH)
    else:
        for dx in (-30, 30):
            d.line([(cx + dx, huefte), (cx + dx, fuss)], fill=STRICH, width=9)
            d.ellipse([cx + dx - 14, fuss - 14, cx + dx + 46, fuss + 8], fill=STRICH)
    # Körper: schmal, leicht trapezförmig
    d.polygon([(cx - 62, schulter), (cx + 62, schulter), (cx + 78, huefte), (cx - 78, huefte)], fill=farbe, outline=STRICH)
    d.polygon([(cx + 20, schulter), (cx + 62, schulter), (cx + 78, huefte), (cx + 34, huefte)], fill=schatten)
    d.line([(cx - 62, schulter), (cx - 78, huefte), (cx + 78, huefte), (cx + 62, schulter)], fill=STRICH, width=5)
    if art == "genz":
        d.rounded_rectangle([cx - 46, huefte - 110, cx + 46, huefte - 50], radius=14, outline=schatten, width=6)  # Bauchtasche
        d.line([(cx - 20, schulter + 6), (cx - 24, schulter + 90)], fill=WEISS, width=5)                          # Kordeln
        d.line([(cx + 20, schulter + 6), (cx + 24, schulter + 90)], fill=WEISS, width=5)
    else:
        d.polygon([(cx - 24, schulter), (cx + 24, schulter), (cx, schulter + 60)], fill=WEISS)
        d.polygon([(cx - 9, schulter + 14), (cx + 9, schulter + 14), (cx + 12, schulter + 120), (cx, schulter + 140),
                   (cx - 12, schulter + 120)], fill=(170, 40, 50))
    # Arme (Strich) + Hände
    links, rechts = (cx - 60, schulter + 20), (cx + 60, schulter + 20)
    if arm == "achselzucken":
        al = [links, (cx - 150, schulter + 110), (cx - 210, schulter + 30)]
        ar = [rechts, (cx + 150, schulter + 110), (cx + 210, schulter + 30)]
    elif arm == "zeigen":
        al = [links, (cx - 90, huefte - 30)]
        ar = [rechts, (cx + 140, schulter - 10), (cx + 190, schulter - 90)]
    elif arm == "handy":
        al = [links, (cx - 40, schulter + 150), (cx + 10, schulter + 110)]
        ar = [rechts, (cx + 60, schulter + 150), (cx + 20, schulter + 110)]
    elif arm == "tisch":
        al = [links, (cx - 140, schulter + 150), (cx - 230, schulter + 160)]
        ar = [rechts, (cx - 40, schulter + 170), (cx - 120, schulter + 180)]
    else:
        al, ar = [links, (cx - 90, huefte - 30)], [rechts, (cx + 90, huefte - 30)]
    for a in (al, ar):
        d.line(a, fill=STRICH, width=9, joint="curve")
        x, y = a[-1]
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=STRICH)
    if handy or arm == "handy":
        d.rounded_rectangle([cx - 30, schulter + 60, cx + 30, schulter + 140], radius=10, fill=(30, 30, 36), outline=STRICH, width=3)
        d.rectangle([cx - 24, schulter + 68, cx + 24, schulter + 130], fill=(120, 190, 230))
    # Kopf
    d.line([(cx, schulter - 20), (cx, schulter)], fill=STRICH, width=10)
    if art == "genz":
        _kopf(d, cx, kopf_y, r, haare_vorhang, augen, mund)
        d.ellipse([cx - r - 10, kopf_y + 10, cx - r + 12, kopf_y + 34], fill=WEISS, outline=STRICH, width=3)  # AirPod
    else:
        _kopf(d, cx, kopf_y, r, haare_glatze, augen, mund, brille=True, bart=True)
    return img


def titel(img, text):
    d = ImageDraw.Draw(img)
    f = font("h800", 58)
    zeilen = wrap(d, text.upper(), f, W - 220)
    h = 36 + len(zeilen) * 66
    d.rounded_rectangle([90, 260, W - 90, 260 + h], radius=26, fill=(246, 246, 246))
    for i, z in enumerate(zeilen):
        d.text((W // 2, 278 + i * 66), z, font=f, fill=STRICH, anchor="ma")
    return img


def untertitel(img, text):
    """Untertitel wie bei TikTok/Reels: weiße Schrift mit dunkler Kontur, mittig über den Figuren."""
    d = ImageDraw.Draw(img)
    f = font("h800", 52)
    for i, z in enumerate(wrap(d, text, f, W - 240)):
        d.text((W // 2, 640 + i * 66), z, font=f, fill=WEISS, anchor="ma", stroke_width=8, stroke_fill=STRICH)
    return img


def abspann(text, knopf):
    img = hintergrund()
    d = ImageDraw.Draw(img)
    for i, z in enumerate(wrap(d, text, font("h800", 66), W - 200)):
        d.text((W // 2, 560 + i * 80), z, font=font("h800", 66), fill=STRICH, anchor="ma")
    fk = font("h800", 44)
    kw = d.textlength(knopf, font=fk)
    d.rounded_rectangle([W / 2 - kw / 2 - 50, 900, W / 2 + kw / 2 + 50, 990], radius=45, fill=ORANGE)
    d.text((W // 2, 945), knopf, font=fk, fill=KNOPFTEXT, anchor="mm")
    lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
    platte = Image.new("RGBA", (lg.width + 60, lg.height + 40), NAVY + (255,))
    platte.paste(lg, (30, 20), lg)
    img.paste(platte, ((W - platte.width) // 2, 1080), platte)
    return img
