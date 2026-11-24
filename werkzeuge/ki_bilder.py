#!/usr/bin/env python3
"""Lokale Bild-KI (CPU) für Cartoon-Figuren und Hintergründe: DreamShaper 8 (CreativeML OpenRAIL-M, gewerblich
nutzbar) + LCM-LoRA (schnell, 6–8 Schritte). Kostenlos, ohne Konto. Freistellen der Figuren mit rembg.
Aufruf: python werkzeuge/ki_bilder.py <ausgabeordner> <auftrag.json>
auftrag.json: [{"name": "...", "prompt": "...", "breite": 512, "hoehe": 896, "seed": 1, "freistellen": true}, ...]"""
import json
import os
import sys
import time

import torch
from diffusers import LCMScheduler, StableDiffusionPipeline

STIL = ("2d cartoon illustration, modern meme cartoon animation style, clean bold outlines, vibrant flat colors, "
        "soft cel shading, high quality, ")
NEG = "photo, realistic, blurry, deformed hands, extra fingers, text, watermark, logo"


def main(ordner, auftrag):
    os.makedirs(ordner, exist_ok=True)
    torch.set_num_threads(os.cpu_count() or 4)
    pipe = StableDiffusionPipeline.from_pretrained("Lykon/dreamshaper-8", torch_dtype=torch.float32,
                                                   safety_checker=None)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5")
    pipe.fuse_lora()
    rem = None
    for a in json.load(open(auftrag, encoding="utf-8")):
        ziel = os.path.join(ordner, a["name"] + ".png")
        if os.path.exists(ziel):
            continue
        t = time.time()
        img = pipe(STIL + a["prompt"], negative_prompt=NEG, num_inference_steps=a.get("schritte", 7),
                   guidance_scale=1.6, width=a.get("breite", 512), height=a.get("hoehe", 896),
                   generator=torch.Generator().manual_seed(a.get("seed", 1))).images[0]
        img.save(os.path.join(ordner, a["name"] + "_roh.png"))
        if a.get("freistellen"):
            if rem is None:
                from rembg import new_session, remove
                rem = (new_session("isnet-general-use"), remove)
            img = rem[1](img, session=rem[0])
        img.save(ziel)
        print(a["name"], round(time.time() - t), "s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
