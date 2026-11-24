# Kostenlose Werkzeuge für realistische Reels mit den drei Inhabern

Stand der Recherche: 21.11.2026. Alle Angaben mit Quelle und Abrufdatum (21.11.2026), sofern nicht anders vermerkt.
**[unsicher]** = nur aus Drittquellen, widersprüchlich oder nicht auf einer offiziellen Seite bestätigt.
Keine Rechtsberatung; Lizenztexte vor dem Einsatz selbst prüfen.

Anwendungsfall: „Do's and Don'ts im Vorstellungsgespräch“. Zwei Inhaber spielen die Szene, das Bild friert ein und
wird durchgestrichen, der dritte Inhaber erscheint und gibt die bessere Antwort.

---

## 0. Wichtigste Erkenntnis vorweg: Rechtliches und „soll nicht nach KI aussehen“

1. **EU-KI-Verordnung Art. 50 Abs. 4 (Deepfake-Kennzeichnung) gilt seit 02.08.2026.** Wer KI-erzeugte oder
   -veränderte Videos/Audios zeigt, die echten Personen ähneln und fälschlich echt wirken, muss das offenlegen.
   Bei erkennbar künstlerischen/fiktionalen Werken reicht ein Hinweis, der die Darstellung nicht stört.
   Der „Digital Omnibus“ hat diese Pflicht nach Kanzlei-Analysen **nicht** verschoben (nur die maschinenlesbare
   Markierung für Anbieter nach Abs. 2 auf 02.12.2026). [Omnibus-Inkrafttreten im Amtsblatt: unsicher]
   - Art. 50: https://artificialintelligenceact.eu/article/50/
   - Gibson Dunn (05/2026): https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/
   - Jones Walker: https://www.joneswalker.com/en/insights/blogs/ai-law-blog/yes-august-2-still-matters-the-eu-approved-a-high-risk-ai-delay-but-most-trans.html
2. **Meta verlangt das Label „AI info“** für fotorealistische Videos oder realistisch klingende Audios, die digital
   erzeugt oder verändert wurden (auch eine realistische KI-Stimme im Reel). Ohne Label drohen Sanktionen.
   - https://www.meta.com/help/artificial-intelligence/1783222608822690/
3. **Folge für Inpernell:** Ein KI-Video der Inhaber, das „nicht nach KI aussehen soll“, muss trotzdem gekennzeichnet
   werden. Für Glaubwürdigkeit und Rechtssicherheit ist es klar besser, **echt zu filmen** und nur klassisch zu
   schneiden (Freeze-Frame, Durchstreichen, Untertitel). Das ist keine KI-Veränderung und braucht kein Label.
4. CLAUDE.md-Regel: „Keine bekannten oder fremden Stimmen nachahmen/klonen.“ Das Klonen der **eigenen** Stimmen der
   Inhaber mit Einwilligung ist davon nicht erfasst, sollte aber schriftlich vom Inhaber freigegeben werden und löst
   ebenfalls die Kennzeichnung aus (KI-Audio).

---

## 1. Foto zu sprechendem Video / Lippensynchron / Avatar

### Open Source

