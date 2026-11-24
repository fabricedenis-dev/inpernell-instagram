#!/usr/bin/env python3
"""Storyboards für Memes nach viralen Mechaniken (Recherche: research_notes/Memes Job Formate/viral.md).
Figuren: KI-Comic-Porträts der Inhaber (Freigabe in CLAUDE.md, KI-Hinweis beim Posten Pflicht).
Aufruf: python werkzeuge/storyboard_memes.py  ->  vorschau/memes/storyboard_<n>.jpg + uebersicht.jpg"""
import os
import sys

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
from bild import NAVY, ORANGE, WEISS, font, wrap  # noqa: E402

PW, PH = 540, 960            # Panel (halbe Reel-Größe)
ZIEL = os.path.join(HIER, "vorschau", "memes")
GRAU = (90, 100, 120)
ROT, GRUEN = (226, 60, 60), (34, 170, 96)
_KOPF = {}


def kopf(wer, breite):
    if (wer, breite) not in _KOPF:
        im = Image.open(os.path.join(HIER, "assets", "team", f"{wer}_comic.png")).convert("RGBA")
        _KOPF[(wer, breite)] = im.resize((breite, int(im.height * breite / im.width)), Image.LANCZOS)
    return _KOPF[(wer, breite)]


def panel(hg=(232, 236, 242)):
    img = Image.new("RGB", (PW, PH), hg)
    return img


def figur(img, wer, x, y, breite=360):
    k = kopf(wer, breite)
    img.paste(k, (x, y), k)


def text_oben(img, text, farbe=NAVY, hg=WEISS, y=110):
    d = ImageDraw.Draw(img)
    f = font("h800", 34)
    z = wrap(d, text, f, PW - 80)
    h = 24 + len(z) * 42
    d.rounded_rectangle([30, y, PW - 30, y + h], radius=16, fill=hg)
    for i, t in enumerate(z):
        d.text((50, y + 12 + i * 42), t, font=f, fill=farbe)


def blase(img, text, x, y, w=420, spitze="links", farbe=WEISS):
    d = ImageDraw.Draw(img)
    f = font("h700", 30)
    z = wrap(d, text, f, w - 40)
    h = 24 + len(z) * 38
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=farbe, outline=NAVY, width=3)
    sx = x + 50 if spitze == "links" else x + w - 70
    d.polygon([(sx, y + h - 2), (sx + 30, y + h - 2), (sx + 5, y + h + 34)], fill=farbe, outline=NAVY)
    d.line([(sx + 2, y + h - 1), (sx + 28, y + h - 1)], fill=farbe, width=4)
    for i, t in enumerate(z):
        d.text((x + 20, y + 12 + i * 38), t, font=f, fill=NAVY)


