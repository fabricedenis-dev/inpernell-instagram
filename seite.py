"""Inpernell – "Link in der Bio"-Seite: zeigt immer den aktuellen TOP Job des Tages.

erzeuge_seite(post, ziel) schreibt eine einzelne, eigenständige HTML-Datei (Schriften, Logo und Foto
sind eingebettet). Sie kann so direkt im Browser geöffnet oder über GitHub Pages ausgeliefert werden.
"""
import base64
import html
import os

import kategorien

HIER = os.path.dirname(os.path.abspath(__file__))
ALLE_STELLEN = "https://www.inpernell.de/jobboerse/"


def _datei_als_daten(pfad, typ):
    with open(pfad, "rb") as f:
        return f"data:{typ};base64," + base64.b64encode(f.read()).decode()


def _foto_klein(kategorie):
    """Foto für die Seite verkleinern (spart Ladezeit auf dem Handy)."""
    from io import BytesIO
    from PIL import Image
    foto = Image.open(kategorien.foto_pfad(kategorie)).convert("RGB")
    foto.thumbnail((1200, 1200))
    puffer = BytesIO()
    foto.save(puffer, "JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(puffer.getvalue()).decode()


def erzeuge_seite(post, ziel):
    e = lambda s: html.escape(str(s or ""))
    kat = post.get("kategorie") or kategorien.erkenne(post.get("titel"))
    feld = kategorien.BERUFSFELDER.get(kat, {})
    fx, fy = feld.get("fokus", (0.5, 0.5))
    fonts = {name: _datei_als_daten(os.path.join(HIER, "fonts", f"{name}.woff"), "font/woff")
             for name in ("archivo-latin-800-normal", "archivo-latin-600-normal",
                          "lato-latin-400-normal", "lato-latin-700-normal")}
    logo = _datei_als_daten(os.path.join(HIER, "assets", "logo.png"), "image/png")
    foto = _foto_klein(kat)
    fakten = post.get("fakten") or []
    wert = lambda b: e(b).replace(" h", "&nbsp;h").replace(" €", "&nbsp;€")   # Einheit nicht allein umbrechen
    kacheln = "".join(f'<div class="k"><b>{e(a)}</b><span>{wert(b)}</span></div>' for a, b in fakten[:3])
    punkte = "".join(f"<li>{e(p)}</li>" for p in (post.get("punkte") or [])[:3])
    job_url = post.get("job_url") or ALLE_STELLEN
    titel = e(post.get("titel"))
    ort = e(post.get("ort"))
    beschreibung = f"TOP Job des Tages bei Inpernell: {post.get('titel', '')}" + (f" in {post['ort']}" if post.get("ort") else "")

    seite = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TOP Job des Tages – Inpernell</title>
<meta name="description" content="{e(beschreibung)}">
<meta property="og:title" content="TOP Job des Tages: {titel}">
<meta property="og:description" content="{e(beschreibung)}">
<style>
@font-face{{font-family:Archivo;font-weight:800;src:url({fonts["archivo-latin-800-normal"]}) format("woff")}}
@font-face{{font-family:Archivo;font-weight:600;src:url({fonts["archivo-latin-600-normal"]}) format("woff")}}
@font-face{{font-family:Lato;font-weight:400;src:url({fonts["lato-latin-400-normal"]}) format("woff")}}
@font-face{{font-family:Lato;font-weight:700;src:url({fonts["lato-latin-700-normal"]}) format("woff")}}
:root{{--navy:#0A1730;--navy2:#10284A;--orange:#ED6D05;--peach:#FFD7B5;--hell:#D6DEEA}}
*{{box-sizing:border-box;margin:0}}
html{{background:var(--navy)}}
body{{background:linear-gradient(var(--navy2),var(--navy));color:#fff;font-family:Lato,system-ui,sans-serif;
     min-height:100vh;max-width:560px;margin:0 auto}}
.hero{{height:min(46vh,360px);padding:22px 20px;display:flex;flex-direction:column;justify-content:space-between;
      background:linear-gradient(180deg,rgba(10,23,48,.65),rgba(10,23,48,.15) 45%,#0f2647 100%),
      url({foto}) {fx*100:.0f}% {fy*100:.0f}%/cover}}
.logo{{height:34px;width:auto;align-self:flex-start}}
.feld{{display:inline-block;margin-top:10px;border:1.5px solid rgba(255,255,255,.4);border-radius:99px;
      padding:5px 11px;font:600 11px Archivo,sans-serif;letter-spacing:.16em;text-transform:uppercase;
      background:rgba(10,23,48,.5)}}
.badge{{display:inline-block;background:var(--orange);color:#160b02;font:600 12px Archivo,sans-serif;
       letter-spacing:.2em;padding:7px 12px;border-radius:99px}}
.datum{{font:600 12px Archivo,sans-serif;letter-spacing:.2em;color:var(--peach);margin-left:10px}}
main{{padding:6px 20px 32px}}
h1{{font:800 clamp(28px,8.5vw,38px)/1.05 Archivo,sans-serif;margin:12px 0 4px;overflow-wrap:anywhere}}
.ort{{font:800 clamp(20px,6vw,26px) Archivo,sans-serif;color:var(--orange)}}
.kacheln{{display:grid;grid-template-columns:repeat(auto-fit,minmax(96px,1fr));gap:8px;margin:22px 0}}
.k{{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.2);border-radius:14px;padding:11px}}
.k b{{display:block;font:600 9px Archivo,sans-serif;letter-spacing:.15em;color:var(--peach);margin-bottom:6px;
     text-transform:uppercase}}
.k span{{font:700 15px Lato,sans-serif}}
h2{{font:600 11px Archivo,sans-serif;letter-spacing:.2em;color:var(--peach);margin:4px 0 8px;text-transform:uppercase}}
ul{{list-style:none;padding:0}}
li{{padding:6px 0 6px 28px;position:relative;color:var(--hell);font-size:16px;line-height:1.35}}
li:before{{content:"✓";position:absolute;left:2px;color:var(--orange);font-weight:700}}
.cta{{display:block;text-align:center;background:var(--orange);color:#160b02;text-decoration:none;
     font:800 19px Archivo,sans-serif;padding:17px;border-radius:99px;margin:26px 0 12px}}
.cta:active{{transform:scale(.98)}}
.alle{{display:block;text-align:center;color:#fff;border:1px solid rgba(255,255,255,.35);text-decoration:none;
      font:700 15px Lato,sans-serif;padding:13px;border-radius:99px}}
.hinweis{{margin-top:22px;color:var(--hell);font-size:13px;line-height:1.5;text-align:center}}
.fuss{{margin-top:18px;text-align:center;font:600 10px Archivo,sans-serif;letter-spacing:.18em;color:var(--peach)}}
.fuss a{{color:inherit;text-decoration:none}}
</style>
</head>
<body>
<div class="hero">
  <div><img class="logo" src="{logo}" alt="Inpernell"><br>{f'<span class="feld">{e(feld.get("name"))}</span>' if feld.get("name") else ""}</div>
  <div><span class="badge">TOP JOB DES TAGES</span>{f'<span class="datum">{e(post.get("datum"))}</span>' if post.get("datum") else ""}</div>
</div>
<main>
  <h1>{titel}</h1>
  {f'<div class="ort">{ort}.</div>' if ort else ""}
  {f'<div class="kacheln">{kacheln}</div>' if kacheln else ""}
  {f'<h2>{e(post.get("punkte_titel") or "Das erwartet dich")}</h2><ul>{punkte}</ul>' if punkte else ""}
  <a class="cta" href="{e(job_url)}">Jetzt bewerben →</a>
  <a class="alle" href="{ALLE_STELLEN}">Alle offenen Stellen ansehen</a>
  <p class="hinweis">Direktvermittlung in Festanstellung – keine Zeitarbeit.<br>Für dich als Bewerber kostenlos.</p>
  <div class="fuss"><a href="https://www.inpernell.de/">INPERNELL.DE</a> · PERSONALBERATUNG FÜR FACH- UND FÜHRUNGSKRÄFTE</div>
</main>
</body>
</html>
"""
    os.makedirs(os.path.dirname(ziel) or ".", exist_ok=True)
    with open(ziel, "w", encoding="utf-8") as f:
        f.write(seite)
    return ziel
