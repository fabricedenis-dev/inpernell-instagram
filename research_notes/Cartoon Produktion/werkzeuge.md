# Werkzeuge für animierte Cartoon-Memes (Reels 9:16, 10–25 s)

Stand: 24.11.2026. Alle Links an diesem Tag abgerufen. Zahlen aus Drittquellen (Blogs, Foren) sind als
**[unsicher]** markiert; Preise und Gratis-Kontingente ändern sich oft. Vor dem ersten Einsatz die
offizielle Preisseite erneut prüfen.

Ziel: Qualität wie bei deutschen Meme-Cartoon-Seiten (z. B. @cartoonslustig): ausgearbeitete 2D-Figuren mit
Schattierung, detaillierte Hintergründe, ausdrucksstarke Gesichter, einfache Arm- und Mundbewegung,
POV-Textkasten oben, Ton. Umgebung: Linux-Container, nur CPU (4 Kerne, 15 GB RAM, gemessen am 24.11.2026),
Python, ffmpeg, Pillow, Internet über Proxy, API-Schlüssel nur über das sichere Formular.

---

## 0. Kurzfazit

1. **Bilder (Figuren, Posen, Mundformen, Hintergründe): Cloudflare Workers AI mit FLUX.2 [klein] 4B.**
   Täglich 10.000 Neuronen gratis, bis zu 4 Referenzbilder pro Aufruf (Figurentreue), Modellgewichte unter
   Apache 2.0 (kommerziell erlaubt). Nach meiner Rechnung reichen die Gratis-Neuronen für etwa 80 Bilder pro Tag.
2. **Bewegung: kein KI-Video, sondern eigene Ausschnitt-Animation (Cutout/Puppet) in Python.** Die Figur wird
   in Teile zerlegt (Körper, Kopf, Augen offen/zu, 6–9 Mundformen) und mit Pillow/numpy bewegt. Den Ton legt
   ElevenLabs, die Mundformen setzt **Rhubarb Lip Sync** (MIT, Kommandozeile). Das läuft vollständig auf der CPU,
   ist kostenlos, wiederholbar und erlaubt die kommerzielle Nutzung. Genau diese Machart (Standbild-Figur,
   Kopfwackeln, Mundwechsel, Schnitte) ist bei Meme-Cartoon-Seiten üblich.
3. **KI-Videodienste (Kling, Hailuo, Luma, Veo):** In den Gratisstufen gibt es Wasserzeichen und/oder **keine
   kommerziellen Rechte**. Veo hat über die Gemini-API keine Gratisstufe. Sie eignen sich höchstens für
   einzelne bezahlte „Hero-Shots“.
4. **Gemini „Nano Banana“ über die API ist nicht kostenlos**: Laut offizieller Preisseite gibt es für alle
   Bildmodelle keine Gratisstufe. Das Modell bietet aber die beste Figurentreue, für etwa 0,04 $ pro Bild.
   Es ist die beste günstige Bezahl-Variante.

---

## 1. Bildgenerierung über APIs (Gratisstufen, Figurentreue, Rechte)

