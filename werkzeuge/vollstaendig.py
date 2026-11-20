#!/usr/bin/env python3
"""Vollständigkeitsprüfung für fertige Videos: hört das Video per Spracherkennung ab und prüft, ob jedes Wort
der vorgesehenen Texte in der richtigen Reihenfolge vorkommt. Fehlende Wörter werden gemeldet.

Aufruf: python werkzeuge/vollstaendig.py video.mp4 "Satz 1" "Satz 2" ...
"""
import re
import subprocess
import sys
from difflib import SequenceMatcher

import numpy as np


_ZAHLEN = dict(enumerate("null eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf".split()))


def _woerter(text):
    text = text.lower().replace("-", " ").replace("ß", "ss")
    text = re.sub(r"(\d)([a-zäöü])|([a-zäöü])(\d)", r"\1\3 \2\4", text)
    w_ = [w for w in re.sub(r"[^\wäöü ]", " ", text).split() if w]
    return [_ZAHLEN.get(int(w), w) if w.isdigit() and int(w) in _ZAHLEN else w for w in w_]   # 3 = „drei“


def _gleich(a, b):
    # auch zusammengeschrieben erkannt („Job-Mythen“ als „Jobmythen“)
    return a == b or SequenceMatcher(None, a, b).ratio() >= 0.7 or (len(a) >= 3 and b.startswith(a))


_M = {}


def _modell():
    if "m" not in _M:
        from faster_whisper import WhisperModel
        _M["m"] = WhisperModel("small", device="cpu", compute_type="int8")
    return _M["m"]


def _ton(video):
    roh = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", video, "-f", "s16le", "-ac", "1", "-ar", "16000", "pipe:1"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(roh, np.int16).astype(np.float32) / 32768


def _hoeren(a, versatz=0.0):
    segs, _ = _modell().transcribe(a, language="de", word_timestamps=True)
    return [(w.word.strip(), versatz + w.start) for s in segs for w in s.words]


def abhoeren(video):
    return _hoeren(_ton(video))


def pruefe(video, texte, streng=False):
    """Gibt die Liste fehlender Wörter zurück. streng=True: Fehler auslösen, wenn ein Wort mit mehr als
    drei Buchstaben fehlt (kurze Wörter wie „im“/„in“ verhört die Erkennung oft, sie werden nur gemeldet)."""
    ton = _ton(video)
    gehoert = _hoeren(ton)
    hw = []
    for w, t in gehoert:
        hw += [(x, t) for x in _woerter(w)]
    fehlt, pos, t_zuletzt = [], 0, 0.0
    for text in texte:
        for w in _woerter(text):
            treffer = next((j for j in range(pos, min(len(hw), pos + 6)) if _gleich(w, hw[j][0])), None)
            if treffer is not None:
                pos, t_zuletzt = treffer + 1, hw[treffer][1]
                continue
            # Gegenprobe: Stelle einzeln abhören (im ganzen Video verhört sich die Erkennung manchmal)
            gefunden = False
            t_naechst = hw[pos][1] if pos < len(hw) else t_zuletzt + 1   # nächstes gehörtes Wort
            for v0 in (t_naechst - 0.6, t_naechst - 1.2, t_zuletzt + 0.25):
                v0 = max(0.0, v0)
                stueck = ton[int(v0 * 16000):int((v0 + 4) * 16000)]
                if any(_gleich(w, x) for ww, _ in _hoeren(stueck, v0) for x in _woerter(ww)):
                    gefunden = True
                    break
            if not gefunden:
                fehlt.append((w, text))
    print("Gehört:", " ".join(w for w, _ in gehoert))
    if not fehlt:
        print("VOLLSTÄNDIG: alle Wörter zu hören.")
    for w, text in fehlt:
        print(f"FEHLT: „{w}“ in „{text}“")
    schwer = [w for w, _ in fehlt if len(w) > 3]
    if streng and schwer:
        raise RuntimeError("Video unvollständig, fehlende Wörter: " + ", ".join(schwer))
    return fehlt


if __name__ == "__main__":
    f = pruefe(sys.argv[1], sys.argv[2:])
    sys.exit(1 if any(len(w) > 3 for w, _ in f) else 0)
