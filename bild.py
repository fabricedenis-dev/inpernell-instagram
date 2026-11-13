"""Inpernell – Top Job des Tages: Instagram-Bild (1080x1350, JPEG) im Stil von www.inpernell.de."""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
NAVY, NAVY_HELL = (10, 23, 48), (16, 40, 74)     # #0A1730 / #10284A
ORANGE = (237, 109, 5)                           # #ED6D05
PFIRSICH = (255, 215, 181)                       # #FFD7B5
WEISS, HELL = (255, 255, 255), (214, 222, 234)
KNOPFTEXT = (22, 11, 2)
M = 84
HIER = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    "h800": "archivo-latin-800-normal.woff",
    "h700": "archivo-latin-700-normal.woff",
    "h600": "archivo-latin-600-normal.woff",
    "t400": "lato-latin-400-normal.woff",
    "t700": "lato-latin-700-normal.woff",
}


def font(key, size):
    return ImageFont.truetype(os.path.join(HIER, "fonts", FONTS[key]), size)


def gesperrt(d, xy, text, f, fill, abstand):
    """Text mit Buchstabenabstand zeichnen; gibt die rechte x-Position zurück."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + abstand
    return x - abstand


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(d, text, key, start, minimum, maxw, maxlines):
    size = start
    while size > minimum:
        f = font(key, size)
        lines = wrap(d, text, f, maxw)
        if len(lines) <= maxlines and all(d.textlength(l, font=f) <= maxw for l in lines):
            return f, lines
        size -= 4
    f = font(key, minimum)
    return f, wrap(d, text, f, maxw)[:maxlines]


def _glas(img, box, radius, fill, outline):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)
    img.paste(ov, (0, 0), ov)
    return ImageDraw.Draw(img)


def erzeuge_bild(job, ziel):
    """job: dict mit titel, ort, extra, punkte (Liste), datum. Speichert ein JPEG nach ziel."""
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NAVY_HELL[i] + (NAVY[i] - NAVY_HELL[i]) * t) for i in range(3)))

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for r in (150, 270, 390, 510):
        od.ellipse([W - 60 - r, 120 - r, W - 60 + r, 120 + r], outline=(255, 255, 255, 16), width=2)
    img.paste(ov, (0, 0), ov)
    d = ImageDraw.Draw(img)

    # Kopf: Logo + Claim
    lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
    img.paste(lg, (M - 10, 62), lg)
    d = ImageDraw.Draw(img)
    x = M - 10 + lg.width - 8
    d.line([(x + 26, 74), (x + 26, 130)], fill=(90, 108, 136), width=2)
    fc = font("h600", 17)
    gesperrt(d, (x + 50, 80), "PERSONALBERATUNG FÜR", fc, WEISS, 2.6)
    gesperrt(d, (x + 50, 106), "FACH- UND FÜHRUNGSKRÄFTE", fc, WEISS, 2.6)

    # Überzeile
    label = "TOP JOB DES TAGES" + ("  ·  " + job["datum"] if job.get("datum") else "")
    ex = gesperrt(d, (M, 262), label, font("h700", 25), PFIRSICH, 4.5)
    d.line([(ex + 24, 278), (ex + 104, 278)], fill=ORANGE, width=3)

    # Titel (weiß) + Ort (orange)
    ft, lines = fit(d, job["titel"], "h800", 96, 54, W - 2 * M, 4)
    y = 330
    for l in lines:
        d.text((M, y), l, font=ft, fill=WEISS)
        y += int(ft.size * 1.08)
    if job.get("ort"):
        fo, ol = fit(d, job["ort"] + ".", "h800", min(ft.size, 80), 44, W - 2 * M, 2)
        for l in ol:
            d.text((M, y), l, font=fo, fill=ORANGE)
            y += int(fo.size * 1.08)

    # Chip mit Gehalt / Homeoffice
    y += 34
    if job.get("extra"):
        fx, xl = fit(d, job["extra"], "t700", 32, 24, W - 2 * M - 90, 1)
        tw = d.textlength(xl[0], font=fx)
        d = _glas(img, [M, y, M + tw + 86, y + 64], 32, (255, 255, 255, 20), (255, 255, 255, 60))
        d.ellipse([M + 24, y + 24, M + 40, y + 40], fill=(52, 199, 123))
        d.text((M + 56, y + 32), xl[0], font=fx, fill=WEISS, anchor="lm")
        y += 64

    # Karte mit bis zu drei Punkten
    punkte = [p for p in job.get("punkte", []) if p][:3]
    if punkte:
        y += 40
        fp = font("t400", 35)
        zeilen = [wrap(d, p, fp, W - 2 * M - 150)[:2] for p in punkte]
        kh = min(44 + sum(len(z) * 46 + 22 for z in zeilen) + 22, H - 230 - y)
        d = _glas(img, [M, y, W - M, y + kh], 28, (255, 255, 255, 14), (255, 255, 255, 46))
        py = y + 44
        for z in zeilen:
            if py + len(z) * 46 > y + kh - 10:
                break
            d.line([(M + 40, py + 22), (M + 51, py + 33), (M + 70, py + 10)], fill=ORANGE, width=6, joint="curve")
            for l in z:
                d.text((M + 100, py), l, font=fp, fill=HELL)
                py += 46
            py += 22

    # Knopf + Fußzeile
    fk = font("h700", 36)
    kt = "Jetzt bewerben"
    kw = d.textlength(kt, font=fk)
    ky = H - 190
    d.rounded_rectangle([M, ky, M + kw + 150, ky + 86], radius=43, fill=ORANGE)
    d.text((M + 46, ky + 43), kt, font=fk, fill=KNOPFTEXT, anchor="lm")
    ax = M + 46 + kw + 26
    d.line([(ax, ky + 43), (ax + 36, ky + 43)], fill=KNOPFTEXT, width=4)
    d.line([(ax + 22, ky + 30), (ax + 36, ky + 43), (ax + 22, ky + 56)], fill=KNOPFTEXT, width=4, joint="curve")
    d.text((M + kw + 186, ky + 43), "Link in der Bio", font=font("t700", 30), fill=WEISS, anchor="lm")
    gesperrt(d, (M, H - 66), "KEINE ZEITARBEIT. DIREKTVERMITTLUNG.  ·  INPERNELL.DE", font("h600", 19), PFIRSICH, 2.6)

    img.save(ziel, "JPEG", quality=93, optimize=True)
    return ziel
