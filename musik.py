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


# ---------------------------------------------------------------- Chillige Miami-Stimmungen (eigene Kompositionen)

def _rhodes(f, n):
    """E-Piano-artiger Klang: Sinus mit Obertönen, weicher Anschlag, Tremolo."""
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3) + 0.12 * np.sin(6 * np.pi * f * t) * np.exp(-t * 6)
    return s * np.exp(-t * 1.2) * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t)) * np.minimum(1, t / 0.005)


def _pluck(f, n):
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 9) * np.minimum(1, t / 0.002)


CHILL_STILE = {
    # Name: bpm, Akkordfolge (Grundton MIDI, Moll/Dur, Septime), Instrumente
    "sunset_drive": dict(bpm=96, folge=[(52, "m", 10), (48, "M", 11), (55, "M", 11), (50, "m", 10)],
                         pad="saege", bass="achtel", arp="saege", lead=True, drums="synthwave", swing=0.0),
    "ocean_lofi": dict(bpm=82, folge=[(50, "m", 10), (55, "M", 10), (48, "M", 11), (45, "m", 10)],
                       pad="rhodes", bass="ganz", arp=None, lead=False, drums="lofi", swing=0.12, knistern=True),
    "palm_breeze": dict(bpm=108, folge=[(53, "M", 11), (57, "m", 10), (50, "m", 10), (55, "M", 10)],
                        pad="rhodes", bass="offbeat", arp="pluck", lead=False, drums="house", swing=0.05),
    "neon_nights": dict(bpm=112, folge=[(54, "m", 10), (50, "M", 11), (57, "M", 11), (52, "M", 10)],
                        pad="saege", bass="achtel", arp="saege", lead=True, drums="synthwave", swing=0.0),
}


