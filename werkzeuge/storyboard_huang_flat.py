#!/usr/bin/env python3
"""Storyboard „Jensen nach 11 Tagen zurück“ im flachen Meme-Cartoon-Stil (privater Account, Satire).
Fakten: Rücktritt 12.11.2026, Wiedereinsetzung 23.11.2026 (11 Tage); GTA VI erschien am 19.11.2026.
Aufruf: python werkzeuge/storyboard_huang_flat.py  ->  vorschau/memes/storyboard_huang_flat.jpg"""
import os
import sys

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import flat_cartoon as fc  # noqa: E402
from bild import font, wrap  # noqa: E402


def satire(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([fc.W - 210, 1440, fc.W - 40, 1490], radius=12, fill=(226, 60, 60))
    d.text((fc.W - 125, 1465), "SATIRE", font=font("h800", 28), fill=(255, 255, 255), anchor="mm")


def buero(huang, chef, oben=None, blase_chef=None, blase_huang=None):
    img = fc.hintergrund_buero()
    c = fc.figur(haar="glatze", brille=False, jacke="anzug", **chef)
    h = fc.figur(**huang)
    img.paste(c, (30, 760), c)
    img.paste(h, (540, 760), h)
    y = fc.text_oben(img, oben) + 40 if oben else 260
    if blase_chef:
        fc.blase(img, blase_chef, 60, y)
    if blase_huang:
        fc.blase(img, blase_huang, 440, y if not blase_chef else y + 260, w=580, rechts=True)
    satire(img)
    return img


def sofa(tv, huang, oben):
    img = fc.hintergrund_wohnzimmer()
    h = fc.figur(jacke="hoodie", pose="sitzt", **huang)
    img.paste(h, (280, 880), h)
    fc.fernseher(img, tv, y=560)
    fc.text_oben(img, oben)
    satire(img)
    return img


def main():
    panels = [
        (buero(dict(gesicht="laecheln", arm="jubel"), dict(gesicht="laecheln"),
               "POV: Jensen nach 11 Tagen Pause zurück bei Nvidia", "Willkommen zurück! Was hast du gemacht?"),
         "0–3 s", "Hook. Chef begrüßt ihn, Jensen jubelt. Kurzer Trend-Sound."),
        (buero(dict(gesicht="geschlossen"), dict(gesicht="fragend"), None, None,
               "Reflektiert. An mir gearbeitet. Viel nachgedacht."),
         "3–6 s", "Jensen, sehr seriös, Augen zu."),
        (sofa([("GTA VI", (255, 200, 60)), ("Tag 1", (255, 255, 255))], dict(gesicht="seitenblick", arm="controller"),
              "Was er wirklich gemacht hat:"),
         "6–8 s", "Harter Schnitt, Plattenkratzer. Nachts auf dem Sofa mit Controller."),
        (sofa([("Tag 11", (255, 255, 255)), ("100 % abgeschlossen", (120, 230, 120))],
              dict(gesicht="laecheln", arm="jubel"), "Was er wirklich gemacht hat:"),
         "8–10 s", "Tag 11: alles durch, Jensen jubelt. Siegessound."),
        (buero(dict(gesicht="seitenblick"), dict(gesicht="fragend"), None, "Und? Hast du was gelernt?",
               "Ja. Fluchtwagen fahren ist auch Führungserfahrung."),
         "10–14 s", "Zurück im Büro. Pointe."),
        (buero(dict(gesicht="laecheln", arm="zeigen"), dict(gesicht="schock"), None, "Okay. Du bist eingestellt."),
         "14–16 s", "Chef völlig perplex, Boom-Effekt, Zoom auf Jensens Grinsen."),
    ]
    tw, th = 300, 533
    B = 60 + len(panels) * tw + (len(panels) - 1) * 24 + 60
    blatt = Image.new("RGB", (B, 900), (245, 247, 251))
    d = ImageDraw.Draw(blatt)
    d.text((60, 36), "STORYBOARD: JENSEN NACH 11 TAGEN ZURÜCK (MEME-CARTOON-STIL)", font=font("h800", 44),
           fill=(20, 30, 60))
    d.text((60, 98), "Privater Account · Satire · ca. 16 s · Rücktritt 12.11., zurück seit 23.11.2026, "
                     "GTA VI seit 19.11.", font=font("t400", 26), fill=(90, 100, 120))
    for i, (img, zeit, txt) in enumerate(panels):
        x = 60 + i * (tw + 24)
        blatt.paste(img.resize((tw, th), Image.LANCZOS), (x, 160))
        d.rectangle([x, 160, x + tw, 160 + th], outline=(200, 206, 218), width=2)
        d.text((x, 710), zeit, font=font("h800", 26), fill=(237, 109, 5))
        for k, z in enumerate(wrap(d, txt, font("t400", 22), tw)[:5]):
            d.text((x, 748 + k * 28), z, font=font("t400", 22), fill=(20, 30, 60))
    ziel = os.path.join(HIER, "vorschau", "memes", "storyboard_huang_flat.jpg")
    blatt.save(ziel, quality=90)
    print(ziel)


if __name__ == "__main__":
    main()
