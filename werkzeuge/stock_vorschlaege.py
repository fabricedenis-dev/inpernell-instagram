#!/usr/bin/env python3
"""Vorschläge: freie Stock-Clips (Mixkit) im Do's-&-Don'ts-Reel. Nutzt Vorschaubilder der Clips.
Aufruf: python werkzeuge/stock_vorschlaege.py <ordner mit <id>.jpg>  ->  vorschau/reichweite/stock_vorschlaege.jpg"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import demo_dosdonts as dd  # noqa: E402
from bild import NAVY, ORANGE, WEISS, font  # noqa: E402

W, H = dd.W, dd.H
ORDNER = sys.argv[1] if len(sys.argv) > 1 else "."


def clip(cid, box=(W, H), fokus=0.5):
    im = Image.open(os.path.join(ORDNER, f"{cid}.jpg")).convert("RGB")
    bw, bh = box
    s = max(bw / im.width, bh / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = int((im.width - bw) * fokus)
    return im.crop((x, (im.height - bh) // 2, x + bw, (im.height - bh) // 2 + bh))


def verlauf_unten(img, ab=1000):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(ab, H):
        a = int(200 * (y - ab) / (H - ab))
        d.line([(0, y), (W, y)], fill=(10, 24, 52, a))
    img.paste(ov, (0, 0), ov)


def avatar(img, wer, xy, r=120):
    f = dd.FOTOS[wer].resize((2 * r, 2 * r), Image.LANCZOS)
    m = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    d = ImageDraw.Draw(img)
    d.ellipse([xy[0] - 8, xy[1] - 8, xy[0] + 2 * r + 8, xy[1] + 2 * r + 8], fill=ORANGE)
    img.paste(f, xy, m)
    d.rounded_rectangle([xy[0] + 20, xy[1] + 2 * r - 10, xy[0] + 2 * r - 20, xy[1] + 2 * r + 46], radius=14, fill=ORANGE)
    d.text((xy[0] + r, xy[1] + 2 * r + 18), dd.NAMEN[wer], font=font("h800", 32), fill=NAVY, anchor="mm")


def fertig(img):
    rgba = img.convert("RGBA")
    dd.rd.logo_marke(rgba)
    return rgba.convert("RGB")


def v1():
    """Clip als Vollbild, Sprecher als runder Avatar mit Sprechblase."""
    img = clip(49470, fokus=0.55)
    verlauf_unten(img, 700)
    dd.kopfzeile(img)
    dd.blase(img, "Was stellst du dir beim Gehalt vor?", 1.0)
    avatar(img, "fabrice", (W - 450, 1130))
    return fertig(img)


def v2():
    """Zwischenschnitt: Maschinen-Clip, während Pascal von der Fräse spricht."""
    img = clip(2244, fokus=0.5)
    verlauf_unten(img, 900)
    dd.kopfzeile(img)
    img = dd.etikett(img, "DO", dd.GRUEN, 1.0)
    dd.blase(img, "Mit 3 Jahren Erfahrung an der 5-Achs-Fräse stelle ich mir 30 Euro pro Stunde vor.", 1.0)
    avatar(img, "pascal", (W - 450, 1130))
    return fertig(img)


def v3():
    """Geteilter Bildschirm: oben Gesprächs-Clip, unten euer Porträt."""
    img = dd.HG.copy()
    img.paste(clip(46022, (W, 760), 0.5), (0, 0))
    dd.kopfzeile(img)
    k = dd.FOTOS["waldemar"].resize((620, 620), Image.LANCZOS)
    m = Image.new("L", (620, 620), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, 619, 619], radius=40, fill=255)
    img.paste(k, (230, 800), m)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([640, 1380, 850, 1440], radius=16, fill=ORANGE)
    d.text((745, 1410), "Waldemar", font=font("h800", 34), fill=NAVY, anchor="mm")
    d.rounded_rectangle([60, 600, W - 60, 760], radius=26, fill=WEISS)
    d.text((100, 625), "Stopp. Verkauf dich nicht unter Wert.", font=font("h800", 46), fill=NAVY)
    d.text((100, 690), "Begründe deinen Wunsch.", font=font("h800", 46), fill=NAVY)
    return fertig(img)


def v4():
    """Abschluss: Handschlag-Clip mit Botschaft."""
    img = clip(46755, fokus=0.45)
    img = ImageEnhance.Brightness(img).enhance(0.85)
    verlauf_unten(img, 600)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([90, 1000, W - 90, 1120], radius=24, fill=dd.GRUEN)
    d.text((W // 2, 1060), "Konkret, begründet, selbstbewusst", font=font("h800", 46), fill=WEISS, anchor="mm")
    d.text((W // 2, 1230), "Verkauf dich nicht unter Wert.", font=font("h800", 62), fill=WEISS, anchor="mm",
           stroke_width=4, stroke_fill=NAVY)
    return fertig(img)


def main():
    karten = [
        (v1(), "A  Clip als Hintergrund", "Gesprächs-Clip im Vollbild, ihr als runder Avatar mit Sprechblase. Clip: Mixkit 49470"),
        (v2(), "B  Zwischenschnitt zum Thema", "Während Pascal von der Fräse spricht, läuft ein Maschinen-Clip. Clip: Mixkit 2244"),
        (v3(), "C  Geteilter Bildschirm", "Oben Gesprächs-Clip, unten euer Porträt. Clip: Mixkit 46022"),
        (v4(), "D  Abschluss mit Handschlag", "Erfolgsmoment am Ende, dann Logo. Clip: Mixkit 46755"),
    ]
    tw, th = 450, 800
    B = 60 + 4 * tw + 3 * 40 + 60
    blatt = Image.new("RGB", (B, 1180), (245, 247, 251))
    d = ImageDraw.Draw(blatt)
    d.text((60, 40), "BEWEGTE BILDER IM REEL – 4 VORSCHLÄGE", font=font("h800", 50), fill=NAVY)
    d.text((60, 110), "Freie Stock-Clips (Mixkit) · im Video bewegt, hier als Standbild · Vorschau, nichts veröffentlicht",
           font=font("t400", 28), fill=(90, 100, 120))
    for i, (img, t, u) in enumerate(karten):
        x = 60 + i * (tw + 40)
        blatt.paste(img.resize((tw, th), Image.LANCZOS), (x, 170))
        d.rectangle([x, 170, x + tw, 170 + th], outline=(200, 206, 218), width=2)
        d.text((x, 995), t, font=font("h800", 30), fill=NAVY)
        from bild import wrap
        y = 1040
        for z in wrap(d, u, font("t400", 24), tw):
            d.text((x, y), z, font=font("t400", 24), fill=(90, 100, 120))
            y += 30
    ziel = os.path.join(HIER, "vorschau", "reichweite", "stock_vorschlaege.jpg")
    blatt.save(ziel, quality=90)
    print(ziel)


if __name__ == "__main__":
    main()