| Werkzeug | Was es macht | Lizenz für kommerzielle Nutzung | CPU? | Deutsch |
|---|---|---|---|---|
| **LivePortrait** (Kuaishou/Kling-Team) | Überträgt Mimik/Kopfbewegung eines Fahrvideos auf ein Foto (kein Ton-zu-Lippe) | Code MIT; **InsightFace-Modelle nur nicht-kommerziell**, laut LICENSE für kommerzielle Nutzung ersetzen | Nur GPU offiziell; Apple-MPS ca. 20× langsamer als RTX 4090; ONNX-CPU laut FasterLivePortrait „extremely slow, not recommended“ | entfällt (mimikbasiert) |
| **SadTalker** | Foto + Audio zu sprechendem Kopf | Apache 2.0 (Nicht-kommerziell-Klausel entfernt); Drittkomponenten (GFPGAN, facexlib u. a.) eigene Lizenzen | GPU empfohlen; seit 06/2023 kein Update | sprachunabhängig, Qualität sichtbar veraltet |
| **Wav2Lip** | Lippen eines Videos an Audio anpassen | **Nur nicht-kommerziell** (LRS2-Datensatz); kommerziell nur über sync.so (kostenpflichtig) | GPU | sprachunabhängig, 96-px-Mund, unscharf |
| **LatentSync 1.6** (ByteDance, 06/2025) | Lippensynchronisierung eines echten Videos an neues Audio (Diffusion) | **Apache 2.0** | Nein, mind. 18 GB VRAM (v1.6), 8 GB (v1.5) | keine Sprachliste; v1.5 verbessert Chinesisch [Deutsch ungetestet] |
| **MuseTalk 1.5** (Tencent, 03/2025) | Echtzeit-Lippensynchron eines Videos | Code MIT, Modelle „any purpose, even commercially“; Whisper/VAE/DWPose eigene Lizenzen | Nein; Minimum RTX 3050 Ti 4 GB (8 s Video ≈ 5 min) | Chinesisch, Englisch, Japanisch genannt; Deutsch nicht erwähnt |
| **Hallo3** (Fudan) | Foto + Audio zu Video, Basis CogVideoX-5B | Code MIT, Gewichte an CogVideoX-Lizenz gebunden [kommerziell unsicher] | Nein, getestet nur auf H100 | **nur Englisch** („Audio must be in English“) |
| **EchoMimic V2/V3** (Ant Group) | Halbkörper-Animation aus Foto + Audio | Apache 2.0, aber Hinweis „for academic research“ [kommerziell unsicher] | Nein (getestet V100 16 GB bis A100) | trainiert auf Englisch und Mandarin |
| **Wan 2.2 S2V-14B / Animate-14B** (Alibaba, 08–09/2025) | Sprache zu Video bzw. Figur animieren/ersetzen | **Apache 2.0**, keine Rechte am Output beansprucht | Nein, 80 GB VRAM für 14B (TI2V-5B: 24 GB) | nicht angegeben [unsicher] |

Quellen: https://github.com/KwaiVGI/LivePortrait und LICENSE (https://raw.githubusercontent.com/KwaiVGI/LivePortrait/main/LICENSE),
https://github.com/OpenTalker/SadTalker, https://github.com/Rudrabha/Wav2Lip, https://github.com/bytedance/LatentSync,
https://github.com/TMElyralab/MuseTalk, https://github.com/fudan-generative-vision/hallo3,
https://github.com/antgroup/echomimic_v2, https://github.com/Wan-Video/Wan2.2,
FasterLivePortrait: https://huggingface.co/spaces/AndroidGuy/FasterLivepotrait/blob/main/README.md

**Bewertung Realismus:** Ältere Modelle (Wav2Lip, SadTalker) wirken erkennbar künstlich (unscharfer Mund, starrer Kopf).
LatentSync/MuseTalk sind deutlich besser, arbeiten aber nur auf dem Gesichtsausschnitt (256–512 px), bei 1080×1920 oft
sichtbare Weichheit am Mund. Ein unabhängiger Lippensync-Benchmark mit Deutsch wurde nicht gefunden. [unsicher]

**Fazit Server ohne GPU:** Keines dieser Modelle ist auf unserem Server (4 CPU-Kerne, 15 GB RAM, keine GPU) praktisch
nutzbar. Möglich wäre nur gemietete/kostenlose Cloud-GPU (z. B. Google Colab Free, Hugging Face Spaces); deren
Kontingente sind nicht garantiert und wurden hier nicht geprüft. [unsicher]

### Freemium-Dienste

