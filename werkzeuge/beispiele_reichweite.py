#!/usr/bin/env python3
"""Beispielbilder zu den Reichweiten-Empfehlungen (Inpernell-Stil) -> vorschau/reichweite/beispiele.jpg"""
import os
import sys

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
from bild import NAVY, ORANGE, WEISS, font, wrap  # noqa: E402

W, H = 1080, 1920
ZIEL = os.path.join(HIER, "vorschau", "reichweite")
DUNKEL = (16, 34, 66)
HELL = (190, 204, 226)


def grund():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)], fill=(int(14 + 14 * t), int(30 + 22 * t), int(64 + 30 * t)))
    return img


def zeilen(d, text, f, x, y, maxw, farbe=WEISS, abstand=1.15, mitte=False):
    for z in wrap(d, text, f, maxw):
        if mitte:
            d.text((W // 2, y), z, font=f, fill=farbe, anchor="ma")
        else:
            d.text((x, y), z, font=f, fill=farbe)
        y += int(f.size * abstand)
    return y


def logo(img):
    p = os.path.join(HIER, "assets", "logo.png")
    if os.path.exists(p):
        l = Image.open(p).convert("RGBA")
        l = l.resize((260, int(l.height * 260 / l.width)), Image.LANCZOS)
        img.paste(l, (74, 1420), l)


def a_gesicht():
    """Wiederkehrende Serie mit eurem Gesicht (Handyvideo)."""
    img = grund()
    d = ImageDraw.Draw(img)
    # Platzhalter Handyvideo: Person spricht in die Kamera
    d.rectangle([0, 0, W, H], fill=(58, 70, 92))
    d.ellipse([390, 520, 690, 840], fill=(120, 132, 156))                      # Kopf
    d.rounded_rectangle([250, 860, 830, 1700], radius=200, fill=(120, 132, 156))  # Oberkörper
    d.text((W // 2, 1000), "HIER: EUER HANDYVIDEO", font=font("h800", 44), fill=WEISS, anchor="mm")
    d.text((W // 2, 1060), "Fabrice spricht direkt in die Kamera", font=font("t400", 36), fill=WEISS, anchor="mm")
    d.rounded_rectangle([60, 250, W - 60, 470], radius=26, fill=WEISS)
    d.text((100, 280), "INSIDER-TIPP NR. 3", font=font("h800", 34), fill=ORANGE)
    zeilen(d, "Das schaut sich jeder Personaler zuerst an", font("h800", 52), 100, 330, W - 200, farbe=NAVY)
    d.rounded_rectangle([90, 1180, W - 90, 1330], radius=20, fill=(0, 0, 0))
    zeilen(d, "Nicht dein Foto. Sondern deine letzten 2 Jahre.", font("h800", 46), 0, 1205, W - 220, mitte=True)
    logo(img)
    return img


def b_gehalt():
    """Stellenanzeige mit Gehalt groß und Bewerbung per DM (Angaben aus der echten Anzeige vom 20.11.)."""
    img = grund()
    d = ImageDraw.Draw(img)
    d.text((80, 300), "TOP JOB IN TUTTLINGEN", font=font("h800", 40), fill=ORANGE)
    y = zeilen(d, "Konstrukteur & Entwickler (m/w/d)", font("h800", 70), 80, 370, W - 160)
    d.rounded_rectangle([60, y + 50, W - 60, y + 330], radius=30, fill=ORANGE)
    d.text((W // 2, y + 120), "65.000 – 80.000 €", font=font("h800", 96), fill=NAVY, anchor="mm")
    d.text((W // 2, y + 230), "im Jahr · Hybrid möglich", font=font("h700", 44), fill=NAVY, anchor="mm")
    y += 420
    for p in ("Festanstellung direkt beim Arbeitgeber", "Für dich kostenlos"):
        d.ellipse([90, y + 12, 118, y + 40], fill=ORANGE)
        d.text((140, y), p, font=font("h700", 42), fill=WEISS)
        y += 74
    d.rounded_rectangle([60, y + 40, W - 60, y + 170], radius=26, fill=WEISS)
    d.text((W // 2, y + 105), "Schreib uns „TUTTLINGEN“ per DM", font=font("h800", 44), fill=NAVY, anchor="mm")
    logo(img)
    return img


def c_teilbar():
    """Karussell mit Nutzwert, den man Freunden schickt (Sends)."""
    img = grund()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 300, 460, 370], radius=20, fill=ORANGE)
    d.text((260, 335), "GEHALTSGESPRÄCH", font=font("h800", 30), fill=NAVY, anchor="mm")
    y = zeilen(d, "4 Sätze, mit denen du dich unter Wert verkaufst", font("h800", 78), 80, 420, W - 160)
    y += 40
    for s in ("„Ich nehme, was Sie zahlen.“", "„Geld ist mir nicht so wichtig.“", "„Ich bin flexibel.“", "„Das passt schon so.“"):
        d.rounded_rectangle([60, y, W - 60, y + 110], radius=22, fill=DUNKEL, outline=(60, 86, 130), width=3)
        d.line([(92, y + 37), (128, y + 73)], fill=(226, 75, 74), width=9)
        d.line([(92, y + 73), (128, y + 37)], fill=(226, 75, 74), width=9)
        d.text((170, y + 55), s, font=font("h700", 42), fill=WEISS, anchor="lm")
        y += 132
    d.text((W // 2, y + 40), "Wischen: Das sagst du stattdessen", font=font("h700", 38), fill=HELL, anchor="ma")
    logo(img)
    return img


def d_sketch():
    p = os.path.join(HIER, "reels", "fertig", "2026-11-28-sketch-gleitzeit.jpg")
    return Image.open(p).convert("RGB").resize((W, H))


def main():
    os.makedirs(ZIEL, exist_ok=True)
    kacheln = [
        (a_gesicht(), "1  Eure Gesichter als Serie", "Handyvideo, 20–40 s, jede Woche gleiches Format"),
        (b_gehalt(), "2  Stellenanzeige mit Gehalt groß", "Echte Angaben vom 20.11. · Bewerbung per DM"),
        (c_teilbar(), "3  Nutzwert zum Weiterschicken", "Karussell mit Musik · zielt auf geteilte Beiträge"),
        (d_sketch(), "4  Comic-Sketch mit Wiedererkennung", "Läuft schon (Mi/Sa) · Humor wird geteilt"),
    ]
    tw, th = 540, 960
    B = 60 + 4 * tw + 3 * 40 + 60
    blatt = Image.new("RGB", (B, 1300), (245, 247, 251))
    d = ImageDraw.Draw(blatt)
    d.text((60, 50), "WAS REICHWEITE BRINGT – BEISPIELE FÜR INPERNELL", font=font("h800", 52), fill=NAVY)
    d.text((60, 125), "Vorschau, nichts davon ist veröffentlicht", font=font("t400", 32), fill=(90, 100, 120))
    for i, (bild, titel, unter) in enumerate(kacheln):
        x = 60 + i * (tw + 40)
        blatt.paste(bild.resize((tw, th), Image.LANCZOS), (x, 200))
        d.rectangle([x, 200, x + tw, 200 + th], outline=(200, 206, 218), width=2)
        d.text((x, 1185), titel, font=font("h800", 30), fill=NAVY)
        d.text((x, 1230), unter, font=font("t400", 24), fill=(90, 100, 120))
        bild.save(os.path.join(ZIEL, f"beispiel_{i + 1}.jpg"), quality=90)
    pfad = os.path.join(ZIEL, "beispiele.jpg")
    blatt.save(pfad, quality=90)
    print(pfad)


if __name__ == "__main__":
    main()
