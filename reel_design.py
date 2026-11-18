"""Inpernell – neue Reel-Folien (Entwurf 2): moderner, aber im Inpernell-Stil (Navy, Orange, Archivo/Lato).

Gestaltungsmittel (aktuelle Instagram-Trends, im Markenrahmen):
  * Duoton-Foto (Navy/Blau) mit feinem Filmkorn statt Stockfoto mit Schleier
  * übergroße Schrift, Schlüsselwörter mit orangem Marker hinterlegt
  * schräg gesetzte "Sticker"-Etiketten
  * Fehler/Besser-Vergleich (✗ / ✓) als Karten
  * Zahl als Held + Balkenvergleich für Fakten
  * segmentierter Fortschrittsbalken, Wisch-/Speichern-Hinweis
Die Funktionen zeichnen Einzelbilder; die Animation baut darauf auf.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from bild import HELL, KNOPFTEXT, NAVY, ORANGE, PFIRSICH, WEISS, _foto_vorbereiten, font, gesperrt, gesperrt_breite, wrap

W, H = 1080, 1920
M, R = 80, 140
HIER = os.path.dirname(os.path.abspath(__file__))
NAVY2 = (18, 40, 78)
BLAU = (70, 110, 170)
ROT = (226, 75, 74)
GRUEN = (52, 199, 123)


# ---------------------------------------------------------------- Grundbausteine

def korn(img, staerke=14, seed=1):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, staerke, (img.height, img.width, 1)).astype(np.int16)
    a = np.asarray(img.convert("RGB")).astype(np.int16) + n
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def duoton(foto, dunkel=NAVY, hell=BLAU, akzent=None):
    g = ImageOps.autocontrast(foto.convert("L"), cutoff=2)
    bild = ImageOps.colorize(g, black=dunkel, white=hell, mid=None)
    if akzent:
        bild = ImageOps.colorize(g, black=dunkel, white=akzent, mid=hell)
    return bild.convert("RGBA")


def grund(kat, foto_hoehe=1150, variante="oben"):
    """Navy-Fläche mit Duoton-Foto oben, weichem Übergang und Korn."""
    img = Image.new("RGBA", (W, H), (*NAVY, 255))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(NAVY2[0] * (1 - t) + NAVY[0] * t), int(NAVY2[1] * (1 - t) + NAVY[1] * t),
                                       int(NAVY2[2] * (1 - t) + NAVY[2] * t), 255))
    if foto_hoehe:
        foto = duoton(_foto_vorbereiten(kat, W, foto_hoehe))
        maske = Image.new("L", (W, foto_hoehe), 255)
        md = ImageDraw.Draw(maske)
        for y in range(foto_hoehe):
            a = 255 if y < foto_hoehe * 0.45 else int(255 * max(0, 1 - (y - foto_hoehe * 0.45) / (foto_hoehe * 0.55)) ** 1.4)
            md.line([(0, y), (W, y)], fill=int(a * 0.9))
        if variante != "oben":
            maske = maske.transpose(Image.FLIP_TOP_BOTTOM)
        img.paste(foto, (0, 0 if variante == "oben" else H - foto_hoehe), maske)
    return korn(img)


def marker_text(d, xy, zeilen, f, markiert=(), farbe=WEISS, marker=ORANGE, marker_text_farbe=KNOPFTEXT,
                zeilenabstand=1.04):
    """Zeilen setzen; Wörter in `markiert` bekommen einen orangen Marker-Balken dahinter."""
    x0, y = xy
    for zeile in zeilen:
        x = x0
        for wort in zeile.split():
            rein = wort.strip(",.!?:").lower()
            breite = d.textlength(wort, font=f)
            if rein in markiert:
                pad = int(f.size * 0.12)
                d.rounded_rectangle([x - pad, y + int(f.size * 0.12), x + breite + pad, y + int(f.size * 1.08)],
                                    radius=int(f.size * 0.12), fill=marker)
                d.text((x, y), wort, font=f, fill=marker_text_farbe)
            else:
                d.text((x, y), wort, font=f, fill=farbe)
            x += breite + d.textlength(" ", font=f)
        y += int(f.size * zeilenabstand)
    return y


def sticker(img, text, xy, winkel=-5, fuell=ORANGE, schrift=KNOPFTEXT, groesse=26):
    f = font("h800", groesse)
    m = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    tw = gesperrt_breite(m, text, f, 2.6)
    s = Image.new("RGBA", (int(tw + 56), groesse + 40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(s)
    sd.rounded_rectangle([0, 0, s.width - 1, s.height - 1], radius=14, fill=fuell)
    gesperrt(sd, (28, 18), text, f, schrift, 2.6)
    s = s.rotate(winkel, expand=True, resample=Image.BICUBIC)
    schatten = Image.new("RGBA", s.size, (0, 0, 0, 0))
    schatten.putalpha(s.getchannel("A").point(lambda a: int(a * 0.35)))
    schatten = schatten.filter(ImageFilter.GaussianBlur(8))
    img.alpha_composite(schatten, (xy[0] + 6, xy[1] + 10))
    img.alpha_composite(s, xy)


def kopf(img, szene, anzahl):
    d = ImageDraw.Draw(img)
    lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
    img.alpha_composite(lg, (M - 10, 96))
    luecke, y = 10, 210
    breite = (W - M - R - luecke * (anzahl - 1)) / anzahl
    for i in range(anzahl):
        x0 = M + i * (breite + luecke)
        d.rounded_rectangle([x0, y, x0 + breite, y + 8], radius=4,
                            fill=ORANGE if i <= szene else (255, 255, 255, 70))


def icon_x(d, cx, cy, r, farbe=ROT):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=farbe)
    k = r * 0.42
    d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=WEISS, width=int(r * 0.22))
    d.line([(cx - k, cy + k), (cx + k, cy - k)], fill=WEISS, width=int(r * 0.22))


def icon_haken(d, cx, cy, r, farbe=GRUEN):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=farbe)
    d.line([(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.48, cy - r * 0.35)],
           fill=WEISS, width=int(r * 0.22), joint="curve")


def icon_lesezeichen(d, x, y, b, h, farbe=WEISS):
    d.polygon([(x, y), (x + b, y), (x + b, y + h), (x + b / 2, y + h * 0.72), (x, y + h)], fill=farbe)


def glas(img, box, radius=36, fuell=(255, 255, 255, 22), rand=(255, 255, 255, 60)):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(box, radius=radius, fill=fuell, outline=rand, width=2)
    img.alpha_composite(ov)


def caption_box(img, text, xy, groesse=40, maxw=W - M - R):
    """Weiße Textbox mit dunkler Schrift (TikTok-/Reels-Untertitel-Look)."""
    d = ImageDraw.Draw(img)
    f = font("h700", groesse)
    zeilen = wrap(d, text, f, maxw - 48)
    x, y = xy
    for z in zeilen:
        tw = d.textlength(z, font=f)
        d.rounded_rectangle([x, y, x + tw + 44, y + groesse + 30], radius=14, fill=WEISS)
        d.text((x + 22, y + 12), z, font=f, fill=NAVY)
        y += groesse + 36
    return y


def sprechblase(img, text, xy, maxw, eigen=True):
    """Chat-Blase: eigene Nachricht orange rechts, fremde weiß links."""
    d = ImageDraw.Draw(img)
    f = font("t700", 40)
    zeilen = wrap(d, text, f, maxw - 64)
    h = len(zeilen) * 52 + 44
    b = max(d.textlength(z, font=f) for z in zeilen) + 64
    x, y = xy
    if eigen:
        x = x + maxw - b
    farbe, schrift = (ORANGE, KNOPFTEXT) if eigen else (WEISS, NAVY)
    d.rounded_rectangle([x, y, x + b, y + h], radius=34, fill=farbe)
    spitze = [(x + b - 30, y + h - 6), (x + b + 14, y + h + 18), (x + b - 60, y + h - 6)] if eigen else \
        [(x + 30, y + h - 6), (x - 14, y + h + 18), (x + 60, y + h - 6)]
    d.polygon(spitze, fill=farbe)
    for i, z in enumerate(zeilen):
        d.text((x + 32, y + 22 + i * 52), z, font=f, fill=schrift)
    return y + h + 40


# ---------------------------------------------------------------- Folientypen

def folie_hook(kat, rubrik, zeilen, markiert, unterzeile, szene=0, anzahl=5):
    img = grund(kat, 1250)
    kopf(img, szene, anzahl)
    d = ImageDraw.Draw(img)
    sticker(img, rubrik.upper(), (M - 6, 300), winkel=-4)
    f = font("h800", 124)
    y = marker_text(d, (M, 600), zeilen, f, markiert)
    caption_box(img, unterzeile, (M, y + 30))
    # Hinweis noch in der sicheren Zone (unten blendet Instagram den Bildtext ein)
    d = ImageDraw.Draw(img)
    gesperrt(d, (M, 1185), "SPEICHERN LOHNT SICH", font("h700", 24), WEISS, 4)
    icon_lesezeichen(d, M + 430, 1179, 26, 36, ORANGE)
    return img


def folie_vergleich(kat, nr, fehler, besser, detail, szene, anzahl=5):
    img = grund(kat, 700)
    kopf(img, szene, anzahl)
    d = ImageDraw.Draw(img)
    # große Nummer als Umriss
    f = font("h800", 210)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ov).text((M - 8, 250), f"{nr:02d}", font=f, fill=(*ORANGE, 40), stroke_width=4, stroke_fill=ORANGE)
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    breite = W - M - R
    # Fehler-Karte
    y = 520
    glas(img, [M, y, W - R, y + 270], fuell=(226, 75, 74, 38), rand=(226, 75, 74, 160))
    d = ImageDraw.Draw(img)
    icon_x(d, M + 70, y + 74, 34)
    gesperrt(d, (M + 126, y + 58), "FEHLER", font("h800", 28), (255, 200, 200), 4)
    ff = font("h800", 54)
    zz = wrap(d, fehler, ff, breite - 80)
    yy = y + 124
    for z in zz[:2]:
        d.text((M + 40, yy), z, font=ff, fill=(255, 255, 255, 190))
        # durchgestrichen: der Fehler ist "erledigt"
        d.line([(M + 40, yy + 32), (M + 40 + d.textlength(z, font=ff), yy + 32)], fill=(226, 75, 74), width=5)
        yy += 62
    # Besser-Karte
    y = 820
    glas(img, [M, y, W - R, y + 410], fuell=(52, 199, 123, 34), rand=(52, 199, 123, 170))
    d = ImageDraw.Draw(img)
    icon_haken(d, M + 70, y + 74, 34)
    gesperrt(d, (M + 126, y + 58), "BESSER", font("h800", 28), (190, 245, 215), 4)
    fb = font("h800", 64)
    yy = y + 124
    for z in wrap(d, besser, fb, breite - 80)[:3]:
        d.text((M + 40, yy), z, font=fb, fill=WEISS)
        yy += 72
    fd = font("t400", 38)
    yy += 14
    for z in wrap(d, detail, fd, breite - 80)[:3]:
        d.text((M + 40, yy), z, font=fd, fill=HELL)
        yy += 50
    return img


def folie_zahl(kat, rubrik, zahl, einheit, label, balken, quelle, szene, anzahl=5):
    """balken: Liste (Text, Wert, hervorheben?)"""
    img = grund(kat, 600)
    kopf(img, szene, anzahl)
    d = ImageDraw.Draw(img)
    sticker(img, rubrik.upper(), (M - 6, 290), winkel=3, fuell=WEISS, schrift=NAVY)
    fz = font("h800", 300)
    d.text((M - 12, 370), zahl, font=fz, fill=ORANGE)
    zw = d.textlength(zahl, font=fz)
    d.text((M + zw + 20, 570), einheit, font=font("h800", 64), fill=WEISS)
    y = 720
    for z in wrap(d, label, font("h800", 56), W - M - R):
        d.text((M, y), z, font=font("h800", 56), fill=WEISS)
        y += 64
    # Balkenvergleich
    y += 40
    maxwert = max(b[1] for b in balken)
    breite = W - M - R - 220
    for text, wert, hervor in balken:
        d.text((M, y), text, font=font("t700", 34), fill=WEISS if hervor else HELL)
        y += 48
        lang = max(14, int(breite * wert / maxwert))
        d.rounded_rectangle([M, y, M + breite, y + 30], radius=15, fill=(255, 255, 255, 30))
        d.rounded_rectangle([M, y, M + lang, y + 30], radius=15, fill=ORANGE if hervor else (255, 255, 255, 170))
        d.text((M + breite + 24, y - 8), f"{wert:g}".replace(".", ","), font=font("h800", 40), fill=WEISS)
        y += 70
    d.text((M, y + 10), quelle, font=font("t400", 26), fill=PFIRSICH)
    return img


def folie_ende(kat, titel_zeilen, markiert, zusatz, szene, anzahl=5):
    img = grund(kat, 900, variante="unten")
    kopf(img, szene, anzahl)
    d = ImageDraw.Draw(img)
    icon_lesezeichen(d, M, 320, 80, 110, ORANGE)
    y = marker_text(d, (M, 480), titel_zeilen, font("h800", 104), markiert)
    d.text((M, y + 30), zusatz, font=font("t400", 42), fill=HELL)
    y += 150
    glas(img, [M, y, W - R, y + 200], radius=40)
    d = ImageDraw.Draw(img)
    d.text((M + 40, y + 36), "Neue Top Jobs jeden Abend", font=font("h800", 46), fill=WEISS)
    fk = font("h700", 36)
    kt = "Link in der Bio"
    kw = d.textlength(kt, font=fk)
    d.rounded_rectangle([M + 40, y + 108, M + 40 + kw + 120, y + 172], radius=32, fill=ORANGE)
    d.text((M + 75, y + 140), kt, font=fk, fill=KNOPFTEXT, anchor="lm")
    ax = M + 75 + kw + 18
    d.line([(ax, y + 140), (ax + 30, y + 140)], fill=KNOPFTEXT, width=4)
    d.line([(ax + 18, y + 128), (ax + 30, y + 140), (ax + 18, y + 152)], fill=KNOPFTEXT, width=4, joint="curve")
    gesperrt(d, (M, y + 240), "INPERNELL.DE  ·  DIREKTVERMITTLUNG", font("h600", 22), PFIRSICH, 3)
    return img


def folie_formulierung(kat, ueberschrift, frage, antwort, tipp, szene, anzahl=5):
    """'So sagst du's': Chatverlauf Recruiter/Kandidat als Formulierungshilfe."""
    img = grund(kat, 600)
    kopf(img, szene, anzahl)
    d = ImageDraw.Draw(img)
    sticker(img, "SO SAGST DU'S", (M - 6, 290), winkel=-3)
    y = marker_text(d, (M, 420), wrap(d, ueberschrift, font("h800", 72), W - M - R), font("h800", 72), set())
    y += 40
    gesperrt(d, (M, y), "RECRUITER", font("h700", 22), PFIRSICH, 3)
    y = sprechblase(img, frage, (M, y + 40), W - M - R - 120, eigen=False)
    d = ImageDraw.Draw(img)
    gesperrt(d, (W - R - gesperrt_breite(d, "DU", font("h700", 22), 3), y), "DU", font("h700", 22), PFIRSICH, 3)
    y = sprechblase(img, antwort, (M + 60, y + 40), W - M - R - 60, eigen=True)
    caption_box(img, tipp, (M, y + 10), groesse=34)
    return img
