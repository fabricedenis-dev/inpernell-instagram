#!/usr/bin/env python3
"""Inpernell – Instagram-Statistik auslesen (nur lesen, nichts veröffentlichen).

Gibt Konto- und Beitragszahlen als JSON aus. Im Workflow wird die Ausgabe verschlüsselt (öffentliches Repo:
die Zahlen sollen nicht offen im Protokoll stehen). Umgebungsvariablen wie agent.py: IG_ACCESS_TOKEN, IG_USER_ID.
"""
import json
import os
import sys
import time
import urllib.parse

import agent

METRIKEN = {
    "REELS": ["reach", "views", "likes", "comments", "saved", "shares", "total_interactions",
              "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"],
    "FEED": ["reach", "views", "likes", "comments", "saved", "shares", "total_interactions"],
    "STORY": ["reach", "views", "replies", "shares", "total_interactions", "navigation"],
}


def hole(basis, pfad, token, **params):
    return agent.http(f"{basis}/{pfad}?" + urllib.parse.urlencode({**params, "access_token": token}), versuche=1)


def insights(basis, media_id, token, metriken):
    erg, fehler = {}, []
    try:
        d = hole(basis, f"{media_id}/insights", token, metric=",".join(metriken))
        for m in d.get("data", []):
            erg[m["name"]] = (m.get("values") or [{}])[0].get("value", m.get("total_value", {}).get("value"))
        return erg, fehler
    except Exception:
        pass
    for m in metriken:                      # einzeln, falls eine Kennzahl nicht erlaubt ist
        try:
            d = hole(basis, f"{media_id}/insights", token, metric=m)
            for x in d.get("data", []):
                erg[x["name"]] = (x.get("values") or [{}])[0].get("value", x.get("total_value", {}).get("value"))
        except Exception as e:
            fehler.append(f"{m}: {str(e)[:120]}")
    return erg, fehler


def main():
    token = os.environ["IG_ACCESS_TOKEN"].strip()
    basis, ig_id, name = agent.instagram_konto(token)
    out = {"konto": name, "abgerufen": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}
    out["profil"] = hole(basis, ig_id, token, fields="followers_count,follows_count,media_count")
    konto = {}
    jetzt = int(time.time())
    for m in ["reach", "views", "accounts_engaged", "total_interactions", "profile_links_taps", "follows_and_unfollows",
              "profile_views", "website_clicks"]:
        try:
            d = hole(basis, f"{ig_id}/insights", token, metric=m, period="day", metric_type="total_value",
                     since=jetzt - 7 * 86400, until=jetzt)
            konto[m] = [x.get("total_value") for x in d.get("data", [])]
        except Exception as e:
            konto[m] = f"Fehler: {str(e)[:120]}"
    out["konto_7_tage"] = konto
    beitraege = []
    media = hole(basis, f"{ig_id}/media", token, limit=30,
                 fields="id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count")
    for m in media.get("data", []):
        art = "REELS" if m.get("media_product_type") == "REELS" else "FEED"
        werte, fehler = insights(basis, m["id"], token, METRIKEN[art])
        beitraege.append({"id": m["id"], "zeit": m.get("timestamp"), "art": art, "typ": m.get("media_type"),
                          "titel": (m.get("caption") or "").split("\n")[0][:90], "likes": m.get("like_count"),
                          "kommentare": m.get("comments_count"), "insights": werte, "fehler": fehler})
    out["beitraege"] = beitraege
    stories = []
    try:
        for s in hole(basis, f"{ig_id}/stories", token, fields="id,timestamp,media_type").get("data", []):
            werte, fehler = insights(basis, s["id"], token, METRIKEN["STORY"])
            stories.append({"id": s["id"], "zeit": s.get("timestamp"), "insights": werte, "fehler": fehler})
    except Exception as e:
        stories = f"Fehler: {str(e)[:120]}"
    out["stories_aktiv"] = stories
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
