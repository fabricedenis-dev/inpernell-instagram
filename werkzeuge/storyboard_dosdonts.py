#!/usr/bin/env python3
"""Storyboard „Do's & Don'ts: Gehaltsfrage“ mit echten Handyclips (Platzhalter) -> vorschau/reichweite/storyboard_gehalt.jpg"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
from bild import NAVY, ORANGE, WEISS, font, wrap  # noqa: E402

W, H = 1080, 1920
ROT, GRUEN = (226, 60, 60), (40, 180, 100)


def clip(name, rolle, farbe):
    """Platzhalter für einen echten Handyclip: Büro-Hintergrund, Person als Silhouette mit Namen."""
    img = Image.new("RGB", (W, H), (205, 210, 218))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 1100], fill=(222, 226, 232))
    d.rectangle([0, 1100, W, H], fill=(150, 120, 92))                       # Tisch
    d.rectangle([80, 260, 520, 760], fill=(186, 214, 236), outline=(160, 168, 180), width=10)   # Fenster
    d.ellipse([380, 560, 700, 880], fill=farbe)
    d.rounded_rectangle([250, 900, 830, 1500], radius=180, fill=farbe)
    d.rounded_rectangle([300, 960, 780, 1070], radius=20, fill=(255, 255, 255))
    d.text((W // 2, 1015), f"CLIP: {name.upper()}", font=font("h800", 46), fill=NAVY, anchor="mm")
    d.text((W // 2, 1110), rolle, font=font("t400", 38), fill=WEISS, anchor="mm")
    return img


def untertitel(img, text, mark=None):
    d = ImageDraw.Draw(img)
    f = font("h800", 58)
    y = 1200
    for z in wrap(d, text, f, W - 160):
        d.text((W // 2, y), z, font=f, fill=WEISS, anchor="ma", stroke_width=8, stroke_fill=(0, 0, 0))
        y += 72


def etikett(img, text, farbe, y=320):
    d = ImageDraw.Draw(img)
    f = font("h800", 60)
    b = d.textlength(text, font=f) + 80
    d.rounded_rectangle([(W - b) / 2, y, (W + b) / 2, y + 110], radius=24, fill=farbe)
    d.text((W // 2, y + 55), text, font=f, fill=WEISS, anchor="mm")


def hook():
    img = clip("Fabrice", "fragt als Personaler", (96, 110, 140))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 230, W - 60, 470], radius=26, fill=WEISS)
    d.text((100, 260), "DO'S & DON'TS IM VORSTELLUNGSGESPRÄCH", font=font("h800", 34), fill=ORANGE)
    y = 310
    for z in wrap(d, "Die Gehaltsfrage: So verkaufst du dich unter Wert", font("h800", 54), W - 200):
        d.text((100, y), z, font=font("h800", 54), fill=NAVY)
        y += 62
    untertitel(img, "„Was stellst du dir beim Gehalt vor?“")
    return img


def dont_live():
    img = clip("Pascal", "antwortet als Bewerber", (120, 96, 86))
    untertitel(img, "„Äh … so 20 Euro die Stunde wären okay.“")
    return img


def dont_freeze():
    img = dont_live()
    g = ImageEnhance.Brightness(ImageOps.grayscale(img).convert("RGB")).enhance(0.75)
    d = ImageDraw.Draw(g)
    d.line([(60, 300), (W - 60, 1500)], fill=ROT, width=34)
    d.line([(W - 60, 300), (60, 1500)], fill=ROT, width=34)
    etikett(g, "DON'T", ROT, y=230)
    d.rounded_rectangle([80, 1370, W - 80, 1510], radius=22, fill=(0, 0, 0))
    y = 1385
    for z in wrap(d, "Unsicher, zu niedrig, ohne Begründung", font("h800", 46), W - 220):
        d.text((W // 2, y), z, font=font("h800", 46), fill=WEISS, anchor="ma")
        y += 56
    return g


def waldemar():
    img = clip("Waldemar", "kommt ins Bild und erklärt", (70, 112, 96))
    untertitel(img, "„Stopp. Verkauf dich nicht unter Wert. Begründe deinen Wunsch.“")
    return img


def do_live():
    img = clip("Pascal", "zweiter Versuch", (120, 96, 86))
    etikett(img, "DO", GRUEN, y=230)
    untertitel(img, "„Mit 3 Jahren Erfahrung an der 5-Achs-Fräse stelle ich mir 30 Euro pro Stunde vor.“")
    return img


def tipp():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 420), "SO GEHT'S", font=font("h800", 46), fill=ORANGE, anchor="mm")
    y = 520
    for nr, t in enumerate(("Vorher recherchieren: Was ist für deinen Beruf in deiner Region üblich?",
                            "Konkrete Zahl nennen, keine Spanne nach unten.",
                            "Mit Erfahrung, Maschinen und Erfolgen begründen."), 1):
        d.ellipse([90, y, 160, y + 70], fill=ORANGE)
        d.text((125, y + 35), str(nr), font=font("h800", 40), fill=NAVY, anchor="mm")
        yy = y
        for z in wrap(d, t, font("h700", 46), W - 290):
            d.text((190, yy), z, font=font("h700", 46), fill=WEISS)
            yy += 56
        y = yy + 50
    d.text((W // 2, 1330), "Michael spricht den Abschluss", font=font("t400", 34),
           fill=(190, 204, 226), anchor="mm")
    lg = os.path.join(HIER, "assets", "logo.png")
    if os.path.exists(lg):
        l = Image.open(lg).convert("RGBA")
        l = l.resize((520, int(l.height * 520 / l.width)), Image.LANCZOS)
        img.paste(l, ((W - 520) // 2, 1420), l)
    return img


def main():
    bilder = [
        (hook(), "1  Hook (0–2 s)", "Fabrice stellt die Frage, Titel oben"),
        (dont_live(), "2  Don't (2–5 s)", "Pascal antwortet unsicher"),
        (dont_freeze(), "3  Standbild (5–7 s)", "Bild friert ein, wird grau, rotes X"),
        (waldemar(), "4  Auflösung (7–11 s)", "Waldemar kommt ins Bild"),
        (do_live(), "5  Do (11–16 s)", "Pascal antwortet selbstbewusst"),
        (tipp(), "6  Tipps + Abschluss", "3 Punkte, Logo, Michael spricht"),
    ]
    tw, th = 360, 640
    B = 60 + 6 * tw + 5 * 30 + 60
    blatt = Image.new("RGB", (B, 1000), (245, 247, 251))
    d = ImageDraw.Draw(blatt)
    d.text((60, 40), "STORYBOARD: DO'S & DON'TS – DIE GEHALTSFRAGE", font=font("h800", 46), fill=NAVY)
    d.text((60, 105), "Grau = Platzhalter für eure echten Handyclips · Zahlen werden vor dem Dreh aus dem "
                      "Entgeltatlas der Arbeitsagentur belegt", font=font("t400", 28), fill=(90, 100, 120))
    for i, (img, t, u) in enumerate(bilder):
        x = 60 + i * (tw + 30)
        blatt.paste(img.resize((tw, th), Image.LANCZOS), (x, 170))
        d.rectangle([x, 170, x + tw, 170 + th], outline=(200, 206, 218), width=2)
        d.text((x, 835), t, font=font("h800", 28), fill=NAVY)
        y = 875
        for z in wrap(d, u, font("t400", 24), tw):
            d.text((x, y), z, font=font("t400", 24), fill=(90, 100, 120))
            y += 30
    ziel = os.path.join(HIER, "vorschau", "reichweite", "storyboard_gehalt.jpg")
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    blatt.save(ziel, quality=90)
    print(ziel)


if __name__ == "__main__":
    main()