| Dienst | Kostenlos | Wasserzeichen | Kommerziell im Gratis-Tarif | Günstigster Tarif mit Rechten | Deutsch |
|---|---|---|---|---|---|
| **HeyGen** | 3 Videos/Monat, je bis 1 min; 1 eigener Video-Avatar, 3 Foto-Avatare, 1 Stimmklon; 720p [Drittquelle] | Ja | **Nein** („personal, non-commercial and internal evaluation use“, Blog aktualisiert 04.11.2026) | Creator 29 $/Monat (24 $ jährlich) | 30+ Sprachen (Deutsch üblich enthalten) |
| **Hedra** (Character-3) | 100–400 Credits je nach Quelle [unsicher]; Character-3 ca. 6 Credits/s | Ja | **Nein** (laut Hedra-Seite) | Basic 20 $/Monat, 2.000 Credits, kommerziell | nicht geprüft |
| **D-ID** | Testversion | Ja, Vollbild-Wasserzeichen | nicht angegeben | Preis nicht auf Seite | nicht geprüft |
| **Kling (inkl. Avatar)** | ca. 66 Credits (täglich oder monatlich, widersprüchlich) [unsicher] | Ja | **Nein**; AGB §4.6: kommerzielle Nutzung nur mit schriftlicher Erlaubnis, §4.5 Marken-Kennzeichnung; Kling erhält breite Lizenz inkl. Training (Stand 21.04.2026) | bezahlte Mitgliedschaft (laut Drittquellen kommerziell) [unsicher] | nicht geprüft |
| **Dreamina/CapCut (OmniHuman)** | 120 Credits/Tag | nicht geprüft | ungeklärt; Dreamina selbst: Gratis-Credits begründen keine kommerzielle Erlaubnis | Bezahltarif | nicht geprüft |
| **Meta AI-Übersetzung für Reels** | kostenlos für öffentliche Instagram-Konten | – | eigener Inhalt | – | **Deutsch seit 14.07.2026**, optionaler Lippensync; nur in Ländern mit Meta AI [für DE im Konto prüfen] |

Quellen: https://www.heygen.com/pricing, https://www.heygen.com/blog/can-i-use-ai-video-commercially,
https://bigvu.tv/blog/heygen-free-get-free-plan/ (720p), https://www.hedra.com/play/pricing,
https://hedra.com/uses/ai-character-generator, https://www.d-id.com/pricing/studio/, https://kling.ai/docs/user-policy,
https://dreamina.capcut.com/ai-video/free-ai-video-commercial-use,
https://about.fb.com/news/2025/10/discover-reels-around-world-meta-ai-translation/

**Fazit Kategorie 1:** Kostenlos UND kommerziell UND ohne Wasserzeichen gibt es bei den Avatar-Diensten nicht.
Wer HeyGen o. Ä. nutzt, braucht einen Bezahltarif (ab ca. 20–29 $/Monat) und muss das Ergebnis als KI kennzeichnen.

---

## 2. Bild zu Video / Bewegung aus Fotos

| Werkzeug | Kostenlos | Wasserzeichen | Kommerziell gratis | Realismus (Beleg) |
|---|---|---|---|---|
| **Google Flow (Veo 3.1)** | 50 Credits/Tag ohne Abo; Veo 3.1 Lite 10, Fast 20 Credits je Clip (Google-Hilfe); Google-One-Seite nennt abweichend 100 Credits/Monat [widersprüchlich] | sichtbares Wasserzeichen bei Gratis [unsicher] | Nutzungsrechte nicht geprüft [unsicher] | Veo 3.1 Platz 28 (Elo 955) im Image-to-Video-Ranking von Artificial Analysis |
| **Runway** | 125 Credits einmalig, verfallen nicht | **Ja** (alle Gratis-Videos) | Laut Runway-Hilfe keine nicht-kommerzielle Einschränkung | nicht im Ranking gelistet |
| **Luma Dream Machine** | kein Gratis-Tarif auf Preisseite; Lizenzseite: Gratis nur „personal use“ | Ja, nicht entfernbar | **Nein** | – |
| **Kling 3.0** | siehe oben | Ja | **Nein** | Platz 23/24 (Elo ca. 1.000) |
| **Hailuo/MiniMax** | ca. 150–200 Start-Credits, kein Nachfüllen [Drittquellen] | Ja | **Nein** [Drittquellen] | MiniMax H3 Platz 5 (Elo 1134) |
| **Wan 2.2 (Open Source)** | lokal kostenlos | nein | **Ja, Apache 2.0** | Wan 3.0 Platz 12 (Elo 1108; Open-Weights-Status unklar) |
| **Instagram Edits** | Foto animieren integriert | nein | eigene Nutzung | Test von Planoly: „blurry and low-res“ |

