# Inpernell – TOP Job des Tages auf Instagram

Dieses Projekt veröffentlicht automatisch einen Beitrag "TOP Job des Tages" (Zeitplan siehe unten) auf dem Instagram-Konto der Inpernell GmbH. Es läuft kostenlos bei
GitHub (GitHub Actions) und nutzt die offizielle Instagram-Schnittstelle von Meta.

## So läuft ein Tag ab

1. **Claude bereitet vor (optional):** Die geplante Claude-Aufgabe wählt die Stelle, schreibt den
   Text und legt beides als `overrides/JJJJ-MM-TT.json` in dieses Projekt.
2. **Das Programm startet um 12:50 Uhr:** Liegt eine Vorgabe von Claude vor, nimmt es diese.
   Wenn nicht, wählt es selbst eine Stelle aus Recruitee und baut den Text aus der Anzeige.
3. **Berufsfeld:** `kategorien.py` erkennt am Stellentitel das Berufsfeld (z. B. Zerspanung & CNC,
   Konstruktion, IT & ERP, Banking & Finance …) und nimmt das passende Foto aus `assets/berufsfelder/`.
4. **Bild oder Reel:** `bild.py` erzeugt im Stil von www.inpernell.de
   - das **Bild** (1080 × 1350, JPEG): Foto, Titel, Ort, drei Eckdaten-Kacheln
     (Gehalt, Arbeitszeit, Arbeitsmodell), drei Highlights, Bewerben-Knopf;
   - an Reel-Tagen (derzeit keine, siehe unten) zusätzlich ein **Reel** (1080 × 1920, 10 Sekunden, MP4): dieselben Inhalte
     erscheinen nacheinander, das Foto zoomt langsam heran.
   Alles landet unter `posts/` und hat so die öffentliche Adresse, die Instagram verlangt.
5. **Veröffentlichen:** `agent.py` schickt Bild bzw. Reel und Text an Instagram.
6. **Protokoll:** `data/protokoll.csv` merkt sich die Stelle; die letzten 30 werden nicht wiederholt.

## Einmalige Einrichtung

### 1. Projekt bei GitHub
- Kostenloses GitHub-Konto anlegen und ein **öffentliches** Projekt (Repository) erstellen,
  z. B. `inpernell-instagram`. Öffentlich ist nötig, damit Instagram das Bild abrufen kann.
- Alle Dateien dieses Ordners hochladen (inklusive des Ordners `.github`).

### 2. Zugang zu Instagram (Meta)
Voraussetzung: Das Instagram-Konto ist ein Business- oder Creator-Konto.
1. Auf developers.facebook.com als Entwickler registrieren und eine App erstellen.
2. In der App das Produkt **Instagram** hinzufügen und **"API setup with Instagram login"** öffnen.
3. Unter **App roles > Roles** das Instagram-Konto als **Instagram Tester** eintragen.
   Die Einladung in Instagram annehmen: Einstellungen > Apps und Websites > Tester-Einladungen.
4. Zurück bei "API setup with Instagram login" unter **"Generate access tokens"** das Konto
   hinzufügen, die Berechtigung zum Veröffentlichen erlauben und **Generate token** klicken.
   Den Schlüssel sofort kopieren – er wird nur einmal angezeigt.

Eine Facebook-Seite und eine App-Prüfung durch Meta sind für das eigene Konto nicht nötig.

**Schlüssel beginnt mit `EAA`?** Dann stammt er aus dem Facebook- bzw. "Unified Login". Das Programm
erkennt das und veröffentlicht dann über graph.facebook.com. Voraussetzungen: Das Instagram-Konto ist mit
einer Facebook-Seite verknüpft, und der Schlüssel hat die Rechte `instagram_basic`,
`instagram_content_publish`, `pages_show_list` und `pages_read_engagement`. Ein solcher Schlüssel wird
nicht automatisch verlängert; das Programm zeigt im Lauf an, bis wann er gilt, und warnt 10 Tage vorher.
Ein Probelauf prüft den Schlüssel, ohne etwas zu veröffentlichen.

