#!/usr/bin/env python3
"""Strichmännchen-Figuren im Stil beliebter Meme-Cartoons: großer ovaler Kopf, große Augen, dicke Augenbrauen,
dicke schwarze Strich-Arme und -Beine, kleiner farbiger Oberkörper, flache Farben mit kräftiger Kontur.
Alles als Vektor gezeichnet (2-fach überabgetastet), dadurch scharf und frei animierbar (Winkel je Gelenk).

figur(img, x, y_fuss, **merkmale) zeichnet direkt auf ein RGBA- oder RGB-Bild (1080 × 1920).
"""
import math

from PIL import Image, ImageDraw

SS = 2  # Überabtastung
SCHWARZ = (20, 20, 24)
HAND = (70, 70, 76)


def _rot(px, py, w):
    w = math.radians(w)
    return px * math.cos(w) - py * math.sin(w), px * math.sin(w) + py * math.cos(w)


class _Stift:
    def __init__(self, d, ox, oy, s, spiegel=1):
        self.d, self.ox, self.oy, self.s, self.m = d, ox, oy, s, spiegel

    def p(self, x, y):
        return ((self.ox + self.m * x * self.s) * SS, (self.oy + y * self.s) * SS)

    def w(self, b):
        return max(1, int(b * self.s * SS))

    def linie(self, pts, b=10, f=SCHWARZ):
        q = [self.p(*a) for a in pts]
        self.d.line(q, fill=f, width=self.w(b), joint="curve")
        r = self.w(b) / 2
        for x, y in (q[0], q[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=f)

    def poly(self, pts, f, rand=SCHWARZ, b=6):
        q = [self.p(*a) for a in pts]
        self.d.polygon(q, fill=f)
        if rand:
            self.d.line(q + [q[0]], fill=rand, width=self.w(b), joint="curve")

    def ellipse(self, cx, cy, rx, ry, f, rand=SCHWARZ, b=6):
        (x1, y1), (x2, y2) = self.p(cx - rx, cy - ry), self.p(cx + rx, cy + ry)
        x1, x2 = min(x1, x2), max(x1, x2)
        self.d.ellipse([x1, y1, x2, y2], fill=f, outline=rand, width=self.w(b) if rand else 0)

    def bogen(self, cx, cy, rx, ry, a0, a1, b=6, f=SCHWARZ, n=24):
        pts = []
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
        self.linie(pts, b, f)


def _glied(st, x0, y0, w1, w2, l1, l2, b=11):
    """Arm/Bein aus zwei Segmenten; Winkel in Grad, 0 = nach unten, positiv = nach außen (vom Körper weg)."""
    x1 = x0 + l1 * math.sin(math.radians(w1))
    y1 = y0 + l1 * math.cos(math.radians(w1))
    x2 = x1 + l2 * math.sin(math.radians(w2))
    y2 = y1 + l2 * math.cos(math.radians(w2))
    st.linie([(x0, y0), (x1, y1), (x2, y2)], b)
    return x2, y2, w2


def _hand(st, x, y, w, faust=False):
    if faust:
        st.ellipse(x, y, 24, 22, HAND, b=4)
        return
    dx, dy = math.sin(math.radians(w)), math.cos(math.radians(w))
    st.ellipse(x + dx * 10, y + dy * 10, 22, 22, HAND, b=4)
    for k in (-1, 0, 1):
        a = math.radians(w + k * 28)
        st.linie([(x + dx * 18, y + dy * 18), (x + dx * 18 + 22 * math.sin(a), y + dy * 18 + 22 * math.cos(a))], 9, HAND)


def _gesicht(st, hy, haut, augen, brauen, mund, blick, brille):
    ex, ey = 48, hy - 8
    for sx in (-1, 1):
        x = sx * ex
        if augen == "zu":
            st.bogen(x, ey + 4, 26, 14, 20, 160, b=7)
        elif augen == "punkt":
            st.ellipse(x, ey, 11, 15, SCHWARZ, None)
        else:
            ry = 34 if augen == "gross" else 30
            st.ellipse(x, ey, 26, ry, (255, 255, 255), b=6)
            st.ellipse(x + blick[0] * 9, ey + 6 + blick[1] * 8, 9 if augen != "gross" else 7,
                       11 if augen != "gross" else 8, SCHWARZ, None)
            if augen == "genervt":
                st.poly([(x - 30, ey - 34), (x + 30, ey - 34), (x + 30, ey - 2), (x - 30, ey - 2)], haut, None)
                st.linie([(x - 26, ey - 2), (x + 26, ey - 2)], 7)
        # Augenbrauen: (Winkel, Höhe) – positiver Winkel = innen tiefer (böse)
        if brauen:
            wi, hoch = brauen
            y0 = ey - 48 - hoch
            st.linie([(x - sx * 26, y0 + wi * 0.4), (x + sx * 28, y0 - wi * 0.4)], 11)
    if brille:
        for sx in (-1, 1):
            x = sx * ex
            st.poly([(x - 40, ey - 32), (x + 40, ey - 32), (x + 38, ey + 28), (x - 38, ey + 28)], None, SCHWARZ, 9)
        st.linie([(-8, ey - 14), (8, ey - 14)], 8)
        st.linie([(-ex - 40, ey - 24), (-132, ey - 30)], 8)
        st.linie([(ex + 40, ey - 24), (132, ey - 30)], 8)
    my = hy + 62
    if mund == "neutral":
        st.linie([(-18, my), (18, my)], 7)
    elif mund == "laecheln":
        st.bogen(0, my - 14, 30, 18, 20, 160, b=7)
    elif mund == "grinsen":
        st.linie([(-34, my - 2), (-8, my + 8), (20, my + 2), (40, my - 16)], 7)
    elif mund == "skeptisch":
        st.linie([(-24, my + 6), (0, my + 2), (26, my - 6)], 7)
    elif mund in ("offen", "lachen"):
        st.poly([(-40, my - 14), (40, my - 14), (26, my + 26), (0, my + 34), (-26, my + 26)], (120, 30, 40), b=6)
        st.poly([(-34, my - 12), (34, my - 12), (30, my - 2), (-30, my - 2)], (255, 255, 255), None)
        st.ellipse(0, my + 22, 16, 8, (230, 90, 100), None)
    elif mund == "zaehne":
        st.poly([(-40, my - 16), (40, my - 16), (36, my + 16), (-36, my + 16)], (255, 255, 255), b=6)
        st.linie([(-38, my), (38, my)], 4)
        for k in (-20, 0, 20):
            st.linie([(k, my - 14), (k, my + 14)], 4)
    elif mund == "schock":
        st.ellipse(0, my + 8, 20, 30, (120, 30, 40), b=6)


def figur(img, x, y_fuss, groesse=1.0, spiegeln=False,
          haut=(236, 236, 236), haar=None, haar_farbe=(178, 180, 188), brille=False,
          oberteil="tshirt", farbe=(60, 160, 90),
          augen="normal", brauen=(0, 0), mund="neutral", blick=(0, 0),
          arm_l=(15, 5), arm_r=(15, 5), faust=(False, False), bein="stehen", kopf_neigung=0,
          halt=None, ruecken=False):
    """arm_l/arm_r: (Oberarm-, Unterarm-Winkel) in Grad, 0 = hängt, 90 = waagerecht nach außen, 170 = hoch.
    bein: 'stehen' | 'sitzen'. halt: 'controller' für Gamepad in beiden Händen."""
    w, h = img.size
    ebene = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(ebene)
    st = _Stift(d, x, y_fuss, groesse, -1 if spiegeln else 1)

    sitz = bein == "sitzen"
    huefte = -230 if sitz else -380
    t_oben = huefte - 290
    # Beine
    for sx in (-1, 1):
        if sitz:
            st.linie([(sx * 40, huefte), (sx * 70, huefte + 40), (sx * 74, -10), (sx * 74 + sx * 26, 0)], 11)
        else:
            st.linie([(sx * 34, huefte), (sx * 40, -4), (sx * 40 + sx * 30, 0)], 11)
    # Arme hinter dem Oberkörper beginnen
    sch_y = t_oben + 34
    hand = []
    for sx, (w1, w2), fa in ((-1, arm_l, faust[0]), (1, arm_r, faust[1])):
        xh, yh, wh = _glied(st, sx * 70, sch_y, sx * w1, sx * w2, 150, 140)
        hand.append((xh, yh, wh, fa))
    # Oberkörper
    tb, ub = 78, 96
    rumpf = [(-tb, t_oben + 20), (-tb + 20, t_oben), (tb - 20, t_oben), (tb, t_oben + 20), (ub, huefte), (-ub, huefte)]
    if oberteil == "lederjacke":
        st.poly(rumpf, (34, 34, 38), (10, 10, 12), 7)
        st.poly([(-26, t_oben + 4), (26, t_oben + 4), (14, t_oben + 120), (-14, t_oben + 120)], (14, 14, 16), None)
        for sx in (-1, 1):
            st.poly([(sx * 26, t_oben + 2), (sx * 66, t_oben + 6), (sx * 34, t_oben + 110)], (58, 58, 64),
                    (10, 10, 12), 4)
            st.linie([(sx * 56, t_oben + 150), (sx * 82, huefte - 60)], 3, (80, 80, 88))
        st.linie([(12, t_oben + 120), (16, huefte - 4)], 4, (110, 110, 118))
        st.linie([(-ub + 6, huefte - 24), (ub - 6, huefte - 24)], 4, (70, 70, 78))
    elif oberteil == "anzug":
        st.poly(rumpf, farbe, SCHWARZ, 7)
        st.poly([(-30, t_oben + 2), (30, t_oben + 2), (0, t_oben + 130)], (255, 255, 255), None)
        st.poly([(-9, t_oben + 14), (9, t_oben + 14), (12, t_oben + 160), (0, t_oben + 182), (-12, t_oben + 160)],
                (200, 40, 40), SCHWARZ, 3)
        for sx in (-1, 1):
            st.linie([(sx * 30, t_oben + 2), (sx * 4, t_oben + 170)], 5, tuple(max(0, c - 50) for c in farbe))
    elif oberteil == "hoodie":
        st.poly(rumpf, farbe, SCHWARZ, 7)
        dunkel = tuple(max(0, c - 40) for c in farbe)
        if ruecken:
            st.poly([(-70, t_oben + 4), (70, t_oben + 4), (54, t_oben + 110), (0, t_oben + 140), (-54, t_oben + 110)],
                    dunkel, SCHWARZ, 5)
        else:
            st.bogen(0, t_oben + 6, 52, 30, 0, 180, b=5, f=dunkel)
        for sx in (() if ruecken else (-1, 1)):
            st.linie([(sx * 14, t_oben + 30), (sx * 16, t_oben + 110)], 4, (240, 240, 240))
        if not ruecken:
            st.poly([(-52, huefte - 90), (52, huefte - 90), (60, huefte - 20), (-60, huefte - 20)], None, dunkel, 4)
    else:
        st.poly(rumpf, farbe, SCHWARZ, 7)
    # Hände
    if ruecken and halt == "controller":
        pass
    elif halt == "controller":
        cx, cy = 0, t_oben + 200
        st.poly([(-70, cy - 22), (70, cy - 22), (84, cy + 26), (40, cy + 30), (0, cy + 12), (-40, cy + 30),
                 (-84, cy + 26)], (45, 45, 52), SCHWARZ, 5)
        st.ellipse(-40, cy, 9, 9, (110, 110, 120), None)
        for k, f in ((30, (80, 200, 120)), (48, (220, 80, 80))):
            st.ellipse(k, cy - 4 + (k - 30) / 3, 7, 7, f, None)
        for sx in (-1, 1):
            st.ellipse(sx * 74, cy + 8, 24, 22, HAND, b=4)
    else:
        for xh, yh, wh, fa in hand:
            _hand(st, xh, yh, wh, fa)
    # Kopf
    hy = t_oben - 130
    if haar == "lang" and not ruecken:                     # lange Haare hinter dem Kopf
        st.poly([(-150, hy - 60), (-120, hy - 160), (0, hy - 196), (120, hy - 160), (150, hy - 60), (168, hy + 150),
                 (110, hy + 190), (-110, hy + 190), (-168, hy + 150)], haar_farbe, SCHWARZ, 7)
    st.ellipse(0, hy, 132, 152, haut, b=7)
    if haar == "lang" and not ruecken:                     # Pony
        st.poly([(-136, hy - 20), (-130, hy - 100), (-80, hy - 150), (0, hy - 160), (80, hy - 150), (130, hy - 100),
                 (136, hy - 20), (110, hy - 70), (60, hy - 100), (10, hy - 112), (-10, hy - 80), (-60, hy - 96),
                 (-110, hy - 66)], haar_farbe, SCHWARZ, 6)
    if haar == "jensen":
        # voluminöse, nach hinten gekämmte graue Tolle
        st.poly([(-134, hy - 6), (-136, hy - 70), (-112, hy - 150), (-60, hy - 200), (10, hy - 222), (80, hy - 212),
                 (126, hy - 172), (142, hy - 100), (136, hy - 30), (120, hy - 60), (104, hy - 104), (60, hy - 124),
                 (0, hy - 128), (-60, hy - 116), (-104, hy - 80), (-116, hy - 10)], haar_farbe, SCHWARZ, 7)
        for pts in (((-100, hy - 120), (-50, hy - 170), (20, hy - 196)),
                    ((-60, hy - 126), (0, hy - 166), (80, hy - 180)),
                    ((-10, hy - 132), (60, hy - 150), (112, hy - 128))):
            st.linie(list(pts), 5, (120, 122, 130))
    elif haar == "kurz":
        # kurze, strubbelige Haare mit Stirnfransen (junger Bewerber)
        st.poly([(-136, hy - 20), (-140, hy - 90), (-110, hy - 146), (-60, hy - 170), (-40, hy - 198), (-6, hy - 172),
                 (30, hy - 204), (52, hy - 168), (96, hy - 176), (100, hy - 140), (134, hy - 120), (140, hy - 40),
                 (124, hy - 60), (110, hy - 96), (70, hy - 92), (40, hy - 110), (10, hy - 86), (-30, hy - 108),
                 (-70, hy - 90), (-110, hy - 90), (-120, hy - 30)], haar_farbe, SCHWARZ, 7)
    elif haar == "glatze":
        st.bogen(-60, hy - 60, 30, 26, 200, 260, b=5, f=(255, 255, 255))
    if ruecken:
        st.poly([(-134, hy + 30), (-138, hy - 70), (-110, hy - 150), (-50, hy - 196), (20, hy - 210), (90, hy - 190),
                 (132, hy - 130), (140, hy - 40), (134, hy + 50), (96, hy + 116), (0, hy + 140), (-96, hy + 116), (-134, hy + 50)],
                haar_farbe, SCHWARZ, 7)
        for k in (-70, -25, 20, 65):
            st.linie([(k * 0.8, hy - 190), (k, hy - 60), (k * 0.9, hy + 70)], 5, (120, 122, 130))
        if brille:
            st.linie([(-134, hy - 20), (-112, hy - 14)], 8)
            st.linie([(134, hy - 20), (112, hy - 14)], 8)
    else:
        _gesicht(st, hy, haut, augen, brauen, mund, blick, brille)
    if halt == "handy":                                     # Handy am Ohr (rechte Seite)
        st.poly([(132, hy - 70), (176, hy - 74), (182, hy + 40), (138, hy + 44)], (30, 30, 36), SCHWARZ, 5)
        st.ellipse(180, hy - 6, 24, 26, HAND, b=4)

    klein = ebene.resize((w, h), Image.LANCZOS)
    if img.mode == "RGBA":
        img.alpha_composite(klein)
    else:
        img.paste(klein, (0, 0), klein)
    return img


JENSEN = dict(haut=(240, 214, 184), haar="jensen", brille=True, oberteil="lederjacke")
BEWERBER = dict(haut=(240, 214, 184), haar="kurz", haar_farbe=(120, 78, 40), oberteil="hoodie", farbe=(60, 160, 90))
OPA = dict(haut=(236, 214, 190), haar="glatze", brille=True, oberteil="tshirt", farbe=(140, 100, 60))
KUMPEL = dict(haut=(236, 236, 236), haar="kurz", haar_farbe=(40, 40, 44), oberteil="tshirt", farbe=(60, 110, 200))
PERSONALERIN = dict(haut=(244, 220, 196), haar="lang", haar_farbe=(200, 150, 70), oberteil="tshirt",
                    farbe=(200, 70, 110))
PERSONALER = dict(haut=(236, 236, 236), haar="glatze", oberteil="anzug", farbe=(90, 92, 100))
CHEF = dict(haut=(236, 236, 236), haar="glatze", oberteil="anzug", farbe=(40, 70, 150))
