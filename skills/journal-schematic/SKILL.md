---
name: journal-schematic
description: Build publication-quality schematic figures — study-design diagrams, flowcharts, analytic pipelines, CONSORT-style charts, mechanism and pipeline schematics — as hand-generated SVG at true print size, verified by rasterising and looking at them. Use when asked to make, redesign, or polish a diagram for a paper, or to turn a PowerPoint slide into a journal figure, or to convert SVG into editable PowerPoint shapes. Not for data-driven statistical plots (forest, Kaplan–Meier, scatter, survival, bar) — use a plotting library for those. SVG generation runs anywhere; the bundled rasteriser and the editable-PowerPoint export are Windows-only.
---

# Print figures from code

A figure for a journal is not a drawing you make once. It is a program you run
dozens of times while a human tells you what is still wrong. Optimise for the
loop, not for the first render.

## What this is for

**In scope — figures whose content is a structure, not a dataset:**
study-design and cohort diagrams, CONSORT and participant-flow charts, analytic
pipelines, mechanism and conceptual schematics, timelines, exposure/outcome
layouts. What these have in common is that every element's position is a
decision you make, so hand-placing them in a script is an advantage.

**Out of scope — figures whose content is a dataset:** forest plots,
Kaplan–Meier curves, scatter and regression plots, histograms, heatmaps,
anything with a fitted line or more than a handful of plotted points. Use
matplotlib, ggplot2 or plotnine. Do not hand-place a hundred data points to
avoid a dependency; the axis logic, tick placement and legend handling in those
libraries are worth more than the styling control you would gain.

The boundary case is a schematic carrying a few summary statistics — a design
diagram with three medians on it, say. That belongs here: the numbers are
annotation on a structure, not a plotted series.

**Also note:** the design rules in `reference/design-rules.md` are calibrated
for a *journal* figure. Posters and slides differ on titles (a poster panel
usually needs one), minimum type size (viewing distance is metres, not
centimetres) and colour weight. Take the layout and honesty rules; re-judge the
typographic ones.

## Platform

Three layers, with different portability:

| layer | what | runs on |
| --- | --- | --- |
| **1. Design and drawing** | the design rules, the content-model discipline, true-print-size setup, `svgkit.py`, `check_align.py` | any OS with Python + Pillow |
| **2. Rasterising** | `render_svg.ps1` (headless Edge) | Windows; substitute elsewhere |
| **3. Editable PPTX export** | `svg_to_pptx.ps1` (PowerPoint COM automation) | Windows + desktop PowerPoint only |

Layer 1 is the substance of this skill and is portable. `svgkit` measures text
with Pillow against Arial or, where Arial is absent, Liberation Sans — which is
metric-compatible with Arial by design, so layout numbers agree across
platforms. If neither is installed it raises rather than silently substituting a
font with different widths.

Layer 2 is replaceable: any rasteriser that honours an exact pixel size will do.
`rsvg-convert -w <px>`, `resvg`, or headless Chrome driven the same way
`render_svg.ps1` drives Edge. Keep the rule that matters — inline the SVG into an
HTML page at exact pixel dimensions rather than screenshotting the `.svg`.

Layer 3 has no cross-platform equivalent. LibreOffice can open an SVG but does
not decompose it into native shapes, so the output is not editable in the sense
users mean. On macOS or Linux, deliver PNG and PDF and say so.

## The core commitments

1. **Generate the SVG from a Python script.** Never hand-edit SVG, and within
   the scope above never reach for a chart library — a schematic has no axes to
   fit, so a plotting library only gets in the way. Every number in the figure
   is a variable you can move.
2. **Draw at true print size.** SVG root gets `width="180mm"`, the viewBox is in
   typographic points. Then `font-size="6.5"` is literally 6.5 pt on paper and
   you can judge legibility honestly. `MM = 72 / 25.4`; a 180 mm column is
   510.24 pt.
3. **Look at every render.** Rasterise and open the PNG with the view tool after
   every change. Claims like "this should be aligned now" are worthless; a
   200 dpi crop is proof.
4. **Archive every version to its own folder.** Users say "go back to the one
   with the rounded lanes". `figure/versions/v13/` costs nothing.
5. **Measure instead of guessing.** Text width comes from PIL, alignment from a
   pixel scan, a suspected offset from a centroid diff. Never eyeball a number
   you could compute.

## Workflow

### 1. Get the content right before drawing anything

