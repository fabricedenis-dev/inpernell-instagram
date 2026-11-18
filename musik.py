"""Eigene Hintergrundmusik für Reels – vollständig selbst erzeugt, damit ohne Lizenz- oder GEMA-Risiko.

erzeuge_track(sekunden, ziel_wav, bpm=118, variante=0) baut einen modernen, gut gelaunten House-/Lo-Fi-Beat:
Kick auf jedem Schlag, Offbeat-Hi-Hats, Clap auf 2 und 4, warme Akkordflächen, Bass, leichtes "Pumpen"
(Sidechain). Intro ohne Kick, Ausblenden am Ende. Verschiedene Varianten = andere Akkordfolgen.
"""
import wave

import numpy as np

SR = 48000
FOLGEN = [  # Akkordfolgen (Grundtöne als MIDI-Noten, Moll/Dur über die Terz)
    [(57, "m"), (53, "M"), (48, "M"), (55, "M")],   # Am – F – C – G
    [(50, "m"), (55, "M"), (48, "M"), (57, "m")],   # Dm – G – C – Am
    [(53, "M"), (55, "M"), (57, "m"), (52, "m")],   # F – G – Am – Em
]


def _hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def _hull(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / r)


def _kick(n):
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 0.95


def _hat(n, rng):
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))          # Hochpass grob
    return x * _hull(n, 0.001, 0.03) * 0.12


def _clap(n, rng):
    x = rng.standard_normal(n)
    x = np.convolve(x, np.ones(8) / 8, "same") - np.convolve(x, np.ones(64) / 64, "same")
    return x * _hull(n, 0.002, 0.12) * 0.35


def _pad(freqs, n):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for verstimmung in (-0.12, 0.0, 0.12):     # leichtes Schweben
            ff = f * 2 ** (verstimmung / 12)
            s += np.sin(2 * np.pi * ff * t) + 0.3 * np.sin(4 * np.pi * ff * t) + 0.12 * np.sin(6 * np.pi * ff * t)
    huell = np.minimum(1, t / 0.08) * np.minimum(1, (n / SR - t) / 0.15)
    return s / (len(freqs) * 3) * huell * 0.32


def _bass(f, n):
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return s * np.minimum(1, t / 0.01) * np.exp(-t * 2.5) * 0.4


def erzeuge_track(sekunden, ziel_wav, bpm=118, variante=0, seed=3):
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    n_ges = int((sekunden + 1) * SR)
    mix = np.zeros(n_ges)
    pump = np.ones(n_ges)
    folge = FOLGEN[variante % len(FOLGEN)]
    takt = 4 * beat
    n_takte = int(np.ceil(sekunden / takt)) + 1

    def setze(sig, start):
        i = int(start * SR)
        if i >= n_ges:
            return
        sig = sig[: n_ges - i]
        mix[i:i + len(sig)] += sig

    for tk in range(n_takte):
        t0 = tk * takt
        grund, art = folge[tk % len(folge)]
        terz = 3 if art == "m" else 4
        akkord = [_hz(grund), _hz(grund + terz), _hz(grund + 7), _hz(grund + 12)]
        setze(_pad(akkord, int(takt * SR)), t0)
        intro = tk < 1                                  # erster Takt ohne Beat
        for b in range(4):
            tb = t0 + b * beat
            if not intro:
                setze(_kick(int(0.45 * SR)), tb)
                i = int(tb * SR)
                k = np.arange(min(int(beat * SR), n_ges - i)) / SR
                pump[i:i + len(k)] = np.minimum(pump[i:i + len(k)], 0.35 + 0.65 * np.minimum(1, k / (beat * 0.6)))
                if b in (1, 3):
                    setze(_clap(int(0.3 * SR), rng), tb)
                setze(_bass(_hz(grund - 12), int(beat * 0.9 * SR)), tb + beat / 2)
            setze(_hat(int(0.08 * SR), rng), tb + beat / 2)
            if not intro and tk % 2 == 1:
                setze(_hat(int(0.05 * SR), rng) * 0.6, tb + beat * 0.75)

    # Pumpen nur auf Flächen/Bass wirkt natürlicher – vereinfacht: auf den ganzen Mix, aber abgeschwächt
    mix *= 0.55 + 0.45 * pump
    n = int(sekunden * SR)
    mix = mix[:n]
    ausblenden = int(1.5 * SR)
    mix[-ausblenden:] *= np.linspace(1, 0, ausblenden)
    mix /= max(1e-6, np.max(np.abs(mix))) / 0.85
    # leichte Stereobreite
    links = mix
    rechts = np.concatenate([np.zeros(int(0.012 * SR)), mix])[:n]
    stereo = np.stack([links, 0.85 * rechts + 0.15 * links], axis=1)
    pcm = (stereo * 32767).astype(np.int16)
    with wave.open(ziel_wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return ziel_wav
