"""Poster-Figuren im Neon-Sunset-Look: Silhouette aus dem freigestellten Foto, Helligkeit in 5 Farbstufen
(Violett, Magenta, Koralle, Orange, Hellgelb), Tuschelinien, türkises Kantenlicht. Ohne Weichzeichner im Ergebnis."""
import cv2
import numpy as np
from PIL import Image

STUFEN = [(0.20, (38, 8, 62)), (0.38, (150, 30, 120)), (0.55, (238, 84, 110)), (0.70, (255, 140, 80)),
          (0.84, (255, 196, 110)), (1.01, (255, 238, 190))]


def poster(pfad, hoehe=1100, kante=(40, 230, 230)):
    p = Image.open(pfad).convert("RGBA")
    p = p.crop(p.getbbox())
    p = p.resize((int(p.width * hoehe / p.height), hoehe), Image.LANCZOS)
    arr = np.array(p)
    maske = (arr[..., 3] > 128).astype(np.uint8)
    rgb = arr[..., :3].copy()
    for _ in range(5):
        rgb = cv2.bilateralFilter(rgb, 9, 45, 9)
    l = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32) / 255
    werte = l[maske > 0]
    lo, hi = np.percentile(werte, 3), np.percentile(werte, 97)
    l = np.clip((l - lo) / max(1e-3, hi - lo), 0, 1)
    l = cv2.medianBlur((l * 255).astype(np.uint8), 7).astype(np.float32) / 255     # Flächen beruhigen
    out = np.zeros_like(rgb)
    untere = 0
    for grenze, farbe in STUFEN:
        out[(l >= untere) & (l < grenze)] = farbe
        untere = grenze
    grau = cv2.medianBlur(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), 5)
    linien = cv2.adaptiveThreshold(grau, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 13, 7)
    out[(linien == 0) & (maske > 0)] = (24, 6, 40)
    innen = cv2.erode(maske, np.ones((9, 9), np.uint8))
    rand_r = (maske - cv2.erode(np.roll(maske, 16, axis=1) * maske, np.ones((3, 3), np.uint8))) * innen
    out[rand_r > 0] = kante
    kontur = cv2.dilate(maske, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)))
    erg = np.zeros((*maske.shape, 4), np.uint8)
    erg[kontur > 0] = (20, 6, 36, 255)
    erg[maske > 0, :3] = out[maske > 0]
    erg[maske > 0, 3] = 255
    return Image.fromarray(erg, "RGBA")
