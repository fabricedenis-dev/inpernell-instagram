#!/usr/bin/env python3
"""Storyboard „Jensen nach 11 Tagen zurück“ mit Bildern der lokalen Bild-KI (privater Account, Satire).
Aufruf: python werkzeuge/storyboard_huang_ki.py <ordner mit KI-Bildern>  ->  vorschau/memes/storyboard_huang_ki.jpg"""
import os
import sys

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import flat_cartoon as fc  # noqa: E402
from bild import font, wrap  # noqa: E402

W, H = 1080, 1920
ORDNER = sys.argv[1] if len(sys.argv) > 1 else "."


def lade(name):
    return Image.open(os.path.join(ORDNER, name + ".png"))


def hg(name):
    return lade(name).convert("RGB").resize((W, H), Image.LANCZOS)


def figur(img, name, x, fuss=1500, hoehe=1050, spiegeln=False):
    f = lade(name).convert("RGBA")
    box = f.getchannel("A").getbbox()
    if box:
        f = f.crop(box)
    s = hoehe / f.height
    f = f.resize((int(f.width * s), hoehe), Image.LANCZOS)
    if spiegeln:
        f = f.transpose(Image.FLIP_LEFT_RIGHT)
    img.paste(f, (int(x - f.width / 2), fuss - hoehe), f)


def satire(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([W - 210, 1440, W - 40, 1490], radius=12, fill=(226, 60, 60))
    d.text((W - 125, 1465), "SATIRE", font=font("h800", 28), fill=(255, 255, 255), anchor="mm")


def buero(chef, huang, oben=None, b_chef=None, b_huang=None):
    img = hg("bg_buero")
    figur(img, chef, 300, hoehe=1000)
    figur(img, huang, 790, hoehe=1060, spiegeln=True)
    y = fc.text_oben(img, oben) + 30 if oben else 240
    if b_chef:
        fc.blase(img, b_chef, 50, y, w=560)
        y += 230
    if b_huang:
        fc.blase(img, b_huang, 440, y, w=590, rechts=True)
    satire(img)
    return img


def sofa(huang, tv, oben):
    img = hg("bg_wohnzimmer")
    figur(img, huang, 540, fuss=1560, hoehe=900)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([250, 560, 830, 760], radius=18, fill=(10, 12, 24), outline=(90, 200, 255), width=6)
    for i, (t, c) in enumerate(tv):
        d.text((540, 600 + i * 70), t, font=font("h800", 52), fill=c, anchor="ma")
    fc.text_oben(img, oben)
    satire(img)
    return img


def main():
    panels = [
        (buero("chef_freundlich", "huang_grinsen", "POV: Jensen nach 11 Tagen Pause zurück bei Nvidia",
               "Willkommen zurück! Was hast du gemacht?"), "0–3 s", "Chef begrüßt ihn, Jensen grinst."),
        (buero("chef_fragend", "huang_ernst", None, None, "Reflektiert. An mir gearbeitet. Viel nachgedacht."),
         "3–6 s", "Jensen ganz seriös, nachdenklich."),
        (sofa("huang_sofa", [("GTA VI", (255, 200, 60)), ("Tag 1", (255, 255, 255))], "Was er wirklich gemacht hat:"),
         "6–8 s", "Plattenkratzer. Nachts mit Controller."),
        (sofa("huang_sofa", [("Tag 11", (255, 255, 255)), ("100 % abgeschlossen", (120, 230, 120))],
              "Was er wirklich gemacht hat:"), "8–10 s", "Tag 11, alles durchgespielt. Siegessound."),
        (buero("chef_fragend", "huang_grinsen", None, "Und? Hast du was gelernt?",
               "Ja. Fluchtwagen fahren ist auch Führungserfahrung."), "10–14 s", "Pointe."),
        (buero("chef_schock", "huang_grinsen", None, "Okay. Du bist eingestellt."), "14–16 s",
         "Chef geschockt, Boom, Zoom auf Jensens Grinsen."),
    ]
    tw, th = 300, 533
    B = 60 + len(panels) * tw + (len(panels) - 1) * 24 + 60
    blatt = Image.new("RGB", (B, 900), (245, 247, 251))
    d = ImageDraw.Draw(blatt)
    d.text((60, 36), "STORYBOARD: JENSEN NACH 11 TAGEN ZURÜCK (LOKALE BILD-KI)", font=font("h800", 44), fill=(20, 30, 60))
    d.text((60, 98), "Privater Account · Satire · ca. 16 s · Bilder: DreamShaper 8, auf eigenem Server erzeugt, kostenlos",
           font=font("t400", 26), fill=(90, 100, 120))
    for i, (img, zeit, txt) in enumerate(panels):
        x = 60 + i * (tw + 24)
        img.save(os.path.join(ORDNER, f"szene_{i + 1}.png"))
        blatt.paste(img.resize((tw, th), Image.LANCZOS), (x, 160))
        d.rectangle([x, 160, x + tw, 160 + th], outline=(200, 206, 218), width=2)
        d.text((x, 710), zeit, font=font("h800", 26), fill=(237, 109, 5))
        for k, z in enumerate(wrap(d, txt, font("t400", 22), tw)[:4]):
            d.text((x, 748 + k * 28), z, font=font("t400", 22), fill=(20, 30, 60))
    ziel = os.path.join(HIER, "vorschau", "memes", "storyboard_huang_ki.jpg")
    blatt.save(ziel, quality=90)
    print(ziel)


if __name__ == "__main__":
    main()
