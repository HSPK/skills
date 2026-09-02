# Design rules

Distilled from ~18 rounds of correction on a real journal figure. Each rule
exists because a specific version was rejected for breaking it.

## What belongs in the figure

- **No title inside the figure.** "A. Study Design" is the journal's job. The
  cohort name, N, and date range go in the caption — or, if the user wants them
  visible, into a small masthead line, never a heading.
- **No element that duplicates another.** A timeline across the top is redundant
  if the lanes below already carry the same three columns; delete it. Ask "what
  does this line tell me that the thing under it does not?" for every rule,
  axis, and connector.
- **Every icon gets a text label.** A bare icon is a guessing game regardless of
  how obvious it seems to you.
- **Do not invent wording.** Construct and outcome names come from the source
  document verbatim. If a name does not fit the box, change the box.

## Line and frame

- **Simple frames are not absent frames.** "简约框线" means one weight, one
  radius, consistently applied — not borderless panels floating in white.
- **Every line that carries meaning must be clearly visible.** No hairlines, no
  10% tints for something the reader is supposed to see. If a line is too faint
  to matter, delete it; if it matters, draw it at full strength.
- **Delete lines that collide with data.** A reference rule that happens to sit
  where the data sits is indistinguishable from the data. Encode it with tint
  contrast between bands instead.
- **Arrows: one shape, used everywhere.** Solid block arrows, not stroked lines
  with markers. Pick one `(shaft, head width, head length)` triple and reuse it
  for the flow arrow, the derivation arrow, and the time axis. Square the
  joins where an arrow meets a panel — rounded ends read as unfinished.

## Type

- **All text is full-strength ink at every size.** Never grey small type.
  Hierarchy comes from size and weight only. Grey reads as "disabled".
- **No decorative separators.** A middot between a logo and a statistic reads as
  a typo at 6 pt; use a thin vertical rule.
- **Widow control on wrapped text.** A last line holding one short token —
  `(SDQ)`, `(eHCI)` — looks like a mistake. Pull a word down, but only when the
  widow is genuinely short (< ~0.32 of the measure), or two-word phrases start
  breaking badly.
- **Symbols must be internally consistent.** Arial's `≥` is a slanted arm over a
  *horizontal* bar; users notice. No Windows font carries the fully-slanted
  U+2A7E in both weights, and depending on a symbol font breaks the figure
  elsewhere — so draw it as polygons matching Arial's own advance and ink box.
  `svgkit` does this; the advance matches, so text metrics are unaffected.

## Colour

- **Hue encodes one thing.** One hue per group (e.g. mothers vs daughters), a
  neutral graphite for outcomes and furniture. Never decorate.
- **Tints must be far enough apart to read as deliberate.** A 242-grey panel
  beside a 202-grey panel looks like a rendering error, not a design. When you
  deepen one block, check its neighbours.
- **Ordinal strata get equal bands, not proportional ones.** If the top category
  is open-ended (`≥8 h/d`), a linear axis has to invent an extent. Equal bands
  labelled by category, with the construction stated in the caption, is the
  honest choice — and it is the most reviewer-visible judgement call in the
  figure, so flag it to the user.

## Layout

- **Align everything, and verify numerically.** Frames, icons, and their labels
  all on the same grid. Run an alignment scan on the render; "looks aligned" is
  not a finding.
- **Icons align to the centre of the text stack they label**, not to its top.
- **Underlines and separators must clear descenders and the block below.**
  A heading rule that touches the first list item is the most common collision.
- **Compact, but not cramped.** Users ask for both, in that order, several
  rounds apart. Tighten global padding first; only then reduce leading.
- **Avoid the boxy grid look.** Rounded tinted lanes, pills, and chevrons read
  as designed; a lattice of rectangles reads as a table. When told "太方正",
  the fix is fewer frames and more shape, not smaller frames.

## Honesty

- **Never encode a quantity the data cannot support.** A ribbon whose thickness
  varies implies a measured flow; if you do not have those counts, it is a lie.
  Check the encoding against the numbers before committing to it.
- **State constructed axes in the caption.** Anything the reader could mistake
  for a measured scale needs one sentence explaining how it was built.
