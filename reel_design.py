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

KORN = 8          # Filmkorn-Stärke; im Video kleiner, weil Rauschen beim Zoomen viel Speicher kostet


def korn(img, staerke=None, seed=1):
    staerke = KORN if staerke is None else staerke
    if staerke <= 0:
        return img.convert("RGBA")
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
    """Nur der Fortschrittsbalken. Kein Logo oben: dort blendet Instagram schon Kontoname/Profilbild ein."""
    d = ImageDraw.Draw(img)
    luecke, y = 10, 210
    breite = (W - M - R - luecke * (anzahl - 1)) / anzahl
    for i in range(anzahl):
        x0 = M + i * (breite + luecke)
        d.rounded_rectangle([x0, y, x0 + breite, y + 8], radius=4,
                            fill=ORANGE if i <= szene else (88, 104, 136))


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

class Stufe:
    """Zählt Bausteine einer Folie. bis=k: nur die ersten k zeichnen; nur=k: ausschließlich Baustein k
    (für die Animation, dann auf schwarzem und weißem Grund, um echte Transparenz zu gewinnen)."""
    def __init__(self, bis, nur=None):
        self.bis, self.nur, self.i = bis, nur, 0

    def __call__(self):
        self.i += 1
        return self.i == self.nur if self.nur else self.i <= self.bis


_LOGO = {}
LOGO_XY, LOGO_BREITE = (M - 6, 1420), 260


def logo_marke(img):
    """Kleines Logo unten links (Variante B, vom Inhaber freigegeben): über Kontoname/Bildtext von Instagram,
    innerhalb des Feed-Ausschnitts, frei von Kopfzeile und Knopfleiste. Nicht auf der Abschlussfolie."""
    if "b" not in _LOGO:
        lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
        _LOGO["b"] = lg.resize((LOGO_BREITE, round(lg.height * LOGO_BREITE / lg.width)), Image.LANCZOS)
    img.alpha_composite(_LOGO["b"], LOGO_XY)
    return img


def _start(kat, foto_hoehe, szene, anzahl, mit_kopf, variante="oben", basis="grund", logo=True):
    if basis in ("schwarz", "weiss"):
        return Image.new("RGBA", (W, H), (0, 0, 0, 255) if basis == "schwarz" else (255, 255, 255, 255))
    img = grund(kat, foto_hoehe, variante)
    if mit_kopf:
        kopf(img, szene, anzahl)
        if logo:
            logo_marke(img)
    return img


def folie_hook(kat, rubrik, zeilen, markiert, unterzeile, szene=0, anzahl=5, bis=99, mit_kopf=True, nur=None, basis="grund"):
    g = Stufe(bis, nur)
    img = _start(kat, 1250, szene, anzahl, mit_kopf, basis=basis)
    if g():
        sticker(img, rubrik.upper(), (M - 6, 300), winkel=-4)
    # Schrift so groß wie möglich, aber jede Zeile (inkl. Marker-Rand) muss in die Breite passen
    mess = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    groesse = 124
    while groesse > 64 and any(mess.textlength(z, font=font("h800", groesse)) + groesse * 0.3 > W - M - R
                               for z in zeilen):
        groesse -= 4
    f = font("h800", groesse)
    y = 600
    for zeile in zeilen:                         # jede Zeile ein Baustein (Wort-für-Wort-Gefühl)
        if g():
            marker_text(ImageDraw.Draw(img), (M, y), [zeile], f, markiert)
        y += int(f.size * 1.04)
    if g():
        caption_box(img, unterzeile, (M, y + 30))
    if g():
        d = ImageDraw.Draw(img)
        gesperrt(d, (M, 1185), "SPEICHERN LOHNT SICH", font("h700", 24), WEISS, 4)
        icon_lesezeichen(d, M + 430, 1179, 26, 36, ORANGE)
    return img


