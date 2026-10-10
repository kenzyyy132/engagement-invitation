"""
Derives the website's image layers from the original invitation artwork.

  python tools/build_assets.py

Requires: opencv-python-headless, numpy.
Input : assets/source/invitation-original.png   (never modified)
Output: assets/card/*  and  assets/og-image.jpg, assets/favicon.png

The arch on the artwork is a single flat colour (#576A59), so the lettering
can be lifted off as transparent layers and the arch re-filled underneath.
That lets the website animate each line of the real artwork independently.
"""
import json
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "source", "invitation-original.png")
OUT = os.path.join(ROOT, "assets", "card")
ARCH_BGR = np.array([89, 106, 87], dtype=np.float32)  # #576A59

# Boxes in original-artwork pixels: (x0, y0, x1, y1)
LAYERS = {
    "bismillah": (1150, 1050, 2700, 1435),
    "monogram": (1000, 1440, 2900, 3045),
    "invite": (940, 3190, 2960, 3460),
    "arabic": (1500, 3475, 2400, 3650),
    "november": (1600, 3700, 2320, 3900),
    "date-row": (770, 3940, 3120, 4200),
}
# Areas re-filled with the arch colour on the plate (lettering removed).
CLEAR = list(LAYERS.values()) + [(1120, 4320, 2785, 4645)]  # "FOR FULL DETAILS…" line

PLATE_WIDTHS = (1600, 900)
LAYER_SCALE = 1600 / 3875  # layers exported at the 1600px plate scale


def unmix(crop, fg_colours):
    """Return BGRA: alpha = coverage of the nearest foreground colour over the arch."""
    px = crop.astype(np.float32)
    d = px - ARCH_BGR
    best_a = np.zeros(px.shape[:2], np.float32)
    best_c = np.zeros_like(px)
    best_err = np.full(px.shape[:2], 1e9, np.float32)
    for fg in fg_colours:
        v = np.array(fg, np.float32) - ARCH_BGR
        a = np.clip((d @ v) / (v @ v), 0, 1)
        err = np.linalg.norm(d - a[..., None] * v, axis=2)
        pick = err < best_err
        best_err[pick], best_a[pick] = err[pick], a[pick]
        best_c[pick] = fg
    alpha = np.where(best_a < 0.04, 0, best_a)
    return np.dstack([best_c, alpha * 255]).astype(np.uint8)


def drop_border_specks(rgba):
    """Remove small fragments of neighbouring artwork (e.g. a vine tip) caught at the crop's edge."""
    solid = (rgba[..., 3] > 20).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(solid, connectivity=8)
    h, w = solid.shape
    total = max(1, solid.sum())
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        touches = x == 0 or y == 0 or x + bw >= w or y + bh >= h
        if touches and area < 0.02 * total:
            rgba[labels == i, 3] = 0
    return rgba


def fg_colour(crop):
    """Typical lettering colour: the brightest few percent of the crop."""
    px = crop.reshape(-1, 3).astype(np.float32)
    lum = px.sum(1)
    return px[lum >= np.percentile(lum, 98)].mean(0)


def scaled(img, scale):
    h, w = img.shape[:2]
    return cv2.resize(img, (max(1, round(w * scale)), max(1, round(h * scale))), interpolation=cv2.INTER_AREA)


