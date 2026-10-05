#!/usr/bin/env node
// Render a GSAP scene (HTML) to MP4 by seeking the timeline frame by frame.
// Usage: node render.mjs <scene.html> <out.mp4> [--fps 30] [--width 1920] [--height 1080] [--duration <s>]
// The scene must expose a PAUSED GSAP timeline as `window.tl`.
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const pos = args.filter((a, i) => !a.startsWith('--') && !(args[i - 1] || '').startsWith('--'));
const opt = (n, d) => { const i = args.indexOf(`--${n}`); return i > -1 ? Number(args[i + 1]) : d; };
const [scene, out] = pos;
if (!scene || !out) { console.error('usage: render.mjs <scene.html> <out.mp4> [--fps N --width N --height N --duration S]'); process.exit(1); }

const fps = opt('fps', 30), width = opt('width', 1920), height = opt('height', 1080);
const gsapLocal = join(here, 'node_modules/gsap/dist');

const log = (m) => process.env.DEBUG && console.error('[render]', m);
const browser = await chromium.launch(
  (process.env.CHROMIUM_PATH || existsSync('/opt/pw-browsers/chromium')) ? { executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium' } : {});
log('launched');
const page = await browser.newPage({ viewport: { width, height } });

// Serve GSAP (core + plugins) from node_modules so scenes render offline.
// Fail font CDNs fast (a stalled stylesheet blocks the scripts after it). Self-host fonts for exact type offline.
await page.route(/fonts\.(googleapis|gstatic)\.com/, (route) => route.abort());
await page.route(/gsap.*\/dist\/([\w.-]+\.js)$|\/gsap\/([\w.-]+\.js)$/, (route) => {
  const file = route.request().url().split('/').pop();
  const p = join(gsapLocal, file);
  return existsSync(p) ? route.fulfill({ body: readFileSync(p), contentType: 'text/javascript' }) : route.continue();
});

// Don't let a slow font CDN hang the render: wait for DOM, then give fonts up to 8s.
await page.goto(pathToFileURL(resolve(scene)).href, { waitUntil: 'domcontentloaded' });
log('loaded dom');
await page.waitForFunction(() => window.gsap, null, { timeout: 15000 });
log('gsap ready');
await page.evaluate(() => Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, 8000))]));
log('fonts done');
const total = await page.evaluate(() => {
  if (!window.tl) throw new Error('Scene must expose a paused GSAP timeline as window.tl');
  window.tl.pause(0);
  return window.tl.duration();
});
const duration = opt('duration', total);
const frames = Math.round(duration * fps);

log('frames=' + frames);
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-movflags', '+faststart', resolve(out)], { stdio: ['pipe', 'inherit', 'inherit'] });

for (let f = 0; f < frames; f++) {
  await page.evaluate((t) => { window.tl.time(t, false); }, f / fps);
  const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
  if (f < 3) log('frame ' + f + ' ' + buf.length + 'B');
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
}
ff.stdin.end();
await new Promise((r) => ff.on('close', r));
await browser.close();
console.log(`wrote ${out}: ${frames} frames, ${duration.toFixed(2)}s @ ${fps}fps, ${width}x${height}`);
