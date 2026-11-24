#!/usr/bin/env python3
"""Vorschau: Meme-Vergleich „Erwartung vs. Realität“ mit freien Stock-Clips (Mixkit), Inpernell-Stil.
Aufruf: python werkzeuge/meme_vorschlaege.py <ordner mit <id>.jpg>  ->  vorschau/reichweite/meme_vorschlaege.jpg"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
import reel_design as rd  # noqa: E402
from bild import NAVY, ORANGE, WEISS, font  # noqa: E402

W, H = 1080, 1920
ORDNER = sys.argv[1] if len(sys.argv) > 1 else "."

PAARE = [
    ("Bewerber", ("Laut Lebenslauf:", "belastbar & dynamisch"), 50080, 0.47,
     ("Am ersten Montag", "um 7:58 Uhr"), 33743, 0.5),
    ("Das Team", ("Laut Stellenanzeige:", "jung & dynamisch"), 51295, 0.45,
     ("In echt", "am Montagmorgen"), 4607, 0.55),
    ("Bewerber", ("Tag 1 nach", "„Wir melden uns“"), 47985, 0.42,
     ("Tag 21 nach", "„Wir melden uns“"), 11281, 0.62),
]


def bild(cid, fokus):
    im = Image.open(os.path.join(ORDNER, f"{cid}.jpg")).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = int((im.width - W) * fokus)
    return im.crop((x, 0, x + W, H))


def kachel(oben, zeilen, cid, fokus):
    img = bild(cid, fokus).convert("RGBA")
    # großes Etikett mit weichem Schatten (wie im Meme-Format)
    sch = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sch).text((W // 2 + 4, 700 + 6), oben, font=font("h800", 110), fill=(0, 0, 0, 170), anchor="mm")
    img.alpha_composite(sch.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    d.text((W // 2, 700), oben, font=font("h800", 110), fill=WEISS, anchor="mm")
    # Kästen unten links mit orangem Balken
    y = 1150
    d.rectangle([70, y, 84, y + 2 * 104 - 14], fill=ORANGE)
    for z in zeilen:
        f = font("h800", 66)
        b = d.textlength(z, font=f)
        d.rectangle([100, y, 100 + b + 40, y + 90], fill=WEISS)
        d.text((120, y + 45), z, font=f, fill=NAVY, anchor="lm")
        y += 104
    rd.logo_marke(img)
    return img.convert("RGB")


def main():
    tw, th = 300, 533
    B = 60 + 3 * (2 * tw + 20) + 2 * 50 + 60
    blatt = Image.new("RGB", (B, 900), (245, 247, 251))
    d = ImageDraw.Draw(blatt)
    d.text((60, 36), "MEME-VERGLEICH IM INPERNELL-STIL – 3 IDEEN", font=font("h800", 46), fill=NAVY)
    d.text((60, 100), "Freie Stock-Clips (Mixkit), im Reel bewegt mit hartem Schnitt und Soundeffekt · Vorschau",
           font=font("t400", 26), fill=(90, 100, 120))
    titel = ["1  Lebenslauf vs. Montag", "2  Stellenanzeige vs. Realität", "3  „Wir melden uns“"]
    for i, (oben, z1, c1, f1, z2, c2, f2) in enumerate(PAARE):
        x = 60 + i * (2 * tw + 20 + 50)
        for j, (zz, cid, fo) in enumerate(((z1, c1, f1), (z2, c2, f2))):
            k = kachel(oben, zz, cid, fo).resize((tw, th), Image.LANCZOS)
            blatt.paste(k, (x + j * (tw + 20), 160))
            d.rectangle([x + j * (tw + 20), 160, x + j * (tw + 20) + tw, 160 + th], outline=(200, 206, 218), width=2)
            d.text((x + j * (tw + 20) + tw // 2, 160 + th + 14), "erst" if j == 0 else "dann (harter Schnitt)",
                   font=font("t400", 22), fill=(90, 100, 120), anchor="ma")
        d.text((x, 760), titel[i], font=font("h800", 30), fill=NAVY)
    ziel = os.path.join(HIER, "vorschau", "reichweite", "meme_vorschlaege.jpg")
    blatt.save(ziel, quality=90)
    print(ziel)


if __name__ == "__main__":
    main()