**Schlüssel eines Systembenutzers** (Meta Business Suite): Zusätzlich das Secret `IG_USER_ID` mit der
ID des Instagram-Kontos anlegen. Die ID steht unter business.facebook.com > Einstellungen > Konten >
Instagram-Konten (beim Konto angezeigt). Dem Systembenutzer muss das Instagram-Konto als Asset
zugewiesen sein.

### 3. Schlüssel bei GitHub hinterlegen
Im Projekt: **Settings > Secrets and variables > Actions > New repository secret**
- Name: `IG_ACCESS_TOKEN`
- Wert: der kopierte Schlüssel

Den Schlüssel nirgendwo sonst speichern oder verschicken, auch nicht an Claude.

### 4. Testen
Im Projekt: **Actions > Top Job des Tages > Run workflow**
- Mit Haken bei "Probelauf": Es entstehen nur Bild und Text im Ordner `posts/`. Nichts wird veröffentlicht.
- Ohne Haken: Der Beitrag wird sofort veröffentlicht.

## Berufsfelder und Fotos

| Schlüssel | Berufsfeld | erkannt z. B. an |
|---|---|---|
| zerspanung | Zerspanung & CNC | Zerspanung, CNC, Dreher, Fräser, Einrichter, Werkzeugmechaniker |
| konstruktion | Konstruktion & Entwicklung | Konstrukteur, Entwickler, Technischer Zeichner |
| projektleitung | Projektleitung & Management | Projektleiter, Produktmanager, Werksleiter |
| qualitaet | Qualität & Arbeitssicherheit | Qualität, QS/QM, Messtechniker, Arbeitsschutz |
| technik | Technik & Instandhaltung | Mechatroniker, Instandhaltung, Elektriker |
| it | IT & ERP | IT, IFS, SAP, ERP, Software, Consultant |
| banking | Banking & Finance | Kundenberater, Bank, Kredit, Wertpapier |
| finanzen | Finanzen & Rechnungswesen | Buchhaltung, Controlling, Steuern, Lohn |
| personal | Personal & HR | Personalreferent, HR, Recruiting |
| einkauf | Einkauf | Einkauf, Beschaffung, Disponent |
| logistik | Logistik & Lager | Logistik, Lager, Versand, Supply Chain |
| vertrieb | Vertrieb | Vertrieb, Sales, Key Account, Außen-/Innendienst |
| produktion | Produktion & Fertigung | Produktion, Fertigung, Kunststoff, Schichtleiter (auch Standard) |

- **Eigene Fotos:** Einfach `assets/berufsfelder/<schlüssel>.jpg` ersetzen (Querformat, mind. 1600 px breit).
  Die mitgelieferten Fotos sind von Unsplash (kostenlos, auch kommerziell, ohne Namensnennung).
- **Neues Berufsfeld:** In `kategorien.py` einen Eintrag ergänzen und ein Foto mit dem Schlüssel ablegen.

## Umgesetzte Empfehlungen aus dem Reichweiten-Bericht (`reports/`)

- **Karussell statt Einzelbild:** Seite 1 = Top-Job-Design, Seite 2 = Aufgaben, Seite 3 = Anforderungen,
  Seite 4 = „So bewirbst du dich“ (Link in der Bio, Lebenslauf genügt, DM „Interesse“, Weiterleiten-Bitte).
- **Bildtext:** erste Zeile als Suchzeile „Beruf (m/w/d) in Ort – Gehalt – Arbeitsmodell“, danach Eckdaten,
  Bewerbungsweg, DM-Option und die Bitte, den Beitrag an passende Bekannte weiterzuschicken.
