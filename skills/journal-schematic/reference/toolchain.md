# Toolchain notes

Sections are marked **[any]** or **[Windows]**. The Windows ones describe this
skill's bundled scripts; the portable ones are properties of the method and
apply wherever you run it.

## uv — [any]

Scripts carry a PEP-723 header, so `uv run script.py` resolves dependencies with
no venv management:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "numpy"]
# ///
```

- There may be **no system `python` on PATH** — always `uv run`.
- If PyPI is blocked (TLS `HandshakeFailure`), set a mirror before *any* command
  that resolves packages:
  `$env:UV_DEFAULT_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"`
- `uv run python -c "..."` does **not** read the PEP-723 header of a module it
  imports. Pass `--with pillow --with numpy` explicitly for ad-hoc probes.
- Set `$env:PYTHONUTF8="1"` for anything printing CJK or typographic characters.

## PowerShell traps — [Windows]

- **`$args` is reserved.** Name your splat variable something else (`$cliArgs`).
- **No heredocs.** For an inline script, pipe a single-quoted here-string:
  `@'` … `'@ | python -`, or use `python -c "..."` for one-liners.
- **Escaped double quotes inside a regex character class break the parser.**
  `uv run python -c "... r'\sd=\"([^\"]+)\"' ..."` fails with
  *Missing type name after '['*. Write the probe to a `.py` file instead — this
  is worth doing anyway, because probes get rerun.
- `&&` only chains native commands; use `;` before PowerShell keywords.
- Office interop enums are **not loaded** in PowerShell 7. Use raw values.

## Rasterising — [Windows tooling, portable principle]

`cairosvg` needs libcairo and will not install on ARM64 Windows. Use headless
Edge via `assets/render_svg.ps1`. Elsewhere, `rsvg-convert -w <px> -h <px>`,
`resvg`, or headless Chrome all work — pass an exact pixel size computed from
the figure's millimetre width and the target DPI, and never trust a tool's own
DPI flag without checking the output dimensions.

The trap below is a browser property, not a Windows one, and applies to headless
Chrome on any platform:

- Screenshotting an `.svg` URL directly, or reusing a running browser instance,
  **silently ignores `--window-size`**. The script inlines the SVG into a temp
  HTML page at exact pixel dimensions with a throwaway `--user-data-dir`.
- The script occasionally hangs. Run it standalone, one figure per call, and be
  ready to stop and retry rather than chaining it after a build.
- A local HTTP server plus a browser canvas is a good live proof surface; bump a
  `?v=N` query parameter to force a refresh. **Stop the server before any
  command that deletes or recreates the icon directory**, or `rmtree` fails with
  `PermissionError`.

## Text metrics — [any]

`tw()` measures with PIL at 4× the size and divides by 4, which keeps hinting
error under a tenth of a point.

`svgkit` measures against Arial where it exists and Liberation Sans otherwise.
The two are metric-compatible by design, so layout numbers agree across
platforms; it raises rather than fall back to an arbitrary font, because a
substitute with different widths misaligns the figure silently.

**PIL and the browser disagree by a fraction of a percent.** Irrelevant for a
whole line, fatal when you split a line into separately-positioned runs: over
~15 characters the drift is enough to swallow a 1.75 pt space. If you must
split a line (e.g. to interleave a drawn glyph), pin each run with
`textLength` + `lengthAdjust="spacing"` and advance the spaces by hand.

Note that **PowerPoint ignores `textLength`**, so a split line is the one place
the PPTX export can still drift. Keep splits rare.

## SVG features to avoid — [any]

Anything from SVG 2, and anything whose behaviour depends on the renderer:

- **`width`/`height` on `<use>`** to scale a `<symbol>` — SVG 2. Define icons as
  plain `<g>` and place them with `transform="translate(...) scale(...)"`, which
  is SVG 1.1 and universal. Keep each icon's viewBox so a non-zero origin can be
  undone with a trailing `translate(-minx -miny)`.
- **`<symbol viewBox>` as a crop.** `<symbol>` clips implicitly; `<g>` does not.
  If you were relying on that clip, crop the artwork at the source instead —
  traced paths use only absolute `M/L/C/Z`, so you can split `d` on `M`, compute
  each subpath's bounding box, and drop the ones outside the crop. Renderer
  independent, and it survives the PPTX export. `clipPath` is a fallback but
  PowerPoint's support for it is unverified.
- **Presentation attributes through `<use>`.** PowerPoint does not propagate
  `fill`, `stroke` or `stroke-width` from `<use>` into the referenced content.
  Stroke icons vanish; filled icons arrive black, or — if the traced source had
  a colour baked into the path — silently keep *that* colour and look plausible.
  Inline the path instead; `<use>` is not worth using at all.

## Tracing raster icons — [any]

`potrace` inverts polarity depending on the input: check whether you got the
artwork or its negative, and QA by rasterising the trace and computing IoU
against the source. Below ~90% something is wrong.

## Measuring a suspected offset — [any]

Do not argue about a shift you can measure. Take the same crop from two renders,
sum darkness per row into a profile, and either cross-correlate the profiles or
compare ink centroids:

```python
w = (255 - np.asarray(img.convert("L").crop(box), float)).sum(axis=1)
centroid = (w * np.arange(len(w))).sum() / w.sum()
```

Use a box with generous margins that fully contains the ink in **both** images —
a crop that clips one of them produces a confident, wrong answer. Words without
descenders (`GMATCH`, `Mothers`) make the cleanest rulers, because the ink-row
range maps directly onto cap height and baseline. Measure at 600 dpi when you
need better than a quarter point.
