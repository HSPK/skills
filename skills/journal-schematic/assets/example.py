# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""Smoke test for the packaged kit: builds a tiny figure using only assets."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import svgkit as k

DEFS = k.load_defs(markers={"m1": k.OUTC})

s = k.Svg(120)
H = 74.0
s.rect(6, 6, s.w - 12, H - 12, rx=4, fill=k.tint(k.G1C, 0.9))
s.sicon("chart", 20, 24, 14, k.G1C, 1.0)
s.text(32, 21, "Exposure \u22656 h/d", 7.0, 700, k.INK)
s.text(32, 31, " ".join(k.wrap("wrapped caption text for the widow rule", 6.0, 120)), 6.0, 400, k.INK)
s.arrow(250, 24, 40, "right", k.OUTC, 5.4, 14.0, 9.5)
s.pill(320, 24, "Outcome", 7.0, 700, k.OUTC)

out = Path(__file__).parent / "_smoke.svg"
out.write_text(s.render(H, DEFS, "smoke test"), encoding="utf-8")
print("ok:", out, out.stat().st_size, "bytes,", s.render(H, DEFS, "x").count("<text"), "text runs")
