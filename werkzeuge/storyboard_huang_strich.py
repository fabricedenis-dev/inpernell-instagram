#!/usr/bin/env python3
"""Storyboard „Jensen nach 11 Tagen zurück“ im Strichmännchen-Meme-Stil (wie @cartoonslustig):
gemalte Hintergründe (lokale Bild-KI) + Vektor-Strichfiguren (werkzeuge/strichmann.py). Privater Account, Satire.
Aufruf: python werkzeuge/storyboard_huang_strich.py <ordner mit bg_buero.png, bg_wohnzimmer.png>"""
import os
import sys

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import flat_cartoon as fc  # noqa: E402
import strichmann as sm  # noqa: E402
from bild import font, wrap  # noqa: E402

W, H = 1080, 1920
ORDNER = sys.argv[1] if len(sys.argv) > 1 else "."
HOODIE = {**sm.JENSEN, "oberteil": "hoodie", "farbe": (130, 130, 138)}


def hg(name, oben=0.0):
    im = Image.open(os.path.join(ORDNER, name + ".png")).convert("RGB")
    im = im.crop((0, int(im.height * oben), im.width, im.height))
    return im.resize((W, H), Image.LANCZOS)


def satire(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([W - 210, 1440, W - 40, 1490], radius=12, fill=(226, 60, 60))
    d.text((W - 125, 1465), "SATIRE", font=font("h800", 28), fill=(255, 255, 255), anchor="mm")


def hud(img, zeilen, y=470):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([250, y, 830, y + 60 + 70 * (len(zeilen) - 1)], radius=16, fill=(10, 12, 24),
                        outline=(90, 200, 255), width=5)
    for i, (t, c) in enumerate(zeilen):
        d.text((540, y + 30 + i * 70), t, font=font("h800", 46), fill=c, anchor="mm")


def buero(chef, jensen, oben=None, b_chef=None, b_jensen=None):
    img = hg("bg_buero")
    sm.figur(img, 290, 1790, groesse=1.2, **sm.CHEF, **chef)
    sm.figur(img, 790, 1790, groesse=1.2, spiegeln=True, **sm.JENSEN, **jensen)
    y = fc.text_oben(img, oben) + 30 if oben else 200
    if b_chef:
        fc.blase(img, b_chef, 40, y, w=600)
        y += 170 if len(b_chef) > 22 else 130
    if b_jensen:
        fc.blase(img, b_jensen, 420, y, w=620, rechts=True)
    satire(img)
    return img


def sofa(jensen, zeilen):
    img = hg("bg_wohnzimmer", oben=0.04)
    sm.figur(img, 540, 1860, groesse=1.2, bein="sitzen", **HOODIE, **jensen)
    fc.text_oben(img, "Was er wirklich gemacht hat:")
    hud(img, zeilen)
    satire(img)
    return img


def main():
    jubel = dict(arm_l=(140, 160), arm_r=(140, 160), faust=(True, True))
    panels = [
        (buero(dict(mund="laecheln", brauen=(-6, 6), arm_l=(40, 60), arm_r=(40, 60)),
               dict(mund="lachen", brauen=(-10, 10), **jubel),
               "POV: Jensen nach 11 Tagen Pause zurück bei Nvidia", "Willkommen zurück! Was hast du gemacht?"),
         "0–3 s", "Chef begrüßt ihn, Jensen jubelt."),
        (buero(dict(mund="neutral", brauen=(-8, 10), blick=(1, 0)),
               dict(augen="zu", mund="laecheln", brauen=(-12, 4), arm_l=(10, -40), arm_r=(10, -40)),
               None, None, "Reflektiert. An mir gearbeitet. Viel nachgedacht."),
         "3–6 s", "Jensen ganz seriös, Augen zu."),
        (sofa(dict(augen="gross", brauen=(14, 0), mund="zaehne", arm_l=(20, -40), arm_r=(20, -40),
                   halt="controller"), [("GTA VI", (255, 200, 60)), ("Tag 1", (255, 255, 255))]),
         "6–8 s", "Plattenkratzer. Nachts auf dem Sofa mit Controller."),
        (sofa(dict(mund="lachen", brauen=(-12, 10), **jubel),
              [("Tag 11", (255, 255, 255)), ("100 % abgeschlossen", (120, 230, 120))]),
         "8–10 s", "Tag 11: alles durchgespielt, Jensen jubelt. Siegessound."),
        (buero(dict(mund="skeptisch", brauen=(10, 4), blick=(1, 0)),
               dict(augen="genervt", mund="grinsen", brauen=(-6, 0), arm_l=(15, 5), arm_r=(60, 150), faust=(False, True)),
               None, "Und? Hast du was gelernt?", "Ja. Fluchtwagen fahren ist auch Führungserfahrung."),
         "10–14 s", "Pointe, Jensen völlig selbstsicher."),
        (buero(dict(augen="gross", mund="schock", brauen=(-14, 22), arm_l=(5, 0), arm_r=(5, 0)),
               dict(augen="genervt", mund="grinsen", brauen=(-6, 0)), None, "Okay. Du bist eingestellt."),
         "14–16 s", "Chef geschockt, Boom, Zoom auf Jensens Grinsen."),
    ]
    tw, th = 300, 533
    B = 60 + len(panels) * tw + (len(panels) - 1) * 24 + 60
    blatt = Image.new("RGB", (B, 900), (245, 247, 251))
    d = ImageDraw.Draw(blatt)
    d.text((60, 36), "STORYBOARD: JENSEN NACH 11 TAGEN ZURÜCK (STRICHMÄNNCHEN-MEME-STIL)", font=font("h800", 44),
           fill=(20, 30, 60))
    d.text((60, 98), "Privater Account · Satire · ca. 16 s · Hintergründe lokale Bild-KI, Figuren als Vektor, kostenlos",
           font=font("t400", 26), fill=(90, 100, 120))
    for i, (img, zeit, txt) in enumerate(panels):
        x = 60 + i * (tw + 24)
        img.save(os.path.join(ORDNER, f"strich_{i + 1}.png"))
        blatt.paste(img.resize((tw, th), Image.LANCZOS), (x, 160))
        d.rectangle([x, 160, x + tw, 160 + th], outline=(200, 206, 218), width=2)
        d.text((x, 710), zeit, font=font("h800", 26), fill=(237, 109, 5))
        for k, z in enumerate(wrap(d, txt, font("t400", 22), tw)[:4]):
            d.text((x, 748 + k * 28), z, font=font("t400", 22), fill=(20, 30, 60))
    ziel = os.path.join(HIER, "vorschau", "memes", "storyboard_huang_strich.jpg")
    blatt.save(ziel, quality=90)
    print(ziel)


if __name__ == "__main__":
    main()
