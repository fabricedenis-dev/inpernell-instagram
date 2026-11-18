"""Inpernell – TOP Job des Tages: Instagram-Bild (1080x1350) und Reel (1080x1920, MP4).

Beide Formate werden aus denselben Bausteinen ("Elementen") gebaut: Foto des Berufsfelds oben,
darunter Titel, Ort, drei Eckdaten-Kacheln, drei Highlights und der Bewerben-Knopf.
Beim Bild werden alle Elemente auf einmal gezeigt, beim Reel erscheinen sie nacheinander,
während das Foto langsam heranzoomt.

job (dict):
  titel, ort, datum            Pflicht ist nur titel
  kategorie                    Schlüssel aus kategorien.py (sonst wird er aus dem Titel erkannt)
  fakten                       Liste aus [Beschriftung, Wert], max. 3, z. B. [["Gehalt", "65.000 – 80.000 €"]]
  punkte, punkte_titel         bis zu 3 kurze Highlights und ihre Überschrift
  extra                        (alt) eine Zeile wie "65.000 € / Jahr · Homeoffice möglich"
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

import kategorien

NAVY, NAVY_HELL = (10, 23, 48), (16, 40, 74)     # #0A1730 / #10284A
ORANGE = (237, 109, 5)                           # #ED6D05
PFIRSICH = (255, 215, 181)                       # #FFD7B5
WEISS, HELL = (255, 255, 255), (214, 222, 234)
KNOPFTEXT = (22, 11, 2)
HIER = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    "h800": "archivo-latin-800-normal.woff",
    "h700": "archivo-latin-700-normal.woff",
    "h600": "archivo-latin-600-normal.woff",
    "t400": "lato-latin-400-normal.woff",
    "t700": "lato-latin-700-normal.woff",
}
_FONTCACHE = {}

# Maße je Format. "foto" = Höhe des Fotobereichs, "rechts" = rechter Rand (beim Reel breiter,
# weil Instagram dort die Knöpfe einblendet), "unten" = Unterkante des Inhalts.
FORMATE = {
    "bild": dict(W=1080, H=1350, M=72, rechts=72, foto=720, oben=56, unten=1350 - 44, titel=84),
    "reel": dict(W=1080, H=1920, M=72, rechts=150, foto=940, oben=150, unten=1920 - 300, titel=92),
}
# Story: gleiches Hochformat wie das Reel, aber als Standbild mit Link zur Stellenanzeige
FORMATE["story"] = dict(FORMATE["reel"], unten=1920 - 340)


def font(key, size):
    if (key, size) not in _FONTCACHE:
        _FONTCACHE[(key, size)] = ImageFont.truetype(os.path.join(HIER, "fonts", FONTS[key]), size)
    return _FONTCACHE[(key, size)]


def gesperrt(d, xy, text, f, fill, abstand):
    """Text mit Buchstabenabstand zeichnen; gibt die rechte x-Position zurück."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + abstand
    return x - abstand


def gesperrt_breite(d, text, f, abstand):
    return sum(d.textlength(ch, font=f) for ch in text) + abstand * (len(text) - 1)


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
        size -= 2
    f = font(key, minimum)
    return f, wrap(d, text, f, maxw)[:maxlines]


# ---------------------------------------------------------------- Hintergrund und Foto

def _verlauf_navy(W, H):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NAVY_HELL[i] + (NAVY[i] - NAVY_HELL[i]) * t) for i in range(3)))
    return img