def folie_vergleich(kat, nr, fehler, besser, detail, szene, anzahl=5, bis=99, mit_kopf=True, nur=None, basis="grund",
                    label_schlecht="FEHLER", label_gut="BESSER", durchstreichen=True):
    g = Stufe(bis, nur)
    img = _start(kat, 700, szene, anzahl, mit_kopf, basis=basis)
    breite = W - M - R
    if g():                                      # große Umriss-Nummer
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).text((M - 8, 275), f"{nr:02d}", font=font("h800", 190), fill=(*ORANGE, 40),
                                stroke_width=4, stroke_fill=ORANGE)
        img.alpha_composite(ov)
    y = 520
    ff = font("h800", 54)
    zz = wrap(ImageDraw.Draw(img), fehler, ff, breite - 80)[:2]
    if g():                                      # Fehler-Karte
        glas(img, [M, y, W - R, y + 270], fuell=(226, 75, 74, 38), rand=(226, 75, 74, 160))
        d = ImageDraw.Draw(img)
        icon_x(d, M + 70, y + 74, 34)
        gesperrt(d, (M + 126, y + 58), label_schlecht.upper(), font("h800", 28), (255, 200, 200), 4)
        for i, z in enumerate(zz):
            d.text((M + 40, y + 124 + i * 62), z, font=ff, fill=(214, 218, 228))
    if g() and durchstreichen:                   # Durchstreichen
        d = ImageDraw.Draw(img)
        for i, z in enumerate(zz):
            yy = y + 124 + i * 62 + 32
            d.line([(M + 40, yy), (M + 40 + d.textlength(z, font=ff), yy)], fill=(226, 75, 74), width=5)
    y = 820
    fb = font("h800", 64)
    zb = wrap(ImageDraw.Draw(img), besser, fb, breite - 80)[:3]
    _detail_y = y + 124 + 72 * len(zb) + 14
    if g():                                      # Besser-Karte
        glas(img, [M, y, W - R, y + 410], fuell=(52, 199, 123, 34), rand=(52, 199, 123, 170))
        d = ImageDraw.Draw(img)
        icon_haken(d, M + 70, y + 74, 34)
        gesperrt(d, (M + 126, y + 58), label_gut.upper(), font("h800", 28), (190, 245, 215), 4)
        for i, z in enumerate(zb):
            d.text((M + 40, y + 124 + i * 72), z, font=fb, fill=WEISS)
    if g():
        d = ImageDraw.Draw(img)
        fd = font("t400", 38)
        for i, z in enumerate(wrap(d, detail, fd, breite - 80)[:3]):
            d.text((M + 40, _detail_y + i * 50), z, font=fd, fill=HELL)
    return img


def folie_zahl(kat, rubrik, zahl, einheit, label, balken, quelle, szene, anzahl=5, bis=99, mit_kopf=True, nur=None, basis="grund"):
    """balken: Liste (Text, Wert, hervorheben?)"""
    g = Stufe(bis, nur)
    img = _start(kat, 600, szene, anzahl, mit_kopf, basis=basis)
    d = ImageDraw.Draw(img)
    if g():
        sticker(img, rubrik.upper(), (M - 6, 290), winkel=3, fuell=WEISS, schrift=NAVY)
    groesse = 300
    fe = font("h800", 64)
    while groesse > 140 and d.textlength(zahl, font=font("h800", groesse)) > W - M - R:
        groesse -= 10
    fz = font("h800", groesse)
    zw = d.textlength(zahl, font=fz)
    daneben = zw + 20 + d.textlength(einheit, font=fe) <= W - M - R
    y_zahl = 370 + (300 - groesse) // 2
    if g():
        ImageDraw.Draw(img).text((M - 12, y_zahl), zahl, font=fz, fill=ORANGE)
    y = 720 if daneben else 760
    if g():
        d = ImageDraw.Draw(img)
        if daneben:
            d.text((M + zw + 20, y_zahl + int(groesse * 0.67)), einheit, font=fe, fill=WEISS)
        else:
            d.text((M, y_zahl + int(groesse * 1.0)), einheit, font=fe, fill=WEISS)
        for z in wrap(d, label, font("h800", 56), W - M - R):
            d.text((M, y), z, font=font("h800", 56), fill=WEISS)
            y += 64
    else:
        y += 64 * len(wrap(d, label, font("h800", 56), W - M - R))
    y += 40
    maxwert = max([b[1] for b in balken] or [1])
    breite = W - M - R - 290                    # Werte enden vor Instagrams Knopfleiste rechts
    for eintrag in balken:
        text, wert, hervor = eintrag[:3]
        anzeige = eintrag[3] if len(eintrag) > 3 else (f"{wert:,.0f}".replace(",", ".") if wert >= 1000
                                                        else f"{wert:g}".replace(".", ","))
        if g():
            d = ImageDraw.Draw(img)
            d.text((M, y), text, font=font("t700", 34), fill=WEISS if hervor else HELL)
            lang = max(14, int(breite * wert / maxwert))
            d.rounded_rectangle([M, y + 48, M + breite, y + 78], radius=15, fill=(40, 58, 92))
            d.rounded_rectangle([M, y + 48, M + lang, y + 78], radius=15, fill=ORANGE if hervor else (196, 205, 222))
            d.text((M + breite + 24, y + 40), anzeige, font=font("h800", 40), fill=WEISS)
        y += 118
    if g():
        d = ImageDraw.Draw(img)
        for i, z in enumerate(wrap(d, quelle, font("t400", 26), W - M - R)):
            d.text((M, y + 10 + i * 34), z, font=font("t400", 26), fill=PFIRSICH)
    return img


