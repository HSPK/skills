# SVG → editable PowerPoint

**Requires Windows and desktop PowerPoint.** There is no cross-platform
equivalent: the conversion is a ribbon command driven through COM automation.
LibreOffice imports an SVG as a single opaque object rather than decomposing it
into native shapes, so it does not substitute. Where this route is unavailable,
deliver PNG and PDF and tell the user, rather than shipping a deck that only
looks editable.

PowerPoint is the best SVG-to-shapes converter available on a stock Windows box,
and better than most anywhere: it reads the SVG itself and emits native
DrawingML, so **type stays type** (real Arial runs, not outlines) and fills stay
editable. Inkscape and LibreOffice are not usually installed; do not assume them.

`assets/svg_to_pptx.ps1` encodes everything below.

## Verifying the result is genuinely editable

Unzip the `.pptx` and check `ppt/slides/slide1.xml`:

- `<a:t>` runs present → live text, one per run
- `typeface="Arial"` → font preserved, not outlined
- **zero `<a:blip>`** → no raster fallback anywhere
- a mix of `<a:prstGeom>` and `<a:custGeom>` → real shapes

## The conversion recipe

1. `AddPicture(svg, 0, -1, l, t, w, h)` — the SVG lands as **`msoGraphic`
   (type 28)**, i.e. genuinely vector.
2. `Shape.Ungroup()` **refuses it**: *"This member can only be accessed for a
   group"*. `Shape.ConvertToShapes()` does not exist.
3. The conversion is only reachable through the ribbon command
   `CommandBars.ExecuteMso("ObjectsUngroup")`. Every other plausible idMso
   (`GraphicsConvertToShape`, `ConvertToShapes`, `PictureConvertToShapes`,
   `ConvertIconToShape`, `GraphicsConvertToFreeform`, `Ungroup`) is **invalid**.
4. `ObjectsUngroup` reports `enabled=False` until there is a genuine UI
   selection: `ActiveWindow.Activate()`, `ActiveWindow.View.GotoSlide(1)`,
   `shape.Select()`. Then execute and allow ~1.5 s.
5. PowerPoint cannot run invisibly over COM — set `Visible = -1`.
6. Interop enums are not loaded in PowerShell 7. Raw values:
   `msoTrue -1`, `msoFalse 0`, `ppLayoutBlank 12`,
   `ppSaveAsOpenXMLPresentation 24`, `msoGroup 6`, `msoFreeform 5`,
   `msoGraphic 28`.
7. Size the slide to the figure first, so the deck exports back at true print
   size and can also be copy-pasted into another deck as one group.

## The four importer defects — all must be pre-compensated in the SVG

Apply these to a **throwaway copy**; never to the print SVG.

### 0. `<use>` does not inherit presentation attributes

This is the one that hides longest. `<use href="#icon" fill="#A3202E"/>` and
`<use href="#icon" stroke="..." stroke-width="..."/>` are correct SVG 1.1 and
render properly in every browser, but PowerPoint's importer does not push the
attributes into the referenced content. Stroke icons vanish entirely (they are
`fill="none"` with no stroke left). Filled icons are more insidious: they either
arrive flat black, or — if the traced source had a `fill` baked into the path —
they keep the *source* colour and look plausible, so you conclude the mechanism
works and stop checking.

**Do not use `<use>` at all.** Inline the path at every use site with an
explicit `fill` or `stroke`/`stroke-width`. Keep the path data in a module-level
dict so the call site stays one line; `assets/svgkit.py` does this in both
`Svg.use()` and `Svg.sicon()`. The `<defs>` block then usually ends up empty.

Diagnose it by rendering the same icon in the browser and in the PPTX proof and
comparing colour, not shape.

### 1. `<use width/height>` is ignored

Scaling a `<symbol>` via `width`/`height` on `<use>` is SVG 2. PowerPoint drops
every icon in at native size — hundreds of points, covering the figure. Define
icons as `<g>` and place them with a `transform`. (This is a change to the SVG
itself, not the throwaway copy; it costs nothing in browsers.) Moot once you
follow defect 0 and stop using `<use>` entirely, but worth knowing why.

### 2. Font size is read as pixels

Geometry is scaled by the viewBox→canvas factor, but `font-size` is taken as a
raw pixel value. Type arrives **25% small** inside full-size artwork, so
absolutely-positioned runs drift apart and tuned letter-spacing looks huge.

Pre-multiply every `font-size` by that same factor:

```
k = (slide_width_pt / 72 * 96) / viewBox_width
```

For a 180 mm figure with a point-based viewBox, `k = 4/3` exactly.

### 3. The text baseline is lifted by 0.2335 em

PowerPoint places the text box as if the baseline sat **1.207 em** below the box
top (verifiable from `<a:off y>` and `tIns` in the XML), then draws it at about
**0.973 em**. Every line ends up ~0.23 em too high. You will not notice on
ordinary text — but any *drawn* glyph placed on that baseline sinks below its
own sentence, which is exactly what a hand-drawn `≥` does.

Add `0.2335 × font_size` to every `<text y=...>` in the throwaway copy, computed
from the **original** size before applying `k`. Verified at 600 dpi: residual
error < 0.15 pt.

### And one thing not to do

**Do not resize the group after ungrouping.** PowerPoint gives every converted
text box a 7.2 pt inset, so the group's bounding box overhangs the artwork.
Forcing it back to the slide size shrinks the geometry *without* shrinking the
font sizes, and all the type comes out too wide for its layout. Leave the shapes
where PowerPoint put them; they are already correct relative to the slide.

## Verification pass

After conversion, export a proof PNG from the slide and compare it to the
browser render of the same SVG. Check specifically:

- every icon at the right size and position (defect 1)
- text size and inter-run spacing (defect 2)
- baselines, especially any drawn glyph (defect 3)
- stroke icons still present (they vanish if defined via `<use>`)
- any `<symbol>`-based crop still cropped

Measure the offsets rather than judging them — see `toolchain.md`.

## Known residual

A line split into runs around a drawn glyph becomes several text boxes plus path
shapes in PowerPoint, so that one line is awkward to retype there. Tell the user.
