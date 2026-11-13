#!/usr/bin/env python3
"""Inpernell – TOP Job des Tages auf Instagram.

Ablauf: Stelle wählen -> Bild erzeugen -> Bild ins Repository legen (öffentliche Adresse)
-> über die offizielle Instagram-Schnittstelle veröffentlichen -> Protokoll schreiben.

Liegt für heute eine Datei overrides/JJJJ-MM-TT.json vor (von Claude vorbereitet), werden
Stelle, Bildtexte und Beitragstext daraus genommen. Sonst wählt das Programm selbst.

Umgebungsvariablen:
  IG_ACCESS_TOKEN    Instagram-Zugangsschlüssel (GitHub-Secret), nötig zum Veröffentlichen
  GITHUB_REPOSITORY  "konto/projekt" (setzt GitHub Actions automatisch)
  GITHUB_REF_NAME    Zweig, Standard "main"
  DRY_RUN            "true" = alles vorbereiten, aber NICHT veröffentlichen
  ERZWINGEN          "true" = auch außerhalb der Mittagsstunde laufen (Handstart)
  OFFERS_FILE        nur für Tests: Stellen aus lokaler JSON-Datei statt aus dem Netz
  KEIN_GIT           nur für Tests: nichts committen/pushen
"""
import csv
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from bild import erzeuge_bild

HIER = os.path.dirname(os.path.abspath(__file__))
RECRUITEE = "https://inpernellgmbh.recruitee.com/api/offers/"
GRAPH = "https://graph.instagram.com/v26.0"
PROTOKOLL = os.path.join(HIER, "data", "protokoll.csv")
SPERRFRIST = 30          # so viele letzte Posts werden nicht wiederholt
POSTSTUNDE = 12          # veröffentlicht wird in der Stunde ab 12 Uhr (Europe/Berlin)
HASHTAGS_FEST = ["#TopJobDesTages", "#Inpernell", "#Jobs", "#Karriere", "#Stellenangebot", "#Direktvermittlung"]


def wahr(name):
    return os.environ.get(name, "").strip().lower() in ("1", "true", "ja", "yes")


def http(url, daten=None, methode=None, versuche=3):
    """Kleine HTTP-Hilfe; gibt geparstes JSON zurück. Der Zugangsschlüssel taucht nie in Fehlermeldungen auf."""
    body = urllib.parse.urlencode(daten).encode() if daten is not None else None
    req = urllib.request.Request(url, data=body, method=methode or ("POST" if body else "GET"),
                                 headers={"Accept": "application/json", "User-Agent": "inpernell-topjob/1.0"})
    letzter = None
    for i in range(versuche):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:600]
            letzter = RuntimeError(f"HTTP {e.code} bei {url.split('?')[0]}: {text}")
            if e.code < 500:
                break
        except Exception as e:  # Netzfehler
            letzter = RuntimeError(f"Netzfehler bei {url.split('?')[0]}: {type(e).__name__}")
        time.sleep(3 * (i + 1))
    raise letzter


def text_aus_html(s):
    s = re.sub(r"<\s*br\s*/?>", "\n", s or "", flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"[ \t ]+", " ", html.unescape(s)).strip()


def listenpunkte(s):
    return [p for p in (text_aus_html(m) for m in re.findall(r"<li[^>]*>(.*?)</li>", s or "", flags=re.S | re.I)) if p]


def kuerzen(s, n):
    s = s.strip().rstrip(".;,")
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0].rstrip(" ,;:-–") + " …"


