# Regeln für Inpernell-Instagram (vom Inhaber festgelegt)

Diese Regeln gelten für alle Beiträge, Stories, Reels und die Top-Job-Seite.

## Texte
- Deutsch, Du-Form (nie Sie-Form in eigenen Texten), locker, modern, aber seriös.
- Jeder Text vollständig und grammatikalisch korrekt. **Nie abschneiden, nie „…“.** Passt etwas nicht, kürzer
  formulieren oder weglassen.
- Auf Folien kurze, sinnvolle Stichworte statt langer Sätze (nicht überladen).
- Bildtext: erste Zeile als Suchzeile, offene Frage an die Leser (kein „Kommentiere X“), höchstens 5 Hashtags,
  keine Zeichenfolge wie „#1“ im Text (stattdessen „Nr. 1“).
- Fakten und Zahlen nur aus geprüften Primärquellen (BA, Arbeitsagenturen, IHK, Statistisches Landesamt,
  gesetze-im-internet.de), Quelle mit Datum nennen. Nichts erfinden.

## Gestaltung (Reels, Stories, Folien)
- Inpernell-Stil beibehalten: Navy/Orange, Schriften Archivo und Lato.
- **Kein Logo oben links in Reels/Stories** – dort blendet Instagram Profilbild und Kontonamen ein.
  Logo nur im Abschluss bzw. in sicheren Bereichen.
- Logo in Reels (freigegeben, Variante B): klein unten links (x ≈ 74, y ≈ 1420, 260 px breit) auf jeder Folie,
  über Kontoname und Bildtext. Auf der Abschlussfolie steht es stattdessen groß mit „Direktvermittlung“.
- Sichere Zonen in 1080 × 1920: oben ca. 190 px frei (Instagram-Kopfzeile), unten ab ca. 1520 px frei
  (Kontoname, Bildtext), rechts ab x ≈ 940 zwischen y ≈ 1000–1700 frei (Knöpfe). Wichtige Inhalte für den
  Feed-Ausschnitt zwischen y ≈ 285 und 1635.
- Keine Weichzeichner (Instagram empfiehlt unscharfe Videos seltener); Reels immer mit Ton (eigene Musik).
- Vor jeder Änderung am Layout eine Vorschau als Bild zeigen; veröffentlicht wird erst nach Freigabe.
- Sketche (vom Inhaber freigegeben am 26.11.2026, „beibehalten“): Dialog-Stil wie erfolgreiche Meme-Cartoons,
  gebaut mit `werkzeuge/sketch_dialog.py` + JSON (Vorlage `reels/sketch_gleitzeit_dialog.json`). Strichmännchen
  (`werkzeuge/strichmann.py`), feste Hook-Zeile oben, schnelles Hin und Her mit sehr kurzen Sätzen, alle 5–8 s
  eine kleine Pointe, logisch und aus dem echten Arbeitsalltag, am Ende ein Nachklapp. Nahaufnahme der
  sprechenden Figur, Untertitel in Häppchen unten mittig, keine Sprechblasen. Musik Monkeys Spinning Monkeys.
- So sollen Sketche künftig aufgebaut sein (Inhaber, 27.11.2026: „so ist geil, merk dir das“). Vorbilder sind
  `reels/sketch_bewerbung_dialog.json` (ehrlich gesagt → schöngeredet, Steigerung bis zum Rauswurf),
  `reels/sketch_zeugnis_dialog.json` (wütender Chef ↔ ruhige Übersetzung ins Zeugnis-Deutsch) und
  `reels/sketch_funkloch_dialog.json` (Missverständnis-Kreisel, Funkloch verschluckt Wörter, SMS als Nachklapp).
  Muster: eine Formel, die jeder sofort versteht, Zeile für Zeile wiederholt und gesteigert; jede Antwort eine
  Pointe; am Ende ein trockener Nachklapp. Muster und Machart erfolgreicher Meme-Cartoons nachbauen ist gewollt,
  die Sätze aber immer selbst formulieren (fremde Texte/Tonspuren nicht wörtlich übernehmen). Keine Einwände
  zum Humor: Der Inhaber entscheidet, was lustig ist.

## Abläufe
- Redaktionsplan immer bildlich zeigen: `python redaktionsplan.py` erzeugt `vorschau/redaktionsplan.png`
  (ab heute 14 Tage, mit Status und Vorschaubildern). Nach jeder Planänderung neu erzeugen und mitschicken.
- Veröffentlichen nur über die Workflows; Löschen geht nicht über die Schnittstelle (Inhaber löscht in der App).
- Keine bekannten oder fremden Stimmen nachahmen/klonen.

## KI-Darstellungen der Inhaber (Freigabe des Inhabers vom 21.11.2026)
- Fabrice, Pascal und Waldemar dürfen mit KI dargestellt werden: als Comic- oder Stil-Porträt (z. B. GTA-Stil
  wie bei Finanzfluss), animiert oder mit Bibliotheksstimmen vertont. Grundlage: eigene Fotos (Website-Porträts,
  hochgeladene Vorlagen).
- Pflicht dabei: Instagram-Schalter „KI-Info“ setzen und im Bildtext kurz nennen, was KI ist (EU-KI-Verordnung
  Art. 50, Meta-Regeln). Nie als echte Aufnahme ausgeben.
- Gilt ausdrücklich auch für Memes (Wunsch des Inhabers): Meme-Formate wie „Erwartung vs. Realität“ bevorzugt mit
  KI-Darstellungen der Inhaber bauen, ergänzt durch lizenzfreie Stock-Clips; KI-Hinweis wie oben.
- Fremde Logos/Marken (z. B. GTA) nur nach Rückfrage im Einzelfall mit Hinweis auf das Markenrisiko. Fremde
  Videos/Fotos anderer Personen oder Konten nie neu veröffentlichen (Urheber- und Persönlichkeitsrecht), stattdessen
  lizenzfreie Clips oder die Remix-Funktion in der App.
