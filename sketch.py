"""Inpernell – Cartoon-Sketche (Format: zwei gezeichnete Figuren, Meme-Titel oben, Schnitt im Dialog).
Eigene, einfache Figuren im Inpernell-Stil (Navy/Orange). Zeichnet Einzelbilder; Animation folgt nach Freigabe."""
import math
import os

from PIL import Image, ImageDraw

from bild import KNOPFTEXT, NAVY, ORANGE, WEISS, font, wrap

W, H = 1080, 1920
HIER = os.path.dirname(os.path.abspath(__file__))
TINTE = (24, 28, 44)
HAUT = (243, 205, 170)
WAND, BODEN = (226, 231, 238), (196, 204, 216)
HELLBLAU = (70, 110, 170)


def raum(art="hocker"):
    img = Image.new("RGB", (W, H), WAND)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1180, W, H], fill=BODEN)
    d.line([(0, 1180), (W, 1180)], fill=(170, 180, 196), width=4)
    # Fenster und Inpernell-Poster an der Wand
    d.rounded_rectangle([90, 520, 360, 820], radius=10, fill=(205, 222, 240), outline=(170, 180, 196), width=6)
    d.line([(225, 520), (225, 820)], fill=(170, 180, 196), width=6)
    d.rounded_rectangle([720, 540, 960, 760], radius=10, fill=NAVY)
    lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
    lg = lg.resize((200, int(lg.height * 200 / lg.width)))
    img.paste(lg, (740, 620), lg)
    if art == "schreibtisch":
        d.rectangle([60, 1040, 520, 1080], fill=(150, 112, 80))
        d.rectangle([90, 1080, 120, 1330], fill=(120, 90, 64))
        d.rectangle([460, 1080, 490, 1330], fill=(120, 90, 64))
        d.rectangle([250, 930, 400, 1040], fill=TINTE)          # Monitor
        d.rectangle([310, 1040, 340, 1060], fill=TINTE)
    return img


def figur(img, cx, fuss, art="bewerber", mund="zu", augen="normal", arm="unten", sitzt=False):
    """Einfache Cartoon-Figur. art: bewerber (blauer Anzug) / beraterin (Inpernell-Navy mit Orange)."""
    d = ImageDraw.Draw(img)
    s = 1.0
    koerper_h = 330 if not sitzt else 300
    hals_y = fuss - (560 if not sitzt else 470)
    kopf_r = 120
    kopf_y = hals_y - kopf_r + 20
    anzug = (40, 62, 120) if art == "bewerber" else NAVY
    # Stuhl/Hocker
    if sitzt:
        if art == "bewerber":
            d.ellipse([cx - 120, fuss - 250, cx + 120, fuss - 200], fill=(110, 124, 120))
            d.rectangle([cx - 14, fuss - 220, cx + 14, fuss - 40], fill=(90, 100, 96))
            d.ellipse([cx - 110, fuss - 60, cx + 110, fuss - 10], fill=(90, 100, 96))
        else:
            d.rounded_rectangle([cx - 150, fuss - 560, cx + 150, fuss - 230], radius=40, fill=(40, 44, 56))
            d.rectangle([cx - 14, fuss - 230, cx + 14, fuss - 60], fill=(60, 64, 76))
            d.line([(cx - 120, fuss - 20), (cx + 120, fuss - 20)], fill=(60, 64, 76), width=16)
    # Beine
    hy = hals_y + koerper_h
    if sitzt:
        d.line([(cx - 40, hy), (cx - 40, fuss - 210), (cx - 40, fuss - 30)], fill=TINTE, width=34, joint="curve")
        d.line([(cx + 40, hy), (cx + 120, fuss - 210), (cx + 120, fuss - 30)], fill=TINTE, width=34, joint="curve")
        for x in (cx - 40, cx + 120):
            d.ellipse([x - 40, fuss - 46, x + 50, fuss - 10], fill=(30, 30, 34))
    else:
        for x in (cx - 45, cx + 45):
            d.line([(x, hy), (x, fuss - 20)], fill=TINTE, width=36)
            d.ellipse([x - 45, fuss - 36, x + 55, fuss], fill=(30, 30, 34))
    # Rumpf (Sakko)
    d.rounded_rectangle([cx - 105, hals_y, cx + 105, hy + 10], radius=40, fill=anzug, outline=TINTE, width=6)
    d.polygon([(cx - 40, hals_y), (cx + 40, hals_y), (cx, hals_y + 120)], fill=WEISS)
    if art == "bewerber":
        d.polygon([(cx - 14, hals_y + 20), (cx + 14, hals_y + 20), (cx + 18, hals_y + 150), (cx, hals_y + 175),
                   (cx - 18, hals_y + 150)], fill=(170, 40, 50))
    else:
        d.rectangle([cx + 40, hals_y + 120, cx + 90, hals_y + 136], fill=ORANGE)       # Namensschild
    # Arme
    sch_l, sch_r = (cx - 100, hals_y + 40), (cx + 100, hals_y + 40)
    if arm == "unten":
        al, ar = [sch_l, (cx - 130, hy - 40)], [sch_r, (cx + 130, hy - 40)]
    elif arm == "zeigen":
        al, ar = [sch_l, (cx - 130, hy - 40)], [sch_r, (cx + 190, hals_y + 10), (cx + 240, hals_y - 60)]
    elif arm == "achselzucken":
        al = [sch_l, (cx - 190, hals_y + 120), (cx - 250, hals_y + 40)]
        ar = [sch_r, (cx + 190, hals_y + 120), (cx + 250, hals_y + 40)]
    else:   # "tisch": Hände auf dem Tisch
        al, ar = [sch_l, (cx - 180, hals_y + 200)], [sch_r, (cx - 60, hals_y + 220)]
    for a in (al, ar):
        d.line(a, fill=anzug, width=40, joint="curve")
        x, y = a[-1]
        d.ellipse([x - 24, y - 24, x + 24, y + 24], fill=HAUT, outline=TINTE, width=4)
    # Kopf
    d.rectangle([cx - 24, hals_y - 30, cx + 24, hals_y + 10], fill=HAUT)
    d.ellipse([cx - kopf_r, kopf_y - kopf_r, cx + kopf_r, kopf_y + kopf_r], fill=HAUT, outline=TINTE, width=6)
    if art == "bewerber":     # strubbelige dunkle Haare
        pts = [(cx - kopf_r - 6, kopf_y - 10)]
        for i in range(9):
            a = math.pi + i * math.pi / 8
            r = kopf_r + (28 if i % 2 else 8)
            pts.append((cx + r * math.cos(a), kopf_y - 40 + r * math.sin(a) * 0.9))
        pts.append((cx + kopf_r + 6, kopf_y - 10))
        d.polygon(pts, fill=(30, 32, 44))
    else:                     # Beraterin: Zopf, orange Haarband
        d.chord([cx - kopf_r - 8, kopf_y - kopf_r - 12, cx + kopf_r + 8, kopf_y + 40], 180, 360, fill=(120, 70, 40))
        d.ellipse([cx + kopf_r - 30, kopf_y - 70, cx + kopf_r + 50, kopf_y + 30], fill=(120, 70, 40))
        d.arc([cx - kopf_r + 4, kopf_y - kopf_r + 6, cx + kopf_r - 4, kopf_y + 20], 200, 340, fill=ORANGE, width=14)
    # Augen
    for ex in (cx - 45, cx + 45):
        ey = kopf_y + 5
        if augen == "skeptisch":
            d.ellipse([ex - 30, ey - 12, ex + 30, ey + 22], fill=WEISS, outline=TINTE, width=5)
            d.ellipse([ex - 8, ey - 2, ex + 12, ey + 18], fill=TINTE)
            d.line([(ex - 34, ey - 18), (ex + 34, ey - 8 if ex < cx else ey - 28)], fill=TINTE, width=8)
        elif augen == "gross":
            d.ellipse([ex - 34, ey - 34, ex + 34, ey + 34], fill=WEISS, outline=TINTE, width=5)
            d.ellipse([ex - 10, ey - 10, ex + 10, ey + 10], fill=TINTE)
        else:
            d.ellipse([ex - 28, ey - 28, ex + 28, ey + 28], fill=WEISS, outline=TINTE, width=5)
            d.ellipse([ex - 6, ey - 4, ex + 16, ey + 18], fill=TINTE)
    # Mund
    my = kopf_y + 62
    if mund == "offen":
        d.ellipse([cx - 22, my - 14, cx + 22, my + 22], fill=(120, 40, 50), outline=TINTE, width=4)
    elif mund == "laecheln":
        d.arc([cx - 40, my - 30, cx + 40, my + 20], 20, 160, fill=TINTE, width=7)
    else:
        d.line([(cx - 26, my), (cx + 26, my)], fill=TINTE, width=7)
    return img


