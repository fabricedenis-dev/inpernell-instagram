"""Gemalter Illustrations-Look (Ladebildschirm-Stimmung), Gesichtszüge bleiben unverändert:
leichtes kantenerhaltendes Glätten, kräftigere Farben, Sunset-Farbstimmung, Außenkontur und Kantenlicht."""
import cv2
import numpy as np


def illustriere(rgb, maske):
    x = cv2.bilateralFilter(rgb, 7, 22, 5)
    hsv = cv2.cvtColor(x, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.22, 0, 255)
    x = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
    l = x.mean(axis=2, keepdims=True) / 255
    x = x + (1 - l) * np.array([30, -10, 45]) * 0.6 + l * np.array([18, 4, -14]) * 0.6   # Schatten violett, Lichter warm
    x = np.clip(x, 0, 255).astype(np.uint8)
    m = maske.astype(bool)
    links = m & ~np.roll(m, 7, axis=1)
    rechts = m & ~np.roll(m, -7, axis=1)
    x[links] = (x[links] * 0.35 + np.array([255, 80, 170]) * 0.65).astype(np.uint8)
    x[rechts] = (x[rechts] * 0.35 + np.array([40, 230, 230]) * 0.65).astype(np.uint8)
    kontur = cv2.dilate(maske.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    erg = np.zeros((*maske.shape, 4), np.uint8)
    erg[kontur > 0] = (20, 6, 36, 255)
    erg[m, :3] = x[m]; erg[m, 3] = 255
    return erg
