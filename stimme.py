"""Sprecherstimme für Reels mit Piper (Open Source, läuft offline) und der Stimme "Thorsten" (gemeinfrei).

vertonen(texte, ziel_wav) spricht jeden Text als eigene Szene, setzt kurze Pausen dazwischen und gibt
die Länge jeder Szene in Sekunden zurück – damit das Video seine Szenen genau daran ausrichtet.
Modell: de_DE-thorsten-high von huggingface.co/rhasspy/piper-voices (wird beim ersten Mal geladen).
"""
import os
import subprocess
import tempfile
import urllib.request
import wave

HIER = os.path.dirname(os.path.abspath(__file__))
MODELL_ORDNER = os.environ.get("PIPER_MODELLE", os.path.join(HIER, ".piper"))
MODELL = "de_DE-thorsten-high"
QUELLE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high/"
PAUSE_VOR, PAUSE_NACH = 0.35, 0.55     # Sekunden Luft vor/nach jedem Satz innerhalb der Szene


def _modell():
    os.makedirs(MODELL_ORDNER, exist_ok=True)
    pfad = os.path.join(MODELL_ORDNER, MODELL + ".onnx")
    for datei in (MODELL + ".onnx", MODELL + ".onnx.json"):
        ziel = os.path.join(MODELL_ORDNER, datei)
        if not os.path.exists(ziel):
            urllib.request.urlretrieve(QUELLE + datei, ziel)
    return pfad


def zusammensetzen(wav_dateien, ziel_wav):
    """Fügt fertige Sprach-WAVs (eine je Szene) mit Pausen zu einer Tonspur zusammen; gibt Szenenlängen zurück."""
    dauern, teile = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for i, roh in enumerate(wav_dateien):
            with wave.open(roh) as w:
                laenge = w.getnframes() / w.getframerate()
            szene = PAUSE_VOR + laenge + PAUSE_NACH
            dauern.append(szene)
            teil = os.path.join(tmp, f"t{i}.wav")
            # Pause davor, auffüllen bis zur Szenenlänge, einheitlich 48 kHz stereo, gleiche Lautheit
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", roh, "-af",
                            f"adelay={int(PAUSE_VOR * 1000)}:all=1,apad=whole_dur={szene},"
                            "aresample=48000,loudnorm=I=-16:TP=-1.5", "-ac", "2", teil], check=True)
            teile.append(teil)
        liste = os.path.join(tmp, "liste.txt")
        with open(liste, "w") as f:
            f.writelines(f"file '{t}'\n" for t in teile)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", liste,
                        "-c", "pcm_s16le", ziel_wav], check=True)
    return dauern


def vertonen(texte, ziel_wav):
    """Spricht jeden Text mit der Piper-Stimme "Thorsten" und setzt die Tonspur zusammen."""
    from piper import PiperVoice
    stimme = PiperVoice.load(_modell())
    with tempfile.TemporaryDirectory() as tmp:
        roh = []
        for i, text in enumerate(texte):
            pfad = os.path.join(tmp, f"{i}.wav")
            with wave.open(pfad, "wb") as w:
                stimme.synthesize_wav(text, w)
            roh.append(pfad)
        return zusammensetzen(roh, ziel_wav)


# ---------------------------------------------------------------- Azure-Neuralstimmen (natürlicher Klang)

AZURE_REGION = os.environ.get("AZURE_SPEECH_REGION", "germanywestcentral")
AZURE_STIMME = os.environ.get("AZURE_SPEECH_VOICE", "de-DE-FlorianMultilingualNeural")


def _azure_wav(text, ziel, stimme, tempo="+0%", stil=None, staerke=0.8):
    """Ein Text als WAV über Azure Text-to-Speech (Schlüssel aus AZURE_SPEECH_KEY).
    Im Text erzeugt " | " eine kurze natürliche Atempause."""
    from xml.sax.saxutils import escape
    inhalt = escape(text).replace(" | ", ' <break time="250ms"/> ')
    inhalt = f'<prosody rate="{tempo}">{inhalt}</prosody>'
    if stil:
        inhalt = f'<mstts:express-as style="{stil}" styledegree="{staerke}">{inhalt}</mstts:express-as>'
    ssml = ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="de-DE">'
            f'<voice name="{stimme}">{inhalt}</voice></speak>')
    req = urllib.request.Request(
        f"https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1", data=ssml.encode("utf-8"),
        headers={"Ocp-Apim-Subscription-Key": os.environ.get("AZURE_SPEECH_KEY", "proxy-injected"),
                 "Content-Type": "application/ssml+xml", "User-Agent": "inpernell-reels",
                 "X-Microsoft-OutputFormat": "riff-48khz-16bit-mono-pcm"})
    with urllib.request.urlopen(req, timeout=60) as r, open(ziel, "wb") as f:
        f.write(r.read())


def vertonen_azure(texte, ziel_wav, stimme=None, tempo="+0%", stil=None):
    """Spricht jeden Text mit einer Azure-Neuralstimme und setzt die Tonspur zusammen."""
    with tempfile.TemporaryDirectory() as tmp:
        roh = []
        for i, text in enumerate(texte):
            pfad = os.path.join(tmp, f"{i}.wav")
            _azure_wav(text, pfad, stimme or AZURE_STIMME, tempo=tempo, stil=stil)
            roh.append(pfad)
        return zusammensetzen(roh, ziel_wav)