Quellen: https://support.google.com/flow/answer/16526234, https://support.google.com/googleone/answer/16287445,
https://runway.com/pricing, https://help.runwayml.com/hc/en-us/articles/21668707517587-Can-I-use-the-content-I-made-in-Runway-for-commercial-purposes,
https://lumalabs.ai/pricing, https://lumalabs.ai/learning-hub/licensing,
https://www.atlascloud.ai/blog/guides/hailuo-ai-free-credits, https://www.tomsguide.com/ai/this-ai-video-generator-is-going-viral-and-its-completely-free-to-use,
https://artificialanalysis.ai/video/leaderboard/image-to-video (Ranking AA-Video-I2V v2.1, Stand November 2026; Spitze: Seedance 2.5, Elo 1161),
https://planoly.com/blog/instagrams-edits-app-review

**Fazit Kategorie 2:** Für unser Format (echte Gespräche, Sprache, Mimik) sind Bild-zu-Video-Modelle ungeeignet:
Sie erzeugen kurze stumme oder generisch vertonte Clips (5–10 s), Gesichter der Inhaber verändern sich leicht
(„Identitätsdrift“). Sinnvoll höchstens für B-Roll (z. B. Bürofoto leicht bewegt). Dafür reicht auch ein
Ken-Burns-Zoom mit ffmpeg (kein KI-Label nötig).

---

## 3. Kostenlose Schnittwerkzeuge für echtes Smartphone-Material

| Werkzeug | Kosten / Wasserzeichen | Kommerziell | Wichtige Funktionen für das Format | Grenzen |
|---|---|---|---|---|
| **Instagram Edits** (Meta, seit 22.04.2025) | kostenlos, Export „no added watermarks“ | eigener Inhalt, keine Einschränkung bekannt | Bildgenauer Zeitstrahl, Auto-Untertitel (mehrsprachig; Deutsch nicht ausdrücklich bestätigt), Übergänge, Green Screen, Ausschneiden von Personen (für Freeze-Frame-Effekt), Titelkarten, Storyboards/Teleprompter, Beat-Vorlagen (Update 17.12.2025), Skip-Rate-Auswertung | Kein eigenes Freeze-Frame-Werkzeug [Drittquelle]; Untertitel-Timing laut Tests mühsam; Premium-Funktionen angekündigt |
| **CapCut** | Gratis-Export 1080p ohne Wasserzeichen, **wenn keine Pro-Elemente** genutzt werden; Auto-Untertitel im Gratis-Tarif eingeschränkt oder entfernt [widersprüchlich]; Pro 19,99 $/Monat | **Heikel:** Nur Vorlagen/Musik/Effekte mit Kennzeichnung „Commercial Use“ dürfen geschäftlich genutzt werden; manche kommerziellen Sounds nur für CapCut/TikTok; gemischte Projekte gelten als nicht-kommerziell (Materials License Agreement, 22.01.2026; AGB 15.04.2026) | Freeze Frame, Beat-Sync, Auto-Untertitel, viele Übergänge | Breite Lizenz an eigenen Inhalten (laut Kritik an AGB 2025) |
| **DaVinci Resolve 20 (kostenlos)** | kostenlos, kein Wasserzeichen, bis UHD 60 fps, 8-Bit | Ja (Blackmagic beschränkt die Gratisversion nicht auf private Nutzung) [auf Produktseite nicht ausdrücklich genannt] | Freeze Frame, Keyframes, Fusion-Grafiken (rotes Kreuz), Fairlight-Ton | **Nur Studio (Kauf):** Auto-Untertitel aus Audio, Magic Mask, Voice Isolation, Smart Reframe, UltraNR |
| **ffmpeg + faster-whisper** (bereits auf dem Server) | kostenlos, CPU | LGPL/GPL bzw. MIT | Freeze Frame (`tpad=stop_mode=clone`), Durchstreichen (`drawbox`/Overlay-PNG), Übergänge (`xfade`), Untertitel aus Whisper als ASS mit Archivo/Lato, Musik-Ducking (`sidechaincompress`), Lautheit (`loudnorm`) | kein Beat-Sync automatisch (mit librosa lösbar, liegt in requirements-video.txt) |