- **Genau 5 Hashtags:** Beruf, #Jobs<Ort>, Region (z. B. #SchwarzwaldBaar), #Stellenangebot, #TopJobDesTages.
- **Gehalt zuerst:** Stellen mit Gehaltsangabe kommen bevorzugt (schon nach 10 anderen Posts wieder).
- **Zeitplan:** jeden Tag um 18:50 Uhr (änderbar in `poststunde()` in agent.py und in den `cron`-Zeilen
  des Workflows).
- **Link-Seite:** mit Impressum/Datenschutz und Hinweis „kein Anschreiben nötig“.

Von Hand (nicht automatisierbar): Profilname/Bio mit Region und Berufsfeldern, Standort-Markierung,
Link-Sticker in der Story, Direktnachrichten zügig beantworten, gelegentlich ein Berater-Reel mit Gesicht.

## Story

Nach jedem Beitrag wird zusätzlich eine **Story** (1080 × 1920) gepostet: gleiches Design wie der Beitrag,
mit „Jetzt bewerben – Link in der Bio“. Der Bio-Link führt auf die Top-Job-Seite
https://fabricedenis-dev.github.io/inpernell-instagram/ (GitHub Pages, Ordner `docs/`, täglich aktualisiert).

**Wichtig:** Einen anklickbaren Link-Sticker kann die Instagram-Schnittstelle nicht setzen. Wer den Link
anklickbar haben möchte, öffnet die Story in der Instagram-App und fügt über „Sticker > Link“ den Link
hinzu – den Link findet man im Beitragstext bzw. in `posts/JJJJ-MM-TT-story.jpg`.

Story abschalten: im Workflow die Variable `STORY: "false"` setzen. Ist der Beitrag eines Tages schon
online, aber die Story fehlt, holt ein erneuter Lauf nur die Story nach.

## Bild oder Reel

In `agent.py` legt `WOCHENPLAN` fest, an welchem Tag was kommt. Derzeit (Schritt 1) jeden Tag ein Bild;
sobald die Veröffentlichung zuverlässig läuft, können z. B. Di und Do auf Reel gestellt werden.
Beim Handstart kann man das Format im Feld "Format" wählen; in einer Vorgabe von Claude geht es mit
`"format": "reel"`. Das Reel hat eine stille Tonspur – Musik lässt sich über die Schnittstelle nicht
hinzufügen, auf Wunsch nachträglich in der Instagram-App.

## Gut zu wissen

- **Schlüssel läuft ab:** Er gilt 60 Tage. Das Programm verlängert ihn bei jedem Post selbst.
  Erscheint in einem Lauf eine Warnung dazu, im Meta-Dashboard einen neuen Schlüssel erzeugen
  und das Secret ersetzen.
- **Uhrzeit ändern:** In `agent.py` die Zeile `POSTSTUNDE = 12` und in
  `.github/workflows/top-job.yml` die beiden `cron`-Zeilen anpassen (GitHub rechnet in Weltzeit).
- **Pausieren:** Actions > Top Job des Tages > "…" > Disable workflow.
- **Verspätung:** GitHub startet geplante Läufe manchmal einige Minuten später.

## Format der Vorgabe von Claude (`overrides/JJJJ-MM-TT.json`)

```json
{
  "job_id": "2775026",
  "titel": "Teamleitung Buchhaltung (m/w/d)",
  "ort": "Titisee-Neustadt",
  "kategorie": "finanzen",
  "format": "bild",
  "fakten": [["Jahresgehalt", "65.000 – 80.000 €"], ["Arbeitszeit", "Vollzeit · 40 h"], ["Arbeitsmodell", "Hybrid"]],
  "punkte_titel": "Das erwartet dich",
  "punkte": ["Punkt 1 (max. ca. 60 Zeichen)", "Punkt 2", "Punkt 3"],
  "caption": "Fertiger Instagram-Text mit Hashtags"
}
```

`kategorie`, `format`, `fakten` und `punkte` sind freiwillig; fehlen sie, gelten Erkennung bzw. Wochenplan.

Die Schriften Archivo und Lato im Ordner `fonts/` stehen unter der SIL Open Font License.
