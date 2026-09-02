# skills

Agent skills I actually use. Each one is a folder under `skills/` containing a
`SKILL.md` plus whatever reference documents and runnable assets it needs.

A skill here is not a tutorial. It is the residue of a real job that took many
rounds to get right — mostly *negative* knowledge, the kind you cannot look up
because it only shows up as a wrong render or a silently corrupted export.

## Available

| skill | what it does |
| --- | --- |
| [`experiment-engineering`](skills/experiment-engineering) | Large-scale ML/RL experiment engineering — inspect the real system, preserve benchmark semantics, design by ownership and lifecycle, debug from Rollout evidence, validate in stages, and recover remote runs without blind retries. |
| [`journal-schematic`](skills/journal-schematic) | Publication-quality schematic figures — study-design diagrams, CONSORT charts, analytic pipelines — hand-generated as SVG at true print size, verified by rasterising and looking at them, exported to 600 dpi PNG or editable PowerPoint. Not for data plots. |

## Installing

Skills are plain folders. Copy the one you want to wherever your agent looks:

```bash
# GitHub Copilot CLI — user scope
cp -r skills/journal-schematic ~/.copilot/skills/

# GitHub Copilot CLI — project scope
cp -r skills/journal-schematic .github/skills/

# Claude Code
cp -r skills/journal-schematic ~/.claude/skills/
```

Or vendor it into the project it serves, which is usually better: the assets are
meant to be copied and edited, and a figure project should stay reproducible
without the skill installed.

## Writing one

Two things separate a skill that works from a pile of notes:

**Write down what went wrong, not what to do.** "Use `<use>` to reuse an icon"
is advice any model already has. "PowerPoint's SVG importer silently drops
`fill` from `<use>`, and it fails invisibly when the traced path has its colour
baked in" is knowledge that cost an afternoon.

**Say what the skill is not for.** A skill with no stated boundary gets invoked
for adjacent problems it will handle badly. `journal-schematic` names data plots
as out of scope and sends you to matplotlib, because hand-placing a hundred
points to avoid a dependency is a mistake that looks like diligence.

Mark platform dependencies per section rather than globally — most of a skill is
usually portable even when one step is not.
