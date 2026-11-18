"""Inpernell – Sonder-Reel zum Game-Release-Tag (19.11.2026): 80er-Neon-Look, Comic-Figuren, eigene Synthwave-Musik.

Bewusst KEINE fremden Marken: kein Spielname, kein Logo, keine Originalschrift, keine Original-Grafiken.
Der Bezug entsteht über Look (Neon, Palmen + Schwarzwald, Sterne, Mission) und den Starttag.

Comic-Porträts: assets/team/*_comic.png (erzeugt mit werkzeuge/comic.py aus den Fotos von inpernell.de).
Aufruf: python game_reel.py ziel.mp4 titelbild.jpg
"""
import math
import os
import random
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

import reel_design as rd
from bild import ORANGE, WEISS, font
from musik import erzeuge_synthwave
from reel_anim import _ease, _zeige

W, H, FPS, M = rd.W, rd.H, 30, rd.M
HIER = os.path.dirname(os.path.abspath(__file__))
BPM = 112
SCHLAG = 60.0 / BPM
PINK, TUERKIS, GELB, ROT, TINTE = (255, 60, 170), (40, 230, 230), (255, 210, 70), (230, 30, 50), (20, 10, 36)
NACHT = (14, 4, 40)


def portrait(name, hoehe):
    p = Image.open(os.path.join(HIER, "assets", "team", f"{name}_comic.png")).convert("RGBA")
    return p.resize((int(p.width * hoehe / p.height), hoehe), Image.LANCZOS)


# ---------------------------------------------------------------- Hintergrund

def verlauf(stops, w=W, h=H):
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if a <= t <= b:
                k = (t - a) / (b - a)
                c = tuple(int(ca[i] + (cb[i] - ca[i]) * k) for i in range(3))
                break
        d.line([(0, y), (w, y)], fill=c + (255,))
    return img


def _palme(d, x, y, h, farbe, neigung=1):
    pts = [(x + neigung * 40 * math.sin(t / 10 * math.pi / 2), y - h * t / 10) for t in range(11)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d.line([(x0, y0), (x1, y1)], fill=farbe, width=int(h * 0.05))
    kx, ky = pts[-1]
    for w in range(0, 360, 40):
        r, lang = math.radians(w), h * 0.42
        p = [(kx, ky)]
        for i in range(1, 9):
            t = i / 8
            p.append((kx + math.cos(r) * lang * t, ky + math.sin(r) * lang * t * 0.5 + lang * 0.35 * t * t))
        for i in range(8, 0, -1):
            t = i / 8
            p.append((kx + math.cos(r) * lang * t,
                      ky + math.sin(r) * lang * t * 0.5 + lang * 0.35 * t * t + 18 * math.sin(t * math.pi)))
        d.polygon(p, fill=farbe)


def _tanne(d, x, y, h, farbe):
    b = h * 0.42
    for k in range(3):
        yy = y - h * k * 0.28
        d.polygon([(x - b / 2 * (1 - k * 0.22), yy), (x, yy - h * 0.5), (x + b / 2 * (1 - k * 0.22), yy)], fill=farbe)


def welt(grau=False):
    """Neon-Sonnenuntergang: Streifensonne, Sterne, Gitterboden, links Palmen, rechts Schwarzwald-Tannen."""
    img = verlauf([(0, NACHT), (0.30, (58, 14, 92)), (0.52, (214, 50, 130)), (0.64, (255, 140, 60)),
                   (0.72, (255, 196, 90)), (1, NACHT)])
    d = ImageDraw.Draw(img)
    rnd = random.Random(2)
    for _ in range(90):
        x, y, r = rnd.randint(0, W), rnd.randint(200, 800), rnd.choice([1, 1, 2, 3])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 230, 255, 255))
    cx, cy, r = W // 2, 1200, 300
    sonne = Image.new("L", (W, 2 * r))
    ds = ImageDraw.Draw(sonne)
    ds.ellipse([cx - r, 0, cx + r, 2 * r], fill=255)
    for i, y in enumerate(range(r - 40, 2 * r, 40)):
        ds.rectangle([0, y, W, y + 6 + i * 3], fill=0)
    img.paste(verlauf([(0, (255, 230, 90)), (1, (255, 60, 150))], W, 2 * r), (0, cy - r), sonne)
    boden = 1330
    d.rectangle([0, boden, W, H], fill=(20, 6, 46, 255))
    for i in range(14):
        y = boden + int((i / 13) ** 2 * (H - boden))
        d.line([(0, y), (W, y)], fill=PINK + (255,), width=3)
    for i in range(-12, 13):
        d.line([(W / 2 + i * 30, boden), (W / 2 + i * 260, H)], fill=PINK + (255,), width=3)
    sil = (30, 6, 50, 255)
    for x, hh, n in [(60, 520, 1), (180, 420, -1), (300, 330, 1)]:
        _palme(d, x, boden, hh, sil, n)
    for x, hh in [(690, 230), (760, 300), (840, 380), (930, 330), (1010, 420), (1070, 300)]:
        _tanne(d, x, boden + 10, hh, sil)
    if grau:
        g = ImageEnhance.Brightness(ImageOps.grayscale(img.convert("RGB"))).enhance(0.6)
        img = ImageOps.colorize(g, (10, 10, 16), (200, 200, 210)).convert("RGBA")
    return img