If the source is a PPTX, dump its shape tree and text (`python-pptx`) and treat
that dump as the authority for wording. Paraphrasing a construct name is a real
error that survives twenty revisions because it looks plausible. Build a
content model (waves, groups, cut-points, medians, outcomes) as module-level
data, separate from layout code.

### 2. Harvest the icons

Icons carry more of the "looks designed" impression than the layout does.
Extract embedded raster art from the PPTX, trace it to vector with `potrace`,
and QA the trace by rasterising it and computing IoU against the original
(93–96% is a good trace). Add hand-authored 24×24 stroke icons for anything the
source lacks — see `assets/svgkit.py` for a starter set of nine.

Size icons by **optical area** (`sqrt(w*h)` held constant), not by height.
A wide icon and a tall icon at the same height look wildly different in weight.

### 3. Draw

Import `assets/svgkit.py`. It gives you the palette, PIL text metrics (`tw`,
`wrap` with widow control), the icon loader, an `Svg` writer with block arrows,
pills, smooth ribbons, and a drawn slanted `≥` glyph.

Read `reference/design-rules.md` before laying anything out. It is the distilled
result of ~18 rounds of "this still looks wrong", and it will save you most of
them.

### 4. Render and inspect

```powershell
.\render_svg.ps1 -Svg ".\figure\fig1.svg" -Dpi 200 -Out ".\figure\_p1.png"
```

Off Windows, substitute `rsvg-convert -w <px> -h <px>`, `resvg`, or headless
Chrome; the step that matters is not the tool but that you **look at the output
every time**.

Then `view` the PNG. For detail work, crop and upscale a region with PIL, or
stack two renders vertically to compare them. Run `assets/check_align.py` on
the render to get rule positions in points when the user says "not aligned".

Do not screenshot an `.svg` URL directly and do not reuse a running browser —
both silently ignore `--window-size`. `render_svg.ps1` inlines the SVG into a
throwaway HTML page at exact pixel size for this reason, and any substitute
should be driven the same way.

### 5. Iterate with the human

Expect batched correction lists ("1. …, 2. …, 9. …"). Work through them
literally and in order, then say which ones you also changed something adjacent
for. When a request is ambiguous about *what element* is wrong, reproduce the
defect in a zoomed crop first — several rounds were lost to fixing the wrong
thing. When a request conflicts with the data, say so rather than drawing
something the data cannot support.

### 6. Export

- **PNG for the journal**: `-Dpi 600`, one figure per invocation. Portable.
- **PPTX with live editable shapes**: `.\svg_to_pptx.ps1`. **Windows with
  desktop PowerPoint only.** Read `reference/pptx-export.md` first — the SVG
  importer has four systematic defects that must be pre-compensated in the SVG,
  and the conversion is only reachable through an undocumented ribbon command.
  Where PowerPoint is unavailable, deliver PNG and PDF and tell the user the
  editable route is not open to them; LibreOffice imports an SVG as one opaque
  object, not as native shapes.

## Environment notes

Read `reference/toolchain.md` for the specifics. Its uv, text-metric, SVG-feature
and offset-measurement sections apply anywhere; the PowerShell, Edge and
PowerPoint sections are Windows-only and are marked as such.

## Assets

| file | purpose | platform |
| --- | --- | --- |
| `assets/svgkit.py` | the drawing kit — palette, metrics, icons, `Svg` writer, drawn `≥` | any |
| `assets/check_align.py` | scans a render for rules and reports their positions in points | any |
| `assets/example.py` | 20-line runnable figure — use it to smoke-test the chain | any |
| `assets/render_svg.ps1` | headless Edge rasteriser at an exact DPI | Windows |
| `assets/svg_to_pptx.ps1` | SVG → editable PowerPoint shapes, with the text compensations | Windows + PowerPoint |

Copy them into the project rather than referencing them in place, so the project
stays self-contained. Verify the chain before doing real work:

```powershell
uv run example.py
.\render_svg.ps1 -Svg ".\_smoke.svg" -Dpi 200 -Out ".\_smoke.png"
.\svg_to_pptx.ps1 -Svg ".\_smoke.svg" -Out ".\_smoke.pptx" -Proof ".\_p.png"
```

`example.py` alone is the portable smoke test: if it writes an SVG, layer 1
works and the font metrics resolved.

Note PowerPoint refuses slides under 1 inch in either dimension and silently
clamps them, laying the whole figure out at the wrong scale; `svg_to_pptx.ps1`
detects this and throws rather than producing a plausible-looking wrong deck.