| Dienst | Gratis? | Figurentreue / Referenzbilder | Kommerziell | Bewertung |
|---|---|---|---|---|
| **Cloudflare Workers AI – FLUX.2 klein 4B** | 10.000 Neuronen/Tag gratis, Rücksetzung 00:00 UTC | bis 4 Eingabebilder (`input_image_0..3`), jedes **kleiner als 512×512** | Gewichte Apache 2.0 (BFL); Cloudflare verlinkt zusätzlich die BFL-AGB | **Erste Wahl** |
| Cloudflare – FLUX.1 schnell | im selben Kontingent | nur Text, keine Referenz (Schema: `prompt`, `steps` ≤ 8) | Apache 2.0 | gut für Hintergründe |
| Google Gemini 2.5 Flash Image / 3.1 Flash Image / 3 Pro Image | **Gratisstufe „Not available“** | sehr gut (Bearbeiten, mehrere Referenzen) | Google beansprucht kein Eigentum am Ergebnis | bezahlt 0,039 $ (2.5 Flash) bzw. 0,067 $ (3.1 Flash, 1K) pro Bild |
| Pollinations.ai | ohne Schlüssel: 1 Bild/45 s, max. 768×768 Fläche, **Logo im Bild**; mit Schlüssel ohne Logo, Guthaben aber kaum noch gratis | viele Modelle mit Referenzbildern (z. B. flux.2-klein-4b, mai-image-2.7) | keine klare Aussage, hängt am Modell | unzuverlässig, nur Notlösung |
| Together AI – FLUX.1-schnell-Free | laut Modellseite weiter gratis **[unsicher, ursprünglich als befristete Aktion 2024 angekündigt]** | nur Text | Apache 2.0 | Reserve für Hintergründe |
| Hugging Face Inference Providers | 0,10 $/Monat (Free), 2 $/Monat (PRO, 9 $/Monat) | je nach Modell | je nach Modell | zu wenig Guthaben |
| Hugging Face Spaces (ZeroGPU, über `gradio_client`) | etwa 5 GPU-Minuten/Tag für Free **[unsicher, Forenangabe]** | je nach Space (z. B. Kontext/Qwen-Edit) | je nach Modell und Space | wackelig, nicht automatisierbar |
| fal.ai | Startguthaben, Höhe nicht veröffentlicht **[unsicher]** | viele Edit-Modelle | je nach Modell | nur bezahlt sinnvoll |
| Replicate | keine dauerhafte Gratisstufe | viele | je nach Modell | bezahlt |
| Stability AI API | einmalig 25 Credits (≈ 0,25 $) **[Drittquellen]** | begrenzt | Community-Lizenz frei bis 1 Mio. $ Jahresumsatz | nicht lohnend |
| OpenAI gpt-image-1.5 | nur bezahlt: 1024×1536 low 0,013 $ / medium 0,05 $ / high 0,20 $ | gut (Bearbeiten) | erlaubt | zu teuer für die Serie; Abschaltung 1.12.2026 laut Drittquelle **[unsicher]** |

**Rechnung Cloudflare (meine Rechnung, keine Quellenangabe):** FLUX.2 klein 4B kostet 26,05 Neuronen pro
ausgegebener 512×512-Kachel und 5,37 Neuronen pro eingegebener Kachel. Ein Bild in 768×1344 (≈ 4 Kacheln)
mit 2 Referenzbildern kostet also etwa 4 × 26,05 + 2 × 5,37 ≈ 115 Neuronen. Bei 10.000 Neuronen ergibt
das etwa 85 Bilder pro Tag. Darüber hinaus kostet es 0,011 $ je 1.000 Neuronen (≈ 0,0013 $ pro Bild),
dafür braucht man aber den Workers-Paid-Plan.

**Figurentreue praktisch:** Zuerst ein „Character Sheet“ pro Figur erzeugen (neutrale Pose, Mund zu, glatter
Hintergrund). Alle weiteren Bilder (Mund offen, „O“, Lächeln, Augen zu, wütend, Arm hoch) dann als
**Bearbeitung mit diesem Sheet als `input_image_0`** erzeugen, mit gleichem Seed und gleichem Stil-Prompt.
Die 512-px-Grenze für Eingaben reicht für die Identität. Die Ausgabe wird in voller Größe erzeugt.
Dass die Treue an Gemini herankommt, ist **nicht belegt**. Vor der Serie einen Test mit 3 Figuren machen.

Quellen:
- Cloudflare-Preise und Neuronen je Modell: https://developers.cloudflare.com/workers-ai/platform/pricing/
- FLUX.2 klein 4B auf Workers AI (Changelog 15.01.2026, `input_image_0..3`, < 512×512):
  https://developers.cloudflare.com/changelog/2026-01-15-flux-2-klein-4b-workers-ai ,
  https://blog.cloudflare.com/flux-2-workers-ai
- Lizenz FLUX.2 klein 4B (Apache 2.0; 9B nur nicht-kommerziell): https://huggingface.co/black-forest-labs/FLUX.2-klein-4B ,
  https://bfl.ai/blog/flux2-klein-towards-interactive-visual-intelligence
