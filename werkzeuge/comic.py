import cv2, numpy as np
from PIL import Image
PINK = np.array([255, 60, 170]); TUERKIS = np.array([40, 230, 230])

def comic(pfad, hoehe=1100, farben=9):
    p = Image.open(pfad).convert("RGBA"); p = p.crop(p.getbbox())
    p = p.resize((int(p.width * hoehe / p.height), hoehe), Image.LANCZOS)
    a = np.array(p)[..., 3]; maske = (a > 128).astype(np.uint8)
    rgb = np.array(p)[..., :3].copy()
    # flächig glätten (Kanten bleiben scharf)
    glatt = rgb.copy()
    for _ in range(4): glatt = cv2.bilateralFilter(glatt, 9, 40, 9)
    # Cel-Shading: auf wenige Farben reduzieren (nur Person)
    px = glatt[maske > 0].reshape(-1, 3).astype(np.float32)
    _, lab, zentren = cv2.kmeans(px, farben, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 3, cv2.KMEANS_PP_CENTERS)
    zentren = zentren.astype(np.float32)
    # Farbstimmung: Schatten Richtung Violett/Navy, Lichter warm, kräftiger
    hsv = cv2.cvtColor(zentren.reshape(1, -1, 3).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.35 + 10, 0, 255)
    zentren = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).reshape(-1, 3).astype(np.float32)
    hell = zentren.mean(axis=1, keepdims=True) / 255
    zentren = zentren * (0.75 + 0.35 * hell) + (1 - hell) * np.array([40, 10, 70]) * 0.6
    cel = glatt.copy(); cel[maske > 0] = np.clip(zentren[lab.flatten()], 0, 255).astype(np.uint8)
    # Tuschelinien
    grau = cv2.cvtColor(glatt, cv2.COLOR_RGB2GRAY); grau = cv2.medianBlur(grau, 5)
    linien = cv2.adaptiveThreshold(grau, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 6)
    linien = cv2.erode(linien, np.ones((2, 2), np.uint8))
    cel[(linien == 0) & (maske > 0)] = (24, 14, 40)
    # Neon-Kantenlicht: links pink, rechts türkis
    innen = cv2.erode(maske, np.ones((9, 9), np.uint8))
    rand_l = (maske - cv2.erode(np.roll(maske, -14, axis=1) * maske, np.ones((3, 3), np.uint8))) * innen
    rand_r = (maske - cv2.erode(np.roll(maske, 14, axis=1) * maske, np.ones((3, 3), np.uint8))) * innen
    for rmask, farbe in ((rand_l, PINK), (rand_r, TUERKIS)):
        cel[rmask > 0] = (cel[rmask > 0] * 0.25 + farbe * 0.75).astype(np.uint8)
    # dicke Außenkontur
    kontur = cv2.dilate(maske, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19)))
    out = np.zeros((*maske.shape, 4), np.uint8)
    out[kontur > 0] = (20, 10, 36, 255)
    out[maske > 0, :3] = cel[maske > 0]; out[maske > 0, 3] = 255
    return Image.fromarray(out, "RGBA")

if __name__ == "__main__":
    import sys
    web = sys.argv[1]
    ims = [comic(f"{web}/{n}_frei.png", 700) for n in ("fabrice", "pascal", "waldemar")]
    b = Image.new("RGBA", (sum(i.width for i in ims) + 40, 720), (60, 20, 90, 255))
    x = 10
    for i in ims: b.alpha_composite(i, (x, 10)); x += i.width + 10
    b.convert("RGB").save(f"{web}/comic_test.jpg", quality=90)
