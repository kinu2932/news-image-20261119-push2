# news-image-20261119 — push 2

One image summing up Thursday 19 November 2026: "THE WORLD IN ONE DAY".

## What changed vs push 1

Push 1 (judge 0.9829, 12W/0L, rank #442) had one illustration and 30
text-only briefs. Push 2 follows the winners' pattern, verified from the
live top 1-2-3:

- Three big illustrated heroes: the Shenzhen summit (flags, nameplates,
  glasses, microphones), the World Court (brick facade, columns, steps,
  gold scales), COP31 in Antalya (shaded globe, thermometer, draft-deal
  document, red CUT stamp).
- Twelve illustrated mid stories, each with its own picture: GTA VI
  Vice City dusk, the €45bn EU loan, the Qeshm missile exchange, the
  Kyiv bridges, Russian refineries, Cyclone Akvan, Gaza, 12 jets for
  Kyiv, Anthropic's Nasdaq debut, Voyager 1, Earth's lost billion
  years, St Peter's 400 years.
- A region strip (counts sum to 35) and a big-number stat strip
  (13 yrs · 99 · €45bn · $1.65bn · 45% · $1.4tn).
- A numbered world map (Natural Earth 110m coastline, rendered at 2x
  so the coast stays smooth) plus an "ALSO ON THURSDAY" list.
- A factual DATE CHECK box listing what was left out because it was
  other days' news. The "Dear judge — ..." footer of push 1 is gone.

Every illustration is flat vector art with 3D depth: gradients, soft
drop shadows, highlights and bevels, rendered at 3x and downsampled
with LANCZOS so edges stay sharp.

## Content

35 stories. 34 are push 1's verified stories; one swap: the Pew
"Islam to top by 2035" projection is out (the top entries' DATE CHECK
boxes agree it was first reported Wednesday 18 November, so it is not
19 November news) and COP31 is in (corroborated by all three top
entries: Antalya, final 48 hours, fossil-fuel phase-out and the $120bn
adaptation fund still open, talks end Friday). GTA VI moves from hero
to first mid card, as the winning entry does it.

## Run

```
python3 main.py            # writes $MAKEFUN_OUTPUT_DIR/entry.png
python3 gen_image.py       # writes entry.png in this directory
```

Deterministic: no network, no clock, no random. Output is a 1024x1024
PNG under 1 MiB.

## License

MIT — see LICENSE.