def bildschirm(img, zeilen, x=60, y=300, w=420, h=300, farbe=(30, 40, 60)):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=farbe, outline=(20, 20, 30), width=8)
    d.rectangle([x + w // 2 - 40, y + h + 8, x + w // 2 + 40, y + h + 40], fill=(60, 60, 70))
    yy = y + 30
    for t, col in zeilen:
        for z in wrap(d, t, font("h700", 28), w - 50):
            d.text((x + 25, yy), z, font=font("h700", 28), fill=col)
            yy += 36


def roboter(img, x, y, s=1.0, augen="normal"):
    d = ImageDraw.Draw(img)
    k = lambda v: int(v * s)  # noqa: E731
    d.rounded_rectangle([x, y, x + k(220), y + k(180)], radius=k(30), fill=(200, 210, 224), outline=NAVY, width=4)
    d.line([(x + k(110), y), (x + k(110), y - k(40))], fill=NAVY, width=4)
    d.ellipse([x + k(98), y - k(58), x + k(122), y - k(34)], fill=ORANGE)
    for ax in (60, 160):
        if augen == "kaputt":
            d.line([(x + k(ax - 18), y + k(60)), (x + k(ax + 18), y + k(96))], fill=ROT, width=6)
            d.line([(x + k(ax + 18), y + k(60)), (x + k(ax - 18), y + k(96))], fill=ROT, width=6)
        else:
            d.ellipse([x + k(ax - 20), y + k(58), x + k(ax + 20), y + k(98)], fill=(60, 200, 255), outline=NAVY, width=3)
    d.rounded_rectangle([x + k(60), y + k(122), x + k(160), y + k(146)], radius=k(8), fill=NAVY)


def schild(img, oben, zahl, unten, x=70, y=250, w=400, rot=False):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x + w, y + 330], radius=18, fill=(250, 246, 236), outline=NAVY, width=6)
    for i, t in enumerate(wrap(d, oben, font("h700", 22), w - 30)):
        d.text((x + w // 2, y + 16 + i * 27), t, font=font("h700", 22), fill=NAVY, anchor="ma")
    d.rounded_rectangle([x + 110, y + 110, x + w - 110, y + 230], radius=12, fill=ROT if rot else (30, 30, 36))
    d.text((x + w // 2, y + 170), zahl, font=font("h800", 84), fill=WEISS, anchor="mm")
    d.text((x + w // 2, y + 270), unten, font=font("h700", 26), fill=NAVY, anchor="ma")


def tafel(nr, titel, mechanik, panels, pointe, frage, datei):
    """panels: Liste (Bild, Zeitangabe, Beschreibung)."""
    n = len(panels)
    sp = 28
    tw, th = 300, 533
    B = 60 + n * tw + (n - 1) * sp + 60
    Hh = 1120
    t = Image.new("RGB", (B, Hh), (245, 247, 251))
    d = ImageDraw.Draw(t)
    d.text((60, 36), f"MEME-STORYBOARD {nr}", font=font("h800", 28), fill=ORANGE)
    d.text((60, 74), titel, font=font("h800", 52), fill=NAVY)
    d.text((60, 146), "Virale Mechanik: " + mechanik, font=font("t400", 28), fill=GRAU)
    for i, (img, zeit, txt) in enumerate(panels):
        x = 60 + i * (tw + sp)
        t.paste(img.resize((tw, th), Image.LANCZOS), (x, 200))
        d.rectangle([x, 200, x + tw, 200 + th], outline=(200, 206, 218), width=2)
        d.text((x, 748), zeit, font=font("h800", 24), fill=ORANGE)
        for k, z in enumerate(wrap(d, txt, font("t400", 22), tw)[:5]):
            d.text((x, 782 + k * 28), z, font=font("t400", 22), fill=NAVY)
    y = 960
    d.rounded_rectangle([60, y, B - 60, y + 120], radius=16, fill=(16, 40, 74))
    d.text((90, y + 20), "Pointe: " + pointe, font=font("h700", 28), fill=WEISS)
    d.text((90, y + 66), "Frage im Bildtext: " + frage, font=font("t400", 26), fill=(200, 212, 232))
    os.makedirs(ZIEL, exist_ok=True)
    t.save(os.path.join(ZIEL, datei), quality=90)
    return t


# ---------------------------------------------------------------- 1  KI-Recruiter hängt fest
def sb1():
    p = []
    a = panel()
    text_oben(a, "POV: Dein Vorstellungsgespräch 2026 führt eine KI")
    roboter(a, 160, 380, 1.0)
    figur(a, "pascal", 120, 640, 300)
    p.append((a, "0–2 s", "Hook als Text. Pascal sitzt vor einem Bildschirm mit KI-Recruiterin."))
    b = panel()
    roboter(b, 160, 330)
    blase(b, "Erzählen Sie mir von Ihren Stärken.", 60, 140)
    figur(b, "pascal", 120, 640, 300)
    p.append((b, "2–5 s", "Freundliche Roboterstimme stellt die Standardfrage."))
    c = panel()
    roboter(c, 160, 330)
    figur(c, "pascal", 120, 640, 300)
    blase(c, "Ich bin sehr zuverlässig und belastbar.", 90, 520, w=380, spitze="rechts")
    p.append((c, "5–8 s", "Pascal fängt motiviert an zu antworten."))
    e = panel()
    roboter(e, 160, 330, augen="kaputt")
    blase(e, "Stärken. Stärken. Stärken. Stärken. Stärken.", 60, 120)
    figur(e, "pascal", 120, 640, 300)
    p.append((e, "8–12 s", "KI hängt sich auf, wiederholt ein Wort, Bild ruckelt, Fehlerton."))
    f = panel()
    roboter(f, 160, 330, augen="kaputt")
    figur(f, "pascal", 120, 640, 300)
    blase(f, "Kann ich bitte mit einem Menschen sprechen?", 70, 500, w=400, spitze="rechts")
    p.append((f, "12–15 s", "Pascal fragt trocken nach einem Menschen. Kurze Stille."))
    g = panel()
    roboter(g, 160, 330, augen="kaputt")
    blase(g, "Ich bin ein Mensch. Ich bin ein Mensch. Ich bin ein Mensch.", 60, 120)
    figur(g, "pascal", 120, 640, 300)
    p.append((g, "15–18 s", "Pointe. Schnitt, Ba-dum-tss, Logo."))
    return tafel(1, "Die KI-Recruiterin", "Technik versagt genau da, wo sie Menschen ersetzen soll "
                 "(stärkstes neues Thema 2025/26)", p, "„Ich bin ein Mensch. Ich bin ein Mensch. Ich bin ein Mensch.“",
                 "Hattest du schon ein Gespräch mit einer KI?", "storyboard_1.jpg")


# ---------------------------------------------------------------- 2  Übersetzung Stellenanzeige
def sb2():
    paare = [("Flache Hierarchien", "Der Chef sitzt neben dir und sieht deinen Bildschirm."),
             ("Familiäres Arbeitsklima", "Der Chef ist der Onkel vom Chef."),
             ("Hohe Belastbarkeit", "Wir sind zu dritt. Für den Job von sechs."),
             ("Attraktives Gehalt", "Wir sagen dir die Zahl. Im vierten Gespräch.")]
    p = []
    a = panel()
    text_oben(a, "Stellenanzeigen, ehrlich übersetzt")
    figur(a, "fabrice", 30, 560, 250)
    figur(a, "pascal", 270, 560, 250)
    d = ImageDraw.Draw(a)
    d.rounded_rectangle([60, 300, 480, 500], radius=14, fill=WEISS, outline=NAVY, width=4)
    d.text((80, 320), "STELLENANZEIGE", font=font("h800", 26), fill=ORANGE)
    for i, t in enumerate(("Wir bieten:", "flache Hierarchien", "familiäres Klima", "attraktives Gehalt")):
        d.text((80, 360 + i * 32), t, font=font("t400", 26), fill=NAVY)
    p.append((a, "0–2 s", "Hook: Fabrice liest vor, Pascal übersetzt."))
    for k, (floskel, klartext) in enumerate(paare):
        b = panel()
        figur(b, "fabrice", 30, 560, 250)
        figur(b, "pascal", 270, 560, 250)
        d = ImageDraw.Draw(b)
        d.rounded_rectangle([40, 120, PW - 40, 200], radius=14, fill=NAVY)
        d.text((PW // 2, 160), floskel, font=font("h800", 34), fill=WEISS, anchor="mm")
        d.text((PW // 2, 230), "Übersetzung:", font=font("h700", 26), fill=ORANGE, anchor="mm")
        blase(b, klartext, 70, 270, w=400, spitze="rechts", farbe=(255, 238, 214))
        p.append((b, f"{2 + k * 3}–{5 + k * 3} s",
                  f"Fabrice: „{floskel}“. Pascal trocken mit Übersetzung, kurzer Soundeffekt."))
    return tafel(2, "Stellenanzeigen, ehrlich übersetzt", "Korporatsprache in Klartext + Mitmach-Frage "
                 "(Kommentare sind der Inhalt)", p, "„Attraktives Gehalt“ – wir sagen dir die Zahl. Im vierten Gespräch.",
                 "Welche Floskel aus Stellenanzeigen fehlt noch?", "storyboard_2.jpg")


# ---------------------------------------------------------------- 3  Tage ohne „Ich bin Perfektionist“
def sb3():
    p = []
    a = panel()
    text_oben(a, "Unser Büro hat jetzt einen Zähler")
    schild(a, "Tage ohne „Meine Schwäche: Ich bin Perfektionist“", "14", "Rekord: 15")
    figur(a, "waldemar", 110, 640, 300)
    p.append((a, "0–2 s", "Hook. Waldemar zeigt stolz auf das Schild: 14 Tage."))
    b = panel()
    schild(b, "Tage ohne „Meine Schwäche: Ich bin Perfektionist“", "14", "Rekord: 15")
    blase(b, "Und was ist Ihre größte Schwäche?", 60, 620, w=420)
    p.append((b, "2–4 s", "Neues Gespräch. Fabrice stellt die Frage (aus dem Off)."))
    c = panel()
    schild(c, "Tage ohne „Meine Schwäche: Ich bin Perfektionist“", "14", "Rekord: 15")
    figur(c, "pascal", 120, 640, 300)
    blase(c, "Ich würde sagen: Ich bin Perfektionist.", 60, 600, w=420, spitze="rechts")
    p.append((c, "4–7 s", "Pascal als Bewerber, sehr zufrieden mit sich."))
    e = panel()
    schild(e, "Tage ohne „Meine Schwäche: Ich bin Perfektionist“", "0", "Rekord: 15", rot=True)
    figur(e, "waldemar", 110, 640, 300)
    p.append((e, "7–9 s", "Zähler springt auf 0 (rot, Fehlerton). Waldemar reißt resigniert ein Blatt ab."))
    f = panel()
    schild(f, "Tage ohne „Ich arbeite zu viel“", "0", "Rekord: 2", rot=True)
    figur(f, "waldemar", 110, 640, 300)
    p.append((f, "9–12 s", "Zweites Schild daneben, auch auf 0. Waldemar schaut in die Kamera."))
    return tafel(3, "Der Zähler", "„X Tage seit“-Zähler (HRjak-Meme) + Selbstironie aus Recruiter-Sicht",
                 p, "Zähler springt auf 0 – und es gibt noch ein zweites Schild.",
                 "Was war die schlimmste Antwort auf die Schwächen-Frage, die du je gehört oder gesagt hast?",
                 "storyboard_3.jpg")


# ---------------------------------------------------------------- 4  Bewerbungsformular als Horrorfilm
def sb4():
    dunkel = (14, 16, 24)
    p = []
    a = panel(dunkel)
    text_oben(a, "Ein Horrorfilm in 4 Akten: Die Online-Bewerbung", farbe=WEISS, hg=(60, 20, 24))
    figur(a, "pascal", 120, 640, 300)
    p.append((a, "0–2 s", "Dunkel, Gruselmusik. Pascal sitzt nachts am Laptop."))
    b = panel(dunkel)
    bildschirm(b, [("AKT 1", ORANGE), ("Lebenslauf hochladen", WEISS), ("✓ erfolgreich", GRUEN)])
    figur(b, "pascal", 120, 640, 300)
    p.append((b, "2–5 s", "Alles gut. Pascal lächelt erleichtert."))
    c = panel(dunkel)
    bildschirm(c, [("AKT 2", ORANGE), ("Bitte alle Daten aus dem Lebenslauf noch einmal manuell eingeben.", WEISS)])
    figur(c, "pascal", 120, 640, 300)
    p.append((c, "5–8 s", "Musik wird lauter. Pascal schaut langsam hoch."))
    e = panel(dunkel)
    bildschirm(e, [("AKT 3", ORANGE), ("Beschreiben Sie sich in drei Wörtern. Maximal 2.000 Zeichen.", WEISS)])
    figur(e, "pascal", 120, 640, 300)
    p.append((e, "8–11 s", "Licht flackert."))
    f = panel(dunkel)
    bildschirm(f, [("AKT 4", ORANGE), ("Sitzung abgelaufen.", ROT), ("Alle Eingaben gelöscht.", ROT)], farbe=(60, 10, 14))
    figur(f, "pascal", 120, 640, 300)
    p.append((f, "11–14 s", "Jumpscare: roter Bildschirm, Schrei-Effekt (kein fremder Sound)."))
    return tafel(4, "Die Online-Bewerbung (Horrorfilm)", "Reale Angst absurd übertreiben (Formular als Jumpscare)",
                 p, "„Sitzung abgelaufen. Alle Eingaben gelöscht.“",
                 "Bei welchem Bewerbungsportal hast du schon aufgegeben?", "storyboard_4.jpg")


def main():
    tafeln = [sb1(), sb2(), sb3(), sb4()]
    b = max(t.width for t in tafeln)
    u = Image.new("RGB", (b, sum(t.height for t in tafeln)), (245, 247, 251))
    y = 0
    for t in tafeln:
        u.paste(t, (0, y))
        y += t.height
    u = u.resize((u.width // 2, u.height // 2), Image.LANCZOS)
    u.save(os.path.join(ZIEL, "uebersicht.jpg"), quality=88)
    print(ZIEL)


if __name__ == "__main__":
    main()
