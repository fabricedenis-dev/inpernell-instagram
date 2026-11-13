# Inpernell – TOP Job des Tages auf Instagram

Dieses Projekt veröffentlicht montags bis freitags gegen 13 Uhr automatisch einen Beitrag
"TOP Job des Tages" auf dem Instagram-Konto der Inpernell GmbH. Es läuft kostenlos bei
GitHub (GitHub Actions) und nutzt die offizielle Instagram-Schnittstelle von Meta.

## So läuft ein Tag ab

1. **Claude bereitet vor (optional):** Die geplante Claude-Aufgabe wählt die Stelle, schreibt den
   Text und legt beides als `overrides/JJJJ-MM-TT.json` in dieses Projekt.
2. **Das Programm startet um 12:50 Uhr:** Liegt eine Vorgabe von Claude vor, nimmt es diese.
   Wenn nicht, wählt es selbst eine Stelle aus Recruitee und baut den Text aus der Anzeige.
3. **Bild:** `bild.py` erzeugt das Bild (1080 × 1350, JPEG) im Stil von www.inpernell.de und
   legt es unter `posts/` ab. Dadurch hat es die öffentliche Adresse, die Instagram verlangt.
4. **Veröffentlichen:** `agent.py` schickt Bild und Text an Instagram.
5. **Protokoll:** `data/protokoll.csv` merkt sich die Stelle; die letzten 30 werden nicht wiederholt.

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

### 3. Schlüssel bei GitHub hinterlegen
Im Projekt: **Settings > Secrets and variables > Actions > New repository secret**
- Name: `IG_ACCESS_TOKEN`
- Wert: der kopierte Schlüssel

Den Schlüssel nirgendwo sonst speichern oder verschicken, auch nicht an Claude.

### 4. Testen
Im Projekt: **Actions > Top Job des Tages > Run workflow**
- Mit Haken bei "Probelauf": Es entstehen nur Bild und Text im Ordner `posts/`. Nichts wird veröffentlicht.
- Ohne Haken: Der Beitrag wird sofort veröffentlicht.

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
  "extra": "65.000 – 80.000 € / Jahr",
  "punkte": ["Punkt 1", "Punkt 2", "Punkt 3"],
  "caption": "Fertiger Instagram-Text mit Hashtags"
}
```

Die Schriften Archivo und Lato im Ordner `fonts/` stehen unter der SIL Open Font License.
