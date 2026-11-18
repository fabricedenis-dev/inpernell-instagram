"""Miami-Figuren: Gesichtszüge aus den Fotos (Poster-Stil), Körper gezeichnet im 80er-Miami-Look.
Erzeugt assets/team/<name>_figur.png (transparent). Aufruf: python werkzeuge/figuren.py <ordner mit *_frei.png>"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from poster import STUFEN
import cv2

TINTE = (20, 6, 36)
HAUT, HAUT_S = (255, 150, 100), (232, 92, 104)
# Kinnlinie je Foto (600 x 600): unterhalb wird abgeschnitten, nur Kopf und Gesicht bleiben
KINN = {"fabrice": [(150, 330), (205, 425), (300, 478), (405, 420), (455, 330)],
        "pascal": [(150, 330), (200, 395), (270, 448), (335, 482), (398, 432), (440, 318)],
        "waldemar": [(150, 330), (200, 420), (295, 475), (395, 430), (460, 330)]}


def poster_bild(rgba):
    arr = np.array(rgba); maske = (arr[..., 3] > 128).astype(np.uint8); rgb = arr[..., :3].copy()
    for _ in range(5): rgb = cv2.bilateralFilter(rgb, 9, 45, 9)
    l = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32) / 255
    w = l[maske > 0]; lo, hi = np.percentile(w, 3), np.percentile(w, 97)
    l = np.clip((l - lo) / max(1e-3, hi - lo), 0, 1)
    l = cv2.medianBlur((l * 255).astype(np.uint8), 7).astype(np.float32) / 255
    out = np.zeros_like(rgb); u = 0
    for g, f in STUFEN: out[(l >= u) & (l < g)] = f; u = g
    grau = cv2.medianBlur(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), 5)
    lin = cv2.adaptiveThreshold(grau, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 13, 7)
    out[(lin == 0) & (maske > 0)] = (24, 6, 40)
    return out, maske


def kopf(pfad, name):
    p = Image.open(pfad).convert("RGBA").resize((600, 600))
    out, maske = poster_bild(p)
    kinn = KINN[name]; xs = [x for x, _ in kinn]; ys = [y for _, y in kinn]
    grenze = np.interp(np.arange(600), xs, ys, left=ys[0], right=ys[-1])
    yy = np.arange(600)[:, None]
    m = (maske > 0) & (yy < grenze[None, :])
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    kontur = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    erg = np.zeros((600, 600, 4), np.uint8)
    erg[kontur > 0] = TINTE + (255,)
    erg[m > 0, :3] = out[m > 0]; erg[m > 0, 3] = 255
    img = Image.fromarray(erg, "RGBA")
    return img.crop(img.getbbox()), max(ys) - min(y for y in range(600) if m[y].any())


def poly(d, pts, fill, w=8):
    d.polygon(pts, fill=fill, outline=TINTE, width=w)


def beine(d, cx, hose, schatten, schuh):
    poly(d, [(cx - 170, 1080), (cx - 5, 1080), (cx - 30, 1560), (cx - 55, 2050), (cx - 150, 2050), (cx - 165, 1560)], hose)
    poly(d, [(cx - 60, 1100), (cx - 5, 1080), (cx - 30, 1560), (cx - 55, 2050), (cx - 80, 2050), (cx - 70, 1560)], schatten, 0)
    poly(d, [(cx + 5, 1080), (cx + 170, 1080), (cx + 185, 1560), (cx + 215, 2050), (cx + 120, 2050), (cx + 40, 1560)], hose)
    poly(d, [(cx + 115, 1100), (cx + 170, 1080), (cx + 185, 1560), (cx + 215, 2050), (cx + 175, 2050), (cx + 140, 1560)], schatten, 0)
    for x0, x1 in ((cx - 185, cx - 40), (cx + 100, cx + 250)):
        d.rounded_rectangle([x0, 2040, x1, 2110], radius=30, fill=schuh, outline=TINTE, width=8)


def hals(d, cx):
    poly(d, [(cx - 62, 400), (cx + 62, 400), (cx + 72, 500), (cx - 72, 500)], HAUT)
    poly(d, [(cx - 62, 400), (cx + 62, 400), (cx + 50, 440), (cx - 50, 440)], HAUT_S, 0)


def sakko_figur(cx, sakko, sakko_s, shirt, shirt_s, hose, hose_s, schuh):
    img = Image.new("RGBA", (1000, 2160), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    beine(d, cx, hose, hose_s, schuh)
    poly(d, [(cx - 175, 470), (cx + 175, 470), (cx + 165, 1090), (cx - 165, 1090)], shirt)
    poly(d, [(cx + 60, 470), (cx + 175, 470), (cx + 165, 1090), (cx + 90, 1090)], shirt_s, 0)
    hals(d, cx)
    for s in (-1, 1):                                       # Sakko-Hälften mit Revers
        x = lambda v: cx + s * v
        poly(d, [(x(70), 450), (x(215), 470), (x(280), 520), (x(275), 720), (x(215), 930), (x(235), 1150), (x(35), 1165), (x(20), 930), (x(115), 560)], sakko)
        poly(d, [(x(70), 455), (x(150), 545), (x(70), 820), (x(20), 930), (x(115), 560)], sakko_s)
        d.line([(x(150), 1000), (x(240), 990)], fill=TINTE, width=6)          # Tasche
    for s in (-1, 1):                                       # Arme, Hände in den Hosentaschen
        x = lambda v: cx + s * v
        poly(d, [(x(280), 520), (x(318), 640), (x(312), 780), (x(290), 1040), (x(222), 1050), (x(236), 780), (x(222), 600)], sakko)
        poly(d, [(x(225), 770), (x(255), 770), (x(250), 1045), (x(225), 1050)], sakko_s, 0)
        poly(d, [(x(300), 960), (x(325), 1000), (x(222), 1010), (x(225), 965)], sakko_s)       # hochgeschobener Ärmel
        poly(d, [(x(305), 1005), (x(300), 1090), (x(230), 1095), (x(225), 1010)], HAUT)         # Unterarm
        d.arc([x(300) - 40 if s > 0 else x(300) - 40, 1070, x(300) + 40, 1130], 180, 360, fill=TINTE, width=7)
    return img


def hemd_figur(cx, hemd, muster, hose, hose_s, schuh):
    img = Image.new("RGBA", (1000, 2160), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    beine(d, cx, hose, hose_s, schuh)
    hals(d, cx)
    rumpf = [(cx - 240, 500), (cx - 70, 455), (cx, 600), (cx + 70, 455), (cx + 240, 500), (cx + 265, 560), (cx + 205, 760), (cx + 215, 1110), (cx - 215, 1110), (cx - 205, 760), (cx - 265, 560)]
    poly(d, rumpf, hemd)
    # Palmenmuster (nur innerhalb des Hemds)
    m = Image.new("L", img.size); ImageDraw.Draw(m).polygon(rumpf, fill=255)
    pat = Image.new("RGBA", img.size, (0, 0, 0, 0)); pd = ImageDraw.Draw(pat)
    rnd = np.random.default_rng(3)
    for _ in range(26):
        px, py = cx + rnd.integers(-260, 260), rnd.integers(480, 1110)
        for k in range(5):
            a = k * 1.25 + rnd.random()
            pd.polygon([(px, py), (px + 46 * np.cos(a) - 8 * np.sin(a), py + 46 * np.sin(a) + 8 * np.cos(a)),
                        (px + 60 * np.cos(a), py + 60 * np.sin(a)), (px + 46 * np.cos(a) + 8 * np.sin(a), py + 46 * np.sin(a) - 8 * np.cos(a))],
                       fill=muster[k % len(muster)] + (255,))
    img.paste(pat, (0, 0), Image.composite(pat.getchannel("A"), Image.new("L", img.size), m))
    d = ImageDraw.Draw(img)
    d.polygon(rumpf, outline=TINTE, width=8)
    poly(d, [(cx - 68, 458), (cx, 600), (cx + 68, 458), (cx + 45, 455), (cx, 560), (cx - 45, 455)], HAUT, 4)   # offener Kragen
    for s in (-1, 1):
        x = lambda v: cx + s * v
        poly(d, [(x(70), 455), (x(130), 470), (x(20), 640), (x(5), 600)], hemd)                                  # Kragen
        poly(d, [(x(255), 495), (x(325), 700), (x(250), 735), (x(205), 560)], hemd)                               # Kurzarm
        poly(d, [(x(318), 720), (x(310), 1090), (x(240), 1095), (x(250), 735)], HAUT)                             # Arm
        poly(d, [(x(250), 735), (x(270), 735), (x(262), 1092), (x(240), 1095)], HAUT_S, 0)
        d.arc([x(278) - 40, 1070, x(278) + 40, 1130], 180, 360, fill=TINTE, width=7)
    d.rounded_rectangle([cx - 318, 990, cx - 238, 1030], radius=8, fill=(240, 200, 90), outline=TINTE, width=6)    # Uhr
    # Pilotenbrille am Hemd
    for ox in (-42, 42):
        d.ellipse([cx + 90 + ox - 34, 640, cx + 90 + ox + 34, 690], fill=(40, 30, 70), outline=(240, 200, 90), width=5)
    d.line([(cx + 82, 652), (cx + 98, 652)], fill=(240, 200, 90), width=5)
    return img


def figur(name, kopfbild, koerper, kinn_y=430, kopfbreite=320):
    s = kopfbreite / kopfbild.width
    k = kopfbild.resize((kopfbreite, int(kopfbild.height * s)), Image.LANCZOS)
    erg = koerper.copy()
    erg.alpha_composite(k, (500 - k.width // 2 + (10 if name == "pascal" else 0), kinn_y - k.height + 40))
    return erg


def sonnenbrille_oben(img, cx, y):
    d = ImageDraw.Draw(img)
    for ox in (-58, 58):
        d.rounded_rectangle([cx + ox - 50, y, cx + ox + 50, y + 44], radius=18, fill=(30, 20, 60), outline=TINTE, width=6)
        d.line([(cx + ox - 30, y + 10), (cx + ox + 10, y + 10)], fill=(120, 230, 240), width=5)
    d.line([(cx - 10, y + 14), (cx + 10, y + 14)], fill=TINTE, width=8)


if __name__ == "__main__":
    web = sys.argv[1]; ziel = os.path.join(os.path.dirname(__file__), "..", "assets", "team")
    k = {n: kopf(os.path.join(web, f"{n}_frei.png"), n)[0] for n in KINN}
    f = figur("fabrice", k["fabrice"], sakko_figur(500, (255, 150, 195), (222, 100, 160), (50, 215, 215), (30, 160, 175),
                                                  (246, 238, 226), (205, 190, 205), (110, 60, 50)))
    p = figur("pascal", k["pascal"], hemd_figur(500, (250, 110, 90), [(40, 220, 200), (255, 210, 80), (30, 150, 120)],
                                               (44, 30, 86), (28, 18, 60), (40, 26, 20)))
    w = figur("waldemar", k["waldemar"], sakko_figur(500, (244, 244, 250), (196, 196, 220), (150, 60, 175), (110, 40, 140),
                                                    (244, 244, 250), (196, 196, 220), (240, 236, 226)))
    sonnenbrille_oben(w, 500, 105)
    for n, img in (("fabrice", f), ("pascal", p), ("waldemar", w)):
        img.crop(img.getbbox()).save(os.path.join(ziel, f"{n}_figur.png"), optimize=True)
    print("ok")
