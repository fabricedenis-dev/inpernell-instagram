"""Berufsfelder für den TOP Job des Tages: Foto, Bezeichnung und Erkennung anhand der Stellenanzeige.

Jedes Berufsfeld hat ein Foto in assets/berufsfelder/<schluessel>.jpg. Eigene Fotos können die
Dateien einfach ersetzen (Querformat, mindestens 1600 px breit). "fokus" gibt an, welcher Bildteil
beim Zuschneiden in der Mitte bleiben soll (x, y jeweils 0 = links/oben bis 1 = rechts/unten).

Die mitgelieferten Fotos stammen von Unsplash (unsplash.com/license: kostenlos, auch kommerziell,
ohne Namensnennung). Die Quelle steht jeweils unter "foto".
"""
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))

# Reihenfolge = Priorität bei der Erkennung (spezifische Felder zuerst).
BERUFSFELDER = {
    "zerspanung": {
        "name": "Zerspanung & CNC",
        "fokus": (0.5, 0.45),
        "foto": "unsplash.com/photos/1581092335397-9583eb92d232",
        "titel": [r"zerspan", r"\bcnc", r"dreh(er|en|technik|maschine)", r"fräs", r"schleif", r"einricht",
                  r"werkzeugmechan", r"stanz", r"maschinenbedien"],
    },
    "konstruktion": {
        "name": "Konstruktion & Entwicklung",
        "fokus": (0.5, 0.5),
        "foto": "unsplash.com/photos/1581092580497-e0d23cbdf1dc",
        "titel": [r"konstrukt", r"entwickl", r"technische[rn]? zeichner", r"produktdesign", r"\bcad\b", r"ingenieur"],
    },
    "projektleitung": {
        "name": "Projektleitung & Management",
        "fokus": (0.55, 0.4),
        "foto": "unsplash.com/photos/1581092446327-9b52bd1570c2",
        "titel": [r"projekt", r"produktmanag", r"geschäftsf", r"werksleit", r"bereichsleit", r"\bmanager\b(?!.*arbeits)"],
    },
    "qualitaet": {
        "name": "Qualität & Arbeitssicherheit",
        "fokus": (0.6, 0.45),
        "foto": "unsplash.com/photos/1581093588401-fbb62a02f120",
        "titel": [r"qualit", r"\bqs\b", r"\bqm\b", r"messtechn", r"prüf", r"arbeitsschutz", r"arbeitssicherheit"],
    },
    "technik": {
        "name": "Technik & Instandhaltung",
        "fokus": (0.6, 0.4),
        "foto": "unsplash.com/photos/1621905251189-08b45d6a269e",
        "titel": [r"mechatron", r"instandhalt", r"elektr", r"servicetechn", r"wartung", r"industriemechan",
                  r"anlagenmechan"],
    },
    "it": {
        "name": "IT & ERP",
        "fokus": (0.5, 0.5),
        "foto": "unsplash.com/photos/1555066931-4365d14bab8c",
        "titel": [r"\bit\b", r"\bifs\b", r"\bsap\b", r"\berp\b", r"software", r"informatik", r"developer",
                  r"administrat", r"consultant", r"daten", r"digital"],
    },
    "banking": {
        "name": "Banking & Finance",
        "fokus": (0.5, 0.4),
        "foto": "unsplash.com/photos/1600880292203-757bb62b4baf",
        "titel": [r"kundenberater", r"bank", r"kredit", r"vermögen", r"wertpapier", r"finanzberat", r"private banking"],
    },
    "finanzen": {
        "name": "Finanzen & Rechnungswesen",
        "fokus": (0.5, 0.5),
        "foto": "unsplash.com/photos/1554224155-6726b3ff858f",
        "titel": [r"buchhalt", r"controll", r"finanz", r"rechnungswesen", r"steuer", r"bilanz", r"lohn"],
    },
    "personal": {
        "name": "Personal & HR",
        "fokus": (0.5, 0.4),
        "foto": "unsplash.com/photos/1581091877018-dac6a371d50f",
        "titel": [r"personal", r"\bhr\b", r"recruit", r"human resources", r"talent"],
    },
    "einkauf": {
        "name": "Einkauf",
        "fokus": (0.5, 0.5),
        "foto": "unsplash.com/photos/1450101499163-c8848c66ca85",
        "titel": [r"einkauf", r"beschaffung", r"procurement", r"purchas", r"disponent"],
    },
    "logistik": {
        "name": "Logistik & Lager",
        "fokus": (0.5, 0.55),
        "foto": "unsplash.com/photos/1553413077-190dd305871c",
        "titel": [r"logistik", r"lager", r"versand", r"supply chain", r"auftragsplan", r"fertigungsplan", r"stapler"],
    },
    "vertrieb": {
        "name": "Vertrieb",
        "fokus": (0.5, 0.5),
        "foto": "unsplash.com/photos/1521791136064-7986c2920216",
        "titel": [r"vertrieb", r"sales", r"verkauf", r"key account", r"außendienst", r"innendienst", r"account manag"],
    },
    "produktion": {
        "name": "Produktion & Fertigung",
        "fokus": (0.5, 0.5),
        "foto": "unsplash.com/photos/1567789884554-0b844b597180",
        "titel": [r"produktion", r"fertigung", r"verfahrensmechan", r"kunststoff", r"spritzguss", r"schicht",
                  r"montage", r"maschinen", r"operator", r"werker"],
    },
}

STANDARD = "produktion"
# Recruitee-Kategorie als Rückfall, wenn der Titel nichts eindeutig sagt
RECRUITEE_KATEGORIE = {
    "banking": "banking", "finance": "finanzen", "accounting": "finanzen", "it": "it",
    "information_technology": "it", "software_development": "it", "sales": "vertrieb",
    "logistics": "logistik", "purchasing": "einkauf", "human_resources": "personal", "recruitment_hr": "personal",
    "engineering": "konstruktion", "manufacturing": "produktion", "quality_assurance": "qualitaet",
    "project_management": "projektleitung",
}


def foto_pfad(schluessel):
    return os.path.join(HIER, "assets", "berufsfelder", f"{schluessel}.jpg")


def erkenne(titel, recruitee_kategorie=None):
    """Gibt den Schlüssel des passenden Berufsfelds zurück (z. B. "zerspanung")."""
    t = (titel or "").lower()
    for schluessel, feld in BERUFSFELDER.items():
        if any(re.search(muster, t) for muster in feld["titel"]):
            return schluessel
    return RECRUITEE_KATEGORIE.get((recruitee_kategorie or "").lower(), STANDARD)
