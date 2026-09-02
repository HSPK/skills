# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "numpy"]
# ///
"""Scan the rendered figure for vertical/horizontal rules and report their
positions in points, so alignment can be checked numerically rather than by eye."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
W_PT = 180.0 * 72 / 25.4


def runs(idx: np.ndarray) -> list[tuple[float, float]]:
    """Group adjacent indices into (centre, length) runs."""
    out, start = [], None
    for i in range(len(idx)):
        if start is None:
            start = idx[i]
        if i + 1 == len(idx) or idx[i + 1] != idx[i] + 1:
            out.append(((start + idx[i]) / 2, idx[i] - start + 1))
            start = None
    return out


def main(path: str) -> None:
    im = Image.open(path).convert("L")
    a = np.asarray(im)
    h, w = a.shape
    scale = w / W_PT
    dark = a < 200

    v = dark.sum(axis=0)
    hz = dark.sum(axis=1)
    vlines = [c for c, _ in runs(np.flatnonzero(v > h * 0.20))]
    hlines = [c for c, _ in runs(np.flatnonzero(hz > w * 0.30))]

    print(f"{path}: {w}x{h}px, {scale:.4f} px/pt\n")
    print("vertical rules (pt):  ", ", ".join(f"{c / scale:7.2f}" for c in vlines))
    print("horizontal rules (pt):", ", ".join(f"{c / scale:7.2f}" for c in hlines))

    if len(vlines) >= 2:
        left, right = vlines[0] / scale, vlines[-1] / scale
        centre = (left + right) / 2
        print(f"\nouter frame: {left:.2f} .. {right:.2f}   centre {centre:.2f}")
        for c in vlines:
            pt = c / scale
            print(f"  x={pt:7.2f}   offset from centre {pt - centre:+8.2f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "_render.png"))