def protokoll_lesen():
    if not os.path.exists(PROTOKOLL):
        return []
    with open(PROTOKOLL, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def protokoll_schreiben(zeile):
    neu = not os.path.exists(PROTOKOLL)
    with open(PROTOKOLL, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["datum", "job_id", "titel", "media_id", "quelle"], delimiter=";")
        if neu:
            w.writeheader()
        w.writerow(zeile)


def stellen_laden():
    if os.environ.get("OFFERS_FILE"):
        daten = json.load(open(os.environ["OFFERS_FILE"], encoding="utf-8"))
    else:
        daten = http(RECRUITEE)
    stellen = daten.get("offers", daten if isinstance(daten, list) else [])
    return [s for s in stellen if "initiativ" not in (s.get("title") or "").lower()
            and (s.get("status") in (None, "published"))]


def gehalt(s):
    g = s.get("salary") or {}
    lo, hi = g.get("min"), g.get("max")
    try:
        lo, hi = (int(float(lo)) if lo else None), (int(float(hi)) if hi else None)
    except (TypeError, ValueError):
        return ""
    if not (lo or hi):
        return ""
    fmt = lambda v: f"{v:,}".replace(",", ".")
    spanne = f"{fmt(lo)} – {fmt(hi)} €" if lo and hi and lo != hi else f"{fmt(lo or hi)} €"
    periode = {"year": "Jahr", "month": "Monat", "hour": "Stunde"}.get((g.get("period") or "").lower(), "")
    return spanne + (f" / {periode}" if periode else "")


def stelle_waehlen(stellen, protokoll):
    gesperrt = {z["job_id"] for z in protokoll[-SPERRFRIST:]}
    frei = [s for s in stellen if str(s.get("id")) not in gesperrt] or stellen
    if not frei:
        raise RuntimeError("Keine offene Stelle gefunden.")
    # Stellen mit Gehaltsangabe zuerst, dann die neuesten
    frei.sort(key=lambda s: (bool(gehalt(s)), s.get("published_at") or s.get("created_at") or ""), reverse=True)
    return frei[0]


def aus_stelle(s, datum):
    """Bildtexte und Beitragstext ohne KI direkt aus der Stellenanzeige bauen (Ersatzweg)."""
    titel = (s.get("title") or "").strip()
    ort = (s.get("city") or s.get("location") or "").split(",")[0].strip()
    extras = [gehalt(s)]
    if s.get("remote"):
        extras.append("Remote möglich")
    elif s.get("hybrid"):
        extras.append("Homeoffice möglich")
    extra = " · ".join(e for e in extras if e)
    anforderungen = listenpunkte(s.get("requirements")) or listenpunkte(s.get("description"))
    punkte = [kuerzen(p, 42) for p in anforderungen[:3]]
    url = s.get("careers_url") or "https://www.inpernell.de/jobboerse/"

    zeilen = [f"TOP Job des Tages: {titel}" + (f" in {ort}" if ort else ""), ""]
    if extra:
        zeilen += [extra, ""]
    if anforderungen:
        zeilen.append("Das solltest du mitbringen:")
        zeilen += [f"• {kuerzen(p, 110)}" for p in anforderungen[:3]]
        zeilen.append("")
    zeilen += ["Direktvermittlung in Festanstellung – keine Zeitarbeit, für dich als Bewerber kostenlos.", "",
               "Jetzt bewerben über den Link in der Bio oder auf www.inpernell.de", ""]
    tags = list(HASHTAGS_FEST)
    if ort:
        tags.insert(0, "#" + re.sub(r"[^0-9A-Za-zÄÖÜäöüß]", "", ort))
    zeilen.append(" ".join(tags))
    return {"job_id": str(s.get("id")), "titel": titel, "ort": ort, "extra": extra, "punkte": punkte,
            "datum": datum, "caption": "\n".join(zeilen), "job_url": url}


def git(*args):
    subprocess.run(["git", *args], cwd=HIER, check=True)


def git_sichern(nachricht, *pfade):
    if wahr("KEIN_GIT"):
        return
    git("config", "user.name", "inpernell-topjob")
    git("config", "user.email", "actions@users.noreply.github.com")
    git("add", *pfade)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=HIER).returncode == 0:
        return
    git("commit", "-m", nachricht)
    git("pull", "--rebase", "--autostash")
    git("push")


def warte_auf_bild(url):
    for _ in range(20):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "inpernell-topjob/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(6)
    raise RuntimeError("Das Bild ist unter seiner öffentlichen Adresse nicht erreichbar: " + url)


def veroeffentlichen(token, bild_url, caption):
    ich = http(f"{GRAPH}/me?" + urllib.parse.urlencode({"fields": "user_id,username", "access_token": token}))
    ig_id = ich.get("user_id") or ich.get("id")
    print("Instagram-Konto:", ich.get("username"))
    container = http(f"{GRAPH}/{ig_id}/media", {"image_url": bild_url, "caption": caption, "access_token": token})["id"]
    for _ in range(15):
        status = http(f"{GRAPH}/{container}?" + urllib.parse.urlencode({"fields": "status_code", "access_token": token}))
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            raise RuntimeError("Instagram konnte das Bild nicht verarbeiten.")
        time.sleep(4)
    return http(f"{GRAPH}/{ig_id}/media_publish", {"creation_id": container, "access_token": token})["id"]


