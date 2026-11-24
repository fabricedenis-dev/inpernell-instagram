#!/usr/bin/env python3
"""Storyboard Remix „Huang will zurück“: Teil 1 = echtes Nachrichten-Reel per Remix in der App (nur Platzhalter),
Teil 2 = unser Anschluss-Clip (Waldemar als KI-Comic, Lebenslauf-Eintrag als Pointe, kein Bild von Huang).
Aufruf: python werkzeuge/storyboard_remix_huang.py  ->  vorschau/memes/storyboard_remix_huang.jpg"""
import os
import sys

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
import reel_design as rd  # noqa: E402
from bild import NAVY, ORANGE, WEISS, font, wrap  # noqa: E402

W, H = 1080, 1920
ROT = (226, 60, 60)


def grund():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)], fill=(int(12 + 16 * t), int(28 + 24 * t), int(60 + 34 * t)))
    return img


def logo(img):
    rgba = img.convert("RGBA")
    rd.logo_marke(rgba)
    return rgba.convert("RGB")


def waldemar(img, x=190, y=760, breite=700):
    k = Image.open(os.path.join(HIER, "assets", "team", "waldemar_comic.png")).convert("RGBA")
    k = k.resize((breite, int(k.height * breite / k.width)), Image.LANCZOS)
    img.paste(k, (x, y), k)


def blase(img, text, y, groesse=54):
    d = ImageDraw.Draw(img)
    f = font("h800", groesse)
    z = wrap(d, text, f, W - 220)
    h = 50 + len(z) * int(groesse * 1.2)
    d.rounded_rectangle([70, y, W - 70, y + h], radius=30, fill=WEISS)
    d.polygon([(420, y + h - 2), (480, y + h - 2), (430, y + h + 60)], fill=WEISS)
    for i, t in enumerate(z):
        d.text((110, y + 25 + i * int(groesse * 1.2)), t, font=f, fill=NAVY)


def etikett(img, text, farbe=ORANGE, y=240):
    d = ImageDraw.Draw(img)
    f = font("h800", 40)
    b = d.textlength(text, font=f) + 60
    d.rounded_rectangle([70, y, 70 + b, y + 72], radius=18, fill=farbe)
    d.text((100, y + 36), text, font=f, fill=NAVY if farbe == ORANGE else WEISS, anchor="lm")


def f1():
    img = Image.new("RGB", (W, H), (70, 74, 84))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y + 60)], fill=(80, 84, 94), width=2)
    d.rounded_rectangle([90, 700, W - 90, 1120], radius=30, fill=(40, 44, 54))
    for i, t in enumerate(("ORIGINAL-REEL", "Nachricht: Huang bietet", "Rückkehr als Nvidia-Chef an",
                           "(per Remix in der App)")):
        d.text((W // 2, 760 + i * 80), t, font=font("h800" if i == 0 else "h700", 46 if i == 0 else 42),
               fill=ORANGE if i == 0 else WEISS, anchor="ma")
    return img


def f2():
    img = grund()
    etikett(img, "BEWERBUNGSGESPRÄCH")
    waldemar(img)
    blase(img, "Okay. Und die Lücke im Lebenslauf?", 420)
    return logo(img)


def f3():
    img = grund()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([90, 300, W - 90, 1380], radius=18, fill=WEISS, outline=(200, 204, 214), width=3)
    d.text((140, 350), "LEBENSLAUF", font=font("h800", 56), fill=NAVY)
    d.text((140, 430), "J. H., Kalifornien", font=font("t400", 38), fill=(90, 100, 120))
    d.line([(140, 500), (W - 140, 500)], fill=(210, 214, 222), width=3)
    zeilen = [("1993–2026", "Gründer und Chef eines Chip-Herstellers"), ("Sprachen", "Englisch, Mandarin, Lederjacke"),
              ("11/2026", "GTA 6 – 100 % abgeschlossen")]
    y = 540
    for i, (a, b) in enumerate(zeilen):
        letzte = i == len(zeilen) - 1
        if letzte:
            d.rounded_rectangle([120, y - 14, W - 120, y + 150], radius=14, fill=(255, 238, 214))
        d.text((140, y), a, font=font("h800", 36), fill=ORANGE if letzte else NAVY)
        for k, t in enumerate(wrap(d, b, font("h700", 40), W - 520)):
            d.text((420, y + k * 48), t, font=font("h700", 40), fill=NAVY)
        y += 200
    d.text((W // 2, 1300), "Satire", font=font("t400", 30), fill=(140, 150, 170), anchor="mm")
    return logo(img)


def f4():
    img = grund()
    etikett(img, "BEWERBUNGSGESPRÄCH")
    waldemar(img)
    blase(img, "Klingt nach Führungserfahrung. Wann kannst du anfangen?", 380)
    return logo(img)


def f5():
    img = grund()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 700), "Lücke im Lebenslauf?", font=font("h800", 76), fill=WEISS, anchor="mm")
    d.text((W // 2, 800), "Kein Weltuntergang.", font=font("h800", 76), fill=ORANGE, anchor="mm")
    d.rounded_rectangle([290, 920, 790, 1010], radius=45, fill=ORANGE)
    d.text((W // 2, 965), "Link in der Bio", font=font("h800", 44), fill=NAVY, anchor="mm")
    lg = os.path.join(HIER, "assets", "logo.png")
    if os.path.exists(lg):
        l = Image.open(lg).convert("RGBA")
        l = l.resize((520, int(l.height * 520 / l.width)), Image.LANCZOS)
        img.paste(l, ((W - 520) // 2, 1100), l)
    return img


def main():
    bilder = [(f1(), "Teil 1: Original (Remix)", "Echtes News-Reel über Huangs Rückkehrangebot, in der App per Remix eingebunden"),
              (f2(), "Teil 2: 0–3 s", "Waldemar: „Okay. Und die Lücke im Lebenslauf?“"),
              (f3(), "3–7 s", "Lebenslauf wird gezeigt, der letzte Eintrag leuchtet auf: „11/2026 – GTA 6, 100 %“"),
              (f4(), "7–10 s", "Pointe, dann Ba-dum-tss"),
              (f5(), "10–12 s", "Abschluss mit Logo")]
    tw, th = 360, 640
    B = 60 + 5 * tw + 4 * 30 + 60
    blatt = Image.new("RGB", (B, 1010), (245, 247, 251))
    d = ImageDraw.Draw(blatt)
    d.text((60, 36), "REMIX: „HUANG WILL ZURÜCK“", font=font("h800", 50), fill=NAVY)
    d.text((60, 104), "Original-Reel per Remix in der App + unser Anschluss-Clip (Waldemar als KI-Comic) · Vorschau",
           font=font("t400", 28), fill=(90, 100, 120))
    for i, (img, t, u) in enumerate(bilder):
        x = 60 + i * (tw + 30)
        blatt.paste(img.resize((tw, th), Image.LANCZOS), (x, 170))
        d.rectangle([x, 170, x + tw, 170 + th], outline=ORANGE if i == 0 else (200, 206, 218), width=4 if i == 0 else 2)
        d.text((x, 830), t, font=font("h800", 28), fill=NAVY)
        for k, z in enumerate(wrap(d, u, font("t400", 24), tw)[:4]):
            d.text((x, 872 + k * 30), z, font=font("t400", 24), fill=(90, 100, 120))
    ziel = os.path.join(HIER, "vorschau", "memes", "storyboard_remix_huang.jpg")
    blatt.save(ziel, quality=90)
    print(ziel)


if __name__ == "__main__":
    main()
