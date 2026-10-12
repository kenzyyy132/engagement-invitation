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
ARCH_SIDES = (497, 3377)  # x of the arch's straight sides, in artwork pixels
ARCH_TOP = 406            # y of the top of the dome

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


def arch_inset(xs, ys):
    """Signed distance (px) inside the card's arch: >0 inside, <0 outside."""
    x0, x1, top = ARCH_SIDES[0], ARCH_SIDES[1], ARCH_TOP
    r = (x1 - x0) / 2
    cx, cy = (x0 + x1) / 2, top + r
    sides = np.minimum(xs - x0, x1 - xs)
    dome = r - np.hypot(xs - cx, ys - cy)
    return np.where(ys >= cy, sides, np.minimum(dome, sides))


def garland_cutout(art, box):
    """BGRA cut-out of the florals in `box`, free of the stone background, the arch and its hairline."""
    x0, y0, x1, y1 = box
    crop = art[y0:y1, x0:x1]
    h, w = crop.shape[:2]
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    inset = arch_inset(xs, ys)
    inside = inset > 0

    lab = cv2.GaussianBlur(cv2.cvtColor(crop, cv2.COLOR_BGR2LAB).astype(np.float32), (0, 0), 2)
    L = lab[..., 0]
    chroma = np.hypot(lab[..., 1] - 128, lab[..., 2] - 128)
    # stone background: its median colour and the darker colour of its swirl lines
    ref = cv2.cvtColor(art[0:370, 1400:2400], cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    bg = np.median(ref, 0)
    line = ref[ref[:, 0] <= np.percentile(ref[:, 0], 1)].mean(0)
    v = line - bg
    t = np.clip(((lab - bg) @ v) / (v @ v), 0, 1.6)
    d_bg = np.linalg.norm(lab - (bg + t[..., None] * v), axis=2)
    d_arch = np.abs(crop.astype(np.float32) - ARCH_BGR).sum(2)
    hairline = inside & (inset > 110) & (inset < 152) & (L > 195) & (chroma < 14)
    # the card's pale strip just outside the arch edge
    edge_strip = ~inside & (inset > -45) & (chroma < 9) & (L > 165) & (L < 222)

    seed = np.where(inside, (d_arch > 40) & ~hairline, (d_bg > 13) | (L > 229.5)) & ~edge_strip
    seed = cv2.morphologyEx(seed.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    seed = cv2.morphologyEx(seed, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    seed = keep_large(seed, 3000, fill_below=60000)

    # GrabCut refines the colour-key seed (keeps whole petals whose shading nears the background)
    gc = np.where(seed > 0, cv2.GC_PR_FGD, cv2.GC_PR_BGD).astype(np.uint8)
    gc[np.where(inside, d_arch > 90, (d_bg > 28) | (L > 236))] = cv2.GC_FGD
    far = cv2.distanceTransform((1 - seed).astype(np.uint8), cv2.DIST_L2, 5) > 30
    gc[np.where(inside, d_arch < 12, far & (d_bg < 7) & (L < 227)) | hairline | edge_strip] = cv2.GC_BGD
    small = cv2.resize(crop, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    gc_s = cv2.resize(gc, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    cv2.grabCut(small, gc_s, None, np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_MASK)
    keep = cv2.resize(np.isin(gc_s, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8), (w, h), interpolation=cv2.INTER_LINEAR)
    keep[hairline | edge_strip | (inside & (d_arch < 12))] = 0
    keep = cv2.morphologyEx(keep, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    keep = keep_large(keep, 3000, fill_below=8000)

    alpha = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.6)
    alpha = np.clip((alpha - 0.15) / 0.85, 0, 1)
    fy = np.clip(np.minimum(np.arange(h), h - 1 - np.arange(h)) / (0.06 * h), 0, 1)
    alpha *= (fy * fy * (3 - 2 * fy))[:, None]  # stems fade out at the ends instead of stopping dead

    # un-mix the edge pixels from whatever they were blended with (arch or stone)
    stone = cv2.cvtColor(np.uint8([[bg]]), cv2.COLOR_LAB2BGR)[0, 0].astype(np.float32)
    under = np.where(inside[..., None], ARCH_BGR, stone)
    a = np.clip(alpha, 0.15, 1)[..., None]
    fg = np.where(alpha[..., None] < 0.98, (crop - under * (1 - a)) / a, crop)
    return np.dstack([np.clip(fg, 0, 255), alpha * 255]).astype(np.uint8)


def keep_large(mask, min_area, fill_below):
    """Drop specks smaller than min_area; fill enclosed holes smaller than fill_below."""
    n, lbl, st, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = np.zeros_like(mask)
    for i in range(1, n):
        if st[i, 4] >= min_area:
            out[lbl == i] = 1
    h, w = out.shape
    n, lbl, st, _ = cv2.connectedComponentsWithStats((1 - out).astype(np.uint8), connectivity=4)
    for i in range(1, n):
        x, y, bw, bh, area = st[i]
        if area < fill_below and x > 0 and y > 0 and x + bw < w and y + bh < h:
            out[lbl == i] = 1
    return out


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

    # Garlands: the florals growing along the arch's left and right edges, cut out
    # from the card's stone background (and from the arch itself) so only the
    # leaves and blossoms remain. "-arch" variants keep the foliage that spills
    # over the arch, for the message arch where they overlap its sides as on the card.
    for name, box in (
        ("garland-left", (0, 1530, 494, 4420)),
        ("garland-right", (3374, 770, 3875, 4530)),
        ("garland-left-arch", (0, 1530, 760, 4420)),
        ("garland-right-arch", (3100, 770, 3875, 4530)),
    ):
        rgba = garland_cutout(art, box)
        cv2.imwrite(os.path.join(OUT, f"{name}.webp"), scaled(rgba, 0.32), [cv2.IMWRITE_WEBP_QUALITY, 90])

    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