- FLUX.1 schnell Eingabeschema: https://developers.cloudflare.com/workers-ai/models/flux-1-schnell/schema-input.json
- Gemini-Preise („Not available“ im Free Tier für alle Bildmodelle): https://aistudio.google.com/docs/pricing
  (früher ai.google.dev/gemini-api/docs/pricing)
- Gemini-API-Bedingungen (kein Eigentumsanspruch, Unpaid-Daten können geprüft werden, EWR-Regeln):
  https://ai.google.dev/gemini-api/terms_preview
- Pollinations Classic-API (ohne Schlüssel, 45 s Abstand, Logo): https://github.com/pollinations/pollinations/blob/master/APIDOCS.md ;
  Modellliste live: https://gen.pollinations.ai/image/models (24.11.2026 abgerufen) ; Wegfall des stündlichen
  Gratis-Guthabens Juli 2026 **[Drittquelle]**: https://agentdeals.dev/this-week?week=15
- Together FLUX.1-schnell-Free: https://together.ai/models/flux-1-schnell
- Hugging Face Guthaben: https://huggingface.co/docs/inference-providers/pricing ; ZeroGPU:
  https://huggingface.co/docs/hub/spaces-zerogpu , https://discuss.huggingface.co/t/what-is-the-free-zerogpu-quota-for-1-space/178610
- Stability: https://stability.ai/license
- OpenAI gpt-image-1.5: https://developers.openai.com/api/docs/models/gpt-image-1.5

---

## 2. Offene Modelle auf der CPU (ohne GPU)

Messwerte von FastSD CPU (MIT-Lizenz), Intel Core i7-12700, 512×512:

| Modell | Schritte | Zeit pro Bild | Hinweis |
|---|---|---|---|
| SDXS-512 | 1 | 0,82 s (OpenVINO + TAESD) | geringe Qualität |
| SD Turbo | 1 | 1,7 s (OpenVINO + TAESD) | laut FastSD „research purposes only“ |
| SDXL Turbo | 1 | 2,5 s (OpenVINO + TAESD), 10 s (PyTorch) | Lizenz nicht kommerziell **[prüfen]** |
| SDXL-Lightning | 2 | 10–18 s (768×768) | – |
| FLUX.1 schnell | 3 | **270 s**, **≈ 30 GB RAM** | in unserem Container (15 GB) nicht machbar |
| LCM-LoRA (Dreamshaper v8) | 3 | ab 4 GB RAM | LoRA-Unterstützung vorhanden (nicht für OpenVINO-LCM-LoRA) |

Einschätzung: Unser Container hat 4 Kerne (weniger als der i7-12700). Realistisch sind **5–30 s pro 512er-Bild**
mit SD 1.5 + LCM-LoRA + Cartoon-LoRA **[Schätzung]**. Die Qualität bleibt deutlich unter FLUX.2 und Gemini,
und Figurentreue gibt es nur über LoRA-Training (auf der CPU nicht praktikabel). Deshalb nur als Notlösung
ohne Internet. FLUX.2 klein 4B lokal braucht laut Modellkarte etwa 13 GB VRAM (GPU) und ist auf der CPU
nicht sinnvoll.

Quellen: https://github.com/rupeshs/fastsdcpu (Benchmark-Tabelle und RAM-Angaben),
https://huggingface.co/black-forest-labs/FLUX.2-klein-4B

---

## 3. Bild-zu-Video-Dienste (Gratisstufen, Wasserzeichen, Rechte)

