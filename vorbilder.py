#!/usr/bin/env python3
"""Inpernell – öffentliche Beiträge anderer Business-/Creator-Konten lesen (Instagram „Business Discovery“).
Nur lesen. Speichert je Konto Kennzahlen und Bildtexte der letzten Beiträge als JSON (data/vorbilder/<konto>.json)
und lädt Vorschaubilder in einen Arbeitsordner (im Workflow als kurzlebiges Artefakt, NICHT im Repository –
die Bilder gehören den Urhebern und werden nur angesehen, nie veröffentlicht).
Aufruf: python vorbilder.py [konto ...]  (ohne Angabe: data/vorbilder/konten.txt)"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import agent

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HIER, "data", "vorbilder")
BILDER = os.path.join(HIER, "vorbilder_bilder")
FELDER = ("username,name,biography,followers_count,media_count,"
          "media.limit(50){id,caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink,"
          "media_url,thumbnail_url}")


def lesen(basis, ig_id, token, konto):
    q = urllib.parse.urlencode({"fields": f"business_discovery.username({konto}){{{FELDER}}}", "access_token": token})
    return agent.http(f"{basis}/{ig_id}?{q}", versuche=2)["business_discovery"]


def main(konten):
    token = os.environ["IG_ACCESS_TOKEN"].strip()
    basis, ig_id, _ = agent.instagram_konto(token)
    os.makedirs(ZIEL, exist_ok=True)
    fehler = 0
    for konto in konten:
        try:
            bd = lesen(basis, ig_id, token, konto)
        except Exception as e:
            print(f"::warning::{konto}: nicht lesbar (nur Business-/Creator-Konten sind möglich): {str(e)[:160]}")
            fehler += 1
            continue
        beitraege = []
        os.makedirs(os.path.join(BILDER, konto), exist_ok=True)
        for i, m in enumerate(bd.get("media", {}).get("data", [])):
            beitraege.append({k: m.get(k) for k in ("timestamp", "media_type", "media_product_type", "like_count",
                                                     "comments_count", "permalink", "caption")})
            bild = m.get("thumbnail_url") or (m.get("media_url") if m.get("media_type") != "VIDEO" else None)
            if bild:
                try:
                    with urllib.request.urlopen(urllib.request.Request(bild, headers={"User-Agent": "inpernell/1.0"}),
                                                timeout=60) as r:
                        open(os.path.join(BILDER, konto, f"{i:02d}.jpg"), "wb").write(r.read())
                except Exception:
                    pass
        # Optional: die beliebtesten Videos zum Ansehen/Analysieren laden (nur Artefakt, nie veröffentlichen)
        n_vid = int(os.environ.get("VIDEOS", "0") or 0)
        if n_vid:
            vids = [m for m in bd.get("media", {}).get("data", []) if m.get("media_type") == "VIDEO" and m.get("media_url")]
            vids.sort(key=lambda m: m.get("like_count") or 0, reverse=True)
            for j, m in enumerate(vids[:n_vid]):
                try:
                    with urllib.request.urlopen(urllib.request.Request(m["media_url"],
                                                                       headers={"User-Agent": "inpernell/1.0"}),
                                                timeout=120) as r:
                        open(os.path.join(BILDER, konto, f"video_{j:02d}_{m.get('like_count') or 0}likes.mp4"),
                             "wb").write(r.read())
                except Exception as e:
                    print(f"::warning::{konto}: Video {j} nicht ladbar: {str(e)[:120]}")
            print(f"{konto}: {min(n_vid, len(vids))} Videos geladen ({len(vids)} mit Video-Adresse)")
        aus = {"konto": bd.get("username"), "name": bd.get("name"), "bio": bd.get("biography"),
               "follower": bd.get("followers_count"), "beitraege_gesamt": bd.get("media_count"),
               "abgerufen": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "beitraege": beitraege}
        json.dump(aus, open(os.path.join(ZIEL, f"{konto}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{konto}: {len(beitraege)} Beiträge gelesen")
    return 1 if fehler == len(konten) else 0


if __name__ == "__main__":
    k = sys.argv[1:] or [z.strip().lstrip("@") for z in open(os.path.join(ZIEL, "konten.txt"), encoding="utf-8")
                         if z.strip()]
    sys.exit(main(k))
