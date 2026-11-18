#!/usr/bin/env python3
"""Inpernell – TOP Job des Tages auf Instagram.

Ablauf: Stelle wählen -> Bild erzeugen -> Bild ins Repository legen (öffentliche Adresse)
-> über die offizielle Instagram-Schnittstelle veröffentlichen -> Protokoll schreiben.

Liegt für heute eine Datei overrides/JJJJ-MM-TT.json vor (von Claude vorbereitet), werden
Stelle, Bildtexte und Beitragstext daraus genommen. Sonst wählt das Programm selbst.

Umgebungsvariablen:
  IG_ACCESS_TOKEN    Zugangsschlüssel (GitHub-Secret), nötig zum Veröffentlichen. Beginnt er mit "IG",
                     wird graph.instagram.com genutzt, beginnt er mit "EAA", graph.facebook.com.
  IG_USER_ID         nur bei EAA-Schlüssel und mehreren Konten: ID des Instagram-Business-Kontos
  GITHUB_REPOSITORY  "konto/projekt" (setzt GitHub Actions automatisch)
  GITHUB_REF_NAME    Zweig, Standard "main"
  DRY_RUN            "true" = alles vorbereiten, aber NICHT veröffentlichen
  ERZWINGEN          "true" = auch außerhalb der Mittagsstunde laufen (Handstart)
  FORMAT             "bild", "karussell" oder "reel" erzwingen (sonst Vorgabe bzw. WOCHENPLAN)
  STORY              "false" = keine Story zusätzlich zum Beitrag (Standard: Story wird gepostet)
  NEU_POSTEN         "true" = heutigen Beitrag ersetzen: alten Beitrag löschen, dann neu posten (Handstart)
  JOB_ID             nur diese Recruitee-Stelle posten (Handstart)
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

import kategorien
from bild import erzeuge_bild, erzeuge_folgeseiten, erzeuge_reel, erzeuge_story
from seite import erzeuge_seite

HIER = os.path.dirname(os.path.abspath(__file__))
RECRUITEE = "https://inpernellgmbh.recruitee.com/api/offers/"
GRAPH = "https://graph.instagram.com/v26.0"   # Schlüssel aus "Instagram-Login" (beginnt mit IG…)
GRAPH_FB = "https://graph.facebook.com"        # Schlüssel aus Facebook-/Unified-Login (beginnt mit EAA…)
PROTOKOLL = os.path.join(HIER, "data", "protokoll.csv")
SPERRFRIST = 30          # so viele letzte Posts werden nicht wiederholt
POSTSTUNDE = 12          # Standard-Stunde (Europe/Berlin), wenn ZEITPLAN nichts anderes sagt
# Zeitplan: jeden Tag um 18:50 Uhr (Wunsch Inpernell; Berufstätige suchen abends Jobs).
# Gibt die Stunde zurück, in der gepostet wird; None = an diesem Tag kein neuer Top Job.
def poststunde(jetzt):
    return 18
# Format je Wochentag (0 = Montag): "bild" = Feed-Beitrag 4:5, "reel" = 10-Sekunden-Video 9:16.
# Eine Vorgabe von Claude ("format": "reel") oder die Variable FORMAT haben Vorrang.
# "karussell" = 4 Seiten (Top Job, Aufgaben, Anforderungen, So bewirbst du dich) – laut Bericht stärker als
# ein Einzelbild. Reel später z. B. an einzelnen Tagen: {1: "reel", ...}
WOCHENPLAN = {0: "karussell", 1: "karussell", 2: "karussell", 3: "karussell", 4: "karussell", 5: "karussell",
              6: "karussell"}
# Instagram erlaubt seit Dez. 2025 höchstens 5 Hashtags. Satz: Beruf, Jobs<Ort>, Region, Absicht, Marke.
HASHTAG_ABSICHT, HASHTAG_MARKE = "#Stellenangebot", "#TopJobDesTages"
# Region je Ort (für den Regions-Hashtag); unbekannte Orte bekommen #Schwarzwald
REGIONEN = {
    "#SchwarzwaldBaar": ["villingen", "schwenningen", "donaueschingen", "blumberg", "mönchweiler", "bad dürrheim",
                         "st. georgen", "furtwangen", "hüfingen", "bräunlingen", "königsfeld", "brigachtal"],
    "#LandkreisTuttlingen": ["tuttlingen", "gosheim", "renquishausen", "kolbingen", "trossingen", "spaichingen",
                             "wehingen", "mühlheim", "fridingen", "aldingen", "immendingen", "geisingen"],
    "#LandkreisRottweil": ["rottweil", "schramberg", "wellendingen", "oberndorf", "sulz", "dunningen", "deißlingen"],
    "#Hochschwarzwald": ["titisee", "neustadt", "löffingen", "lenzkirch", "hinterzarten", "schluchsee"],
    "#Breisgau": ["freiburg", "bad krozingen", "staufen", "müllheim", "emmendingen", "breisach", "heitersheim"],
}
HASHTAGS_FELD = {   # erster Eintrag = Berufs-Hashtag im Beitrag
    "zerspanung": ["#Zerspanung", "#CNC", "#Metallbearbeitung"],
    "konstruktion": ["#Konstruktion", "#Engineering", "#CAD"],
    "projektleitung": ["#Projektmanagement", "#Führungskraft"],
    "qualitaet": ["#Qualitätsmanagement", "#Qualitätssicherung"],
    "technik": ["#Instandhaltung", "#Mechatronik", "#Technik"],
    "it": ["#ITJobs", "#ERP", "#Digitalisierung"],
    "banking": ["#Banking", "#Finanzberatung", "#Bankjobs"],
    "finanzen": ["#Finanzen", "#Buchhaltung", "#Controlling"],
    "personal": ["#HR", "#Personalwesen"],
    "einkauf": ["#Einkauf", "#Beschaffung"],
    "logistik": ["#Logistik", "#SupplyChain"],
    "vertrieb": ["#Vertrieb", "#Sales"],
    "produktion": ["#Produktion", "#Industrie", "#Fertigung"],
}


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


PROTOKOLL_SPALTEN = ["datum", "job_id", "titel", "media_id", "quelle", "format", "story_id"]


def protokoll_speichern(zeilen):
    with open(PROTOKOLL, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PROTOKOLL_SPALTEN, delimiter=";", extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(zeilen)


def protokoll_schreiben(zeile):
    protokoll_speichern(protokoll_lesen() + [zeile])


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


SPERRFRIST_GEHALT = 10   # Stellen MIT Gehalt dürfen schon nach 10 anderen Posts wieder dran sein


def stelle_waehlen(stellen, protokoll):
    """Stellen mit Gehaltsangabe haben Vorrang (wichtigster Hebel laut Bericht); sonst die neueste freie Stelle."""
    neueste = lambda liste: sorted(liste, key=lambda s: s.get("published_at") or s.get("created_at") or "",
                                   reverse=True)
    gesperrt = {z["job_id"] for z in protokoll[-SPERRFRIST:]}
    gesperrt_kurz = {z["job_id"] for z in protokoll[-SPERRFRIST_GEHALT:]}
    mit_gehalt = [s for s in stellen if gehalt(s) and str(s.get("id")) not in gesperrt_kurz]
    if mit_gehalt:
        # unter den Gehalts-Stellen die am längsten nicht gezeigte nehmen, bei Gleichstand die neueste
        zuletzt = {z["job_id"]: i for i, z in enumerate(protokoll)}
        return sorted(neueste(mit_gehalt), key=lambda s: zuletzt.get(str(s.get("id")), -1))[0]
    frei = [s for s in stellen if str(s.get("id")) not in gesperrt] or stellen
    if not frei:
        raise RuntimeError("Keine offene Stelle gefunden.")
    return neueste(frei)[0]


FUELLWOERTER = {"und", "oder", "sowie", "von", "der", "die", "das", "des", "den", "dem", "für", "mit", "in", "im",
               "bei", "zur", "zum", "auf", "aus", "an", "am", "eine", "einer", "einem", "eines", "ein", "zu"}


def kurzpunkt(s, n=60):
    """Macht aus einem langen Anzeigen-Punkt eine knappe Zeile fürs Bild (max. n Zeichen)."""
    s = re.sub(r"\s+", " ", s.replace("\xad", "")).strip().rstrip(".;,")
    if ":" in s and 10 <= len(s.split(":")[0]) <= n:
        return s.split(":")[0].strip()
    for trenner in (" sowie ", "; ", " – ", " - ", " (", " inkl. ", " unter Berücksichtigung"):
        if len(s) > n and len(s.split(trenner)[0].strip()) >= 18:
            s = s.split(trenner)[0].strip()
    if len(s) <= n:
        return s
    woerter = s[:n].split(" ")[:-1]
    while woerter and (woerter[-1].lower().strip(",") in FUELLWOERTER or woerter[-1].endswith("-")):
        woerter.pop()
    return " ".join(woerter).rstrip(",") + "…"


SIE_FORM = re.compile(r"\b(Sie|Ihnen|Ihr\w*|Du|Dir|Dich|Wir|Uns)\b")


def highlights(aufgaben, anforderungen):
    """Bis zu drei knappe Punkte fürs Bild; Aufgaben bevorzugt, ganze Sätze ("Sie ...") meiden."""
    for liste, titel in ((aufgaben, "Das erwartet dich"), (anforderungen, "Das bringst du mit")):
        gut = [kurzpunkt(p) for p in liste if not SIE_FORM.search(p)]
        gut = [p for p in gut if not p.endswith("…")] + [p for p in gut if p.endswith("…")]
        if len(gut) >= 3:
            return gut[:3], titel
    alle = [kurzpunkt(p) for p in (aufgaben or anforderungen)]
    return alle[:3], "Das erwartet dich" if aufgaben else "Das bringst du mit"


ARBEITSZEIT = {"fulltime": "Vollzeit", "parttime": "Teilzeit", "freelance": "Freiberuflich",
               "internship": "Praktikum", "temporary": "Befristet"}


def fakten(s):
    """Drei Eckdaten für die Kacheln: Gehalt, Arbeitszeit, Arbeitsmodell."""
    g = gehalt(s)
    g_label = {"Jahr": "Jahresgehalt", "Monat": "Monatsgehalt", "Stunde": "Stundenlohn"}.get(g.split(" / ")[-1], "Gehalt")
    g = g.split(" / ")[0]
    art = (s.get("employment_type_code") or "").split("_")[0]
    zeit = ARBEITSZEIT.get(art, "Vollzeit")
    stunden = s.get("min_hours_per_week") or s.get("max_hours_per_week")
    if stunden and art in ("fulltime", "parttime", ""):
        zeit += f" · {int(float(stunden))} h"
    modell = "Remote möglich" if s.get("remote") else ("Hybrid / Homeoffice" if s.get("hybrid") else "Vor Ort")
    return [[g_label if g else "Gehalt", g or "Attraktiv"], ["Arbeitszeit", zeit], ["Arbeitsmodell", modell]]


def hashtags(kat, ort):
    """Genau 5 Hashtags: Beruf, Jobs<Ort>, Region, Absicht, Marke."""
    tags = [HASHTAGS_FELD.get(kat, ["#Jobs"])[0]]
    if ort:
        tags.append("#Jobs" + re.sub(r"[^0-9A-Za-zÄÖÜäöüß]", "", ort.title()))
    region = next((r for r, orte in REGIONEN.items() if any(o in ort.lower() for o in orte)), "#Schwarzwald")
    tags += [region, HASHTAG_ABSICHT, HASHTAG_MARKE]
    return " ".join(dict.fromkeys(tags[:5]))


def bildtext(titel, ort, kat, gehalt_text, fk, aufgaben, anforderungen, ohne_anschreiben=True):
    """Bildtext nach dem Reichweiten-Bericht: Suchzeile zuerst, dann Eckdaten, Weiterleiten, DM, 5 Hashtags."""
    kopf = [titel + (f" in {ort}" if ort else "")]
    if gehalt_text:
        kopf.append(gehalt_text.replace(" / Jahr", " im Jahr").replace(" / Monat", " im Monat"))
    kopf.append(fk[2][1])
    zeilen = [" – ".join(kopf) + " 🔥", "",
              "TOP Job des Tages bei Inpernell: Direktvermittlung in Festanstellung beim Arbeitgeber – "
              "keine Zeitarbeit, für dich kostenlos.", ""]
    zeilen += [f"💶 {gehalt_text or 'Gehalt auf Anfrage'}", f"🕒 {fk[1][1]}", f"🏠 {fk[2][1]}"]
    if ort:
        zeilen.append(f"📍 {ort}")
    zeilen.append("")
    for liste, ueberschrift in ((aufgaben, "Das erwartet dich:"), (anforderungen, "Das bringst du mit:")):
        # Sätze in der Sie-Form passen nicht zur Du-Ansprache auf Instagram und werden ausgelassen
        gut = [re.sub(r"\s+:", ":", p) for p in liste if not SIE_FORM.search(p)]
        if len(gut) >= 2:
            zeilen.append(ueberschrift)
            zeilen += [f"✔️ {kuerzen(p, 110)}" for p in gut[:3]]
            zeilen.append("")
    zeilen += ["👉 Bewerben: Link in der Bio antippen" + (" – Lebenslauf genügt, kein Anschreiben nötig."
                                                        if ohne_anschreiben else "."),
               "💬 Oder schreib uns einfach „Interesse“ per Direktnachricht – wir melden uns.", "",
               f"Kennst du jemanden{' in der Region ' + ort if ort else ''}, für den das passt? "
               "Schick ihm den Beitrag weiter. 📩", "",
               hashtags(kat, ort)]
    return "\n".join(zeilen)


def folienpunkte(liste, n=5):
    """Bis zu n Punkte für die Karussell-Seiten; Du-taugliche Punkte zuerst, sonst alle."""
    gut = [p for p in liste if not SIE_FORM.search(p)]
    quelle = gut if len(gut) >= 2 else liste
    return [kurzpunkt(p, 78) for p in quelle[:n]]


def aus_stelle(s, datum):
    """Bildtexte und Beitragstext ohne KI direkt aus der Stellenanzeige bauen (Ersatzweg)."""
    titel = (s.get("title") or "").strip()
    ort = (s.get("city") or s.get("location") or "").split(",")[0].strip()
    aufgaben = listenpunkte(s.get("description"))
    anforderungen = listenpunkte(s.get("requirements"))
    fk = fakten(s)
    kat = kategorien.erkenne(titel, s.get("category_code"))
    url = s.get("careers_url") or "https://www.inpernell.de/jobboerse/"

    caption = bildtext(titel, ort, kat, gehalt(s), fk, aufgaben, anforderungen,
                       ohne_anschreiben=(s.get("options_cover_letter") or "optional") != "required")
    return {"job_id": str(s.get("id")), "titel": titel, "ort": ort, "kategorie": kat, "fakten": fk,
            "punkte": highlights(aufgaben, anforderungen)[0],
            "punkte_titel": highlights(aufgaben, anforderungen)[1],
            "aufgaben": folienpunkte(aufgaben), "anforderungen": folienpunkte(anforderungen),
            "ohne_anschreiben": (s.get("options_cover_letter") or "optional") != "required",
            "datum": datum, "caption": caption, "job_url": url}


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


def ist_facebook_schluessel(token):
    return token.startswith("EAA")


def instagram_konto(token):
    """Liefert (Basis-Adresse, Instagram-Konto-ID, Name) passend zur Art des Schlüssels."""
    q = lambda **kw: urllib.parse.urlencode({**kw, "access_token": token})
    if not ist_facebook_schluessel(token):
        ich = http(f"{GRAPH}/me?" + q(fields="user_id,username"))
        return GRAPH, ich.get("user_id") or ich.get("id"), ich.get("username")
    if os.environ.get("IG_USER_ID", "").strip():
        ig_id = os.environ["IG_USER_ID"].strip()
        konto = http(f"{GRAPH_FB}/{ig_id}?" + q(fields="id,username"), versuche=1)
        return GRAPH_FB, ig_id, konto.get("username")
    feld = "instagram_business_account{id,username}"
    # Benutzer-Schlüssel: Instagram-Konto über die verknüpfte Facebook-Seite finden
    konten = []
    try:
        for seite in http(f"{GRAPH_FB}/me/accounts?" + q(fields=f"name,{feld}")).get("data", []):
            if seite.get("instagram_business_account"):
                konten.append(seite["instagram_business_account"])
    except RuntimeError:
        pass
    # Seiten-Schlüssel: /me ist dann die Seite selbst
    if not konten:
        try:
            ich = http(f"{GRAPH_FB}/me?" + q(fields=f"name,{feld}"), versuche=1)
            if ich.get("instagram_business_account"):
                konten.append(ich["instagram_business_account"])
        except RuntimeError:
            pass
    if not konten:
        raise RuntimeError("Zum Schlüssel wurde kein Instagram-Business-Konto gefunden. " + facebook_diagnose(token))
    if len(konten) > 1:
        namen = ", ".join(f"{k.get('username')} ({k['id']})" for k in konten)
        wahl = [k for k in konten if "inpernell" in (k.get("username") or "").lower()]
        if len(wahl) != 1:
            raise RuntimeError(f"Mehrere Instagram-Konten gefunden: {namen}. Bitte die gewünschte ID als "
                               "Secret IG_USER_ID hinterlegen.")
        konten = wahl
    return GRAPH_FB, konten[0]["id"], konten[0].get("username")


def facebook_diagnose(token):
    """Erklärt, warum zum EAA-Schlüssel kein Instagram-Konto gefunden wurde (ohne den Schlüssel zu zeigen)."""
    q = lambda **kw: urllib.parse.urlencode({**kw, "access_token": token})
    teile = []
    try:
        ich = http(f"{GRAPH_FB}/me?" + q(fields="id,name"), versuche=1)
        teile.append(f"Schlüssel gehört zu: {ich.get('name')}.")
    except RuntimeError as e:
        teile.append(f"/me nicht lesbar ({e}).")
    try:
        rechte = http(f"{GRAPH_FB}/me/permissions?" + q(), versuche=1).get("data", [])
        erteilt = sorted(r["permission"] for r in rechte if r.get("status") == "granted")
        noetig = ["instagram_basic", "instagram_content_publish", "pages_show_list", "pages_read_engagement"]
        fehlt = [r for r in noetig if r not in erteilt]
        teile.append("Erteilte Rechte: " + (", ".join(erteilt) or "keine") + ".")
        if fehlt:
            teile.append("FEHLENDE Rechte: " + ", ".join(fehlt) + ".")
    except RuntimeError as e:
        teile.append(f"Rechte nicht lesbar ({e}).")
    try:
        seiten = http(f"{GRAPH_FB}/me/accounts?" + q(fields="name"), versuche=1).get("data", [])
        teile.append("Facebook-Seiten: " + (", ".join(x.get("name", "?") for x in seiten) or "keine gefunden") + ".")
    except RuntimeError as e:
        teile.append(f"Seiten nicht lesbar ({e}).")
    teile.append("Lösung: entweder die ID des Instagram-Kontos als Secret IG_USER_ID hinterlegen (bei einem "
                 "Systembenutzer-Schlüssel der einfachste Weg) oder das Instagram-Konto mit einer Facebook-Seite "
                 "verknüpfen und die fehlenden Rechte in den Schlüssel aufnehmen.")
    return " ".join(teile)


def veroeffentlichen(token, caption, bild_url=None, video_url=None, titelbild_url=None, story_url=None,
                     bild_urls=None):
    """Bild, Reel oder Story über die offizielle Instagram-Schnittstelle veröffentlichen; gibt die ID zurück."""
    basis, ig_id, name = instagram_konto(token)
    print("Instagram-Konto:", name, "· Schnittstelle:", basis.split("//")[1].split("/")[0])
    def warten(container, runden, pause):
        for _ in range(runden):
            status = http(f"{basis}/{container}?" + urllib.parse.urlencode({"fields": "status_code,status",
                                                                          "access_token": token}))
            if status.get("status_code") == "FINISHED":
                return
            if status.get("status_code") == "ERROR":
                raise RuntimeError(f"Instagram konnte die Datei nicht verarbeiten: {status.get('status', '')}")
            time.sleep(pause)
        raise RuntimeError("Instagram hat die Datei nicht rechtzeitig verarbeitet.")

    if bild_urls:
        # Karussell: erst jede Seite einzeln anlegen, dann das Karussell daraus
        kinder = []
        for url in bild_urls[:10]:
            kind = http(f"{basis}/{ig_id}/media", {"image_url": url, "is_carousel_item": "true",
                                                   "access_token": token})["id"]
            warten(kind, 15, 3)
            kinder.append(kind)
        daten = {"media_type": "CAROUSEL", "children": ",".join(kinder), "caption": caption, "access_token": token}
        runden, pause = 20, 4
    elif story_url:
        # Hinweis: Link-Sticker kann die Schnittstelle nicht setzen; der Link steht deshalb lesbar im Bild.
        daten = {"media_type": "STORIES", "image_url": story_url, "access_token": token}
        runden, pause = 15, 4
    elif video_url:
        daten = {"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true",
                 "access_token": token}
        if titelbild_url:
            daten["cover_url"] = titelbild_url
        runden, pause = 60, 6        # Videos brauchen bei Instagram bis zu einigen Minuten
    else:
        daten = {"image_url": bild_url, "caption": caption, "access_token": token}
        runden, pause = 15, 4
    container = http(f"{basis}/{ig_id}/media", daten)["id"]
    warten(container, runden, pause)
    return http(f"{basis}/{ig_id}/media_publish", {"creation_id": container, "access_token": token})["id"]


def beitrag_loeschen(token, media_id):
    """Löscht einen eigenen Beitrag über die Schnittstelle. Wirft einen Fehler, wenn Instagram das ablehnt."""
    basis, _, _ = instagram_konto(token)
    r = http(f"{basis}/{media_id}?" + urllib.parse.urlencode({"access_token": token}), methode="DELETE", versuche=1)
    if not (r is True or r.get("success")):
        raise RuntimeError(f"Löschen nicht bestätigt: {r}")


def facebook_schluessel_pruefen(token):
    """Bei EAA-Schlüsseln: Ablaufdatum anzeigen und rechtzeitig warnen (verlängern geht nur im Meta-Dashboard)."""
    try:
        info = http(f"{GRAPH_FB}/debug_token?" + urllib.parse.urlencode({"input_token": token, "access_token": token}),
                    versuche=1).get("data", {})
        ablauf = int(info.get("expires_at") or 0)
        if not ablauf:
            print("Zugangsschlüssel läuft nicht ab.")
            return
        tage = (ablauf - time.time()) / 86400
        print(f"Zugangsschlüssel gültig bis {datetime.fromtimestamp(ablauf, ZoneInfo('Europe/Berlin')):%d.%m.%Y %H:%M}.")
        if tage < 10:
            print(f"::warning::Der Zugangsschlüssel läuft in {tage:.0f} Tagen ab. Im Meta-Dashboard einen neuen "
                  "erzeugen (oder im Access Token Debugger verlängern) und das Secret IG_ACCESS_TOKEN ersetzen.")
    except Exception:
        # z. B. bei Systembenutzer-Schlüsseln, die meist unbegrenzt gelten
        print("Ablaufdatum des Zugangsschlüssels nicht abrufbar (bei Systembenutzer-Schlüsseln normal).")


def schluessel_verlaengern(token):
    """Verlängert die Gültigkeit des Zugangsschlüssels um weitere 60 Tage (geht erst ab 24 h Alter)."""
    if ist_facebook_schluessel(token):
        return facebook_schluessel_pruefen(token)
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


def story_posten(token, story_url, heute):
    """Story veröffentlichen und im Protokoll vermerken. Ein Fehler hier stoppt den (schon geposteten) Beitrag nicht."""
    try:
        story_id = veroeffentlichen(token, "", story_url=story_url)
    except Exception as e:
        print(f"::warning::Story konnte nicht veröffentlicht werden: {e}")
        return None
    print("Story veröffentlicht. ID:", story_id)
    zeilen = protokoll_lesen()
    for z in reversed(zeilen):
        if z["datum"] == heute and z.get("media_id"):
            z["story_id"] = story_id
            break
    protokoll_speichern(zeilen)
    git_sichern(f"Top Job {heute}: Story veröffentlicht", "data/protokoll.csv")
    return story_id


def story_nachholen(zeile, protokoll, jetzt, heute):
    """Der Beitrag ist heute schon online, die Story fehlt noch: Story zur selben Stelle erzeugen und posten."""
    vorgabe = os.path.join(HIER, "overrides", f"{heute}.json")
    if os.path.exists(vorgabe):
        post = json.load(open(vorgabe, encoding="utf-8"))
        post.setdefault("datum", jetzt.strftime("%d.%m.%Y"))
    else:
        stelle = next((s for s in stellen_laden() if str(s.get("id")) == zeile["job_id"]), None)
        if not stelle:
            print(f"::warning::Stelle {zeile['job_id']} ist nicht mehr online – keine Story.")
            return
        post = aus_stelle(stelle, jetzt.strftime("%d.%m.%Y"))
    post.setdefault("kategorie", kategorien.erkenne(post["titel"]))
    print(f"Beitrag ist schon online, Story wird nachgeholt: {post['titel']}")
    story_rel = f"posts/{heute}-story.jpg"
    erzeuge_story(post, os.path.join(HIER, story_rel))
    git_sichern(f"Top Job {heute}: Story", story_rel)
    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Das Secret IG_ACCESS_TOKEN fehlt.")
    basis = f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/{os.environ.get('GITHUB_REF_NAME', 'main')}/"
    warte_auf_bild(basis + story_rel)
    if not story_posten(token, basis + story_rel, heute):
        raise RuntimeError("Story konnte nicht veröffentlicht werden (Details siehe Warnung oben).")


def main():
    jetzt = datetime.now(ZoneInfo("Europe/Berlin"))
    heute = jetzt.strftime("%Y-%m-%d")
    probe = wahr("DRY_RUN")

    stunde = poststunde(jetzt)
    if not wahr("ERZWINGEN") and jetzt.hour != stunde:
        if stunde is None:
            print("Heute (Samstag) ist laut Zeitplan Pause. Ende.")
        else:
            print(f"Es ist {jetzt:%H:%M} Uhr in Berlin – heute wird in der Stunde ab {stunde} Uhr gepostet. Ende.")
        return
    protokoll = protokoll_lesen()
    mit_story = os.environ.get("STORY", "true").strip().lower() not in ("0", "false", "nein", "no")
    alte_story = ""
    heute_gepostet = [z for z in protokoll if z["datum"] == heute and z.get("media_id")
                      and not z["media_id"].startswith("geloescht")]
    if not probe and heute_gepostet and wahr("NEU_POSTEN"):
        alt = heute_gepostet[-1]
        token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
        print(f"Heutigen Beitrag ersetzen: {alt['titel']} (Beitrags-ID {alt['media_id']}) wird gelöscht …")
        try:
            beitrag_loeschen(token, alt["media_id"])
            print("Alter Beitrag gelöscht.")
        except Exception as e:
            if not wahr("TROTZDEM_POSTEN"):
                raise RuntimeError(f"Der alte Beitrag konnte nicht über die Schnittstelle gelöscht werden ({e}). "
                                   "Bitte in der Instagram-App löschen und den Lauf mit 'trotzdem posten' "
                                   "wiederholen. Es wurde nichts Neues veröffentlicht.")
            print(f"::warning::Alter Beitrag nicht gelöscht ({e}) – laut Vorgabe wird trotzdem neu gepostet.")
        alt["media_id"] = "geloescht:" + alt["media_id"]
        protokoll_speichern(protokoll)
        git_sichern(f"Top Job {heute}: alter Beitrag ersetzt", "data/protokoll.csv")
        protokoll = protokoll_lesen()
        heute_gepostet = []
        if not os.environ.get("JOB_ID"):
            os.environ["JOB_ID"] = alt["job_id"]          # dieselbe Stelle neu posten
        alte_story = alt.get("story_id", "")
        if alte_story:
            mit_story = False                             # Story von heute bleibt stehen, keine zweite
    if not probe and heute_gepostet:
        if mit_story and not heute_gepostet[-1].get("story_id"):
            return story_nachholen(heute_gepostet[-1], protokoll, jetzt, heute)
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
        stellen = stellen_laden()
        wunsch = os.environ.get("JOB_ID", "").strip()
        if wunsch:
            stelle = next((s for s in stellen if str(s.get("id")) == wunsch), None)
            if not stelle:
                raise RuntimeError(f"Stelle {wunsch} ist in Recruitee nicht (mehr) veröffentlicht.")
        else:
            stelle = stelle_waehlen(stellen, protokoll)
        post = aus_stelle(stelle, jetzt.strftime("%d.%m.%Y"))
        quelle = "automatisch"
    print(f"Stelle ({quelle}): {post['titel']} – {post.get('ort', '')}")

    post.setdefault("kategorie", kategorien.erkenne(post["titel"]))
    fmt = (os.environ.get("FORMAT") or post.get("format") or WOCHENPLAN[jetzt.weekday()]).strip().lower()
    if fmt not in ("bild", "karussell", "reel"):
        raise RuntimeError(f"Unbekanntes Format '{fmt}' – erlaubt sind 'bild', 'karussell' und 'reel'.")
    print(f"Format: {fmt} · Berufsfeld: {post['kategorie']}")

    bild_rel = f"posts/{heute}.jpg"
    erzeuge_bild(post, os.path.join(HIER, bild_rel))
    dateien = [bild_rel, f"posts/{heute}.txt"]
    seiten_rel = [bild_rel]
    if fmt == "karussell":
        for pfad in erzeuge_folgeseiten(post, os.path.join(HIER, "posts"), heute):
            seiten_rel.append(os.path.relpath(pfad, HIER))
        dateien += seiten_rel[1:]
    # "Link in der Bio"-Seite mit dem aktuellen Top Job (ausgeliefert über GitHub Pages aus dem Ordner docs/)
    erzeuge_seite(post, os.path.join(HIER, "docs", "index.html"))
    dateien.append("docs/index.html")
    story_rel = f"posts/{heute}-story.jpg"
    if mit_story:
        erzeuge_story(post, os.path.join(HIER, story_rel))
        dateien.append(story_rel)
    if fmt == "reel":
        video_rel, titel_rel = f"posts/{heute}.mp4", f"posts/{heute}-reel.jpg"
        erzeuge_reel(post, os.path.join(HIER, video_rel), titelbild=os.path.join(HIER, titel_rel))
        dateien += [video_rel, titel_rel]
    with open(os.path.join(HIER, "posts", f"{heute}.txt"), "w", encoding="utf-8") as f:
        f.write(post["caption"] + "\n")
    git_sichern(f"Top Job {heute}: {fmt.capitalize()} und Text", *dateien)

    if probe:
        token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
        if token:   # Schlüssel prüfen, ohne etwas zu veröffentlichen
            try:
                _, ig_id, name = instagram_konto(token)
                print(f"Zugangsschlüssel funktioniert: Instagram-Konto {name} (ID {ig_id}).")
                if ist_facebook_schluessel(token):
                    facebook_schluessel_pruefen(token)
            except Exception as e:
                print(f"::warning::Zugangsschlüssel funktioniert NICHT: {e}")
        print("PROBELAUF: Dateien liegen im Ordner posts/. Es wurde NICHTS veröffentlicht.")
        return

    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Das Secret IG_ACCESS_TOKEN fehlt (Einstellungen des Projekts > Secrets and variables > Actions).")
    repo = os.environ["GITHUB_REPOSITORY"]
    zweig = os.environ.get("GITHUB_REF_NAME", "main")
    basis = f"https://raw.githubusercontent.com/{repo}/{zweig}/"
    for rel in dateien:
        if not rel.endswith(".txt"):
            warte_auf_bild(basis + rel)

    if fmt == "reel":
        media_id = veroeffentlichen(token, post["caption"][:2200], video_url=basis + video_rel,
                                    titelbild_url=basis + titel_rel)
    elif fmt == "karussell" and len(seiten_rel) > 1:
        media_id = veroeffentlichen(token, post["caption"][:2200], bild_urls=[basis + r for r in seiten_rel])
    else:
        media_id = veroeffentlichen(token, post["caption"][:2200], bild_url=basis + bild_rel)
    print("Veröffentlicht. Beitrags-ID:", media_id)
    zeile = {"datum": heute, "job_id": post.get("job_id", ""), "titel": post["titel"],
             "media_id": media_id, "quelle": quelle, "format": fmt, "story_id": alte_story}
    protokoll_schreiben(zeile)
    git_sichern(f"Top Job {heute}: veröffentlicht", "data/protokoll.csv")
    if mit_story:
        story_posten(token, basis + story_rel, heute)
    schluessel_verlaengern(token)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"::error::{e}")
        sys.exit(1)
