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


# ---------------------------------------------------------------- Synthwave (80er-/Miami-Stimmung, eigene Komposition)

def _saege(f, n, verstimmt=(0.0,)):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for v in verstimmt:
        ff = f * 2 ** (v / 12)
        s += 2 * ((t * ff) % 1.0) - 1
    return s / len(verstimmt)


def _tiefpass(x, grenze):
    from scipy.signal import butter, lfilter
    b, a = butter(2, grenze / (SR / 2))
    return lfilter(b, a, x)


def erzeuge_synthwave(sekunden, ziel_wav, bpm=112, seed=7):
    """Synthwave: Gated-Reverb-Snare, pulsierender Achtel-Bass, breite Sägezahn-Flächen, Arpeggio, Lead-Hook.
    Akkorde Fis-Moll – D – A – E (eigene Folge und Melodie, keine Anlehnung an bestehende Stücke)."""
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    n_ges = int((sekunden + 1) * SR)
    spuren = {k: np.zeros(n_ges) for k in ("drums", "bass", "pad", "arp", "lead")}

    def setze(spur, sig, start, gain=1.0):
        i = int(start * SR)
        if i >= n_ges or i < 0:
            return
        sig = sig[: n_ges - i]
        spuren[spur][i:i + len(sig)] += sig * gain

    folge = [(54, "m"), (50, "M"), (57, "M"), (52, "M")]           # F#m – D – A – E
    melodie = [  # (Schlag im 2-Takt-Muster, Halbton über Grundton der Tonart F#, Länge in Schlägen)
        (0, 12, 1.5), (1.5, 16, 0.5), (2, 19, 1), (3, 16, 1), (4, 14, 1.5), (5.5, 12, 0.5), (6, 9, 2)]
    takt = 4 * beat
    n_takte = int(np.ceil(sekunden / takt)) + 1
    for tk in range(n_takte):
        t0 = tk * takt
        grund, art = folge[tk % len(folge)]
        terz = 3 if art == "m" else 4
        noten = [grund, grund + terz, grund + 7]
        # Fläche: breite, verstimmte Sägezähne, weich gefiltert
        nf = int(takt * SR)
        pad = sum(_saege(_hz(m), nf, (-0.1, 0.0, 0.1)) for m in noten + [grund + 12]) / 4
        env = np.minimum(1, np.arange(nf) / (0.25 * SR)) * np.minimum(1, (nf - np.arange(nf)) / (0.1 * SR))
        setze("pad", pad * env, t0, 0.35)
        intro = tk == 0
        for b in range(4):
            tb = t0 + b * beat
            if not intro:
                setze("drums", _kick(int(0.45 * SR)), tb, 1.0)
                if b in (1, 3):                                   # Gated-Reverb-Snare (typisch 80er)
                    n = int(0.32 * SR); t = np.arange(n) / SR
                    rausch = rng.standard_normal(n) * np.where(t < 0.22, 1.0, np.exp(-(t - 0.22) * 80))
                    koerper = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
                    setze("drums", (rausch * 0.5 + koerper * 0.6) * 0.55, tb)
            for h in range(4):                                    # Sechzehntel-Hats
                if not intro or h % 2 == 1:
                    setze("drums", _hat(int(0.04 * SR), rng), tb + h * beat / 4, 0.7 if h % 2 else 0.4)
            for a8 in range(2):                                   # pulsierender Achtel-Bass (Oktave)
                f = _hz(grund - 24 + (12 if a8 else 0))
                n = int(beat / 2 * 0.9 * SR)
                setze("bass", _saege(f, n, (-0.05, 0.05)) * np.exp(-np.arange(n) / SR * 6), tb + a8 * beat / 2, 0.5)
            for s16 in range(4):                                  # Arpeggio
                m = noten[(b * 4 + s16) % 3] + 12 + (12 if (b * 4 + s16) % 6 == 5 else 0)
                n = int(beat / 4 * 0.8 * SR)
                setze("arp", _saege(_hz(m), n) * np.exp(-np.arange(n) / SR * 18), tb + s16 * beat / 4, 0.22)
        if tk >= 2:                                               # Lead-Melodie ab Takt 3
            for s, iv, lng in melodie:
                if (tk % 2) * 4 <= s < (tk % 2) * 4 + 4:
                    ts = t0 + (s - (tk % 2) * 4) * beat
                    n = int(lng * beat * SR); t = np.arange(n) / SR
                    vib = np.sin(2 * np.pi * 5.5 * t) * 0.15 * np.minimum(1, t / 0.3)
                    f = _hz(54 + iv) * 2 ** (vib / 12)
                    phase = np.cumsum(f) / SR
                    lead = (2 * (phase % 1.0) - 1) * 0.6 + np.sign(np.sin(2 * np.pi * phase)) * 0.4
                    env = np.minimum(1, t / 0.02) * np.minimum(1, (n / SR - t) / 0.08)
                    setze("lead", lead * env, ts, 0.28)

    mix = (spuren["drums"] + _tiefpass(spuren["bass"], 900) + _tiefpass(spuren["pad"], 2200)
           + _tiefpass(spuren["arp"], 3500) + _tiefpass(spuren["lead"], 4200))
    # einfacher Hall/Echo (punktierte Achtel) für die 80er-Weite
    echo = int(beat * 0.75 * SR)
    hall = np.zeros_like(mix); hall[echo:] = mix[:-echo] * 0.25
    mix = mix + _tiefpass(hall, 3000)
    n = int(sekunden * SR); mix = mix[:n]
    aus = int(1.8 * SR); mix[-aus:] *= np.linspace(1, 0, aus)
    mix = np.tanh(mix / max(1e-6, np.max(np.abs(mix))) * 1.6) / np.tanh(1.6) * 0.9
    links = mix
    rechts = np.concatenate([np.zeros(int(0.015 * SR)), mix])[:n]
    stereo = np.stack([links, 0.8 * rechts + 0.2 * links], axis=1)
    with wave.open(ziel_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((stereo * 32767).astype(np.int16).tobytes())
    return ziel_wav