def logo_klein(frame):
    """Kleines Logo unten links (freigegebene Position) auf dunkler Platte, damit es auf dem Neon-Boden lesbar ist."""
    x, y = rd.LOGO_XY
    d = ImageDraw.Draw(frame)
    d.rounded_rectangle([x - 14, y - 12, x + rd.LOGO_BREITE + 14, y + 74], radius=16, fill=NACHT + (255,))
    rd.logo_marke(frame)


# ---------------------------------------------------------------- Bausteine (je eine transparente Ebene)

def neu():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def ebene(img):
    box = img.getbbox()
    return (img.crop(box), box) if box else None


def titel(text, xy, groesse, oben=PINK, unten=GELB, schraeg=0.18, rand=10, mitte=False, maxbreite=W - 2 * M):
    """Schräger Titel mit Farbverlauf, Kontur und hartem Schatten (ohne Weichzeichner). Gibt (Ebene, Unterkante)."""
    mess = ImageDraw.Draw(Image.new("L", (1, 1)))
    while groesse > 40:
        f = font("h800", groesse)
        bw = mess.textbbox((0, 0), text, font=f, stroke_width=rand)
        if bw[2] - bw[0] + groesse * schraeg <= maxbreite:
            break
        groesse -= 4
    tw, th = bw[2] - bw[0] + 40, bw[3] - bw[1] + 40
    pos = (20 - bw[0], 20 - bw[1])
    def maske(**kw):
        m = Image.new("L", (tw, th))
        ImageDraw.Draw(m).text(pos, text, font=f, fill=255, **kw)
        return m
    teil = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    teil.paste((255, 255, 255, 255), (0, 0), maske(stroke_width=rand, stroke_fill=255).point(lambda v: 255 if v else 0))
    teil.paste(TINTE + (255,), (0, 0), maske(stroke_width=max(2, rand // 3), stroke_fill=255))
    teil.paste(verlauf([(0, oben), (1, unten)], tw, th), (0, 0), maske())
    sh = int(th * schraeg)
    teil = teil.transform((tw + sh, th), Image.AFFINE, (1, schraeg, -sh, 0, 1, 0), Image.BICUBIC)
    schatten = Image.new("RGBA", teil.size, (14, 6, 30, 255))
    schatten.putalpha(teil.getchannel("A"))
    x, y = xy
    if mitte:
        x -= teil.width // 2
    img = neu()
    img.alpha_composite(schatten, (x + 12, y + 14))
    img.alpha_composite(teil, (x, y))
    return img, y + teil.height


def ktext(text, xy, groesse, fill=WEISS, breite=6, anchor="la", art="h800"):
    img = neu()
    ImageDraw.Draw(img).text(xy, text, font=font(art, groesse), fill=fill, stroke_width=breite, stroke_fill=TINTE,
                             anchor=anchor)
    return img


def sticker(text, xy, fuell=GELB, schrift=TINTE, groesse=34, winkel=-3):
    img = neu()
    rd.sticker(img, text, xy, winkel=winkel, fuell=fuell, schrift=schrift, groesse=groesse)
    return img


def stern(d, cx, cy, r, farbe=WEISS):
    pts = [(cx + (r if i % 2 == 0 else r * 0.45) * math.sin(i * math.pi / 5),
            cy - (r if i % 2 == 0 else r * 0.45) * math.cos(i * math.pi / 5)) for i in range(10)]
    d.polygon(pts, fill=farbe, outline=TINTE, width=5)


def ein_stern(cx, cy, r=30, farbe=WEISS):
    img = neu()
    stern(ImageDraw.Draw(img), cx, cy, r, farbe)
    return img


# ---------------------------------------------------------------- Szenen

def szene_hook():
    hg = welt()
    el = [(sticker("HEUTE IST RELEASE-TAG", (M - 6, 420)), "pop", -0.3)]
    l1, y = titel("Heute zockt", (M - 10, 520), 104)
    l2, y = titel("ganz Deutschland.", (M - 10, y - 10), 104)
    el += [(l1, "punch", -0.2), (l2, "punch", 1)]
    for i in range(5):
        el.append((ein_stern(660 + i * 72, 270), "pop", 2.5 + 0.5 * i))
    el.append((ktext("GESUCHT: TALENTE", (628, 312), 30, breite=5), "hoch", 5))
    el.append((ktext("Und wir?", (M, y + 30), 64), "hoch", 6))
    el.append((ktext("Haben trotzdem offen.", (M, y + 110), 64, fill=TUERKIS), "pop", 7))
    return {"hg": hg, "schlaege": 10, "el": el}


def szene_gekuendigt():
    hg = welt(grau=True)
    t, _ = titel("GEKÜNDIGT.", (W // 2, 640), 170, oben=(255, 70, 70), unten=ROT, mitte=True, schraeg=0.08)
    knopf = neu()
    d = ImageDraw.Draw(knopf)
    d.rounded_rectangle([M, 1010, W - M, 1130], radius=24, fill=TUERKIS + (255,), outline=TINTE, width=6)
    d.text((W // 2, 1070), "Respawn bei Inpernell", font=font("h800", 62), fill=TINTE, anchor="mm")
    el = [(t, "punch", 0), (ktext("Kein Stress.", (W // 2, 930), 70, anchor="mm"), "hoch", 2.5), (knopf, "pop", 4)]
    return {"hg": hg, "schlaege": 7, "el": el, "wackeln": (0, 0.9), "blitz": True}


def szene_crew():
    hg = welt()
    t, _ = titel("DIE CREW", (M - 10, 250), 130, oben=TUERKIS, unten=(140, 255, 240))
    el = [(t, "links", 0)]
    felder = [("fabrice", [(M - 30, 480), (560, 430), (520, 1010), (M - 30, 1060)], PINK, 640, (-60, 470), "links", 1),
              ("pascal", [(575, 425), (W - 120, 380), (W - 140, 960), (535, 1005)], TUERKIS, 560, (470, 445), "rechts", 2),
              ("waldemar", [(M - 30, 1080), (W - 145, 980), (W - 160, 1340), (M - 30, 1390)], ORANGE, 560, (380, 960),
               "hoch", 3)]
    for n, poly, farbe, skal, (px, py), eff, schlag in felder:
        maske = Image.new("L", (W, H))
        ImageDraw.Draw(maske).polygon(poly, fill=255)
        feld = verlauf([(0, farbe), (1, (60, 14, 90))])
        fd = ImageDraw.Draw(feld)
        for k in range(-H, W, 46):
            fd.line([(k, 0), (k + H, H)], fill=tuple(min(255, c + 25) for c in farbe) + (255,), width=10)
        feld.alpha_composite(portrait(n, skal), (px, py))
        img = neu()
        img.paste(feld, (0, 0), maske)
        ImageDraw.Draw(img).line(poly + [poly[0]], fill=TINTE, width=14, joint="curve")
        el.append((img, eff, schlag))
    for i, (name, xy) in enumerate([("FABRICE", (M, 960)), ("PASCAL", (600, 900)), ("WALDEMAR", (M + 10, 1110))]):
        el.append((ktext(name, xy, 52, breite=7), "pop", 4 + 0.5 * i))
    return {"hg": hg, "schlaege": 8, "el": el}


def szene_gesucht():
    hg = welt()
    t, _ = titel("MEISTGESUCHT", (M - 10, 250), 110, oben=GELB, unten=ORANGE)
    el = [(t, "punch", 0)]
    y = 420
    for i, (n, name, grund) in enumerate([("fabrice", "FABRICE", "schwerem Traumjob-Verdacht"),
                                          ("pascal", "PASCAL", "Gehaltserhöhung in Tateinheit"),
                                          ("waldemar", "WALDEMAR", "bandenmäßiger Ingenieur-Vermittlung")]):
        img = neu()
        d = ImageDraw.Draw(img)
        box = [M - 20, y, W - 140, y + 300]
        d.rounded_rectangle(box, radius=22, fill=(236, 220, 190, 255), outline=TINTE, width=8)
        por = portrait(n, 330)
        x0 = max(0, por.width // 2 - 140)
        img.alpha_composite(por.crop((x0, 0, x0 + 280, 284)), (box[0] + 8, y + 8))
        tx = box[0] + 300
        d.text((tx, y + 28), name, font=font("h800", 54), fill=TINTE)
        for k in range(5):
            stern(d, tx + 22 + k * 52, y + 116, 22, GELB)
        d.text((tx, y + 160), "Gesucht wegen", font=font("h700", 28), fill=(150, 40, 60))
        for z, zeile in enumerate(rd.wrap(d, grund, font("h800", 34), box[2] - tx - 20)):
            d.text((tx, y + 200 + z * 42), zeile, font=font("h800", 34), fill=TINTE)
        el.append((img, "links", 1 + 3.5 * i))
        y += 322
    return {"hg": hg, "schlaege": 14, "el": el}


def szene_cheat():
    hg = welt()
    el = [(sticker("GEHEIMTIPP", (M - 6, 280), fuell=PINK, schrift=WEISS), "pop", 0)]
    l1, y = titel("Cheatcode für", (M - 10, 380), 104, oben=TUERKIS, unten=(170, 255, 250))
    l2, y = titel("deinen Traumjob", (M - 10, y - 10), 104, oben=TUERKIS, unten=(170, 255, 250))
    el += [(l1, "punch", 0.5), (l2, "punch", 1.5)]
    y += 40
    for i, text in enumerate(["Lebenslauf schicken", "Kurz mit uns sprechen", "Vertrag beim Arbeitgeber"]):
        img = neu()
        d = ImageDraw.Draw(img)
        yy = y + i * 150
        d.rounded_rectangle([M, yy, W - 150, yy + 120], radius=60, fill=(20, 6, 46, 255), outline=PINK, width=6)
        d.ellipse([M + 14, yy + 12, M + 110, yy + 108], fill=GELB, outline=TINTE, width=5)
        d.text((M + 62, yy + 60), str(i + 1), font=font("h800", 54), fill=TINTE, anchor="mm")
        d.text((M + 140, yy + 60), text, font=font("h800", 46), fill=WEISS, anchor="lm")
        el.append((img, "links", 3 + i))
    el.append((ktext("Funktioniert auch ohne Konsole.", (M, y + 470), 40, breite=5, art="h700"), "hoch", 6.5))
    return {"hg": hg, "schlaege": 10, "el": el}


def szene_ende():
    hg = welt()
    band = neu()
    ImageDraw.Draw(band).rectangle([0, 470, W, 760], fill=NACHT + (255,))
    t, _ = titel("MISSION ERFÜLLT", (W // 2, 520), 120, oben=GELB, unten=ORANGE, mitte=True, schraeg=0.12,
                 maxbreite=W - 80)
    knopf = neu()
    d = ImageDraw.Draw(knopf)
    fk, kt = font("h800", 46), "Link in der Bio"
    kw = d.textlength(kt, font=fk)
    d.rounded_rectangle([W // 2 - kw / 2 - 50, 990, W // 2 + kw / 2 + 50, 1074], radius=42, fill=PINK, outline=TINTE,
                        width=6)
    d.text((W // 2, 1032), kt, font=fk, fill=WEISS, anchor="mm")
    marke = neu()
    d = ImageDraw.Draw(marke)
    lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
    d.rounded_rectangle([W // 2 - lg.width // 2 - 40, 1120, W // 2 + lg.width // 2 + 40, 1120 + lg.height + 70],
                        radius=24, fill=NACHT + (255,), outline=TUERKIS, width=4)
    marke.alpha_composite(lg, (W // 2 - lg.width // 2, 1140))
    d.text((W // 2, 1120 + lg.height + 40), "DIREKTVERMITTLUNG", font=font("h600", 22), fill=(255, 214, 180),
           anchor="mm")
    el = [(band, "wisch", 0), (t, "punch", 0.5),
          (ktext("Festanstellung freigeschaltet", (W // 2, 830), 54, anchor="mm", breite=7), "hoch", 2),
          (ktext("Level up: neuer Job", (W // 2, 905), 54, fill=TUERKIS, anchor="mm", breite=7), "pop", 2.5),
          (knopf, "pop", 4), (marke, "hoch", 5)]
    return {"hg": hg, "schlaege": 9, "el": el, "ohne_logo": True}


SZENEN = [szene_hook, szene_gekuendigt, szene_crew, szene_gesucht, szene_cheat, szene_ende]


# ---------------------------------------------------------------- Entwurf 4: Ladebildschirm + Poster-Figuren

VIOLETT, MAGENTA, KORALLE, LILA = (60, 14, 90), (200, 40, 130), (250, 110, 90), (120, 30, 140)


def poster(name, hoehe):
    p = Image.open(os.path.join(HIER, "assets", "team", f"{name}_poster.png")).convert("RGBA")
    return p.resize((int(p.width * hoehe / p.height), hoehe), Image.LANCZOS)


def _streifenfeld(poly, farbe, abstand=52, breite=12):
    maske = Image.new("L", (W, H))
    ImageDraw.Draw(maske).polygon(poly, fill=255)
    f = verlauf([(0, farbe), (1, VIOLETT)])
    fd = ImageDraw.Draw(f)
    for k in range(-H, W, abstand):
        fd.line([(k, 0), (k + H, H)], fill=tuple(min(255, c + 28) for c in farbe) + (255,), width=breite)
    return f, maske


def _comicfeld(poly, farbe, name, skal, pos):
    f, maske = _streifenfeld(poly, farbe)
    f.alpha_composite(poster(name, skal), pos)
    img = neu()
    img.paste(f, (0, 0), maske)
    ImageDraw.Draw(img).line(poly + [poly[0]], fill=TINTE, width=16, joint="curve")
    return img


def _lader(text="Traumjob wird geladen"):
    img = neu()
    d = ImageDraw.Draw(img)
    cx, cy = 420, 1452
    for i in range(8):
        a = i / 8 * 2 * math.pi
        r = 7 if i < 6 else 4
        d.ellipse([cx + 26 * math.cos(a) - r, cy + 26 * math.sin(a) - r,
                   cx + 26 * math.cos(a) + r, cy + 26 * math.sin(a) + r], fill=(255, 255, 255, 255))
    d.text((cx + 50, cy), text, font=font("h700", 34), fill=WEISS, anchor="lm", stroke_width=4, stroke_fill=TINTE)
    return img


def szene_lade():
    hg = welt()
    t, y = titel("INPERNELL", (M - 10, 230), 150, oben=GELB, unten=KORALLE)
    el = [(t, "punch", -0.3), (sticker("SCHWARZWALD EDITION", (M + 4, y + 4), fuell=TUERKIS), "pop", 0.5),
          (_comicfeld([(M - 30, 520), (600, 470), (560, 1120), (M - 30, 1170)], MAGENTA, "fabrice", 700, (-80, 500)),
           "links", 1),
          (_comicfeld([(615, 465), (W - 110, 420), (W - 130, 1060), (575, 1115)], KORALLE, "pascal", 640, (480, 450)),
           "rechts", 1.5),
          (_comicfeld([(M - 30, 1190), (W - 135, 1080), (W - 150, 1390), (M - 30, 1400)], LILA, "waldemar", 520,
                      (420, 1010)), "hoch", 2),
          (_lader(), "hoch", 3)]
    return {"hg": hg, "schlaege": 8, "el": el}


def _held(name, anzeige, grund, farbe):
    def szene():
        hg = welt()
        f, maske = _streifenfeld([(0, 560), (W, 430), (W, 1600), (0, 1600)], farbe, 60, 14)
        flaeche = neu()
        flaeche.paste(f, (0, 0), maske)
        ImageDraw.Draw(flaeche).line([(0, 560), (W, 430)], fill=TINTE, width=16)
        p = poster(name, 900 if name == "pascal" else 980)
        figur = neu()
        figur.alpha_composite(p, (W - p.width + (40 if name == "pascal" else 110), 1600 - p.height))
        t, y = titel(anzeige, (M - 10, 250), 140, oben=GELB, unten=KORALLE)
        el = [(flaeche, "wisch", 0), (figur, "rechts", 0.5), (t, "punch", 1)]
        for i in range(5):
            el.append((ein_stern(M + 30 + i * 70, y + 40, 28, GELB), "pop", 1.5 + 0.35 * i))
        box = neu()
        bd = ImageDraw.Draw(box)
        bd.rounded_rectangle([M - 20, 1150, 720, 1360], radius=22, fill=(236, 220, 190, 255), outline=TINTE, width=8)
        bd.text((M + 10, 1176), "GESUCHT WEGEN", font=font("h800", 28), fill=(150, 40, 60))
        for z, zeile in enumerate(rd.wrap(bd, grund, font("h800", 44), 600)):
            bd.text((M + 10, 1218 + z * 52), zeile, font=font("h800", 44), fill=TINTE)
        el.append((box, "hoch", 3))
        return {"hg": hg, "schlaege": 8, "el": el}
    return szene


SZENEN = [szene_lade, szene_hook, szene_gekuendigt,
          _held("fabrice", "FABRICE", "schwerem Traumjob-Verdacht", MAGENTA),
          _held("pascal", "PASCAL", "Gehaltserhöhung in Tateinheit", KORALLE),
          _held("waldemar", "WALDEMAR", "bandenmäßiger Ingenieur-Vermittlung", LILA),
          szene_cheat, szene_ende]


# ---------------------------------------------------------------- Entwurf 7: nach Vorlage des Inhabers (Plakat + Einzelbilder)

def _vorlage(name):
    return Image.open(os.path.join(HIER, "assets", "team", name)).convert("RGB")


def _plakat():
    p = _vorlage("vorlage_poster.png")
    oben = p.getpixel((540, 2))
    img = verlauf([(0, oben), (0.1, oben), (0.8, NACHT), (1, NACHT)])
    img.alpha_composite(p.resize((1002, 1336), Image.LANCZOS).convert("RGBA"), (39, 190))
    return img


def _abdunkeln(img, a):
    img = img.copy()
    img.alpha_composite(Image.new("RGBA", (W, H), NACHT + (int(255 * a),)))
    return img


def _grau(img):
    g = ImageEnhance.Brightness(ImageOps.grayscale(img.convert("RGB"))).enhance(0.7)
    return ImageOps.colorize(g, (10, 10, 16), (210, 210, 220)).convert("RGBA")


def v_hook():
    l1, y = titel("Heute zockt", (M - 10, 560), 110)
    l2, y = titel("ganz Deutschland.", (M - 10, y - 10), 110)
    el = [(sticker("HEUTE IST RELEASE-TAG", (M - 6, 450)), "pop", -0.3), (l1, "punch", -0.2), (l2, "punch", 1),
          (ktext("Und wir?", (M, y + 30), 66), "hoch", 3),
          (ktext("Haben trotzdem offen.", (M, y + 112), 66, fill=TUERKIS), "pop", 4)]
    return {"hg": _abdunkeln(_plakat(), 0.62), "schlaege": 8, "el": el, "ohne_logo": True}


def v_crew():
    return {"hg": _plakat(), "schlaege": 6, "el": [(sticker("DIE CREW IST DA", (M - 6, 230), fuell=TUERKIS), "pop", 0.5)],
            "ohne_logo": True, "blitz": True}


def v_gag():
    t, _ = titel("GEKÜNDIGT.", (W // 2, 560), 170, oben=(255, 70, 70), unten=ROT, mitte=True, schraeg=0.08)
    knopf = neu()
    d = ImageDraw.Draw(knopf)
    d.rounded_rectangle([M, 940, W - M, 1060], radius=24, fill=TUERKIS + (255,), outline=TINTE, width=6)
    d.text((W // 2, 1000), "Respawn bei Inpernell", font=font("h800", 62), fill=TINTE, anchor="mm")
    el = [(t, "punch", 0), (ktext("Kein Stress.", (W // 2, 860), 70, anchor="mm"), "hoch", 2.5), (knopf, "pop", 4)]
    return {"hg": _abdunkeln(_grau(_plakat()), 0.35), "schlaege": 7, "el": el, "ohne_logo": True,
            "wackeln": (0, 0.9), "blitz": True}


def _v_held(name, anzeige, grund):
    def szene():
        bild = _vorlage(f"{name}_vorlage.png").resize((W, H), Image.LANCZOS)
        hg = bild.filter(ImageFilter.UnsharpMask(radius=2, percent=40, threshold=2)).convert("RGBA")
        t, _ = titel(anzeige, (M - 10, 220), 130, oben=GELB, unten=KORALLE)
        karte = neu()
        d = ImageDraw.Draw(karte)
        y = 1150
        d.rounded_rectangle([M - 20, y, 740, y + 240], radius=22, fill=(236, 220, 190, 255), outline=TINTE, width=8)
        for i in range(5):
            stern(d, M + 22 + i * 56, y + 38, 22, GELB)
        d.text((M + 10, y + 74), "GESUCHT WEGEN", font=font("h800", 28), fill=(150, 40, 60))
        for z, zeile in enumerate(rd.wrap(d, grund, font("h800", 44), 620)):
            d.text((M + 10, y + 114 + z * 52), zeile, font=font("h800", 44), fill=TINTE)
        return {"hg": hg, "schlaege": 8, "el": [(t, "punch", 0.5), (karte, "hoch", 2)]}
    return szene


def v_cheat():
    s = szene_cheat()
    s["hg"] = _abdunkeln(_plakat(), 0.7)
    s["ohne_logo"] = True
    return s


def v_ende():
    cta = neu()
    d = ImageDraw.Draw(cta)
    fk, kt = font("h800", 42), "Neue Top Jobs: Link in der Bio"
    kw = d.textlength(kt, font=fk)
    d.rounded_rectangle([W // 2 - kw / 2 - 40, 215, W // 2 + kw / 2 + 40, 295], radius=40, fill=PINK, outline=TINTE,
                        width=6)
    d.text((W // 2, 255), kt, font=fk, fill=WEISS, anchor="mm")
    return {"hg": _plakat(), "schlaege": 8, "el": [(cta, "pop", 1)], "ohne_logo": True}


SZENEN = [v_hook, v_crew, v_gag,
          _v_held("fabrice", "FABRICE", "schwerem Traumjob-Verdacht"),
          _v_held("pascal", "PASCAL", "Gehaltserhöhung in Tateinheit"),
          _v_held("waldemar", "WALDEMAR", "bandenmäßiger Ingenieur-Vermittlung"),
          v_cheat, v_ende]
TITEL_SZENE = 1


# ---------------------------------------------------------------- Video

def standbilder(ordner):
    """Jede Szene fertig aufgebaut als Bild (Vorschau)."""
    os.makedirs(ordner, exist_ok=True)
    for i, fn in enumerate(SZENEN, 1):
        s = fn()
        img = s["hg"].copy()
        for teil, _, _ in s["el"]:
            img.alpha_composite(teil)
        if not s.get("ohne_logo"):
            logo_klein(img)
        img.convert("RGB").save(os.path.join(ordner, f"folie-{i}.jpg"), quality=92)


def erzeuge(ziel, titelbild=None):
    szenen = [fn() for fn in SZENEN]
    for s in szenen:
        s["ebenen"] = [(ebene(teil), eff, schlag) for teil, eff, schlag in s["el"]]
    gesamt = sum(s["schlaege"] for s in szenen) * SCHLAG
    ton = ziel + ".musik.wav"
    erzeuge_synthwave(gesamt + 0.3, ton, bpm=BPM)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", ton, "-map", "0:v", "-map", "1:a", "-shortest",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-g", "60", "-maxrate", "6M", "-bufsize", "12M",
           "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
           "-movflags", "+faststart", ziel]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    rnd = random.Random(5)
    titel_frame = None
    for si, s in enumerate(szenen):
        dauer = s["schlaege"] * SCHLAG
        for i in range(int(round(dauer * FPS))):
            t = i / FPS
            z = 1.0 + 0.03 * (t / dauer) + 0.05 * (1 - _ease(t / 0.3))       # langsamer Zoom + Punch beim Schnitt
            cw, ch = int(W / z), int(H / z)
            x, y = (W - cw) // 2, (H - ch) // 2
            frame = s["hg"].crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
            for eb, eff, schlag in s["ebenen"]:
                _zeige(frame, eb, eff, (t - schlag * SCHLAG) / (0.7 if eff == "wisch" else 0.4))
            if not s.get("ohne_logo"):
                logo_klein(frame)
            if "wackeln" in s and s["wackeln"][0] <= t <= s["wackeln"][1]:     # Bildschirm wackelt
                st = int(26 * (1 - (t - s["wackeln"][0]) / (s["wackeln"][1] - s["wackeln"][0])))
                dx, dy = rnd.randint(-st, st), rnd.randint(-st, st)
                wack = Image.new("RGBA", (W, H), NACHT + (255,))
                wack.alpha_composite(frame, (dx, dy))
                frame = wack
            if s.get("blitz") and t < 2 / FPS:                                  # kurzer Blitz beim Schnitt
                frame = Image.blend(frame, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.7)
            if si == TITEL_SZENE and titel_frame is None and t >= dauer - 0.2:
                titel_frame = frame.copy()
            proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg konnte das Reel nicht erzeugen.")
    os.remove(ton)
    if titelbild and titel_frame is not None:
        titel_frame.convert("RGB").save(titelbild, "JPEG", quality=92)
    return ziel


if __name__ == "__main__":
    erzeuge(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
