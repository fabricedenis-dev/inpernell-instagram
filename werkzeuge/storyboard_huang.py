#!/usr/bin/env python3
"""Storyboard Satire „Was Jensen Huang in den letzten Wochen wirklich gemacht hat“ (Wunsch des Inhabers).
Leitplanken: klar als Satire gekennzeichnet, gezeichnete Karikatur (kein Foto, keine Stimmimitation, kein
Nvidia-/GTA-Logo), kein Bezug auf die Hintergründe des Rücktritts. Pointe: Lücke im Lebenslauf.
Aufruf: python werkzeuge/storyboard_huang.py  ->  vorschau/memes/storyboard_huang.jpg"""
import os
import sys

from PIL import ImageDraw

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import storyboard_memes as sm  # noqa: E402
from bild import NAVY, ORANGE, WEISS, font  # noqa: E402

PW, PH = sm.PW, sm.PH
HAUT, HAAR, JACKE, GLANZ = (232, 196, 160), (28, 28, 32), (24, 24, 28), (90, 90, 100)


def huang(img, cx, fuss, s=1.0, jacke=True, controller=False, sitzt=False, mund="laecheln"):
    """Gezeichnete Karikatur: schwarze Haare, Lederjacke, breites Lächeln."""
    d = ImageDraw.Draw(img)
    k = lambda v: int(v * s)  # noqa: E731
    koerper_h = k(230 if not sitzt else 170)
    top = fuss - koerper_h
    farbe = JACKE if jacke else (70, 90, 130)
    d.rounded_rectangle([cx - k(110), top, cx + k(110), fuss], radius=k(50), fill=farbe, outline=(0, 0, 0), width=4)
    if jacke:                                                         # Revers und Glanzlichter der Lederjacke
        d.polygon([(cx - k(30), top), (cx, top + k(90)), (cx - k(70), top + k(20))], fill=(40, 40, 46), outline=(0, 0, 0))
        d.polygon([(cx + k(30), top), (cx, top + k(90)), (cx + k(70), top + k(20))], fill=(40, 40, 46), outline=(0, 0, 0))
        d.line([(cx - k(80), top + k(40)), (cx - k(85), top + k(140))], fill=GLANZ, width=k(6))
        d.line([(cx + k(80), top + k(40)), (cx + k(85), top + k(140))], fill=GLANZ, width=k(6))
        d.polygon([(cx - k(22), top), (cx + k(22), top), (cx, top + k(60))], fill=(30, 30, 34))
    kopf_y = top - k(95)
    d.ellipse([cx - k(85), kopf_y - k(95), cx + k(85), kopf_y + k(95)], fill=HAUT, outline=(0, 0, 0), width=4)
    d.chord([cx - k(90), kopf_y - k(105), cx + k(90), kopf_y + k(30)], 180, 360, fill=HAAR)   # Haare
    d.polygon([(cx - k(90), kopf_y - k(30)), (cx + k(40), kopf_y - k(70)), (cx + k(90), kopf_y - k(30)),
               (cx + k(88), kopf_y - k(60)), (cx - k(70), kopf_y - k(100))], fill=HAAR)
    for ax in (-35, 35):
        d.arc([cx + k(ax - 16), kopf_y - k(10), cx + k(ax + 16), kopf_y + k(14)], 200, 340, fill=(0, 0, 0), width=k(5))
    if mund == "laecheln":
        d.chord([cx - k(42), kopf_y + k(25), cx + k(42), kopf_y + k(70)], 0, 180, fill=(120, 30, 30), outline=(0, 0, 0))
        d.rectangle([cx - k(34), kopf_y + k(47), cx + k(34), kopf_y + k(52)], fill=WEISS)
    else:
        d.line([(cx - k(25), kopf_y + k(50)), (cx + k(25), kopf_y + k(50))], fill=(0, 0, 0), width=k(5))
    if controller:
        d.rounded_rectangle([cx - k(70), top + k(60), cx + k(70), top + k(110)], radius=k(22), fill=(60, 60, 70),
                            outline=(0, 0, 0), width=3)
        for bx, col in ((40, (220, 60, 60)), (52, (60, 180, 90))):
            d.ellipse([cx + k(bx - 6), top + k(74), cx + k(bx + 6), top + k(86)], fill=col)


