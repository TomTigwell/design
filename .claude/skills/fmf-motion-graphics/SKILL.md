---
name: fmf-motion-graphics
description: >
  Create branded motion graphics (animated headline cards, stat reveals, logo stings, simple explainers)
  for Fill My Funnel as an MP4 or GIF. Use when the user asks for "motion graphic", "animated post",
  "animate this", "video for LinkedIn", "kinetic text", "animated stat", or wants a LinkedIn post visual
  to move. Builds a GSAP timeline in a single HTML scene using the FMF design system (cornflower,
  ABC Arizona Flare + DM Sans), then renders it to video with headless Chromium + ffmpeg. Do NOT use for static
  feed images (linkedin-creative), reports or dashboards (fmf-eom-report, fmf-client-dashboard),
  or 3D / After Effects / Blender work (not set up yet).
---

# FMF Motion Graphics

**Status: renderer verified** (5 Oct 2026, cloud sandbox). Templates render to MP4 in about 10 s; frames checked visually in
all three sizes with the brand fonts.

## Fonts (read this first)

- **Headlines: ABC Arizona Flare. Body and kickers: DM Sans.** Arizona Flare is the FMF and Axis master display font.
- Arizona Flare is **licensed** (ABC Dinamo) and **not stored in this repo**: this repo is public and the licence bars
  storing it on public servers. `render.mjs` embeds it at render time from `fmf-clients/_brand/fonts/` (private repo cloned
  beside this one), falling back to `obsidian-vault/Books/Post Visuals/fonts/`, or `$FMF_FONT_DIR`.
  If it can't be found the render prints a WARNING and falls back to Georgia. Never ship that fallback.
- The copy in `_brand` is the **Unlicensed Trial** build. Buy the full licence from ABC Dinamo before relying on it for
  client work or paid ads.
- Do not add a Google Fonts `<link>` to scenes. It is blocked in the sandbox and `render.mjs` aborts it.

## Sizes (the scene's `<meta name="fmf-size">` sets the output size automatically)

| Template | Size | Use |
|---|---|---|
| `templates/scene.html` | 1920x1080 | 16:9, decks, YouTube, site |
| `templates/scene-square.html` | 1080x1080 | LinkedIn feed 1:1 |
| `templates/scene-portrait.html` | 1080x1350 | LinkedIn feed 4:5 (most reach on mobile) |

GSAP reference skills are vendored beside this one (`gsap-core`, `gsap-timeline`, `gsap-plugins`, `gsap-utils`,
`gsap-performance`, MIT, see `../THIRD-PARTY.md`). Read `gsap-timeline` before building anything with more than one beat.
Their examples assume a live page: in scenes, keep to the one-timeline contract below (no ScrollTrigger, no autoplay).

## Stack (deliberately small)

- **Engine:** GSAP (free, including plugins). Animates HTML/CSS/SVG.
- **Renderer:** headless Chromium seeks the paused timeline frame by frame, ffmpeg encodes to MP4.
- Not included yet: three.js, Remotion (paid licence at 4+ staff, check before adopting), Blender, After Effects.
  Add one only when a job needs it.

## Workflow

1. Copy `templates/scene.html` to a working file. Keep the one-timeline contract (below).
2. Fill the copy from the brief. Every claim and number comes from the user or a tool, never invented
   (`fmf-skills/PRINCIPLES.md` §1).
3. `cd scripts && npm install` (first run only), then
   `node scripts/render.mjs scene.html out.mp4 --fps 30` (add `--width 1080 --height 1080` for square,
   `1080x1350` for portrait feed).
4. Check frames before delivering: extract a still with `ffmpeg -ss 1 -i out.mp4 -frames:v 1 still.png`.
5. GIF if asked: `ffmpeg -i out.mp4 -vf "fps=15,scale=720:-1" out.gif`.

## The one-timeline contract

- All animation lives in a single **paused** `gsap.timeline` exposed as `window.tl`.
- No autoplay, `Date.now()`, `Math.random()`, CSS animations or `setTimeout`. The renderer controls time.
- End with a hold (`tl.to({}, {duration: 1.5})`) so the last frame is readable.
- Scene size is set in the CSS on `html, body` (default 1920x1080). Match `--width/--height`.

## Brand rules

- Type: ABC Arizona Flare regular for headlines, DM Sans 400 to 700 for everything else.
- Colours: cornflower `#6A8FFD`, navy `#0e1034`, alice-blue `#E7ECF3`; status only sage `#7CC4A7`,
  honey `#E0A766`, rose `#E58A97`. 
- British English, no em dashes.
- Motion: ease `power3.out` for entrances, `power2.inOut` for moves, 0.5 to 0.8 s per beat, stagger
  0.08 to 0.15 s. One idea per scene. Under 15 s for LinkedIn feed.
- LinkedIn feed video: 1:1 (1080x1080) or 4:5 (1080x1350), captions burned in (most play muted).

## Smoke test

```
cd scripts && npm install
node render.mjs ../templates/scene.html /tmp/test.mp4 --fps 24
ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/test.mp4   # expect about 4.5
```

## Troubleshooting

- Cloud sandbox: Chromium lives at `/opt/pw-browsers/chromium`; the script uses it by default (override
  with `CHROMIUM_PATH`). Do not run `playwright install`. The npm `playwright-core` version may be newer
  than the pre-installed browser, which is why the executable is passed explicitly.
- The sandbox proxy blocks Google domains. `render.mjs` aborts Google Fonts requests so they cannot stall the page
  (a pending stylesheet blocks the GSAP script behind it).
- `playwright-core` is pinned to 1.56 to match the pre-installed Chromium build (1194). Newer versions fail to launch it.
- Never return the timeline from `page.evaluate` (e.g. `() => tl.time(1)`): serialising it hangs. Wrap in braces.
- Set `DEBUG=1` for step-by-step logging from `render.mjs`.
- Scenes load GSAP from a CDN URL; `render.mjs` serves the local copy from `scripts/node_modules` instead.

## Candidate additions (from the "28 installs" list, not yet vendored)

`anthropics/skills` canvas/GIF skills, `threejs-skills` (unvetted), Remotion skills (licence). Log any vendored skill in
`../THIRD-PARTY.md` with source, licence and commit.