Quellen: https://about.fb.com/news/2025/04/introducing-edits-streamlined-video-creation-app/,
https://techcrunch.com/2025/08/12/a-guide-to-using-edits-metas-new-capcut-rival-for-short-form-video-editing,
https://www.capcut.com/clause/material-license-agreement, https://dreamina.capcut.com/clause/terms-of-service,
https://www.capcut.com/help/join-capcut-pro-for-exporting, https://descript.com/blog/article/capcut-captions-arent-free-anymore-heres-a-better-option,
https://www.blackmagicdesign.com/products/davinciresolve/studio,
https://cloud.wikis.utexas.edu/wiki/spaces/comm/pages/33425449/DaVinci+Resolve+Studio+Only+-+Auto+Caption+and+Subtitle+Workflow,
https://www.cined.com/davinci-resolve-an-in-depth-comparison-between-the-free-and-studio-version/

**Funktionen, die für das Do's-and-Don'ts-Format zählen:**
1. Freeze Frame genau auf der schlechten Antwort, rotes Kreuz plus Stichwort („Don't: Ex-Chef schlechtreden“).
2. Harte Übergänge (Schnitt, kurzer Wisch) statt Effekt-Feuerwerk.
3. Eingebrannte Untertitel (viele schauen ohne Ton), im Inpernell-Stil, in den sicheren Zonen (y 285 bis 1520).
4. Eigene Musik leise unter Sprache (CLAUDE.md: Reels immer mit Ton).
5. Logo klein unten links (x ≈ 74, y ≈ 1420), groß nur auf der Abschlussfolie.

---

## 4. Stimmen (eigene Stimmen der Inhaber)

| Option | Kosten / Grenzen | Kommerziell | Deutsch |
|---|---|---|---|
| **Echte Aufnahme** (Smartphone + Ansteckmikro) | 0 € | ja | ja, am natürlichsten |
| **ElevenLabs Free** | 10.000 Credits/Monat, **kein Stimmklon** | **Nein**, Namensnennung „elevenlabs.io“ Pflicht | ja |
| **ElevenLabs Starter** | 1 $ erster Monat, dann 6 $/Monat, 30.000 Credits, Instant Voice Cloning (Proben unter 2 min) | **Ja** | Multilingual v2 (29 Sprachen inkl. Deutsch) |
| ElevenLabs Professional Voice Cloning | ab Creator-Tarif, Sprachprobe mit Verifizierung der eigenen Stimme | ja | ja |
| **Chatterbox Multilingual** (Resemble AI, Open Source) | 0 €, Zero-Shot-Klon aus ca. 10 s; CPU möglich | MIT; jede Ausgabe mit unhörbarem Perth-Wasserzeichen; **seit 08/2026 nicht mehr gepflegt** | ja (23+ Sprachen) |
| Coqui XTTS-v2 | 0 € | Coqui Public Model License, nach unserem Kenntnisstand nur nicht-kommerziell [Lizenztext prüfen] | ja |
| Piper „Thorsten“ (bereits im Einsatz, `stimme.py`) | 0 €, CPU | gemeinfreie Stimme | ja, aber keine Inhaberstimme |

Quellen: https://elevenlabs.io/pricing, https://elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform,
https://elevenlabs.io/docs/overview/capabilities/voices, https://github.com/resemble-ai/chatterbox, https://huggingface.co/coqui/XTTS-v2

Hinweis: Geklonte Stimmen gelten bei Meta als „realistisch klingendes KI-Audio“ und brauchen das Label „AI info“.

---

## 5. Gesamtvergleich (Kurzform)

| Werkzeug | Gratis nutzbar ohne Wasserzeichen | Kommerziell gratis | Läuft auf unserem Server (CPU) | Wirkt echt |
|---|---|---|---|---|
| Echt filmen + ffmpeg/faster-whisper | ja | ja | **ja** | **ja (ist echt)** |
| Instagram Edits | ja | ja | nein (App) | ja |
| DaVinci Resolve Free | ja | ja | nein (Desktop) | ja |
| CapCut Free | eingeschränkt | nur „Commercial Use“-Elemente | nein (App) | ja |
| LatentSync / MuseTalk / Wan 2.2 | ja | ja | nein (GPU nötig) | mittel bis gut, Kennzeichnung nötig |
| Wav2Lip | ja | **nein** | eingeschränkt | schwach |
| LivePortrait | ja | nur ohne InsightFace-Modelle | sehr langsam | gut für Mimik, kein Ton |
| HeyGen / Hedra / Kling / Luma / Hailuo gratis | **nein** | **nein** | Cloud | gut bis sehr gut, Kennzeichnung nötig |
| Runway gratis | nein (Wasserzeichen) | ja laut Runway | Cloud | gut |
| ElevenLabs Starter (6 $) | ja | ja | Cloud | sehr gut, Kennzeichnung nötig |

---

## 6. Empfehlung

1. **Echt drehen statt generieren.** Die drei Inhaber filmen jede Szene mit dem Smartphone (Hochformat 1080×1920,
   Stativ, Ansteckmikro, Fensterlicht). Das ist kostenlos, wirkt garantiert echt, braucht kein KI-Label und schafft
   Vertrauen, was für eine Personalvermittlung wichtiger ist als Effekte.
2. **Schnitt automatisiert auf unserem Server mit ffmpeg + faster-whisper** (beides vorhanden): Freeze Frame auf der
   Don't-Antwort, rotes Kreuz mit Stichwort, harter Schnitt zum dritten Inhaber mit Do-Antwort, Untertitel im
   Inpernell-Stil aus Whisper, eigene Musik geduckt, Logo nach CLAUDE.md. Vorher Vorschaubild zeigen, Freigabe abwarten.
3. **Für Feinschliff von Hand: Instagram Edits** (kostenlos, ohne Wasserzeichen, direkt nach Instagram). DaVinci Resolve
   Free als Desktop-Alternative; Auto-Untertitel dort nur in Studio, daher Untertitel aus unserem Whisper-Schritt
   als SRT importieren.
4. **CapCut nur mit Vorsicht:** Nur Elemente mit „Commercial Use“-Kennzeichnung, keine CapCut-Musik; besser eigene Musik.
5. **KI-Lippensync/Avatare nur als Ausnahme**, z. B. wenn ein Inhaber nicht verfügbar ist: dann HeyGen Creator
   (29 $/Monat) oder ElevenLabs Starter (6 $/Monat) für die eigene Stimme, mit schriftlicher Einwilligung des Inhabers
   und immer mit „AI info“-Label (Art. 50 KI-VO, Meta-Regeln). Gratis-Tarife scheiden wegen Wasserzeichen und
   fehlender kommerzieller Rechte aus.
6. **Optional ausprobieren:** Meta-AI-Übersetzung (kostenlos, mit Lippensync, Deutsch seit 07/2026) für Reels,
   die zusätzlich auf Englisch erreicht werden sollen; vorher im Konto prüfen, ob in Deutschland verfügbar.

## Offene Punkte / zu prüfen
- Google-Flow-Nutzungsrechte und Wasserzeichen im Gratis-Tarif (nicht auf Google-Seite bestätigt).
- Kling Paid-Service-Bedingungen (kommerzielle Rechte nur über Drittquellen).
- Ob Instagram-Edits-Untertitel Deutsch zuverlässig erkennen (Praxistest).
- Verfügbarkeit der Meta-AI-Übersetzung in Deutschland.
- CPML-Lizenztext (XTTS-v2) vor jeder Nutzung lesen.
