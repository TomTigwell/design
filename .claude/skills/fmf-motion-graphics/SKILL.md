---
name: fmf-motion-graphics
description: >
  Create branded motion graphics (animated headline cards, stat reveals, logo stings, simple explainers)
  for Fill My Funnel as an MP4 or GIF. Use when the user asks for "motion graphic", "animated post",
  "animate this", "video for LinkedIn", "kinetic text", "animated stat", or wants a LinkedIn post visual
  to move. Builds a GSAP timeline in a single HTML scene using the FMF design system (cornflower,
  Lora + DM Sans), then renders it to video with headless Chromium + ffmpeg. Do NOT use for static
  feed images (linkedin-creative), reports or dashboards (fmf-eom-report, fmf-client-dashboard),
  or 3D / After Effects / Blender work (not set up yet).
---

# FMF Motion Graphics

**Status: renderer UNTESTED.** `scripts/render.mjs` was written but its first end-to-end run hung at browser
launch in the cloud sandbox. Before relying on it, run the smoke test below. If it fails, fix the launch
(see Troubleshooting) before building real scenes.

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

- Colours: cornflower `#6A8FFD`, navy `#0e1034`, alice-blue `#E7ECF3`; status only sage `#7CC4A7`,
  honey `#E0A766`, rose `#E58A97`. Fonts: Lora (headlines), DM Sans (body).
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
- The sandbox proxy blocks Google domains. Fonts from Google Fonts may not load, so Lora/DM Sans can fall
  back to system fonts in renders there. Self-host the font files in the scene folder if exact type matters.
- Scenes load GSAP from a CDN URL; `render.mjs` serves the local copy from `scripts/node_modules` instead.

## Candidate additions (from the "28 installs" list, not yet vendored)

`gsap-skills` (teaches correct GSAP), `anthropics/skills` canvas/GIF skills, `remotion/skills` (licence
check first), `threejs-skills`. Vendor a skill folder under `.claude/skills/` with attribution when added.