def main():
    art = cv2.imread(SRC, cv2.IMREAD_COLOR)
    if art is None:
        sys.exit(f"Cannot read {SRC}")
    H, W = art.shape[:2]
    os.makedirs(OUT, exist_ok=True)
    meta = {"width": W, "height": H, "layers": {}}

    for name, (x0, y0, x1, y1) in LAYERS.items():
        crop = art[y0:y1, x0:x1]
        if name == "monogram":
            white = fg_colour(crop)
            taupe = np.array([160, 177, 190], np.float32)  # #BEB1A0 (BGR)
            rgba = drop_border_specks(unmix(crop, [white, taupe]))
            # split into the W (white) and M (taupe) so they can animate separately
            is_taupe = (np.abs(rgba[..., :3].astype(int) - taupe).sum(2) < 5)
            w_layer, m_layer = rgba.copy(), rgba.copy()
            w_layer[is_taupe, 3] = 0
            m_layer[~is_taupe, 3] = 0
            cv2.imwrite(os.path.join(OUT, "monogram-w.png"), scaled(w_layer, LAYER_SCALE))
            cv2.imwrite(os.path.join(OUT, "monogram-m.png"), scaled(m_layer, LAYER_SCALE))
            cv2.imwrite(os.path.join(OUT, "monogram.png"), scaled(rgba, LAYER_SCALE))
            cv2.imwrite(os.path.join(OUT, "monogram-large.png"), scaled(rgba, 0.5))
        else:
            rgba = drop_border_specks(unmix(crop, [fg_colour(crop)]))
            cv2.imwrite(os.path.join(OUT, f"{name}.png"), scaled(rgba, LAYER_SCALE))
        meta["layers"][name] = {
            "left": round(x0 / W * 100, 3), "top": round(y0 / H * 100, 3),
            "width": round((x1 - x0) / W * 100, 3), "height": round((y1 - y0) / H * 100, 3),
        }

    plate = art.copy()
    for x0, y0, x1, y1 in CLEAR:
        plate[y0:y1, x0:x1] = ARCH_BGR.astype(np.uint8)
    for w in PLATE_WIDTHS:
        cv2.imwrite(os.path.join(OUT, f"plate-{w}.webp"), scaled(plate, w / W), [cv2.IMWRITE_WEBP_QUALITY, 86])
        cv2.imwrite(os.path.join(OUT, f"invitation-{w}.webp"), scaled(art, w / W), [cv2.IMWRITE_WEBP_QUALITY, 88])
    cv2.imwrite(os.path.join(OUT, "invitation-1600.jpg"), scaled(art, 1600 / W), [cv2.IMWRITE_JPEG_QUALITY, 88])

    # Open Graph image (1200x630): artwork centred on the card's own stone colour
    og = np.full((630, 1200, 3), (216, 219, 218), np.uint8)
    card = scaled(art, 600 / H)
    ox = (1200 - card.shape[1]) // 2
    og[15:15 + card.shape[0], ox:ox + card.shape[1]] = card
    cv2.imwrite(os.path.join(ROOT, "assets", "og-image.jpg"), og, [cv2.IMWRITE_JPEG_QUALITY, 86])

    # Favicon: the monogram on the arch green
    mono = cv2.imread(os.path.join(OUT, "monogram-large.png"), cv2.IMREAD_UNCHANGED)
    icon = np.zeros((512, 512, 4), np.uint8)
    cv2.circle(icon, (256, 256), 255, (*ARCH_BGR.astype(int).tolist(), 255), -1, cv2.LINE_AA)
    m = scaled(mono, 380 / max(mono.shape[:2]))
    my, mx = (512 - m.shape[0]) // 2, (512 - m.shape[1]) // 2
    roi = icon[my:my + m.shape[0], mx:mx + m.shape[1]].astype(np.float32)
    a = m[..., 3:4].astype(np.float32) / 255
    roi[..., :3] = roi[..., :3] * (1 - a) + m[..., :3] * a
    icon[my:my + m.shape[0], mx:mx + m.shape[1]] = roi.astype(np.uint8)
    cv2.imwrite(os.path.join(ROOT, "assets", "favicon.png"), scaled(icon, 192 / 512))
    cv2.imwrite(os.path.join(ROOT, "assets", "apple-touch-icon.png"), scaled(icon, 180 / 512))

    # Background tile: the card's own leaf/loop pattern, mirrored so it repeats seamlessly
    patch = art[0:370, 0:1350]
    row = np.hstack([patch, patch[:, ::-1]])
    tile = np.vstack([row, row[::-1]])
    cv2.imwrite(os.path.join(ROOT, "assets", "pattern.webp"), scaled(tile, 0.4), [cv2.IMWRITE_WEBP_QUALITY, 80])

    # Garlands: the florals growing along the arch's left and right edges.
    # Their inner edge is the arch edge, so on the site they sit flush against arch panels.
    for name, (x0, y0, x1, y1), inner in (
        ("garland-left", (0, 1530, 494, 4420), "right"),
        ("garland-right", (3374, 770, 3875, 4530), "left"),
    ):
        crop = art[y0:y1, x0:x1]
        h, w = crop.shape[:2]
        fy = np.clip(np.minimum(np.arange(h), h - 1 - np.arange(h)) / (0.12 * h), 0, 1)
        dx = np.arange(w) if inner == "right" else (w - 1 - np.arange(w))
        fx = np.clip(dx / (0.35 * w), 0, 1)  # fade toward the outer (page) edge only
        alpha = (np.outer(fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)) * 255).astype(np.uint8)
        rgba = np.dstack([crop, alpha])
        cv2.imwrite(os.path.join(OUT, f"{name}.webp"), scaled(rgba, 0.32), [cv2.IMWRITE_WEBP_QUALITY, 84])

    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
