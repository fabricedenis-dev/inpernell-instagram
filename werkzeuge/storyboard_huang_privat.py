#!/usr/bin/env python3
"""Storyboard Meme „Jensen zockt GTA 6“ für den PRIVATEN Account des Inhabers (keine Inpernell-Werbung).
Fotos: Wikimedia Commons, Anderseidesvik, CC BY 4.0 (Namensnennung im Video und Bildtext Pflicht).
Satire, kein Bezug auf die Hintergründe des Rücktritts.
Aufruf: python werkzeuge/storyboard_huang_privat.py <ordner mit NN.jpg>  ->  vorschau/memes/storyboard_huang_privat.jpg"""
import os
import sys

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
from bild import font, wrap  # noqa: E402

W, H = 1080, 1920
ORDNER = sys.argv[1] if len(sys.argv) > 1 else "."
NACHWEIS = "Fotos: Anderseidesvik, CC BY 4.0, Wikimedia Commons · Satire"

# (Foto-Nr., Fokus x 0..1, Fokus y 0..1, Text)
SZENEN = [
    (9, 0.5, 0.35, "Nvidia zu Jensen: „Wir holen dich nicht zurück.“"),
    (3, 0.5, 0.45, "Jensen: „Kein Problem. Ich hab eh noch GTA 6 zu zocken.“"),
    (2, 0.6, 0.45, "Zwei Wochen später: 100 % durchgespielt."),
    (10, 0.5, 0.35, "Und jetzt hat er nichts mehr zu tun."),
    (22, 0.45, 0.5, "Also: „Ich wäre dann wieder da.“"),
    (6, 0.5, 0.4, "Lücke im Lebenslauf? „GTA 6. Teamfähig, stressresistent, fahre Fluchtwagen.“"),
]


def foto(nr, fx, fy, w, h):
    im = Image.open(os.path.join(ORDNER, f"{nr:02d}.jpg")).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = int((im.width - w) * fx), int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))


def bild(nr, fx, fy, text):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = font("h800", 58)
    zeilen = wrap(d, text, f, W - 140)
    y = 230
    for z in zeilen:
        d.text((70, y), z, font=f, fill=(10, 10, 10))
        y += 70
    oben = max(560, y + 40)
    img.paste(foto(nr, fx, fy, W, H - oben), (0, oben))
    d.rounded_rectangle([W - 210, oben + 30, W - 40, oben + 80], radius=12, fill=(226, 60, 60))
    d.text((W - 125, oben + 55), "SATIRE", font=font("h800", 28), fill=(255, 255, 255), anchor="mm")
    d.rectangle([0, H - 430, W, H - 390], fill=(0, 0, 0))
    d.text((W // 2, H - 410), NACHWEIS, font=font("t400", 24), fill=(230, 230, 230), anchor="mm")
    return img


def main():
    tw, th = 300, 533
    B = 60 + 6 * tw + 5 * 24 + 60
    blatt = Image.new("RGB", (B, 860), (245, 247, 251))
    d = ImageDraw.Draw(blatt)
    d.text((60, 36), "MEME FÜR DEN PRIVATEN ACCOUNT: JENSEN ZOCKT GTA 6", font=font("h800", 46), fill=(20, 30, 60))
    d.text((60, 100), "Echte Fotos (CC BY 4.0, Wikimedia Commons) · je ca. 2,5 s · harte Schnitte, Trend-Sound "
                      "aus der Instagram-Bibliothek · Vorschau", font=font("t400", 26), fill=(90, 100, 120))
    for i, (nr, fx, fy, text) in enumerate(SZENEN):
        x = 60 + i * (tw + 24)
        blatt.paste(bild(nr, fx, fy, text).resize((tw, th), Image.LANCZOS), (x, 160))
        d.rectangle([x, 160, x + tw, 160 + th], outline=(200, 206, 218), width=2)
        d.text((x, 710), f"{i + 1}", font=font("h800", 30), fill=(237, 109, 5))
    ziel = os.path.join(HIER, "vorschau", "memes", "storyboard_huang_privat.jpg")
    blatt.save(ziel, quality=90)
    print(ziel)


if __name__ == "__main__":
    main()
