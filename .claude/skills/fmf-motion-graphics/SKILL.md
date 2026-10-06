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
| `templates/scene-portrait.html` | 1080x1350 | LinkedIn feed 4:5 |
| `examples/axis-event-nov16/scene.html` | 1080x1920 | **LinkedIn mobile video ad, 9:16: the biggest canvas** |

**LinkedIn mobile video spec (from secondary sources, LinkedIn's own page was not reachable; re-check before a campaign):**
9:16 = 1080x1920, mobile-only delivery, MP4 H.264 + AAC, 30 fps, 75 KB to 200 MB, 3 s to 30 min (15 to 30 s is the
usual recommendation). 4:5 (1080x1350) is the next largest. In the full-screen player the platform UI covers about
260 px at the top, 560 px at the bottom, 112 px left and 210 px right, so keep ALL essential content in
**x 112-870, y 300-1360** (758 x 1060). That box also sits inside a centred 4:5 crop, so the video survives if cropped.
Backgrounds and motion may bleed full-frame. The platform CTA button lives in the bottom overlay, so point down at it.


GSAP reference skills are vendored beside this one (`gsap-core`, `gsap-timeline`, `gsap-plugins`, `gsap-utils`,
`gsap-performance`, MIT, see `../THIRD-PARTY.md`). Read `gsap-timeline` before building anything with more than one beat.
Their examples assume a live page: in scenes, keep to the one-timeline contract below (no ScrollTrigger, no autoplay).

## Hook, music and CTA (pattern from the Axis event video)

- **Hook (first 2 s):** frame 0 must already carry the message. Open on the sharpest real line, big, with no fade from blank
  (Axis: the £4,200 client question from the landing page). Land one new beat per music beat. Use only real copy from the source.
- **No captions unless asked.** (The Axis video had them in v2; removed on request. The caption pattern is in git history.)
- **Palette is FMF only: navy `#0e1034`, cornflower `#6A8FFD`, soft cornflower `#93A9F6`, alice-blue `#E7ECF3`, white.**
  No green, no other accents. Cornflower text only on navy (it is under 3:1 on alice-blue); on light use navy text and
  cornflower shapes.
- **Music bed:** `python3 scripts/make-bed.py bed.wav --seconds 30 --bpm 96` synthesises an original groove (electric
  piano, sub bass, soft kick/snap/hats; needs `pip install numpy`), about -22 LUFS. Default `--style steady`: the SAME
  pattern every bar, so it flows at one speed; only chords and a gentle level lift (`--reveal 15`) change. The older
  `--style arc` builds density (heartbeat, then groove, then 16ths and a riser) and was rejected because it sounds like it
  speeds up. Cuts and hits sit on the beat grid
  (96 bpm = 0.625 s beats, 2.5 s bars). Mux with `node scripts/render.mjs ... --audio bed.wav` (AAC, 1 s fade in, 1.8 s
  fade out). A synthesised bed is a decent placeholder, not a substitute for a licensed premium track.
- **CTA on LinkedIn video:** the platform button sits under the video, so the last beat names the action, shows large
  cascading down-chevrons and "Tap the button below". Do not draw a fake button. Pick the closest native label (LinkedIn
  offers fixed presets such as Register or Sign up).

## Layout and design rules (Axis event v5, after a `frontend-design` pass: read `../frontend-design/SKILL.md` first)

- **One H1 style everywhere:** ABC Arizona Flare 142px, line-height .98, top-left of the safe area (x 112, y 300), width 770,
  visible on the scene's first frame. About 11 characters fit per line at 142px, so measure copy first
  (fontTools advance widths) and write headlines that break well.
- **Logo centred at the bottom, large** (mark 78px + wordmark 60px, top 1720px on 9:16). Small corner logos read as
  floating. This sits in the bottom overlay zone of LinkedIn's full-screen player, so check it in Campaign Manager preview.
- **Pacing:** let a finished visual hold 1.5 to 2.5 s before cutting (e.g. once the thread has joined the blocks), and give
  the reveal scene at least 6 s. Avoid two question headlines in a row. Chat messages from customers are all inbound
  (left, with a role avatar), never right-aligned as if the viewer sent them.
- Leave clear air between the H1 and illustrations (about 50px to a sub-line, 130px+ to graphics). Illustrations and chat
  bubbles may use the full width (x 70-1000); only text that must be read stays inside x 112-870.
- Avoid the generated-design tells: ALL-CAPS tracked labels (use sentence case), one word in a headline picked out in another
  colour (keep headlines one colour; cornflower is for graphics), identical rounded cards, gradient washes and glow orbs,
  a fade-and-slide-up on every element. Spend boldness on one thing per scene; cut between scenes hard, on the beat.
- Gotcha: a `tl.set()` at exactly t=0 is skipped when the renderer seeks to 0. Hide later-revealed elements in CSS and
  reveal them with a set at their beat.

## Stack (deliberately small)

- **Engine:** GSAP (free, including plugins). Animates HTML/CSS/SVG.
- **Renderer:** headless Chromium seeks the paused timeline frame by frame, ffmpeg encodes to MP4. For sharpness it renders
  at `--scale 2` (default) as lossless PNG, Lanczos-downscales to the output size and encodes x264 `-preset slow -tune
  animation -crf 14`. A 25 s 9:16 render takes about 3 minutes; use `--scale 1` for quick drafts.
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

`lottie-web` (needs designer-made Lottie files), `elevenlabs/skills` (paid account), `three.js` (only when 3D is needed). Rejected: React UI kits (generic SaaS look), Remotion (licence), duplicate engines and renderers. Log any vendored skill in
`../THIRD-PARTY.md` with source, licence and commit.
