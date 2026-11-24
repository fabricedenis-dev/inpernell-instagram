#!/usr/bin/env python3
"""Titelbild für das Huang-Meme (privater Account, Satire) in zwei Varianten nebeneinander:
A = Szene im Wohnzimmer mit Inpernell-Kopfband, B = komplett im Inpernell-Stil (Navy/Orange).
Aufruf: python werkzeuge/titelbild_huang.py  ->  vorschau/memes/titelbild_huang.jpg (+ _a.png, _b.png)"""
import os
import sys

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import reel_design as rd  # noqa: E402
import storyboard_huang_strich as sb  # noqa: E402
import strichmann as sm  # noqa: E402
from bild import NAVY, NAVY_HELL, ORANGE, font  # noqa: E402

W, H = 1080, 1920
sb.ORDNER = os.path.join(HIER, "assets", "memes", "huang")
OUT = os.path.join(HIER, "vorschau", "memes")


def ruckel_spiel():
    g = sb.spielbild("spiel_1", "")
    r, gg, bb = g.split()
    g = Image.merge("RGB", (r.transform(g.size, Image.AFFINE, (1, 0, -12, 0, 1, 0)), gg,
                            bb.transform(g.size, Image.AFFINE, (1, 0, 12, 0, 1, 0))))
    for y0 in (120, 260):
        g.paste(g.crop((0, y0, 860, y0 + 30)), (40, y0 + 6))
    d = ImageDraw.Draw(g)
    d.rounded_rectangle([20, 16, 250, 76], radius=12, fill=(0, 0, 0))
    d.text((135, 46), "FPS: 9", font=font("h800", 44), fill=(255, 70, 70), anchor="mm")
    return g


def fernseher(img, y=600):
    d = ImageDraw.Draw(img)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([60, y - 40, 1020, y + 520], radius=60, fill=(255, 80, 80, 70))
    img.alpha_composite(glow)
    d.rounded_rectangle([88, y, 992, y + 530], radius=16, fill=(16, 16, 20), outline=(5, 5, 8), width=8)
    img.paste(ruckel_spiel(), (110, y + 22))


def kopfband(img, transparent=True):
    """Überschrift im Inpernell-Stil: Navy-Band, Archivo, Schlüsselwort orange."""
    d = ImageDraw.Draw(img)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle([40, 250, W - 40, 560], radius=28,
                                         fill=(*NAVY, 235 if transparent else 255), outline=(*ORANGE, 255), width=6)
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    f = font("h800", 84)
    d.text((W // 2, 300), "Wieso Jensen Huang", font=f, fill=(255, 255, 255), anchor="ma")
    w1 = d.textlength("wirklich ", font=f)
    w2 = d.textlength("zurückkam", font=f)
    x0 = W // 2 - (w1 + w2) / 2
    d.text((x0, 400), "wirklich", font=f, fill=ORANGE)
    d.text((x0 + w1, 400), "zurückkam", font=f, fill=(255, 255, 255))
    d.rounded_rectangle([W - 230, 1500 - 70, W - 60, 1500 - 20], radius=12, fill=(226, 60, 60))
    d.text((W - 145, 1455), "SATIRE", font=font("h800", 28), fill=(255, 255, 255), anchor="mm")


def jensen(img, x=540, fuss=1930):
    sm.figur(img, x, fuss, groesse=1.12, **{**sb.HOODIE}, augen="gross", brauen=(18, 0), mund="zaehne",
             arm_l=(20, -40), arm_r=(20, -40), halt="controller")


def variante_a():
    im = Image.open(os.path.join(sb.ORDNER, "bg_wohnzimmer.png")).convert("RGB")
    hh = int(im.height * 0.62)
    bw = int(hh * 9 / 16)
    img = im.crop(((im.width - bw) // 2, int(im.height * 0.03), (im.width + bw) // 2, hh)).resize((W, H), Image.LANCZOS)
    img = img.convert("RGBA")
    fernseher(img, 620)
    jensen(img)
    kopfband(img)
    rd.logo_marke(img)
    return img.convert("RGB")


def variante_b():
    img = Image.new("RGBA", (W, H), (*NAVY, 255))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NAVY_HELL[i] + (NAVY[i] - NAVY_HELL[i]) * t) for i in range(3)))
    for k in range(-H, W, 90):                                          # dezente orange Diagonalen
        d.line([(k, H), (k + H, 0)], fill=(30, 46, 80), width=3)
    fernseher(img, 620)
    jensen(img)
    kopfband(img, transparent=False)
    rd.logo_marke(img)
    return img.convert("RGB")


def main():
    a, b = variante_a(), variante_b()
    a.save(os.path.join(OUT, "titelbild_huang_a.png"))
    b.save(os.path.join(OUT, "titelbild_huang_b.png"))
    blatt = Image.new("RGB", (1200, 1160), (245, 247, 251))
    d = ImageDraw.Draw(blatt)
    for i, (im, name) in enumerate(((a, "A: Szene + Inpernell-Band"), (b, "B: komplett Inpernell-Stil"))):
        x = 40 + i * 580
        blatt.paste(im.resize((540, 960), Image.LANCZOS), (x, 40))
        # Feed-Ausschnitt 3:4 (y 285–1635) als Hilfslinie
        d.rectangle([x, 40 + 285 // 2, x + 540, 40 + 1635 // 2], outline=(237, 109, 5), width=2)
        d.text((x, 1020), name, font=font("h800", 34), fill=(20, 30, 60))
    d.text((40, 1080), "Orange Rahmen = Ausschnitt im Profil-Raster (3:4)", font=font("t400", 26), fill=(90, 100, 120))
    ziel = os.path.join(OUT, "titelbild_huang.jpg")
    blatt.save(ziel, quality=92)
    print(ziel)


if __name__ == "__main__":
    main()
