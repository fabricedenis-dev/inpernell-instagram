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


def spielbild(name, auftrag, erfuellt=False):
    """Spielszene im Open-World-Look (KI-Bild) mit selbst gezeichnetem HUD: Minikarte, Fahndungssterne, Geld."""
    g = Image.open(os.path.join(ORDNER, name + ".png")).convert("RGB").resize((860, 484), Image.LANCZOS)
    d = ImageDraw.Draw(g)
    d.ellipse([22, 340, 142, 460], fill=(30, 40, 50), outline=(255, 255, 255), width=4)
    for k in range(4):
        d.line([(40 + k * 24, 350), (60 + k * 20, 450)], fill=(90, 110, 130), width=3)
    d.polygon([(82, 392), (74, 412), (90, 412)], fill=(255, 255, 255))
    f = font("h800", 34)
    d.text((838, 20), "$ 1.250.000", font=f, fill=(110, 220, 110), anchor="ra", stroke_width=3, stroke_fill=(0, 0, 0))
    for k in range(5):
        cx, cy, r = 838 - 34 - k * 40, 84, 15
        import math
        pts = [(cx + (r if i % 2 == 0 else r * 0.45) * math.sin(math.radians(i * 36)),
                cy - (r if i % 2 == 0 else r * 0.45) * math.cos(math.radians(i * 36))) for i in range(10)]
        d.polygon(pts, fill=(255, 255, 255) if k < 3 else None, outline=(0, 0, 0), width=2)
    d.text((24, 20), auftrag, font=font("h800", 30), fill=(255, 255, 255), stroke_width=3,
           stroke_fill=(0, 0, 0))
    if erfuellt:
        d.rectangle([0, 170, 860, 300], fill=(0, 0, 0, 0))
        ov = Image.new("RGBA", g.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).rectangle([0, 172, 860, 300], fill=(0, 0, 0, 150))
        g = Image.alpha_composite(g.convert("RGBA"), ov).convert("RGB")
        d = ImageDraw.Draw(g)
        d.text((430, 180), "AUFTRAG ERFÜLLT", font=font("h800", 64), fill=(255, 196, 40), anchor="ma",
               stroke_width=4, stroke_fill=(0, 0, 0))
        d.text((430, 256), "100 % abgeschlossen", font=font("h800", 32), fill=(255, 255, 255), anchor="ma",
               stroke_width=3, stroke_fill=(0, 0, 0))
    return g


def sofa(jensen, spiel, tag, auftrag, erfuellt=False):
    im = Image.open(os.path.join(ORDNER, "bg_wohnzimmer.png")).convert("RGB")
    hh = int(im.height * 0.62)
    bw = int(hh * 9 / 16)
    img = im.crop(((im.width - bw) // 2, int(im.height * 0.03), (im.width + bw) // 2, hh)).resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    # Fernseher an der Wand mit Lichtschein
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([40, 470, 1040, 1100], radius=60, fill=(255, 120, 200, 60))
    img.paste(glow, (0, 0), glow)
    d.rounded_rectangle([88, 520, 992, 1050], radius=16, fill=(16, 16, 20), outline=(5, 5, 8), width=8)
    img.paste(spielbild(spiel, auftrag, erfuellt), (110, 542))
    d.rectangle([500, 1050, 580, 1090], fill=(30, 30, 36))
    d.rounded_rectangle([380, 1086, 700, 1104], radius=8, fill=(30, 30, 36))
    # Jensen von hinten auf dem Sofa
    sm.figur(img, 540, 1920, groesse=0.9, bein="sitzen", ruecken=True, **HOODIE, **jensen)
    # Sofalehne im Vordergrund
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 1560, 1020, 1990], radius=70, fill=(170, 40, 60), outline=(20, 20, 24), width=8)
    d.rounded_rectangle([20, 1500, 170, 1990], radius=60, fill=(150, 34, 52), outline=(20, 20, 24), width=8)
    d.rounded_rectangle([910, 1500, 1060, 1990], radius=60, fill=(150, 34, 52), outline=(20, 20, 24), width=8)
    fc.text_oben(img, "Was er wirklich gemacht hat:")
    d.rounded_rectangle([340, 400, 740, 470], radius=14, fill=(20, 22, 34), outline=(255, 200, 60), width=4)
    d.text((540, 435), tag, font=font("h800", 40), fill=(255, 200, 60), anchor="mm")
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
        (sofa(dict(arm_l=(30, 10), arm_r=(30, 10), halt="controller"), "spiel_1", "GTA VI · Tag 1",
              "Auftrag: Entkomme der Polizei"),
         "6–8 s", "Plattenkratzer. Nachts auf dem Sofa mit Controller."),
        (sofa(dict(**jubel), "spiel_2", "GTA VI · Tag 11", "Letzter Auftrag", erfuellt=True),
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