def _foto_vorbereiten(kategorie, W, hoehe, reserve=1.0):
    """Foto des Berufsfelds auf (W*reserve) x (hoehe*reserve) zuschneiden, Fokuspunkt beachten."""
    feld = kategorien.BERUFSFELDER.get(kategorie, kategorien.BERUFSFELDER[kategorien.STANDARD])
    foto = Image.open(kategorien.foto_pfad(kategorie)).convert("RGB")
    zw, zh = int(W * reserve), int(hoehe * reserve)
    skala = max(zw / foto.width, zh / foto.height)
    foto = foto.resize((max(zw, round(foto.width * skala)), max(zh, round(foto.height * skala))), Image.LANCZOS)
    fx, fy = feld["fokus"]
    x = min(max(0, int(foto.width * fx - zw / 2)), foto.width - zw)
    y = min(max(0, int(foto.height * fy - zh / 2)), foto.height - zh)
    return foto.crop((x, y, x + zw, y + zh))


def _foto_schleier(W, hoehe, H):
    """Abdunklung über dem Foto: oben für das Logo, unten weicher Übergang in den Navy-Verlauf."""
    ov = Image.new("RGBA", (W, hoehe), (*NAVY, 0))
    d = ImageDraw.Draw(ov)
    for y in range(hoehe):
        t = y / hoehe
        farbe = tuple(int(NAVY_HELL[i] + (NAVY[i] - NAVY_HELL[i]) * y / H) for i in range(3))
        oben = max(0.0, 1 - y / 260) * 150
        unten = max(0.0, (t - 0.42) / 0.58) ** 1.6 * 255
        d.line([(0, y), (W, y)], fill=(*farbe, int(min(255, 70 + oben + unten))))
    return ov


# ---------------------------------------------------------------- Elemente

def _element(W, H, zeichnen):
    """Zeichnet auf eine transparente Fläche und schneidet auf den benutzten Bereich zu."""
    ebene = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    zeichnen(ImageDraw.Draw(ebene), ebene)
    box = ebene.getbbox() or (0, 0, 1, 1)
    return {"img": ebene.crop(box), "x": box[0], "y": box[1]}


def _glas(d, box, radius, fill=(255, 255, 255, 18), outline=(255, 255, 255, 56)):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)


def fakten_aus_job(job):
    if job.get("fakten"):
        return [(str(a), str(b)) for a, b in job["fakten"] if b][:3]
    # Rückfall für alte Vorgaben mit nur einer "extra"-Zeile
    teile = [t.strip() for t in (job.get("extra") or "").split("·") if t.strip()]
    fakten = []
    for t in teile:
        fakten.append(("Gehalt" if "€" in t else "Arbeitsmodell", t))
    return fakten[:3]


