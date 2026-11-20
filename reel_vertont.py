#!/usr/bin/env python3
"""Vertonte Reels aus der Warteschlange: Sprecher Michael Danisch (ElevenLabs), mitlaufende Untertitel,
Bausteine erscheinen passend zum gesprochenen Text, Musik leise darunter (Ducking).

Jedes Reel in reels/warteschlange.json braucht dafür ein Feld "sprecher": eine Liste mit einem gesprochenen Text je
Szene (gleiche Reihenfolge wie "szenen"). Ergebnis: reels/fertig/<id>.mp4 + .jpg, im Eintrag "fertig_video" /
"fertig_titelbild" gesetzt – reel_post.py veröffentlicht dann genau dieses Video.

Aufruf: python reel_vertont.py <reel_id> [<reel_id> ...]   (ElevenLabs-Schlüssel kommt über den Netzwerk-Proxy)
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

import reel_anim as ra
import reel_design as rd
import topjob_video as tv

HIER = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, SR = tv.W, tv.H, tv.FPS, tv.SR
VOR, NACH, ABSPANN = 0.3, 0.25, 1.8
MIN_QUOTE = 0.85         # Anteil der erkannten Skriptwörter; darunter wird neu angefordert (Wort ausgelassen)


def sprechen(sprich, cache, versuche=3):
    """Wie topjob_video.sprich_abschnitt, aber fordert neu an, wenn die Stimme Wörter auslässt."""
    import hashlib
    beste = None
    for v in range(versuche):
        text = sprich if v == 0 else sprich + " " * v          # anderer Cache-Schlüssel, gleicher gesprochener Text
        erg = tv.sprich_abschnitt(text, cache)
        if beste is None or erg[3] > beste[3]:
            beste = erg
        if erg[3] >= MIN_QUOTE:
            break
        print(f"  Quote {erg[3]:.0%} zu niedrig, neuer Versuch")
    return beste


def _finde(woerter, text, ab=0, sonst=None):
    """Index des ersten gesprochenen Worts ab `ab`, das mit dem ersten sinntragenden Wort von `text` beginnt."""
    kandidaten = [tv._norm(w) for w in str(text).split() if len(tv._norm(w)) >= 3] or [tv._norm(str(text))]
    for ziel in kandidaten[:2]:
        for i in range(ab, len(woerter)):
            if tv._norm(woerter[i])[:5] == ziel[:5]:
                return i
    return sonst if sonst is not None else ab


def ausloeser(s, woerter, n_eff):
    """Wortindex je Baustein, passend zu dem, was gerade gesprochen wird (Reihenfolge wie reel_anim._szene)."""
    n = len(woerter)
    gleich = lambda bis: [round(i * (n - 1) * bis / max(1, n_eff - 1)) for i in range(n_eff)]
    typ = s["typ"]
    if typ == "hook":
        idx, ab = [0], 0
        for z in s["zeilen"]:
            ab = _finde(woerter, z, ab, ab)
            idx.append(ab)
        u = _finde(woerter, s["unterzeile"], ab, min(n - 1, ab + 1))
        idx += [u, min(n - 1, u + 1)]
    elif typ == "vergleich":
        schlecht = _finde(woerter, s["schlecht"], 0, 1)
        gut = _finde(woerter, s.get("label_gut", "Besser"), schlecht + 1, -1)
        if gut < 0:
            gut = _finde(woerter, s["gut"], schlecht + 1, round(n * 0.45))
        detail = _finde(woerter, s["detail"], gut + 2, min(n - 1, gut + max(2, len(s["gut"].split()))))
        idx = [0, schlecht, max(schlecht, gut - 1), gut, detail]
    elif typ == "zahl":
        lab = _finde(woerter, s["label"], 0, round(n * 0.3))
        rest = n_eff - 4
        idx = [0, 0, lab] + [min(n - 1, lab + 2 + k * 2) for k in range(rest)] + [n - 1]
    elif typ == "chat":
        idx = gleich(0.7)
    else:
        idx = gleich(0.6)
    idx = (idx + [idx[-1]] * n_eff)[:n_eff]
    return [min(n - 1, max(0, i)) for i in idx]


def erzeuge(r, ziel, titelbild=None):
    kat = r.get("kategorie", "personal")
    szenen = r["szenen"]
    if len(r.get("sprecher", [])) != len(szenen):
        raise ValueError(f"{r['id']}: 'sprecher' braucht genau einen Text je Szene ({len(szenen)}).")
    cache = os.path.join(HIER, "vorschau", "reels-vertont", "ton")
    rd.KORN = 3
    tmp = tempfile.mkdtemp()
    plan, t = [], 0.0
    for si, (s, sprich) in enumerate(zip(szenen, r["sprecher"])):
        sz = ra._szene(s, kat)
        ton, woerter, zeiten, quote = sprechen(sprich, cache)
        sprech = len(ton) / SR
        ende = sz["fn"] is rd.folie_ende
        dauer = VOR + sprech + (ABSPANN if ende else NACH)
        idx = ausloeser(s, woerter, len(sz["effekte"]))
        trig = [max(0.0, VOR + zeiten[k][0] - 0.12) for k in idx]
        plan.append(dict(fn=sz["fn"], kw=dict(sz["kwargs"], szene=si, anzahl=len(szenen)), effekte=[e for e, _ in sz["effekte"]],
                         start=t, ton=ton, woerter=woerter, zeiten=zeiten, quote=quote, dauer=dauer, sprech=sprech,
                         trigger=trig, ende=ende, sprich=sprich))
        t += dauer
    gesamt = t
    n = int(round(gesamt * FPS)) * SR // FPS
    stimme, maske = np.zeros(n, np.float32), np.zeros(n, bool)
    for p in plan:
        a = int((p["start"] + VOR) * SR)
        stimme[a:a + len(p["ton"])] += p["ton"][: n - a]
        maske[a:a + len(p["ton"])] = True
    sprech_ende = plan[-1]["start"] + VOR + plan[-1]["sprech"]
    tonpfad = tv._musik_mix(stimme, maske, sprech_ende, gesamt, tmp)

    probleme = []
    for p in plan:
        p["grund"], p["ebenen"] = ra._ebenen(p["fn"], p["kw"], len(p["effekte"]))
        for k, e in enumerate(p["ebenen"]):
            if e and e[1][3] > tv.UT_OBEN - 5 and not p["ende"]:
                probleme.append(f"Szene {p['kw']['szene'] + 1} Baustein {k + 1} reicht ins Untertitel-Band ({e[1]})")
        p["bloecke"] = tv.ut_bloecke(p["woerter"])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", tonpfad, "-map", "0:v", "-map", "1:a", "-shortest", "-c:v", "libx264", "-preset", "slow",
           "-crf", "19", "-g", "60", "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-ar", "48000", "-movflags", "+faststart", ziel]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    titel = None
    for si, p in enumerate(plan):
        for i in range(int(round(p["dauer"] * FPS))):
            tl = i / FPS
            z = 1.0 + 0.02 * (tl / p["dauer"]) + 0.03 * (1 - ra._ease(tl / 0.3))
            cw, ch = int(W / z), int(H / z)
            x, y = (W - cw) // 2, (H - ch) // 2
            frame = p["grund"].crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
            for eff, trig, eb in zip(p["effekte"], p["trigger"], p["ebenen"]):
                ra._zeige(frame, eb, eff, (tl - trig) / (0.7 if eff == "wisch" else 0.4))
            ra._fortschritt(frame, si, len(plan), tl / p["dauer"])
            if not p["ende"]:
                rd.logo_marke(frame)
            rel = tl - VOR
            if -0.05 <= rel <= p["sprech"] + 0.3:
                aktiv = max([k for k, (a, _) in enumerate(p["zeiten"]) if a <= rel] or [0])
                block = next(b for b in p["bloecke"] if any(aktiv in zl for zl in b))
                tv.zeichne_untertitel(frame, p["woerter"], block, aktiv if rel <= p["zeiten"][-1][1] + 0.05 else -1)
            if si == 0 and titel is None and tl >= p["dauer"] - 0.1:
                titel = frame.copy()
            proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg-Fehler")
    if titelbild and titel is not None:
        titel.convert("RGB").save(titelbild, "JPEG", quality=92)
    text = " ".join(tv.anzeige_text(p["sprich"]) for p in plan)
    return dict(ziel=ziel, gesamt=round(gesamt, 1), probleme=sorted(set(probleme)), text=text,
                zeichen=sum(len(p["sprich"]) for p in plan), quoten=[round(p["quote"], 2) for p in plan])


def main(ids):
    pfad = os.path.join(HIER, "reels", "warteschlange.json")
    q = json.load(open(pfad, encoding="utf-8"))
    os.makedirs(os.path.join(HIER, "reels", "fertig"), exist_ok=True)
    for r in q:
        if r["id"] not in ids:
            continue
        ziel = os.path.join(HIER, "reels", "fertig", r["id"] + ".mp4")
        info = erzeuge(r, ziel, ziel.replace(".mp4", ".jpg"))
        print(json.dumps(info, ensure_ascii=False, indent=1))
        r["fertig_video"] = f"reels/fertig/{r['id']}.mp4"
        r["fertig_titelbild"] = f"reels/fertig/{r['id']}.jpg"
    json.dump(q, open(pfad, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(pfad, "a").write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