def titel(img, text):
    d = ImageDraw.Draw(img)
    f = font("h800", 54)
    zeilen = wrap(d, text.upper(), f, W - 200)
    h = 40 + len(zeilen) * 64
    d.rounded_rectangle([70, 230, W - 70, 230 + h], radius=18, fill=WEISS, outline=TINTE, width=5)
    for i, z in enumerate(zeilen):
        d.text((W // 2, 250 + i * 64), z, font=f, fill=TINTE, anchor="ma")
    return img


def untertitel(img, text, sprecher=None):
    d = ImageDraw.Draw(img)
    f = font("h800", 50)
    zeilen = wrap(d, text, f, W - 300)
    y = 600                                   # Sprechblase über der Figur, unter dem Titel
    hoehe = 50 + len(zeilen) * 62
    d.rounded_rectangle([110, y, W - 110, y + hoehe], radius=30, fill=WEISS, outline=TINTE, width=5)
    d.polygon([(W // 2 - 30, y + hoehe - 3), (W // 2 + 30, y + hoehe - 3), (W // 2, y + hoehe + 40)], fill=WEISS)
    d.line([(W // 2 - 30, y + hoehe), (W // 2, y + hoehe + 40), (W // 2 + 30, y + hoehe)], fill=TINTE, width=5)
    if sprecher:
        d.text((140, y - 40), sprecher.upper(), font=font("h800", 28), fill=ORANGE)
    for i, z in enumerate(zeilen):
        d.text((W // 2, y + 25 + i * 62), z, font=f, fill=TINTE, anchor="ma")
    return img


def schluss(text_oben, text_unten):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
    lg = lg.resize((560, int(lg.height * 560 / lg.width)))
    img.paste(lg, ((W - lg.width) // 2, 640), lg)
    d.text((W // 2, 840), "DIREKTVERMITTLUNG", font=font("h700", 34), fill=(255, 214, 180), anchor="ma")
    for i, z in enumerate(wrap(d, text_oben, font("h800", 64), W - 200)):
        d.text((W // 2, 400 + i * 76), z, font=font("h800", 64), fill=WEISS, anchor="ma")
    fk = font("h800", 44)
    kw = d.textlength(text_unten, font=fk)
    d.rounded_rectangle([W / 2 - kw / 2 - 50, 1000, W / 2 + kw / 2 + 50, 1090], radius=45, fill=ORANGE)
    d.text((W // 2, 1045), text_unten, font=fk, fill=KNOPFTEXT, anchor="mm")
    return img