def erzeuge_chill(sekunden, ziel_wav, stil="sunset_drive", seed=11):
    c = CHILL_STILE[stil]
    rng = np.random.default_rng(seed)
    bpm = c["bpm"]; beat = 60.0 / bpm; takt = 4 * beat
    n_ges = int((sekunden + 1) * SR)
    sp = {k: np.zeros(n_ges) for k in ("drums", "bass", "pad", "arp", "lead")}

    def setze(spur, sig, start, gain=1.0):
        i = int(start * SR)
        if 0 <= i < n_ges:
            sig = sig[: n_ges - i]; sp[spur][i:i + len(sig)] += sig * gain

    melodie = [(0, 14, 1.5), (1.5, 12, 0.5), (2, 10, 1), (3, 7, 1), (4, 9, 2), (6, 7, 1), (7, 5, 1)]
    for tk in range(int(np.ceil(sekunden / takt)) + 1):
        t0 = tk * takt
        grund, art, sept = c["folge"][tk % len(c["folge"])]
        noten = [grund, grund + (3 if art == "m" else 4), grund + 7, grund + sept]
        nf = int(takt * SR)
        if c["pad"] == "saege":
            pad = sum(_saege(_hz(m), nf, (-0.08, 0.0, 0.08)) for m in noten) / 4
            env = np.minimum(1, np.arange(nf) / (0.4 * SR)) * np.minimum(1, (nf - np.arange(nf)) / (0.15 * SR))
            setze("pad", pad * env, t0, 0.32)
        else:                                                  # E-Piano: Akkord auf 1 und auf die "Und" von 2
            for ts, lg in ((0, 2.5), (1.5 + c["swing"], 2.5)):
                n = int(lg * beat * SR)
                setze("pad", sum(_rhodes(_hz(m + 12), n) for m in noten) / 4, t0 + ts * beat, 0.5)
        intro = tk == 0
        for b in range(4):
            tb = t0 + b * beat
            sw = c["swing"] * beat
            if not intro:
                if c["drums"] in ("synthwave", "house") or b in (0, 2):
                    setze("drums", _kick(int(0.4 * SR)), tb, 0.8 if c["drums"] != "lofi" else 0.65)
                if c["drums"] == "lofi" and b == 2:
                    setze("drums", _kick(int(0.4 * SR)), tb + beat * 0.5 + sw, 0.45)
                if b in (1, 3):
                    n = int(0.3 * SR); t = np.arange(n) / SR
                    if c["drums"] == "synthwave":
                        rausch = rng.standard_normal(n) * np.where(t < 0.2, 1.0, np.exp(-(t - 0.2) * 80))
                        snare = rausch * 0.45 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.5
                    else:
                        snare = _clap(n, rng) * (0.8 if c["drums"] == "house" else 0.6)
                    setze("drums", snare * 0.5, tb)
            for h in range(2):
                setze("drums", _hat(int(0.05 * SR), rng), tb + h * beat / 2 + (sw if h else 0), 0.35 if h == 0 else 0.6)
            f = _hz(grund - 24)
            if c["bass"] == "achtel":
                for a8 in range(2):
                    n = int(beat / 2 * 0.9 * SR)
                    setze("bass", _saege(f * (2 if a8 else 1), n) * np.exp(-np.arange(n) / SR * 6), tb + a8 * beat / 2, 0.42)
            elif c["bass"] == "offbeat":
                setze("bass", _bass(f * 2, int(beat * 0.45 * SR)), tb + beat / 2, 0.9)
            elif c["bass"] == "ganz" and b in (0, 2) and not intro:
                setze("bass", _bass(f * 2, int(beat * 1.8 * SR)), tb, 0.9)
            if c["arp"]:
                for s16 in range(2 if c["arp"] == "pluck" else 4):
                    teil = 2 if c["arp"] == "pluck" else 4
                    m = noten[(b * teil + s16) % 4] + 12
                    n = int(beat / teil * 0.9 * SR)
                    sig = _pluck(_hz(m + 12), n) if c["arp"] == "pluck" else _saege(_hz(m), n) * np.exp(-np.arange(n) / SR * 14)
                    setze("arp", sig, tb + s16 * beat / teil, 0.3 if c["arp"] == "pluck" else 0.16)
        if c["lead"] and tk >= 2:
            for s, iv, lng in melodie:
                if (tk % 2) * 4 <= s < (tk % 2) * 4 + 4:
                    ts = t0 + (s - (tk % 2) * 4) * beat
                    n = int(lng * beat * SR); t = np.arange(n) / SR
                    vib = np.sin(2 * np.pi * 5 * t) * 0.12 * np.minimum(1, t / 0.3)
                    ph = np.cumsum(_hz(c["folge"][0][0] + 12 + iv) * 2 ** (vib / 12)) / SR
                    lead = np.sin(2 * np.pi * ph) * 0.6 + (2 * (ph % 1.0) - 1) * 0.25
                    env = np.minimum(1, t / 0.04) * np.minimum(1, (n / SR - t) / 0.1)
                    setze("lead", lead * env, ts, 0.25)

    mix = (sp["drums"] + _tiefpass(sp["bass"], 700) + _tiefpass(sp["pad"], 1800 if c["pad"] == "saege" else 3000)
           + _tiefpass(sp["arp"], 3200) + _tiefpass(sp["lead"], 3800))
    if c.get("knistern"):                                      # leichtes Platten-Knistern
        k = np.zeros(n_ges); idx = rng.integers(0, n_ges, int(n_ges / SR * 30)); k[idx] = rng.standard_normal(len(idx)) * 0.15
        mix += k + rng.standard_normal(n_ges) * 0.004
    echo = int(beat * 0.75 * SR)
    hall = np.zeros_like(mix); hall[echo:] = mix[:-echo] * 0.22
    mix = mix + _tiefpass(hall, 2500)
    n = int(sekunden * SR); mix = mix[:n]
    ein, aus = int(0.3 * SR), int(2.0 * SR)
    mix[:ein] *= np.linspace(0, 1, ein); mix[-aus:] *= np.linspace(1, 0, aus)
    mix = np.tanh(mix / max(1e-6, np.max(np.abs(mix))) * 1.4) / np.tanh(1.4) * 0.88
    rechts = np.concatenate([np.zeros(int(0.015 * SR)), mix])[:n]
    stereo = np.stack([mix, 0.8 * rechts + 0.2 * mix], axis=1)
    with wave.open(ziel_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((stereo * 32767).astype(np.int16).tobytes())
    return ziel_wav


# ---------------------------------------------------------------- Comedy-Untermalung (Sitcom-Stil, eigene Komposition)

def _zupf(f, dauer, helligkeit=0.5, abkling=0.996):
    """Gezupfte Saite (Karplus-Strong) – klingt wie Pizzicato / Ukulele."""
    from scipy.signal import lfilter
    n = int(dauer * SR)
    p = max(2, int(SR / f))
    rng = np.random.default_rng(int(f * 10))
    x = np.zeros(n)
    x[:p] = rng.uniform(-1, 1, p) * np.hanning(p)
    a = np.zeros(p + 2)
    a[0] = 1.0
    a[p] = -abkling * (1 - helligkeit / 2)
    a[p + 1] = -abkling * helligkeit / 2
    y = lfilter([1.0], a, x)
    return y * np.minimum(1, (n - np.arange(n)) / (0.02 * SR))


def erzeuge_comedy(sekunden, ziel_wav, bpm=108, seed=5):
    """Verspielte Büro-Comedy-Musik: Pizzicato-Melodie mit Pausen, Zupfbass auf 1 und 3, Holzblock auf den Nachschlägen.
    F – Dm – B – C. Bewusst leicht und luftig, damit Stimmen darüber gut verständlich bleiben."""
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    n = int((sekunden + 1) * SR)
    mel, bass, klack = np.zeros(n), np.zeros(n), np.zeros(n)

    def setze(spur, sig, t, g=1.0):
        i = int(t * SR)
        if i < n:
            sig = sig[: n - i]
            spur[i:i + len(sig)] += sig * g

    folge = [(53, [0, 4, 7]), (50, [0, 3, 7]), (46, [0, 4, 7]), (48, [0, 4, 7])]      # F Dm B C
    # Melodie-Muster in Achteln (None = Pause): Tonstufen relativ zum Akkord-Grundton
    muster = [[12, None, 16, 19, None, 16, 12, None], [14, None, 12, None, 7, 9, 12, None],
              [12, 16, None, 19, 21, None, 19, None], [16, None, 14, 12, None, None, 7, None]]
    takt = 4 * beat
    for tk in range(int(np.ceil(sekunden / takt)) + 1):
        t0 = tk * takt
        grund, akk = folge[tk % 4]
        for b in (0, 2):
            ton = grund - 12 + (0 if b == 0 else 7)
            setze(bass, _zupf(_hz(ton), beat * 0.9, 0.3, 0.993), t0 + b * beat, 0.9)
        for b in (1, 3):
            t = np.arange(int(0.05 * SR)) / SR
            setze(klack, np.sin(2 * np.pi * 900 * t) * np.exp(-t * 90) * 0.5, t0 + b * beat + 0.5 * beat * (tk % 2))
        for i, st in enumerate(muster[(tk // 1) % 4]):
            if st is None:
                continue
            setze(mel, _zupf(_hz(grund + st), beat * 0.45, 0.65, 0.990), t0 + i * beat / 2 + rng.uniform(0, 0.006), 0.55)
    mix = mel + bass * 0.8 + klack * 0.5
    n2 = int(sekunden * SR)
    mix = mix[:n2]
    aus = int(1.2 * SR)
    mix[-aus:] *= np.linspace(1, 0, aus)
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.9
    stereo = np.stack([mix, np.concatenate([np.zeros(int(0.01 * SR)), mix])[:n2]], axis=1)
    with wave.open(ziel_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((stereo * 32767).astype(np.int16).tobytes())
    return ziel_wav