def elemente(job, fmt):
    """Liefert die Bausteine (Bild + Position + Einblendzeit in Sekunden) für ein Format."""
    F = FORMATE[fmt]
    W, H, M, R = F["W"], F["H"], F["M"], F["rechts"]
    breite = W - M - R
    mess = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    kat = job.get("kategorie") or kategorien.erkenne(job.get("titel"))
    feldname = kategorien.BERUFSFELDER.get(kat, {}).get("name", "")
    els = []

    # Kopf: Logo + Claim
    def kopf(d, ebene):
        lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
        ebene.paste(lg, (M - 10, F["oben"]), lg)
        x = M - 10 + lg.width - 8
        d.line([(x + 26, F["oben"] + 12), (x + 26, F["oben"] + 68)], fill=(255, 255, 255, 110), width=2)
        fc = font("h600", 17)
        gesperrt(d, (x + 50, F["oben"] + 18), "PERSONALBERATUNG FÜR", fc, WEISS, 2.6)
        gesperrt(d, (x + 50, F["oben"] + 44), "FACH- UND FÜHRUNGSKRÄFTE", fc, WEISS, 2.6)
    els.append({**_element(W, H, kopf), "t": 0.15, "name": "kopf"})

    # Titelblock von unten nach oben planen: zuerst messen, dann platzieren
    ft, tz = fit(mess, job["titel"], "h800", F["titel"], 50, breite, 3)
    th = int(ft.size * 1.06)
    ort = (job.get("ort") or "").strip()
    fo, oz = fit(mess, ort + ".", "h800", min(ft.size, 64), 40, breite, 1) if ort else (None, [])
    oh = int(fo.size * 1.12) if fo else 0
    block = 40 + 22 + len(tz) * th + len(oz) * oh       # Überzeile + Abstand + Titel + Ort
    y0 = F["foto"] - block + (10 if fmt == "bild" else -40)

    # Überzeile: Badge "TOP JOB DES TAGES" + Datum
    def ueberzeile(d, ebene):
        f = font("h700", 21)
        text = "TOP JOB DES TAGES"
        tw = gesperrt_breite(d, text, f, 3.6)
        d.rounded_rectangle([M, y0, M + tw + 40, y0 + 40], radius=20, fill=ORANGE)
        gesperrt(d, (M + 20, y0 + 9), text, f, KNOPFTEXT, 3.6)
        if job.get("datum"):
            gesperrt(d, (M + tw + 62, y0 + 9), job["datum"], f, PFIRSICH, 3.6)
    els.append({**_element(W, H, ueberzeile), "t": 0.45, "name": "ueberzeile"})

    y = y0 + 40 + 22
    for i, zeile in enumerate(tz):
        yy = y
        els.append({**_element(W, H, lambda d, e, z=zeile, yy=yy: d.text((M - 3, yy), z, font=ft, fill=WEISS)),
                    "t": 0.75 + 0.12 * i, "name": "titel"})
        y += th
    if oz:
        yy = y
        els.append({**_element(W, H, lambda d, e: d.text((M - 2, yy), oz[0], font=fo, fill=ORANGE)),
                    "t": 0.75 + 0.12 * len(tz) + 0.1, "name": "ort"})
        y += oh

    # Berufsfeld als kleines Etikett unter dem Logo
    if feldname:
        def feld(d, ebene):
            f = font("h600", 18)
            text = feldname.upper()
            tw = gesperrt_breite(d, text, f, 2.4)
            yb = F["oben"] + 100
            d.rounded_rectangle([M, yb, M + tw + 36, yb + 38], radius=19, fill=(10, 23, 48, 150),
                                outline=(255, 255, 255, 90), width=2)
            gesperrt(d, (M + 18, yb + 9), text, f, WEISS, 2.4)
        els.append({**_element(W, H, feld), "t": 0.3, "name": "feld"})

    # Eckdaten-Kacheln
    fakten = fakten_aus_job(job)
    t_naechst = 0.75 + 0.12 * (len(tz) + 1) + 0.5
    if fakten:
        y += 34 if fmt == "bild" else 56
        luecke = 14
        kw = (breite - luecke * (len(fakten) - 1)) / len(fakten)
        kh = 104 if fmt == "bild" else 118
        for i, (label, wert) in enumerate(fakten):
            x0 = int(M + i * (kw + luecke))
            yy = y

            def kachel(d, ebene, x0=x0, yy=yy, label=label, wert=wert):
                _glas(d, [x0, yy, int(x0 + kw), yy + kh], 22)
                d.rounded_rectangle([x0 + 22, yy + 24, x0 + 28, yy + 44], radius=3, fill=ORANGE)
                gesperrt(d, (x0 + 40, yy + 22), label.upper(), font("h600", 16), PFIRSICH, 2.2)
                fw, wl = fit(d, wert, "t700", 30, 24, kw - 44, 1)
                if d.textlength(wl[0], font=fw) > kw - 44 or len(wrap(d, wert, fw, kw - 44)) > 1:
                    fw, wl = fit(d, wert, "t700", 24, 17, kw - 44, 2)
                for j, l in enumerate(reversed(wl)):
                    d.text((x0 + 22, yy + kh - 24 - j * int(fw.size * 1.15)), l, font=fw, fill=WEISS, anchor="ls")
            els.append({**_element(W, H, kachel), "t": t_naechst + 0.22 * i, "name": "kachel"})
        y += kh
        t_naechst += 0.22 * len(fakten) + 0.5

    # Knopf (Position steht fest), Highlights füllen den Platz dazwischen
    kn_h = 84
    ky = F["unten"] - kn_h - (34 if fmt == "bild" else 0)
    punkte = [p for p in job.get("punkte", []) if p][:3]
    if punkte:
        y += 36 if fmt == "bild" else 64
        fp = font("t400", 32 if fmt == "bild" else 36)
        zh = int(fp.size * 1.3)
        platz = ky - 30 - y
        ueber = (job.get("punkte_titel") or "Das erwartet dich").upper()
        gesamt = 40
        passend = []
        for p in punkte:
            zl = wrap(mess, p, fp, breite - 56)[:2]
            if gesamt + len(zl) * zh + 12 > platz:
                break
            passend.append(zl)
            gesamt += len(zl) * zh + 12
        if passend:
            yy = y
            els.append({**_element(W, H, lambda d, e: gesperrt(d, (M, yy), ueber, font("h700", 19), PFIRSICH, 3.4)),
                        "t": t_naechst, "name": "punkte_titel"})
            py = y + 42
            for i, zl in enumerate(passend):
                pyy = py

                def punkt(d, ebene, zl=zl, pyy=pyy):
                    cy = pyy + fp.size * 0.62
                    d.line([(M + 2, cy), (M + 12, cy + 10), (M + 30, cy - 9)], fill=ORANGE, width=6, joint="curve")
                    for j, l in enumerate(zl):
                        d.text((M + 52, pyy + j * zh), l, font=fp, fill=HELL)
                els.append({**_element(W, H, punkt), "t": t_naechst + 0.25 + 0.35 * i, "name": "punkt"})
                py += len(zl) * zh + 12
            t_naechst += 0.25 + 0.35 * len(passend) + 0.4

    def knopf(d, ebene):
        fk = font("h700", 34)
        kt = "Jetzt bewerben"
        kw_ = d.textlength(kt, font=fk)
        d.rounded_rectangle([M, ky, M + kw_ + 140, ky + kn_h], radius=kn_h // 2, fill=ORANGE)
        d.text((M + 42, ky + kn_h / 2), kt, font=fk, fill=KNOPFTEXT, anchor="lm")
        ax = M + 42 + kw_ + 24
        d.line([(ax, ky + kn_h / 2), (ax + 34, ky + kn_h / 2)], fill=KNOPFTEXT, width=4)
        d.line([(ax + 21, ky + kn_h / 2 - 13), (ax + 34, ky + kn_h / 2), (ax + 21, ky + kn_h / 2 + 13)],
               fill=KNOPFTEXT, width=4, joint="curve")
        if fmt == "story":
            link = (job.get("job_url") or "https://www.inpernell.de/jobboerse/").split("://", 1)[-1].rstrip("/")
            gesperrt(d, (M, ky + kn_h + 30), "ZUR STELLENANZEIGE", font("h600", 18), PFIRSICH, 2.6)
            fl, ll = fit(d, link, "t700", 30, 20, breite, 1)
            d.text((M, ky + kn_h + 62), ll[0], font=fl, fill=WEISS)
            return
        d.text((M + kw_ + 172, ky + kn_h / 2), "Link in der Bio", font=font("t700", 29), fill=WEISS, anchor="lm")
        if fmt == "bild":
            gesperrt(d, (M, F["H"] - 52), "KEINE ZEITARBEIT. DIREKTVERMITTLUNG.  ·  INPERNELL.DE",
                     font("h600", 18), PFIRSICH, 2.6)
        else:
            gesperrt(d, (M, ky + kn_h + 30), "KEINE ZEITARBEIT  ·  INPERNELL.DE", font("h600", 18), PFIRSICH, 2.6)
    els.append({**_element(W, H, knopf), "t": max(t_naechst, 4.2), "name": "knopf"})
    return els, kat


def _einblenden(el, t, dauer=0.5):
    """Liefert (Bild, x, y) für den Zeitpunkt t oder None, wenn noch unsichtbar."""
    p = (t - el["t"]) / dauer
    if p <= 0:
        return None
    if p >= 1:
        return el["img"], el["x"], el["y"]
    e = 1 - (1 - p) ** 3                       # sanft auslaufen
    img = el["img"].copy()
    img.putalpha(img.getchannel("A").point(lambda a: int(a * e)))
    return img, el["x"], el["y"] + int((1 - e) * 36)


# ---------------------------------------------------------------- Ausgabe

def _grund(fmt, kat):
    F = FORMATE[fmt]
    grund = _verlauf_navy(F["W"], F["H"]).convert("RGBA")
    ringe = Image.new("RGBA", (F["W"], F["H"]), (0, 0, 0, 0))
    od = ImageDraw.Draw(ringe)
    cy = F["foto"] + (F["H"] - F["foto"]) // 2
    for r in (180, 300, 420, 540):
        od.ellipse([F["W"] - 40 - r, cy - r, F["W"] - 40 + r, cy + r], outline=(255, 255, 255, 12), width=2)
    return Image.alpha_composite(grund, ringe)


def erzeuge_bild(job, ziel, fmt="bild"):
    """Speichert den Feed-Beitrag (1080x1350 JPEG) bzw. mit fmt="story" die Story (1080x1920) nach ziel."""
    F = FORMATE[fmt]
    els, kat = elemente(job, fmt)
    img = _grund(fmt, kat)
    foto = _foto_vorbereiten(kat, F["W"], F["foto"]).convert("RGBA")
    foto = Image.alpha_composite(foto, _foto_schleier(F["W"], F["foto"], F["H"]))
    img.paste(foto, (0, 0))
    for el in els:
        img.alpha_composite(el["img"], (el["x"], el["y"]))
    img.convert("RGB").save(ziel, "JPEG", quality=93, optimize=True)
    return ziel


def erzeuge_story(job, ziel):
    """Speichert die Story (1080x1920 JPEG) mit Link zur Stellenanzeige nach ziel."""
    return erzeuge_bild(job, ziel, fmt="story")


def erzeuge_reel(job, ziel, sekunden=10, fps=30, titelbild=None):
    """Speichert ein Reel (1080x1920, H.264 + stille Tonspur) nach ziel. Braucht ffmpeg."""
    F = FORMATE["reel"]
    W, H = F["W"], F["H"]
    els, kat = elemente(job, "reel")
    grund = _grund("reel", kat)
    zoom_max = 1.10
    foto_gross = _foto_vorbereiten(kat, W, F["foto"], reserve=zoom_max)
    schleier = _foto_schleier(W, F["foto"], H)

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
           "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", ziel]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(sekunden * fps)
    letztes = None
    for i in range(n):
        t = i / fps
        # Foto langsam heranzoomen (Ken-Burns-Effekt)
        z = zoom_max - (zoom_max - 1.0) * (1 - t / sekunden)
        cw, ch = int(W * zoom_max / z), int(F["foto"] * zoom_max / z)
        cx, cy = (foto_gross.width - cw) // 2, (foto_gross.height - ch) // 2
        foto = foto_gross.crop((cx, cy, cx + cw, cy + ch)).resize((W, F["foto"]), Image.BILINEAR).convert("RGBA")
        foto = Image.alpha_composite(foto, schleier)
        bild = grund.copy()
        bild.paste(foto, (0, 0))
        for el in els:
            r = _einblenden(el, t)
            if r:
                bild.alpha_composite(r[0], (r[1], r[2]))
        # am Ende kurz abblenden
        if t > sekunden - 0.4:
            a = (t - (sekunden - 0.4)) / 0.4
            bild = Image.blend(bild, Image.new("RGBA", (W, H), (*NAVY, 255)), a * 0.85)
        else:
            letztes = bild
        proc.stdin.write(bild.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg konnte das Reel nicht erzeugen.")
    if titelbild and letztes is not None:
        letztes.convert("RGB").save(titelbild, "JPEG", quality=90)
    return ziel