def satire(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([PW - 170, 60, PW - 30, 100], radius=10, fill=(226, 60, 60))
    d.text((PW - 100, 80), "SATIRE", font=font("h800", 24), fill=WEISS, anchor="mm")


def main():
    p = []
    a = sm.panel()
    sm.text_oben(a, "Was Jensen Huang in den letzten Wochen wirklich gemacht hat", y=120)
    d = ImageDraw.Draw(a)
    d.rounded_rectangle([150, 520, 390, 760], radius=20, fill=(110, 80, 60), outline=NAVY, width=4)   # Chefsessel
    d.rectangle([255, 760, 285, 840], fill=(80, 80, 90))
    d.polygon([(170, 530), (370, 530), (350, 700), (190, 700)], fill=JACKE)                       # Jacke auf Sessel
    d.rounded_rectangle([120, 380, 420, 450], radius=10, fill=(255, 240, 170), outline=NAVY, width=3)
    d.text((270, 415), "Bin gleich zurück", font=font("h700", 26), fill=NAVY, anchor="mm")
    satire(a)
    p.append((a, "0–2 s", "Hook + Etikett SATIRE. Leerer Chefsessel, Lederjacke hängt drüber, Zettel."))

    b = sm.panel((24, 26, 40))
    sm.bildschirm(b, [("GTA VI", ORANGE), ("Spielzeit: 212 Std.", WEISS)], y=200)
    huang(b, PW // 2, 900, 0.9, jacke=False, controller=True, sitzt=True)
    satire(b)
    p.append((b, "2–5 s", "Nachts auf dem Sofa, Hoodie statt Lederjacke, Controller. Text: „Tag 1 bis 12“."))

    c = sm.panel((24, 26, 40))
    sm.bildschirm(c, [("Alle Missionen", WEISS), ("100 % abgeschlossen", (60, 200, 120)),
                      ("Grafik: Ultra. Natürlich.", ORANGE)], y=200)
    huang(c, PW // 2, 900, 0.9, jacke=False, controller=True, sitzt=True)
    satire(c)
    p.append((c, "5–8 s", "Erfolg auf dem Bildschirm. Gag: „Grafik: Ultra. Natürlich.“ Siegessound."))

    e = sm.panel()
    huang(e, PW // 2, 900, 1.0, jacke=True)
    sm.blase(e, "So. Durchgespielt. Ich wäre dann wieder da.", 60, 160)
    satire(e)
    p.append((e, "8–11 s", "Zieht die Lederjacke wieder an, steht auf. Zeitlupe, Gitarren-Riff (eigene Musik)."))

    f = sm.panel()
    huang(f, 170, 900, 0.75, jacke=True)
    sm.figur(f, "waldemar", 290, 640, 230)
    sm.blase(f, "Und die Lücke im Lebenslauf?", 120, 160, w=380, spitze="rechts")
    sm.blase(f, "GTA 6. Teamfähig, stressresistent, fahre Fluchtwagen.", 40, 400, w=330)
    satire(f)
    p.append((f, "11–15 s", "Bewerbungsgespräch bei Waldemar. Huang beschreibt seine Lücke selbstbewusst."))

    g = sm.panel()
    sm.figur(g, "waldemar", 110, 640, 300)
    sm.blase(g, "Klingt nach Führungserfahrung. Wann kannst du anfangen?", 60, 260)
    satire(g)
    p.append((g, "15–18 s", "Pointe. Ba-dum-tss. Abschluss: „Lücke im Lebenslauf? Kein Weltuntergang.“"))
    sm.tafel("Huang", "Satire: Huang ist zurück (vom Zocken)",
             "aktueller Aufhänger + Lücke im Lebenslauf (Selbstironie, kein Bezug auf den Rücktrittsgrund)", p,
             "„Klingt nach Führungserfahrung. Wann kannst du anfangen?“",
             "Was war die kreativste Erklärung für eine Lücke im Lebenslauf, die du je gehört hast?",
             "storyboard_huang.jpg")
    print(os.path.join(sm.ZIEL, "storyboard_huang.jpg"))


if __name__ == "__main__":
    main()