| Dienst | Gratis | Wasserzeichen | Kommerziell im Gratis-Plan | API |
|---|---|---|---|---|
| Kling | ca. 66 Credits (täglich oder monatlich, Angaben widersprüchlich) **[Drittquellen]** | ja | **nein** (Basic: „not for commercial use“, laut Drittquelle aus Klings Credit-Leitfaden vom 28.07.2026) | eigene, bezahlte API **[unsicher]** |
| Hailuo / MiniMax | Willkommens-Credits, verfallen nach 3 Tagen **[Drittquelle]** | meist ja, widersprüchlich | **nein**, nur bezahlte Pläne | bezahlt |
| Luma Dream Machine | Free/Lite laut Luma-Lizenzseite | ja | **nein** (nur privat, nicht kommerziell) | bezahlt |
| Runway, Pika | einmalige Test-Credits **[nicht im Detail geprüft]** | ja | in der Regel nein | Runway-API bezahlt |
| Google Veo 3.1 (Gemini-API) | **keine Gratisstufe** | SynthID (unsichtbar) | ja (bezahlt) | 3.1 Lite 0,05 $/s (720p), Fast 0,10 $/s, Standard 0,40 $/s **[Drittquellen, laut Google-Blog „Veo 3.1 Lite“]** |
| Wan 2.2 (offen, Apache 2.0) über fal.ai | nur Startguthaben | nein | Modell ja; fal-AGB **[nicht geprüft]** | A14B turbo: 0,05 $ (480p) bis 0,10 $ (720p) pro Clip; 5B: 0,15 $ pro Clip; A14B-Endpunkt wird am 04.01.2027 abgeschaltet |
| Wan 2.2 lokal auf CPU | – | – | – | **nicht machbar** (Videodiffusion braucht GPU) |

Fazit: Mit kostenlosen Mitteln gibt es kein Bild-zu-Video, das für das Firmenkonto erlaubt ist. Für einzelne
Effekt-Szenen (z. B. 3 s „Figur dreht sich um“) ist Wan 2.2 turbo über fal.ai für 0,05–0,10 $ die günstigste
saubere Lösung. Allerdings bewegen KI-Videos Figuren oft uneinheitlich, und der Mund ist nicht mit dem Ton
synchron.

Quellen:
- Kling: https://eesel.ai/blog/kling-ai-pricing , https://marcandrews.com/kling-ai-free-plan-2026-what-66-credits-buys/
- Luma-Lizenz: https://lumalabs.ai/learning-hub/licensing
- Hailuo/MiniMax: https://wavespeed.ai/blog/posts/free-ai-video-generator-no-watermark/
- Veo-Preise: https://blog.google/innovation-and-ai/technology/ai/veo-3-1-lite/ , https://benchlm.ai/media-pricing/veo
- fal Wan 2.2: https://fal.ai/models/fal-ai/wan/v2.2-a14b/image-to-video/turbo , https://fal.ai/models/fal-ai/wan/v2.2-5b/image-to-video

---

## 4. Code-basierte 2D-Ausschnitt-Animation (CPU, automatisierbar)

| Werkzeug | Headless/CLI | Eignung | Lizenz |
|---|---|---|---|
| **Eigene Python-Pipeline (Pillow + numpy → ffmpeg-Pipe)** | ja | **beste Wahl**: Ebenen (Hintergrund, Körper, Arm, Kopf, Augen, Mund) mit Drehung um Gelenkpunkt, Sinus-Wackeln, Atmen (Skalierung 1–2 %), Blinzeln, Kamera-Zoom, harte Schnitte. Liegt mit `zeichentrick*.py` im Repo schon in Ansätzen vor. | eigen |
| **Rhubarb Lip Sync** | ja (`rhubarb -o out.json -f json stimme.wav`) | Mundformen A–F plus G, H, X aus WAV/OGG als Zeitstempel. Für nicht-englischen Ton den phonetischen Erkenner (`-r phonetic`) nutzen **[Option laut Doku; Qualität auf Deutsch ungeprüft]**. Aktuell v1.14.0 | MIT **[laut Spiegeln/Drittquellen; LICENSE-Datei vor Einsatz prüfen]** |
| faster-whisper (schon im Repo) | ja | Wortzeiten für Untertitel; alternativ Mund nach Lautstärke | MIT |
| rembg (U²-Net/BiRefNet, CPU) | ja | Figur freistellen (Hintergrund entfernen) | MIT **[nicht neu geprüft]** |
| rlottie-python / python-lottie | ja (`save_frame`, `render_pillow_frame`) | gut für Vektor-Effekte (Sterne, Schweißtropfen, Pfeile) als Lottie; für KI-Rasterfiguren unnötig | rlottie: MIT; python-lottie: AGPL **[prüfen]** |
| Synfig CLI | ja (`synfig -t png -o … datei.sifz`) | Knochen-Rigs möglich, aber Rig-Aufbau braucht die GUI | GPL |
| Blender (Grease Pencil) headless | **problematisch**: Grease Pencil und EEVEE brauchen OpenGL, ohne Display Absturzberichte; nur über Xvfb/Software-GL **[ungeprüft]** | übertrieben für Cutout | GPL |
| OpenToonz | Rendern per Kommandozeile möglich **[nicht geprüft]**, Rig-Aufbau in der GUI | – | BSD |
| Rive | CLI nur zum Bauen, Vorschau und Testen; kein Export von Frames belegt | nein | Laufzeit MIT, Editor proprietär |
| Inochi2D (Live2D-Alternative) | Inochi Session ist eine GUI-VTuber-App, kein Offline-Render belegt; „not yet production-ready“ | nein | BSD-2 |