def schluessel_verlaengern(token):
    """Verlängert die Gültigkeit des Zugangsschlüssels um weitere 60 Tage (geht erst ab 24 h Alter)."""
    try:
        r = http(f"{GRAPH.rsplit('/', 1)[0]}/refresh_access_token?" +
                 urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": token}), versuche=1)
        tage = int(r.get("expires_in", 0)) // 86400
        print(f"Zugangsschlüssel verlängert, gültig für weitere {tage} Tage.")
        if r.get("access_token") and r["access_token"] != token:
            print("::warning::Instagram hat einen NEUEN Zugangsschlüssel ausgegeben. Bitte im Meta-Dashboard einen "
                  "neuen Schlüssel erzeugen und als Secret IG_ACCESS_TOKEN hinterlegen.")
    except Exception as e:
        print(f"::warning::Zugangsschlüssel konnte nicht verlängert werden ({e}). "
              "Spätestens nach 60 Tagen im Meta-Dashboard einen neuen erzeugen.")


def main():
    jetzt = datetime.now(ZoneInfo("Europe/Berlin"))
    heute = jetzt.strftime("%Y-%m-%d")
    probe = wahr("DRY_RUN")

    if not wahr("ERZWINGEN") and jetzt.hour != POSTSTUNDE:
        print(f"Es ist {jetzt:%H:%M} Uhr in Berlin – gepostet wird nur in der Stunde ab {POSTSTUNDE} Uhr. Ende.")
        return
    protokoll = protokoll_lesen()
    if not probe and any(z["datum"] == heute and z.get("media_id") for z in protokoll):
        print("Für heute wurde bereits gepostet. Ende.")
        return

    vorgabe = os.path.join(HIER, "overrides", f"{heute}.json")
    if os.path.exists(vorgabe):
        post = json.load(open(vorgabe, encoding="utf-8"))
        post.setdefault("datum", jetzt.strftime("%d.%m.%Y"))
        quelle = "claude"
        for feld in ("titel", "caption"):
            if not post.get(feld):
                raise RuntimeError(f"In {vorgabe} fehlt das Feld '{feld}'.")
    else:
        post = aus_stelle(stelle_waehlen(stellen_laden(), protokoll), jetzt.strftime("%d.%m.%Y"))
        quelle = "automatisch"
    print(f"Stelle ({quelle}): {post['titel']} – {post.get('ort', '')}")

    bild_rel = f"posts/{heute}.jpg"
    erzeuge_bild(post, os.path.join(HIER, bild_rel))
    with open(os.path.join(HIER, "posts", f"{heute}.txt"), "w", encoding="utf-8") as f:
        f.write(post["caption"] + "\n")
    git_sichern(f"Top Job {heute}: Bild und Text", bild_rel, f"posts/{heute}.txt")

    if probe:
        print("PROBELAUF: Bild und Text liegen im Ordner posts/. Es wurde NICHTS veröffentlicht.")
        return

    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Das Secret IG_ACCESS_TOKEN fehlt (Einstellungen des Projekts > Secrets and variables > Actions).")
    repo = os.environ["GITHUB_REPOSITORY"]
    zweig = os.environ.get("GITHUB_REF_NAME", "main")
    bild_url = f"https://raw.githubusercontent.com/{repo}/{zweig}/{bild_rel}"
    warte_auf_bild(bild_url)

    media_id = veroeffentlichen(token, bild_url, post["caption"][:2200])
    print("Veröffentlicht. Beitrags-ID:", media_id)
    protokoll_schreiben({"datum": heute, "job_id": post.get("job_id", ""), "titel": post["titel"],
                         "media_id": media_id, "quelle": quelle})
    git_sichern(f"Top Job {heute}: veröffentlicht", "data/protokoll.csv")
    schluessel_verlaengern(token)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"::error::{e}")
        sys.exit(1)
