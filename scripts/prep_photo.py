"""
Prep a portrait photo for make_ascii_svg.py. Run once per photo, locally --
the daily workflow never touches this.

A flatly-lit face converts to a dark, unreadable blob, so:
  1. isolate the subject -- rembg when it is installed, otherwise a flood fill
     of the near-white backdrop from the image border (good enough for studio
     shots on a plain white wall, and needs no model download)
  2. boost local contrast with CLAHE, then stretch the subject's levels so the
     face spans the whole ASCII ramp
  3. composite onto pure white, so the background maps to the blank glyph

Output: a grayscale PNG (source-prepped.png by default), cropped to the
subject with a little headroom.

usage: python scripts/prep_photo.py source-photo.jpg [--out PATH] [--no-rembg]
"""
import argparse
import os

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))

MAX_SIDE = 900         # working resolution; the ASCII grid is far coarser anyway
BG_THRESH = 228        # flood-fill fallback: gray >= this counts as backdrop
CLAHE_CLIP = 2.4
CLAHE_TILES = 8
STRETCH_LO, STRETCH_HI = 2, 98   # subject percentiles mapped to 0 / 255
PAD_FRAC = 0.04        # margin kept around the subject's bounding box


def subject_alpha(rgb, use_rembg):
    """Return a float mask in 0..1, 1 where the subject is."""
    if use_rembg:
        try:
            from rembg import remove
        except ImportError:
            print("rembg not installed -- falling back to the backdrop flood fill")
        else:
            rgba = np.array(remove(Image.fromarray(rgb)))
            return rgba[..., 3].astype(np.float32) / 255.0

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    light = (gray >= BG_THRESH).astype(np.uint8)
    _, labels = cv2.connectedComponents(light, connectivity=4)
    # only light regions that touch the border are backdrop; a white collar
    # enclosed by the jacket stays part of the subject
    edge = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    edge = np.unique(edge[edge > 0])
    backdrop = np.isin(labels, edge)
    alpha = (~backdrop).astype(np.float32)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.2)   # soften the cut edge
    return alpha


def prep(src, out, use_rembg):
    img = Image.open(src).convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    rgb = np.array(img)

    alpha = subject_alpha(rgb, use_rembg)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(CLAHE_TILES, CLAHE_TILES))
    g = clahe.apply(gray).astype(np.float32)

    subj = g[alpha > 0.5]
    if subj.size:
        lo, hi = np.percentile(subj, [STRETCH_LO, STRETCH_HI])
        g = np.clip((g - lo) / max(hi - lo, 1.0) * 255.0, 0, 255)

    g = g * alpha + 255.0 * (1.0 - alpha)

    ys, xs = np.nonzero(alpha > 0.5)
    if ys.size:
        h, w = g.shape
        pad = int(PAD_FRAC * max(h, w))
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, h)
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, w)
        g = g[y0:y1, x0:x1]

    Image.fromarray(g.astype(np.uint8), "L").save(out)
    print(f"wrote {out}  {g.shape[1]}x{g.shape[0]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "source-prepped.png"))
    ap.add_argument("--no-rembg", action="store_true", help="skip rembg, use the flood fill")
    a = ap.parse_args()
    prep(a.src, a.out, not a.no_rembg)


if __name__ == "__main__":
    main()