**Warum Cutout statt KI-Video:** Mund und Ton sind exakt synchron. Die Figur bleibt zu 100 % gleich, weil
dasselbe Bild immer wieder verwendet wird. Es gibt keine Wasserzeichen und keine Kosten pro Sekunde, das
Ergebnis ist reproduzierbar, und jede Folie lässt sich vorab als Standbild freigeben (Regel in CLAUDE.md).

Quellen:
- Rhubarb Releases: https://github.com/DanielSWolf/rhubarb-lip-sync/releases (v1.14.0, 03. April; Jahr auf der
  Seite nicht angezeigt) ; Mundformen und CLI: README im selben Repository ; Lizenz-Spiegel: https://gitee.com/imjesson/rhubarb-lip-sync
- rlottie-python: https://pypi.org/project/rlottie-python/1.3.4 ; python-lottie: https://pypi.org/project/lottie/0.6.6
- Synfig CLI: https://wiki.synfig.org/Synfig_CLI_syntax , https://forums.synfig.org/t/script-for-multicore-cli-render/453
- Blender headless/Grease Pencil: https://devtalk.blender.org/t/rendering-grease-pencil-objects-on-headless-no-gpu-render-farm-machines-in-blender-2-8/10194 ,
  https://developer.blender.org/T85546
- Rive CLI: https://rive.app/docs/cli/overview
- Inochi Session: https://flathub.org/apps/com.inochi2d.inochi-session , https://github.com/Inochi2D/inochi2d

---

## 5. Was Meme-Cartoon-Seiten tatsächlich nutzen

- **@cartoonslustig:** Welches Werkzeug die Seite nutzt, ist **öffentlich nicht belegt** (Suche am 24.11.2026
  ohne Treffer). Aus der Machart (Standbild-Figuren mit Schattierung, wenig Bewegung, Mundwechsel, Schnitte)
  lässt sich nur vermuten, dass es KI-Bilder oder gezeichnete Bilder mit Cutout-Animation in einem
  Schnittprogramm sind **[Vermutung]**.
- **Belegte KI-Abläufe von Creatorn 2026:** Figur-Standbild mit Nano Banana Pro, dann Bewegung über Kling (Motion
  Control, mit Ton und Lippensynchronität) oder Veo 3/Sora 2. Das ist alles bezahlt, und die Treue der Figuren
  ist laut den Anleitungen eine häufige Fehlerquelle.
  Quellen: https://www.opus.pro/blog/viral-ai-video-styles-2026 , https://www.opus.pro/blog/ai-talking-object-videos ,
  https://www.sostav.ru/blogs/288343/85953
