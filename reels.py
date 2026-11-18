"""Inpernell – Wissens-Reels (1080x1920, MP4): Tipps, Fakten und Top Jobs als kurze Videos.

Ein Reel besteht aus Szenen: Hook (Frage/These), 3 Punkte mit großer Nummer, Abschluss mit
Handlungsaufforderung. Fortschrittsbalken oben (wie bei Stories) halten Zuschauer bis zum Ende.
Das Foto im Hintergrund zoomt langsam, Texte gleiten Wort für Wort herein – kein statisches Plakat.

reel = {
  "rubrik": "Gehaltsverhandlung",            # Etikett oben
  "kategorie": "finanzen",                    # Foto aus assets/berufsfelder
  "hook": "3 Fehler, die dich in der Gehaltsverhandlung Geld kosten",
  "punkte": [{"titel": "…", "text": "…"}, …],  # 3 Stück, kurz und vollständig
  "cta": "Speichern für dein nächstes Gespräch",
  "quelle": "Quelle: …"                        # optional, klein am Ende
}
"""
import subprocess

from PIL import Image, ImageDraw, ImageFilter

from bild import (FORMATE, HELL, KNOPFTEXT, NAVY, ORANGE, PFIRSICH, WEISS, _foto_vorbereiten,
                  _verlauf_navy, font, gesperrt, gesperrt_breite, wrap)
import os

W, H = 1080, 1920
M, R = 80, 150                    # linker Rand / rechter Rand (Instagram-Knöpfe rechts)
OBEN, UNTEN = 260, 1600           # sichere Zone (Kopfzeile und Bildtext von Instagram)
FPS = 30
HIER = os.path.dirname(os.path.abspath(__file__))


