# news-image-20261119 — push 2 build notes

## Entry

- Repo: `~/workspace/makefun/news-image-20261119-push2/`
- Anchor: `makefun anchor 8ae64a5d084056885f355b5d91885f6ea400e32a round 34113931`
  (fresh kit downloaded 20 Nov 2026 ~03:25 WIB from
  https://make.fun/c/news-image-20261119/kit — kit.tar.gz 6,193,665
  bytes, sha256 `1e22ce54fb4ebdda716f8d85ea4c2274a34e227751e65ec6acb08ebd194499c4`,
  kit.json bundle_sha256 `1c4dd40e…` — identical to the push-1 kit, no drift)
- `entry.png`: 1024x1024 PNG, **347,630 bytes** (≤1 MiB ✓)
- sha256: `ecf99cffc17581bd20516ad52c4d4f576f8bd7275bc1ac5733b2c5cabd2f0023`
- `main.py` generates the image via `gen_image.py` (Pillow, Natural
  Earth 110m coastline in `coastline.json`, copied from push 1's
  verified data). Deterministic: `main.py` run twice to different
  dirs + `gen_image.py` re-run — all three byte-identical to the sha
  above. No network, no clock, no random.

## What changed vs push 1 (judge 0.9829, 12W/0L, rank #442)

Winner-profile rebuild, from the live top 1-2-3 (judge 0.9921–0.9923):

- 3 big illustrated heroes: Shenzhen summit (3 flags, nameplates,
  water glasses, microphones, APEC banner), World Court (brick facade
  with gradient, columns, steps, gold scales), COP31 Antalya (shaded
  globe, thermometer, draft-deal document, red CUT stamp).
- 12 illustrated mid stories, each with its own picture: GTA VI Vice
  City dusk, €45bn EU loan, Qeshm missile exchange, Kyiv bridges,
  Russian refineries, Cyclone Akvan, Gaza, 12 jets for Kyiv,
  Anthropic Nasdaq debut, Voyager 1, Earth's lost billion years,
  St Peter's 400 years.
- Region strip (ASIA 5 / MIDDLE EAST 3 / EUROPE 10 / AFRICA 1 /
  AMERICAS 11 / OCEANIA 1 / GLOBAL 4 — sums to 35) + big-number stat
  strip (13 yrs · 99 · €45bn · $1.65bn · 45% · $1.4tn).
- Numbered world map (rendered at 2x, downsampled — smooth coastline)
  + "ALSO ON THURSDAY" list of the remaining 20 stories.
- Factual DATE CHECK box (what was left out as other days' news).
  The "Dear judge — ..." footer of push 1 is GONE.
- 3D depth everywhere (Aa's instruction, 20 Nov ~10:28 WIB):
  gradients, soft drop shadows (blurred RGBA layers), highlights,
  bevels, layered skylines. Every illustration is drawn at 3x and
  downsampled with LANCZOS — edges stay sharp, no blocky pixels.

## Content — 35 stories, one editorial swap

34 are push 1's verified stories. Swap: the Pew "Islam to top by
2035" projection is OUT — the top entries' DATE CHECK boxes agree it
was first reported Wednesday 18 November, so it is not 19 November
news. COP31 is IN, corroborated by all three top entries (Antalya;
enters its final 48 hours; ministers take over; fossil-fuel phase-out
and the $120bn adaptation fund still open; talks end Friday). Region
counts are unchanged (both stories GLOBAL). GTA VI moves from hero to
first mid card, as the winning entry does it.

## Verification (all done, all pass)

1. `gen_image.py` renders entry.png, 347,630 bytes, 1024x1024 RGB.
2. `main.py` twice (different $MAKEFUN_OUTPUT_DIR) + `gen_image.py`
   re-run — byte-identical sha256 `ecf99cff…`.
3. Story count: 3 + 12 + 20 = 35 (asserted in code via region sum).
4. Visual review (full image + 2x zoom crops of every hero, both mid
   rows, the map, the DATE CHECK box, the ALSO list, and a 320px
   phone thumbnail): 4 real defects found and fixed in genuine
   revisions — (a) DATE CHECK ✓ rendered as a tofu box (Liberation
   Serif has no U+2713; the check is now drawn as a vector);
   (b) map badges 3 (Antalya) and 10 (Gaza) collided (offset moved);
   (c) 15 ALSO lines truncated by fit() (headlines shortened, facts
   kept — verified by measuring every line ≤ 212px);
   (d) summit figures too small vs the winners (enlarged ~18%).
   Side-by-side vs top1 reviewed: push 2 matches or beats it on
   illustration count (15 pictures vs 13), DATE CHECK prominence and
   map smoothness; top 1 still has slightly taller hero art and longer
   ALSO headlines (smaller font).
5. `git status` clean; LICENSE MIT (from init).

## Not done (Neng's job)

- NO bundle, NO check, NO Hermes review, NO submit in this turn.
- Next (separate fresh agent): bundle this session + real usage rows,
  check all-pass, Hermes top-10 review, present to Aa, submit only
  after Aa says submit. Competition closes 21 Nov 2026 07:00 WIB.