- **Klassische Programme:**
  - Cartoon Animator 5 (Reallusion): Desktop (Windows/macOS), Ausgabe laut Reallusion-Forum lizenzfrei
    kommerziell nutzbar, Preise in Quellen widersprüchlich, **keine API**. 30 Tage Testversion.
    https://discussions.reallusion.com/t/commercial-rights/14208 , https://www.reallusion.com/crazytalk7/trial.aspx
  - Vyond: Die API existiert (nur Vyond Go/Avatar-Videos, Freischaltung über den Support), Testversion ohne
    kommerzielle Rechte. https://help.vyond.com/hc/en-us/articles/51873650828052-How-do-I-use-the-Vyond-API ,
    https://vyond.com/terms
  - Animaker: ab etwa 19 $/Monat, API nicht belegt **[unsicher]**.
  - Toonly, Plotagon: keine API gefunden; Status von Plotagon nicht geprüft.
  - CapCut-Cartoon-Vorlagen: nur in der App/GUI, keine API.
- **Trending Sound:** Musik aus der Instagram-Bibliothek lässt sich nach meinem Kenntnisstand nicht über die
  Content-Publishing-API hinzufügen **[nicht neu geprüft]**. Für Firmenkonten gibt es zudem nur die
  kommerzielle Audiobibliothek. Deshalb mit eigener Musik veröffentlichen (Regel in CLAUDE.md). Wer einen
  Trend-Sound will, muss ihn in der App hinzufügen.

---

## 6. Empfohlene Pipeline (weitgehend automatisch, kostenlos)

**Einmalig durch den Inhaber (etwa 10 Minuten):**
1. Ein kostenloses Cloudflare-Konto anlegen, die **Account-ID** notieren und unter „My Profile → API Tokens“ ein
   Token mit der Berechtigung **„Workers AI: Read/Edit“** erstellen. Den Schlüssel trägt er über das sichere
   Formular ein (Host `api.cloudflare.com`, Bearer). Die Account-ID ist kein Geheimnis und kann in die
   Konfiguration.
2. Die Figuren freigeben: pro Figur ein Character Sheet ansehen und freigeben (Inhaber-Figuren nur als
   KI-Stil-Porträt nach den Regeln in CLAUDE.md, KI-Hinweis Pflicht).
3. Optional (für bessere Treue): ein Gemini-API-Projekt mit Abrechnung anlegen (≈ 0,04 $ pro Bild).

**Pro Video (Agent, automatisch):**
1. **Drehbuch** (Deutsch, Du-Form): POV-Zeile, 3–5 Einstellungen, Dialog von 10–25 s.
2. **Stimme**: ElevenLabs (Starter vorhanden, Bibliotheksstimmen) → WAV. Rhubarb erzeugt daraus
   Mundformen-Zeiten (JSON), faster-whisper die Wortzeiten für Untertitel.
3. **Bilder** über Cloudflare FLUX.2 klein 4B, 768×1344 bzw. 1080×1920 hochskaliert:
   - 1–2 Hintergründe (Büro, Bewerbungsgespräch) ohne Figuren, detailreich.
   - pro Figur: Grundpose plus Varianten über Referenz-Bearbeitung (Augen zu, 4–6 Mundformen, 1–2 Emotionen,
     ggf. Arm-Pose). Insgesamt etwa 15–25 Bilder pro Video, also 20–30 % des Tageskontingents.
4. **Zerlegen**: Figur mit rembg freistellen. Mundformen und Augen als kleine Ausschnitte an festen Koordinaten
   aus den Varianten schneiden (Differenzbild zur Grundpose). Den Kopf als eigene Ebene mit Drehpunkt am Hals
   anlegen. Koordinaten pro Figur einmal in einer `rig.json` speichern.
5. **Animation** (Python, 30 fps): Kopf ±3° Wackeln beim Sprechen, Atmen, Blinzeln alle 2–4 s, Mund nach
   Rhubarb, langsamer Kamera-Zoom von 2–5 % je Einstellung, Schnitte auf Pointen, kleine Effekte
   (Schweißtropfen, „!“, Zoom-Ruck). **Kein Weichzeichner.**
6. **Layout nach CLAUDE.md**: POV-Kasten oben, aber **unterhalb von y ≈ 190** (weißer Kasten, Archivo, schwarze
   Schrift; wichtige Inhalte zwischen y 285 und 1635). Kein Logo oben links, kleines Logo unten links
   (x ≈ 74, y ≈ 1420, 260 px), Abschlussfolie mit großem Logo und „Direktvermittlung“. Untertitel nicht im
   Bereich ab y 1520 und nicht rechts ab x 940.