def _ease(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def _hintergrund(foto, t, dauer, staerke=210):
    """Foto bildfüllend, langsamer Zoom, dunkler Navy-Schleier für Lesbarkeit."""
    z = 1.0 + 0.10 * (t / dauer)
    cw, ch = int(foto.width / z), int(foto.height / z)
    x, y = (foto.width - cw) // 2, (foto.height - ch) // 2
    bild = foto.crop((x, y, x + cw, y + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")
    schleier = Image.new("RGBA", (W, H), (*NAVY, staerke))
    bild = Image.alpha_composite(bild, schleier)
    # unten zusätzlich abdunkeln (dort liegt Instagrams Bildtext)
    verlauf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(verlauf)
    for yy in range(1100, H):
        vd.line([(0, yy), (W, yy)], fill=(*NAVY, int(200 * (yy - 1100) / (H - 1100))))
    return Image.alpha_composite(bild, verlauf)


def _woerter(d, ebene, text, f, x, y, maxw, t, start, tempo=0.09, farbe=WEISS, zeilenfaktor=1.08):
    """Text Wort für Wort einblenden (kinetische Typo). Gibt die Unterkante zurück."""
    zeilen = wrap(d, text, f, maxw)
    i = 0
    for z, zeile in enumerate(zeilen):
        xx = x
        for wort in zeile.split():
            p = _ease((t - start - i * tempo) / 0.35)
            if p > 0:
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(ov).text((xx, y + z * int(f.size * zeilenfaktor) + int((1 - p) * 30)), wort,
                                        font=f, fill=(*farbe, int(255 * p)))
                ebene.alpha_composite(ov)
            xx += d.textlength(wort + " ", font=f)
            i += 1
    return y + len(zeilen) * int(f.size * zeilenfaktor)


def _fortschritt(d, szene, anzahl, p):
    """Segmentierter Balken oben wie bei Stories."""
    luecke, y = 10, 196
    breite = (W - M - R - luecke * (anzahl - 1)) / anzahl
    for i in range(anzahl):
        x0 = M + i * (breite + luecke)
        d.rounded_rectangle([x0, y, x0 + breite, y + 8], radius=4, fill=(255, 255, 255, 70))
        fuell = 1.0 if i < szene else (p if i == szene else 0.0)
        if fuell > 0:
            d.rounded_rectangle([x0, y, x0 + breite * fuell, y + 8], radius=4, fill=(*ORANGE, 255))


def _kopf(ebene, rubrik):
    d = ImageDraw.Draw(ebene)
    lg = Image.open(os.path.join(HIER, "assets", "logo.png")).convert("RGBA")
    ebene.alpha_composite(lg, (M - 10, 96))
    f = font("h700", 22)
    text = rubrik.upper()
    tw = gesperrt_breite(d, text, f, 3.4)
    x = W - R - tw - 40
    d.rounded_rectangle([x, 108, x + tw + 40, 152], radius=22, fill=(*ORANGE, 255))
    gesperrt(d, (x + 20, 119), text, f, KNOPFTEXT, 3.4)


def erzeuge_wissensreel(reel, ziel, titelbild=None):
    kat = reel.get("kategorie", "personal")
    # nicht weichzeichnen (Instagram empfiehlt unscharfe Videos seltener) – stattdessen stärker abdunkeln
    foto = _foto_vorbereiten(kat, W, H, reserve=1.12)
    punkte = reel["punkte"][:3]
    szenen = [("hook", 3.0)] + [("punkt", 4.2)] * len(punkte) + [("ende", 3.6)]
    if reel.get("dauern"):            # bei Sprecherstimme: Szene so lang wie der gesprochene Satz
        szenen = [(art, max(d, reel["dauern"][i])) for i, (art, d) in enumerate(szenen)]
    gesamt = sum(s[1] for s in szenen)
    mess = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if reel.get("ton") and os.path.exists(reel["ton"]):
        cmd += ["-i", reel["ton"], "-filter_complex", f"[1:a]afade=t=out:st={gesamt - 1.2}:d=1.2[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    cmd += ["-shortest", "-t", f"{gesamt}", "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", ziel]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    titel_frame = None
    t0 = 0.0
    for si, (art, dauer) in enumerate(szenen):
        for i in range(int(dauer * FPS)):
            t = i / FPS
            tg = t0 + t
            ebene = _hintergrund(foto, tg, gesamt)
            d = ImageDraw.Draw(ebene)
            _kopf(ebene, reel.get("rubrik", "Karrieretipp"))
            _fortschritt(d, si, len(szenen), t / dauer)
            breite = W - M - R

            if art == "hook":
                f = font("h800", 92)
                # kleiner, bis höchstens 5 Zeilen und auch das längste Wort in die Breite passt
                while f.size > 56 and (len(wrap(mess, reel["hook"], f, breite)) > 5 or
                                       any(mess.textlength(z, font=f) > breite
                                           for z in wrap(mess, reel["hook"], f, breite))):
                    f = font("h800", f.size - 4)
                y = 560
                gesperrt(d, (M, y - 70), reel.get("kicker", "KURZ ERKLÄRT"),
                         font("h700", 26), PFIRSICH, 4)
                _woerter(mess, ebene, reel["hook"], f, M, y, breite, t, 0.15, tempo=0.11)
                if titel_frame is None and t >= 2.4:
                    titel_frame = ebene.copy()

            elif art == "punkt":
                n = si
                pkt = punkte[n - 1]
                p = _ease(t / 0.45)
                # große Nummer
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                od = ImageDraw.Draw(ov)
                od.text((M - 8 - int((1 - p) * 80), 440), str(n), font=font("h800", 300),
                        fill=(*ORANGE, int(255 * p)))
                ebene.alpha_composite(ov)
                ft = font("h800", 72)
                while ft.size > 48 and (len(wrap(mess, pkt["titel"], ft, breite)) > 3 or
                                        any(mess.textlength(z, font=ft) > breite
                                            for z in wrap(mess, pkt["titel"], ft, breite))):
                    ft = font("h800", ft.size - 4)
                y = _woerter(mess, ebene, pkt["titel"], ft, M, 800, breite, t, 0.25, tempo=0.08)
                fx = font("t400", 46)
                _woerter(mess, ebene, pkt["text"], fx, M, y + 36, breite, t, 0.9, tempo=0.05, farbe=HELL,
                         zeilenfaktor=1.3)

            else:  # ende
                p = _ease(t / 0.5)
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                od = ImageDraw.Draw(ov)
                fc = font("h800", 76)
                y = 640 + int((1 - p) * 40)
                for zeile in wrap(mess, reel.get("cta", "Speichern & weiterschicken"), fc, breite):
                    od.text((M, y), zeile, font=fc, fill=(*WEISS, int(255 * p)))
                    y += int(fc.size * 1.1)
                y += 50
                zweit = reel.get("cta_zusatz", "Und schick es jemandem, der gerade sucht.")
                if zweit:
                    od.text((M, y), zweit, font=font("t400", 42), fill=(*HELL, int(255 * p)))
                y += 120
                fk = font("h700", 38)
                kt = "Top Jobs: Link in der Bio"
                kw = od.textlength(kt, font=fk)
                od.rounded_rectangle([M, y, M + kw + 90, y + 96], radius=48, fill=(*ORANGE, int(255 * p)))
                od.text((M + 45, y + 48), kt, font=fk, fill=(*KNOPFTEXT, int(255 * p)), anchor="lm")
                if reel.get("quelle"):
                    od.text((M, UNTEN - 10), reel["quelle"], font=font("t400", 26), fill=(*PFIRSICH, int(200 * p)))
                ebene.alpha_composite(ov)

            proc.stdin.write(ebene.convert("RGB").tobytes())
        t0 += dauer
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg konnte das Reel nicht erzeugen.")
    if titelbild and titel_frame is not None:
        titel_frame.convert("RGB").save(titelbild, "JPEG", quality=90)
    return ziel