def folie_ende(kat, titel_zeilen, markiert, zusatz, szene, anzahl=5, bis=99, mit_kopf=True, nur=None, basis="grund"):
    g = Stufe(bis, nur)
    img = _start(kat, 900, szene, anzahl, mit_kopf, variante="unten", basis=basis, logo=False)
    if g():
        icon_lesezeichen(ImageDraw.Draw(img), M, 320, 80, 110, ORANGE)
    f = font("h800", 104)
    y = 480
    if g():
        y = marker_text(ImageDraw.Draw(img), (M, y), titel_zeilen, f, markiert)
    else:
        y += int(f.size * 1.04) * len(titel_zeilen)
    if g():
        ImageDraw.Draw(img).text((M, y + 30), zusatz, font=font("t400", 42), fill=HELL)
    y += 150
    if g():
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
        lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
        img.alpha_composite(lg, (M - 10, y + 236))
        gesperrt(ImageDraw.Draw(img), (M + lg.width + 30, y + 266), "DIREKTVERMITTLUNG", font("h600", 22), PFIRSICH, 3)
    return img


def folie_formulierung(kat, ueberschrift, frage, antwort, tipp, szene, anzahl=5, bis=99, mit_kopf=True, nur=None, basis="grund"):
    """'So sagst du's': Chatverlauf Recruiter/Kandidat als Formulierungshilfe."""
    g = Stufe(bis, nur)
    img = _start(kat, 600, szene, anzahl, mit_kopf, basis=basis)
    d = ImageDraw.Draw(img)
    if g():
        sticker(img, "SO SAGST DU'S", (M - 6, 290), winkel=-3)
    fh = font("h800", 72)
    zeilen = wrap(d, ueberschrift, fh, W - M - R)
    if g():
        marker_text(ImageDraw.Draw(img), (M, 420), zeilen, fh, set())
    y = 420 + int(fh.size * 1.04) * len(zeilen) + 40
    # Höhen vorab berechnen, damit spätere Bausteine an der richtigen Stelle stehen
    probe = Image.new("RGBA", (W, H))
    y_frage = y
    y2 = sprechblase(probe, frage, (M, y + 40), W - M - R - 120, eigen=False)
    y3 = sprechblase(probe, antwort, (M + 60, y2 + 40), W - M - R - 60, eigen=True)
    if g():
        d = ImageDraw.Draw(img)
        gesperrt(d, (M, y_frage), "RECRUITER", font("h700", 22), PFIRSICH, 3)
        sprechblase(img, frage, (M, y_frage + 40), W - M - R - 120, eigen=False)
    if g():
        d = ImageDraw.Draw(img)
        gesperrt(d, (W - R - gesperrt_breite(d, "DU", font("h700", 22), 3), y2), "DU", font("h700", 22), PFIRSICH, 3)
        sprechblase(img, antwort, (M + 60, y2 + 40), W - M - R - 60, eigen=True)
    if g():
        caption_box(img, tipp, (M, y3 + 10), groesse=34)
    return img