7. **Ton**: Stimme, eigene Musik (`musik.py`) und Effektgeräusche (selbst erzeugt oder lizenzfrei) mischen.
8. **Vorschau**: 3–4 Standbilder plus MP4 zur Freigabe, dann über die Workflows veröffentlichen. KI-Info-Schalter
   setzen und KI-Hinweis in den Bildtext.

**Erwartung:**
- Qualität: Die Bilder liegen nahe an der Optik von Meme-Seiten (FLUX.2 kann schattierte 2D-Cartoons). Die
  Bewegung ist „Motion-Comic“/Cutout, also weniger flüssig als echte Animation, aber genau die übliche
  Meme-Machart. Die Figurentreue zwischen Varianten ist bei klein 4B **ungeprüft**: Test nötig.
- Zeit pro Video: Bilder etwa 15–25 Aufrufe à wenige Sekunden **[Schätzung]**, also 2–5 min. Rhubarb unter 1 min.
  Das Rendern von 600–750 Frames mit Pillow auf 4 Kernen dauert etwa 1–3 min **[Schätzung, abgeleitet aus den
  bestehenden Skripten]**. Insgesamt etwa 10–15 min Rechenzeit plus Prüfung. Die erste Figur einzurichten
  (Rig) kostet einmalig etwa 30–60 min.
- Kosten: 0 € (innerhalb von 10.000 Neuronen/Tag), plus das vorhandene ElevenLabs-Abo.

## 7. Ausweichlösungen

1. **Bessere Figurentreue für wenige Cent:** Bildschritt mit Gemini 2.5 Flash Image (0,039 $/Bild) oder
   3.1 Flash Image (0,067 $/Bild bei 1K). Bei 20 Bildern sind das etwa 0,80–1,35 $ pro Video. Der Rest der
   Pipeline bleibt gleich.
2. **Einzelne echte Bewegungsszenen:** 1–2 Clips mit Wan 2.2 A14B turbo über fal.ai (0,05–0,10 $ pro Clip,
   480p/720p, ohne Wasserzeichen) zwischen die Cutout-Szenen schneiden. Den Endpunkt-Wechsel am 04.01.2027
   beachten.
3. **Ganz ohne API-Schlüssel:** Pollinations Classic (1 Bild/45 s, Logo in der Ecke). Das Logo muss weggeschnitten
   werden und die Rechte sind unklar, daher **nur für das private Konto**. Oder die bestehenden, selbst
   gezeichneten Pillow-Figuren (`zeichentrick.py`) mit Schattierung (Verlaufsschatten, Lichtkante) und
   detaillierteren Hintergründen aufwerten. Das ist rechtlich am saubersten, optisch aber einfacher.
4. **Ohne Internet:** SD 1.5 + LCM-LoRA + Cartoon-LoRA über FastSD CPU (etwa 5–30 s pro 512er-Bild
   **[Schätzung]**). Die Qualität ist deutlich geringer, und die Lizenz der LoRAs muss einzeln geprüft werden.
5. **Desktop-Programm (nur wenn wirklich nötig):** Cartoon Animator 5 (Testversion 30 Tage, Ausgabe kommerziell
   nutzbar). Das bedeutet Handarbeit des Inhabers und ist deshalb nicht empfohlen.

## Offene Punkte / vor Einsatz prüfen
- Figurentreue von FLUX.2 klein 4B mit Referenzbildern im Test (3 Figuren × 6 Varianten).
- Rhubarb mit deutscher Stimme (`-r phonetic`) gegen eine einfache Lautstärke-Mundsteuerung vergleichen.
- Die LICENSE-Dateien von Rhubarb und rembg direkt lesen; die BFL-AGB für die Nutzung über Cloudflare lesen.
- Den aktuellen Gratisumfang von Together FLUX.1-schnell-Free prüfen.
