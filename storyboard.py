#!/usr/bin/env python3
"""Storyboards für Comic-Sketche: je Idee eine Bildtafel (Hook oben, 6 Bilder mit Dialog, Abschluss unten).
Dient zur Auswahl, bevor ein Video gebaut wird. Aufruf: python storyboard.py -> vorschau/storyboards/*.jpg"""
import math
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

import reel_design as rd
import zeichentrick_comic as c
from bild import NAVY, ORANGE, WEISS, font, wrap

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HIER, "vorschau", "storyboards")
W, H, K = c.W, c.H, c.K
STRICH = c.STRICH
KOPF_Y = 1007          # Kopfmitte sitzender Figuren (für Effekte)


def szene(wer, stuhl=None, sticker=None, fx=None, sepia=False, schnee=False, schild=None, zoom=1.0, **kw):
    stuhl = stuhl or ("hocker" if wer == "genz" else "buero")
    cx = 540 if wer == "genz" else 680
    img = c.hintergrund(stuhl)
    c.figur(img, cx, 1560, wer, sitzt=True, **kw)
    if fx:
        c.effekte(img, fx, cx, KOPF_Y)
    img = c.fertig(img)
    if zoom != 1.0:
        cw, ch = int(W / zoom), int(H / zoom)
        x, y = max(0, min(W - cw, cx - cw // 2)), max(0, min(H - ch, int(1000 - ch * 0.45)))
        img = img.crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
    if schnee:
        d = ImageDraw.Draw(img)
        import random
        r = random.Random(3)
        for _ in range(260):
            x, y, s = r.randint(0, W), r.randint(0, H), r.choice([3, 4, 6])
            d.ellipse([x - s, y - s, x + s, y + s], fill=(240, 246, 255))
    if schild:
        d = ImageDraw.Draw(img)
        d.rectangle([800, 980, 820, 1300], fill=(150, 150, 160), outline=STRICH, width=4)
        d.rounded_rectangle([700, 880, 920, 990], radius=12, fill=(250, 200, 40), outline=STRICH, width=6)
        d.text((810, 935), schild, font=font("h800", 56), fill=STRICH, anchor="mm")
    if sepia:
        g = ImageEnhance.Contrast(ImageOps.grayscale(img)).enhance(1.05)
        img = ImageOps.colorize(g, (60, 40, 20), (250, 232, 200))
    if sticker:
        rgba = img.convert("RGBA")
        rd.sticker(rgba, sticker, (W // 2 - 200, 330), winkel=-3, fuell=(255, 196, 64), schrift=STRICH, groesse=40)
        img = rgba.convert("RGB")
    return img


def winterstrasse(text_schild="B 500"):
    """Schwarzwald-Winterstraße bei Nacht: Tannen, Schneefall, rutschendes Auto, Straßenschild."""
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)], fill=(int(14 + 20 * t), int(30 + 30 * t), int(62 + 40 * t)))
    for x, h in ((60, 520), (220, 640), (380, 480), (760, 560), (930, 680), (1060, 500)):          # Tannen
        for k in range(4):
            yy = 1150 - k * h * 0.22
            b = h * 0.55 * (1 - k * 0.2)
            d.polygon([(x - b / 2, yy), (x, yy - h * 0.38), (x + b / 2, yy)], fill=(20, 60, 54), outline=STRICH)
            d.line([(x - b / 2 + 10, yy - 6), (x + b / 2 - 10, yy - 6)], fill=(236, 242, 250), width=8)
    d.rectangle([0, 1150, W, H], fill=(226, 234, 244))
    d.polygon([(300, 1150), (780, 1150), (1080, H), (0, H)], fill=(90, 98, 116))
    for k in range(6):                                                                         # Mittellinie
        y0 = 1180 + k * 130
        d.polygon([(536 - k * 4, y0), (544 + k * 4, y0), (546 + k * 6, y0 + 70), (534 - k * 6, y0 + 70)], fill=WEISS)
    auto = Image.new("RGBA", (520, 300), (0, 0, 0, 0))
    a = ImageDraw.Draw(auto)
    a.rounded_rectangle([20, 110, 500, 230], radius=40, fill=ORANGE, outline=STRICH, width=8)
    a.polygon([(110, 115), (170, 40), (360, 40), (420, 115)], fill=ORANGE, outline=STRICH)
    a.polygon([(140, 112), (185, 58), (260, 58), (260, 112)], fill=(170, 210, 240), outline=STRICH)
    a.polygon([(275, 112), (275, 58), (345, 58), (395, 112)], fill=(170, 210, 240), outline=STRICH)
    for wx in (120, 400):
        a.ellipse([wx - 50, 180, wx + 50, 280], fill=STRICH)
        a.ellipse([wx - 22, 208, wx + 22, 252], fill=(150, 150, 160))
    auto = auto.rotate(14, resample=Image.BICUBIC, expand=True)
    img.paste(auto, (300, 1260), auto)
    for k in range(5):                                                                         # Rutsch-Striche
        d.arc([180 + k * 18, 1430 + k * 22, 360 + k * 18, 1560 + k * 22], 200, 300, fill=WEISS, width=6)
    d.rectangle([880, 1000, 900, 1300], fill=(150, 150, 160), outline=STRICH, width=4)
    d.rounded_rectangle([780, 900, 1000, 1010], radius=12, fill=(250, 200, 40), outline=STRICH, width=6)
    d.text((890, 955), text_schild, font=font("h800", 56), fill=STRICH, anchor="mm")
    import random
    r = random.Random(5)
    for _ in range(320):
        x, y, s = r.randint(0, W), r.randint(0, H), r.choice([3, 4, 6])
        d.ellipse([x - s, y - s, x + s, y + s], fill=(240, 246, 255))
    return img


def tafel(nr, titel, hook, bilder, ende, warum, datei):
    """bilder: Liste von (Bild, Sprecher, Text, pointe?)."""
    B, Hh = 1200, 2400
    tafel = Image.new("RGB", (B, Hh), NAVY)
    d = ImageDraw.Draw(tafel)
    d.text((50, 40), f"SKETCH-IDEE {nr}", font=font("h800", 30), fill=ORANGE)
    d.text((50, 80), titel, font=font("h800", 56), fill=WEISS)
    d.rounded_rectangle([50, 165, B - 50, 245], radius=18, fill=(255, 196, 64))
    d.text((70, 205), "Hook (Sek. 0–2): " + hook, font=font("h800", 30), fill=STRICH, anchor="lm")
    pw, ph = 350, 622
    for i, (img, wer, text, pointe) in enumerate(bilder):
        x = 50 + (i % 3) * (pw + 25)
        y = 280 + (i // 3) * (ph + 300)
        tafel.paste(img.resize((pw, ph), Image.LANCZOS), (x, y))
        d.rectangle([x, y, x + pw, y + ph], outline=ORANGE if pointe else (60, 84, 124), width=8 if pointe else 3)
        d.ellipse([x - 14, y - 14, x + 40, y + 40], fill=ORANGE, outline=STRICH, width=3)
        d.text((x + 13, y + 13), str(i + 1), font=font("h800", 30), fill=STRICH, anchor="mm")
        if pointe:
            d.rounded_rectangle([x + pw - 140, y + 10, x + pw - 10, y + 50], radius=12, fill=ORANGE)
            d.text((x + pw - 75, y + 30), "POINTE", font=font("h800", 22), fill=STRICH, anchor="mm")
        d.text((x, y + ph + 14), wrap(d, wer.upper(), font("h800", 22), pw)[0], font=font("h800", 22), fill=ORANGE)
        for k, z in enumerate(wrap(d, text, font("h700", 28), pw)[:6]):
            d.text((x, y + ph + 46 + k * 36), z, font=font("h700", 28), fill=WEISS)
    y = 280 + 2 * (ph + 300) - 20
    d.rounded_rectangle([50, y, B - 50, y + 130], radius=18, fill=(16, 40, 74), outline=ORANGE, width=3)
    d.text((70, y + 18), "ABSCHLUSS (Michael spricht, blaue Inpernell-Seite):", font=font("h800", 24), fill=ORANGE)
    for k, z in enumerate(wrap(d, ende, font("h700", 30), B - 140)[:2]):
        d.text((70, y + 54 + k * 36), z, font=font("h700", 30), fill=WEISS)
    for k, z in enumerate(wrap(d, "Warum es zündet: " + warum, font("t400", 26), B - 100)[:3]):
        d.text((50, y + 150 + k * 34), z, font=font("t400", 26), fill=(200, 210, 228))
    os.makedirs(ZIEL, exist_ok=True)
    tafel.save(os.path.join(ZIEL, datei), quality=90)
    return tafel


def main():
    t = []
    # 1 – Runde 6
    t.append(tafel(1, "Runde 6", "„Glückwunsch, du bist in Runde 6!“", [
        (szene("personaler", arm="tisch_hoch", mund="grinsen", augen="gross", sticker="RUNDE 6"), "Personaler",
         "Glückwunsch, du bist in Runde 6!", False),
        (szene("genz", arm="handy", augen="muede", sticker="RUNDE 1–5"), "Bewerber",
         "Nach HR, Fachbereich, Fallstudie, Teamessen und Geschäftsführung?", False),
        (szene("personaler", arm="tisch", brauen="sorge", augen="normal"), "Personaler",
         "Leider haben wir die Stelle intern besetzt.", False),
        (szene("genz", arm="achselzucken", augen="gross", brauen="hoch", mund="offen"), "Bewerber", "Mit wem?", False),
        (szene("personaler", arm="tisch", mund="schief", fx="schweiss", zoom=1.25), "Personaler",
         "Mit dem aus Runde 3. Der hat dich interviewt.", True),
        (szene("genz", arm="handy", augen="genervt", fx="fragezeichen"), "Bewerber", "(schweigt, Ba-dum-tss)", False)],
        "Bevor du in Runde 1 gehst, klären wir mit dem Arbeitgeber, ob die Stelle wirklich offen ist.",
        "Endlose Interviewrunden kennt jeder Bewerber. Die Pointe: Er war nie wirklich im Rennen.", "1-runde-6.jpg"))
    # 2 – Laptop kommt Montag
    t.append(tafel(2, "Laptop kommt Montag", "„Erster Arbeitstag. Wo ist mein Laptop?“", [
        (szene("genz", arm="achselzucken", augen="gross", sticker="TAG 1"), "Neuer", "Erster Tag! Wo ist mein Laptop?", False),
        (szene("personaler", arm="tisch", mund="grinsen"), "Chef", "Kommt Montag.", False),
        (szene("genz", arm="handy", augen="muede", sticker="TAG 8"), "Neuer", "Und? Laptop?", False),
        (szene("personaler", arm="tisch", mund="grinsen"), "Chef", "Kommt Montag.", False),
        (szene("genz", arm="handy", augen="muede", sticker="TAG 60", brauen="gelangweilt"), "Neuer",
         "(liest das ausgedruckte Handbuch, Seite 412)", False),
        (szene("genz", arm="achselzucken", mund="grinsen", augen="normal", sticker="TAG 61", zoom=1.2), "Neuer",
         "Zum nächsten Neuen: „Laptop? Kommt Montag.“", True)],
        "Wir fragen nach deiner ersten Woche nach, ob alles läuft. Und wenn nicht, klären wir das.",
        "Chaotisches Onboarding kennt jeder. Die Pointe: Er ist jetzt selbst Teil des Systems (Kreislauf).",
        "2-laptop-kommt-montag.jpg"))
    # 3 – Bewerbung 1995 vs. heute
    t.append(tafel(3, "Bewerbung 1995 vs. heute", "„1995: Mappe, Passfoto, Briefmarke.“", [
        (szene("personaler", arm="tisch", mund="grinsen", sepia=True, sticker="1995"), "Bewerber 1995",
         "Mappe, Passfoto, Briefmarke. Fertig.", False),
        (szene("genz", arm="handy", augen="muede", sticker="HEUTE"), "Bewerber heute",
         "45 Minuten Portal. Lebenslauf hochladen.", False),
        (szene("genz", arm="handy", augen="gross", brauen="hoch", mund="offen"), "Bewerber heute",
         "„Bitte alle Daten noch einmal manuell eingeben.“", False),
        (szene("personaler", arm="tisch", sepia=True, brauen="hoch"), "Bewerber 1995", "Und wann kam die Antwort?", False),
        (szene("genz", arm="achselzucken", augen="genervt", mund="schief", zoom=1.25), "Bewerber heute",
         "Nach drei Wochen. Wie bei dir. Nur automatisch.", True),
        (szene("personaler", arm="tisch_hoch", sepia=True, mund="grinsen", fx="fragezeichen"), "Bewerber 1995",
         "(lacht, Ba-dum-tss)", False)],
        "30 Jahre Fortschritt und trotzdem warten? Bei uns sprichst du mit einem Menschen.",
        "Die Technik hat das Warten nicht abgeschafft, nur automatisiert. Jeder hat schon Daten doppelt eingetippt.",
        "3-bewerbung-1995.jpg"))
    # 4 – Gleitzeit (Schwarzwald)
    t.append(tafel(4, "Gleitzeit", "„Top-Job in Stuttgart, nur eine Stunde!“", [
        (szene("personaler", arm="tisch_hoch", mund="grinsen", augen="gross"), "Recruiter",
         "Top-Job in Stuttgart. Nur eine Stunde Fahrt!", False),
        (szene("genz", arm="handy", augen="genervt", brauen="skeptisch"), "Fachkraft (Schwarzwald)",
         "Von hier? Im Januar?", False),
        (szene("personaler", arm="tisch", mund="grinsen"), "Recruiter", "Kein Problem. Wir haben Gleitzeit.", False),
        (szene("genz", arm="handy", augen="muede", zoom=1.2), "Fachkraft", "(Pause, Grillen zirpen)", False),
        (szene("genz", arm="achselzucken", mund="schief", augen="genervt", zoom=1.25), "Fachkraft",
         "Gleiten tu ich auf der B 500 auch.", True),
        (winterstrasse(), "Einspieler", "Auto rutscht auf der verschneiten B 500 (Ba-dum-tss)", False),
        ],
        "Gute Jobs gibt es auch hier im Schwarzwald. Wir kennen die Arbeitgeber in der Region persönlich.",
        "Pendeln im Schwarzwald-Winter kennt hier jeder. Das Wortspiel Gleitzeit/glatte Straße sitzt sofort.",
        "4-gleitzeit.jpg"))
    u = Image.new("RGB", (4 * 600 + 60, 1200), "white")
    for i, im in enumerate(t):
        u.paste(im.resize((600, 1200), Image.LANCZOS), (i * 620, 0))
    u.save(os.path.join(ZIEL, "uebersicht.jpg"), quality=88)


if __name__ == "__main__":
    main()
