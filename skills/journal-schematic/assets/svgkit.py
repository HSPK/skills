# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""Drawing kit for hand-generated print figures.

Everything is drawn at true print size: the SVG root carries a millimetre
width while the viewBox is in typographic points, so a `font-size` of 6.5 is
literally 6.5 pt on paper.

Copy this into the project and edit the palette to suit. Traced icons are read
from ICONS as single-path SVGs; call `load_defs([...])` once at module level
before any `fit_optical()`, since it populates RATIOS/VBOX as a side effect.
"""

from __future__ import annotations

import math
import re
from html import escape
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parent
ICONS = ROOT / "icons" / "svg"

MM = 72 / 25.4

# ---------------------------------------------------------------------- palette
# One hue per group, a neutral for furniture, and full-strength ink for all type
# at every size. Hierarchy comes from size and weight, never from grey.
INK = "#14171A"          # all type, at every size
PAPER = "#FFFFFF"

G1C = "#A3202E"          # group 1 — pick from the project's own branding
G2C = "#17646D"          # group 2 — a second hue, so group is a colour
OUTC = "#333B44"         # outcomes / results — neutral graphite
AXIS = "#8A9199"         # chart furniture only, never used for words

FONT_STACK = "Arial,Helvetica,'Helvetica Neue',sans-serif"

# Metrics only. The SVG always names the stack above and the renderer picks
# whatever it has; these files exist so tw() can measure. Liberation Sans is
# metric-compatible with Arial by design, so a Linux box measures the same
# widths a Windows box does.
_FONT_CANDIDATES = {
    400: [
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/LiberationSans-Regular.ttf",
    ],
    700: [
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/LiberationSans-Bold.ttf",
    ],
}


def _font_file(weight: int) -> str:
    for p in _FONT_CANDIDATES[weight]:
        if Path(p).exists():
            return p
    raise RuntimeError(
        f"no Arial-metric font found for weight {weight}. Install Arial or "
        f"Liberation Sans, or add the path to _FONT_CANDIDATES[{weight}]. "
        f"Every layout number in the figure comes from these metrics, so "
        f"substituting a font with different widths will silently misalign it."
    )


def mix(a: str, b: str, t: float) -> str:
    """Blend two hex colours; t=0 gives a, t=1 gives b."""
    ar, ag, ab = (int(a[i : i + 2], 16) for i in (1, 3, 5))
    br, bg, bb = (int(b[i : i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * t) for x, y in ((ar, br), (ag, bg), (ab, bb)))


def tint(c: str, t: float) -> str:
    return mix(c, PAPER, t)


# ------------------------------------------------------------------ text metrics
_cache: dict[tuple[int, int], ImageFont.FreeTypeFont] = {}


def _font(size: float, weight: int) -> ImageFont.FreeTypeFont:
    key = (round(size * 4), weight)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(_font_file(weight), max(1, round(size * 4)))
    return _cache[key]


def tw(s: str, size: float, weight: int = 400) -> float:
    return _font(size, weight).getlength(s) / 4


# ------------------------------------------------------------- slanted >= glyph
# Arial draws U+2265 as a slanted arm over a *horizontal* bar. The wholly
# slanted form is wanted instead, but no font shipped with Windows carries
# U+2A7E in both weights, and leaning on a symbol font would break the figure
# anywhere that font is absent. So it is drawn, with the same advance and ink
# box as Arial's glyph — text metrics are therefore unaffected and `tw` needs
# no special case.
GE = "\u2265"
_GE_ADV, _GE_X, _GE_W, _GE_H = 0.55, 0.035, 0.485, 0.65


def _ge_outlines(x: float, y: float, size: float, weight: int):
    """Left ink edge at x, baseline at y. Returns the chevron and the bar."""
    tv = size * (0.132 if weight >= 600 else 0.098)   # vertical stroke thickness
    gap = size * 0.075
    xl, xr = x, x + size * _GE_W
    ytop, ybot = y - size * _GE_H, y
    av = ((ybot - ytop) - tv - gap) / 2               # arm vertical half-span
    ymid = ytop + av
    notch = xl + (xr - xl) * (1 - tv / av)
    return [
        [(xl, ytop), (xr, ymid), (xl, ymid + av),
         (xl, ymid + av - tv), (notch, ymid), (xl, ytop + tv)],
        [(xl, ybot - tv), (xr, ybot - tv - av), (xr, ybot - av), (xl, ybot)],
    ]


def wrap(s: str, size: float, max_w: float, weight: int = 400) -> list[str]:
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and tw(trial, size, weight) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    # Widow control: a last line holding one short token — "(eHCI)", "(SDQ)" —
    # reads as a typo. Pull a word down to it, but only when the widow really is
    # short, or a two-word phrase would break as "Early / childhood development".
    if len(lines) > 1 and len(lines[-1].split()) == 1 and tw(lines[-1], size, weight) < max_w * 0.32:
        head = lines[-2].split()
        if len(head) > 1:
            lines[-2] = " ".join(head[:-1])
            lines[-1] = f"{head[-1]} {lines[-1]}"
    return lines


# ------------------------------------------------------------------ icon symbols
RATIOS: dict[str, tuple[float, float]] = {}
# Icons are defined as plain <g> and placed with a transform rather than as
# <symbol> scaled by width/height on <use>. The latter is SVG 2 and PowerPoint's
# importer ignores it, dropping every icon in at its native size; transforms are
# SVG 1.1 and universally understood. VBOX keeps each icon's own user space so
# the transform can undo it.
VBOX: dict[str, tuple[float, float, float, float]] = {}
# Path data and baked fill for the traced picture icons, so Svg.use() can inline
# them rather than reference a def.
PIC_D: dict[str, str] = {}
PIC_FILL: dict[str, str] = {}

# Hand-drawn line icons, all normalised to the same optical box on a 24x24 grid.
STROKE_ICONS: dict[str, str] = {
    "calendar": "M3.5 5.5h17v15.5h-17z M3.5 10.5h17 M8.5 3v5 M15.5 3v5 M8.3 15.4l2.6 2.6 4.8-4.8",
    "tally": "M3.5 20.5h17 M7.5 20.5V13 M12 20.5V8 M16.5 20.5V3.5",
    "repeat": "M16.5 2.5l4 4-4 4 M20.5 6.5H7.5a4 4 0 0 0-4 4v1.5 "
              "M7.5 21.5l-4-4 4-4 M3.5 17.5h13a4 4 0 0 0 4-4V12",
    "dyad": "M8.4 10.2a3.4 3.4 0 1 0 0-6.8 3.4 3.4 0 0 0 0 6.8z "
            "M3.2 20.6v-1.2a5.2 5.2 0 0 1 5.2-5.2 5.2 5.2 0 0 1 5.2 5.2v1.2 "
            "M17.2 12.4a2.4 2.4 0 1 0 0-4.8 2.4 2.4 0 0 0 0 4.8z "
            "M13.8 20.6v-1a3.4 3.4 0 0 1 3.4-3.4 3.4 3.4 0 0 1 3.4 3.4v1",
    "mind-heart": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z "
                  "M12 16.6c-2.4-1.9-4-3.3-4-5.1a2.1 2.1 0 0 1 4-1 "
                  "2.1 2.1 0 0 1 4 1c0 1.8-1.6 3.2-4 5.1z",
    "sprout": "M12 20.6V10.6 M5.5 20.6h13 "
              "M12 11.8C12 7.2 15.2 3.8 19.8 3.6c.3 4.6-3 8.2-7.8 8.2z "
              "M12 15.4C12 11.4 9 8.6 4.4 8.4c-.3 4 2.8 7 7.6 7z",
    "chart": "M3.5 3.5v17h17 M7 15.4l4.2-5.2 3.4 3.2 4.9-6.2",
    "device": "M6.5 3.2h11a1.6 1.6 0 0 1 1.6 1.6v14.4a1.6 1.6 0 0 1-1.6 1.6h-11a1.6 1.6 0 0 1-1.6-1.6V4.8a1.6 1.6 0 0 1 1.6-1.6z "
              "M4.9 7.2h14.2 M4.9 16.4h14.2 M10.4 18.6h3.2",
    "clock": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 7.2V12l3.4 2",
}

LOGO_CROP: dict[str, tuple[float, float]] = {}   # icon name -> (keep_w, keep_h)


def _crop_subpaths(d: str, w: float, h: float) -> str:
    """Drop whole subpaths that fall outside the crop box.

    A crop used to come free from <symbol viewBox>, which clips. A plain <g>
    does not, and clip-path is not something PowerPoint's importer can be
    trusted with, so artwork is cropped at the source instead — a logo's
    wordmark, for instance, is simply a set of subpaths below the mark. Traced
    icons use only absolute M/L/C/Z, so every number in a subpath is one
    coordinate of a pair.
    """
    keep = []
    for sub in re.split(r"(?=M)", d):
        if not sub.strip():
            continue
        n = [float(v) for v in re.findall(r"-?\d+\.?\d*", sub)]
        xs, ys = n[0::2], n[1::2]
        if min(xs) >= w or min(ys) >= h or max(xs) <= 0 or max(ys) <= 0:
            continue
        keep.append(sub)
    return "".join(keep)


def load_defs(
    pic_icons: tuple[str, ...] | list[str] = (),
    markers: dict[str, str] | None = None,
    crops: dict[str, tuple[float, float]] | None = None,
) -> str:
    """Build the <defs> block and populate RATIOS/VBOX as a side effect.

    `pic_icons` are traced single-path SVGs in ICONS. `crops` maps an icon name
    to the (width, height) of the region to keep. Call this at module level,
    before any fit_optical().
    """
    crops = crops or {}
    syms = []
    for name in pic_icons:
        raw = (ICONS / f"{name}.svg").read_text(encoding="utf-8")
        vb = re.search(r'viewBox="([\d.\s-]+)"', raw).group(1)
        d = re.search(r'\sd="([^"]+)"', raw).group(1)
        root_fill = re.search(r'<svg[^>]*\sfill="([^"]+)"', raw).group(1)
        mx, my, vw, vh = (float(v) for v in vb.split())
        if name in crops:
            mx, my = 0.0, 0.0
            vw, vh = crops[name]
            d = _crop_subpaths(d, vw, vh)
        RATIOS[name] = (vw, vh)
        VBOX[name] = (mx, my, vw, vh)
        PIC_D[name] = d
        PIC_FILL[name] = root_fill if root_fill != "currentColor" else INK

    # Picture icons are inlined at each use site too (see Svg.use): PowerPoint
    # does not inherit fill through <use> either, so a recoloured icon arrives
    # in the deck as flat black — or, worse, silently keeps the traced source
    # colour, which is the failure mode that hides longest.

    # Stroke icons are inlined at each use site (see Svg.sicon), not referenced
    # from defs, because PowerPoint does not inherit stroke through <use>. They
    # still need their ratios registered for fit_optical().
    for name in STROKE_ICONS:
        RATIOS[name] = (24.0, 24.0)
        VBOX[name] = (0.0, 0.0, 24.0, 24.0)

    for mid, colour in (markers or {}).items():
        syms.append(
            f'    <marker id="{mid}" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="5" '
            f'markerHeight="5" orient="auto-start-reverse">'
            f'<path d="M0 0.8 L10 5 L0 9.2 z" fill="{colour}"/></marker>'
        )
    return ("  <defs>\n" + "\n".join(syms) + "\n  </defs>") if syms else ""


def fit_optical(icon: str, area: float) -> tuple[float, float]:
    """Scale so every icon covers the same optical area rather than the same
    height — girl-child is wide (512x418) and woman-avatar is tall (358x512),
    so matching heights makes the daughter read ~75% larger."""
    vw, vh = RATIOS[icon]
    h = area / math.sqrt(vw / vh)
    return vw / vh * h, h


# ------------------------------------------------------------------- svg writer
class Svg:
    def __init__(self, w_mm: float) -> None:
        self.w_mm = w_mm
        self.w = w_mm * MM
        self.p: list[str] = []

    # -- primitives ---------------------------------------------------------
    def add(self, m: str) -> None:
        self.p.append("  " + m)

    def rect(self, x, y, w, h, rx=0, fill="none", stroke=None, sw=0.7, dash=None, op=None) -> None:
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' fill-opacity="{op}"' if op is not None else ""
        self.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{fill}"{o}{s}{d}/>')

    def line(self, x1, y1, x2, y2, stroke=INK, sw=0.7, dash=None, marker=None, cap="butt") -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = f' marker-end="url(#{marker})"' if marker else ""
        c = f' stroke-linecap="{cap}"' if cap != "butt" else ""
        self.add(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}{m}{c}/>'
        )

    def path(self, d, fill="none", stroke=None, sw=0.7, dash=None, cap="round", join="round", marker=None) -> None:
        s = f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}" stroke-linejoin="{join}"' if stroke else ""
        da = f' stroke-dasharray="{dash}"' if dash else ""
        m = f' marker-end="url(#{marker})"' if marker else ""
        self.add(f'<path d="{d}" fill="{fill}"{s}{da}{m}/>')

    def poly(self, pts, fill=INK, stroke=None, sw=0.7) -> None:
        d = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        s = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else ""
        self.add(f'<polygon points="{d}" fill="{fill}"{s}/>')

    def circle(self, cx, cy, r, fill=INK, stroke=None, sw=0.7) -> None:
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}"{s}/>')

    def text(self, x, y, s, size=6.5, weight=400, fill=INK, anchor="start", ls=None) -> None:
        if GE in s:
            # The line is laid out run by run, so the drawn glyph has to land
            # where PIL says it will. Browser metrics drift from PIL's by a
            # fraction of a percent, which over a dozen characters is enough to
            # swallow the space before the symbol, so each run is pinned with
            # textLength and the spaces around the symbol are advanced by hand.
            sp = tw(" ", size, weight)
            total = tw(s, size, weight)
            cx = x - (total / 2 if anchor == "middle" else total if anchor == "end" else 0)
            for run in re.split(f"({GE})", s):
                if not run:
                    continue
                if run == GE:
                    for pts in _ge_outlines(cx + size * _GE_X, y, size, weight):
                        self.poly(pts, fill)
                    cx += size * _GE_ADV
                    continue
                core = run.strip(" ")
                cx += (len(run) - len(run.lstrip(" "))) * sp
                if core:
                    w = tw(core, size, weight)
                    self._text(cx, y, core, size, weight, fill, "start", ls, w)
                    cx += w
                cx += (len(run) - len(run.rstrip(" "))) * sp
            return
        self._text(x, y, s, size, weight, fill, anchor, ls)

    def _text(self, x, y, s, size, weight, fill, anchor, ls, tl=None) -> None:
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        t = f' letter-spacing="{ls}"' if ls else ""
        n = f' textLength="{tl:.2f}" lengthAdjust="spacing"' if tl else ""
        self.add(
            f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT_STACK}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}"{a}{t}{n}>{escape(s)}</text>'
        )

    def use(self, icon, x, y, w, h, fill=None) -> None:
        # Inlined for the same reason as sicon(): PowerPoint's SVG importer does
        # not inherit presentation attributes from <use> into the referenced
        # content, so a recoloured icon arrives in the deck as flat black.
        mx, my, vw, vh = VBOX[icon]
        t = f"translate({x:.2f} {y:.2f}) scale({w / vw:.5f} {h / vh:.5f})"
        if mx or my:
            t += f" translate({-mx:.2f} {-my:.2f})"
        self.add(f'<path fill-rule="evenodd" fill="{fill or PIC_FILL[icon]}" '
                 f'd="{PIC_D[icon]}" transform="{t}"/>')

    def sicon(self, name, cx, cy, size, stroke=INK, weight=0.9) -> None:
        # Inlined rather than <use href="#si-...">: PowerPoint's SVG importer
        # does not inherit stroke/stroke-width from <use> into the referenced
        # content, so every stroke icon vanished in the PPTX export.
        k = size / 24.0
        self.add(
            f'<path d="{STROKE_ICONS[name]}" fill="none" stroke-linecap="round" '
            f'stroke-linejoin="round" stroke="{stroke}" stroke-width="{weight / k:.2f}" '
            f'transform="translate({cx - size / 2:.2f} {cy - size / 2:.2f}) scale({k:.5f})"/>'
        )

    # -- composites ---------------------------------------------------------
    def pill(self, cx, cy, label, size=7.0, weight=700, fill=INK, colour=PAPER, padx=6.0, h=11.0) -> float:
        w = tw(label, size, weight) + padx * 2
        self.rect(cx - w / 2, cy - h / 2, w, h, rx=h / 2, fill=fill)
        self.text(cx, cy + size * 0.35, label, size, weight, colour, "middle")
        return w

    def arrow(self, x, y, length, direction="right", fill=INK, t=5.0, hw=12.5, hl=9.0) -> None:
        """A solid block arrow; (x, y) is the centre of the tail."""
        a, b = t / 2, hw / 2
        if direction == "right":
            x2, xb = x + length, x + length - hl
            pts = [(x, y - a), (xb, y - a), (xb, y - b), (x2, y), (xb, y + b), (xb, y + a), (x, y + a)]
        elif direction == "down":
            y2, yb = y + length, y + length - hl
            pts = [(x - a, y), (x + a, y), (x + a, yb), (x + b, yb), (x, y2), (x - b, yb), (x - a, yb)]
        else:
            raise ValueError(direction)
        self.poly(pts, fill)

    def render(self, h: float, defs: str, label: str) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w_mm:g}mm" height="{h / MM:.2f}mm" '
            f'viewBox="0 0 {self.w:.2f} {h:.2f}" role="img" aria-label="{escape(label)}">\n'
            f"{defs}\n" + "\n".join(self.p) + "\n</svg>\n"
        )


# ------------------------------------------------------------------- curve util
def smooth(pts: list[tuple[float, float]], tension: float = 0.42) -> str:
    """A cubic path through pts with horizontal tangents — good for flow ribbons."""
    d = f"M{pts[0][0]:.2f},{pts[0][1]:.2f}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx = (x1 - x0) * tension
        d += f" C{x0 + dx:.2f},{y0:.2f} {x1 - dx:.2f},{y1:.2f} {x1:.2f},{y1:.2f}"
    return d


def ribbon(top: list[tuple[float, float]], bot: list[tuple[float, float]]) -> str:
    """A closed band between an upper and a lower smooth edge."""
    d = smooth(top)
    rev = list(reversed(bot))
    d += f" L{rev[0][0]:.2f},{rev[0][1]:.2f}"
    for (x0, y0), (x1, y1) in zip(rev, rev[1:]):
        dx = (x1 - x0) * 0.42
        d += f" C{x0 + dx:.2f},{y0:.2f} {x1 - dx:.2f},{y1:.2f} {x1:.2f},{y1:.2f}"
    return d + " Z"

