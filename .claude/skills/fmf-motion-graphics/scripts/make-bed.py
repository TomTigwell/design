#!/usr/bin/env python3
"""Synthesise a subtle, original ambient music bed (no samples, so no licensing issues).

Usage: python3 make-bed.py out.wav [--seconds 15] [--bpm 96]

Soft pad chords (Cmaj9 / Am9 / Fmaj9 / G6/9 / Fmaj9 / Cmaj9), a low root, and a quiet ping-pong plucked arpeggio.
Deterministic: same arguments give the same audio. Needs numpy. Output is a quiet bed (about -22 LUFS)
meant to sit under captions; the renderer adds fades. Beats fall on multiples of 60/bpm, so scene cuts placed on
that grid (96 bpm: 0.625 s) line up with the music.
"""
import sys, wave
import numpy as np

SR = 44100
out = sys.argv[1]
arg = lambda n, d: float(sys.argv[sys.argv.index(f'--{n}') + 1]) if f'--{n}' in sys.argv else d
SECS, BPM = arg('seconds', 15.0), arg('bpm', 96.0)
beat = 60.0 / BPM
bar = 4 * beat
n = int(SR * SECS)
rng = np.random.default_rng(7)
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)
t_all = np.arange(n) / SR

CHORDS = [  # midi notes, root first
    [48, 52, 55, 59, 62],  # Cmaj9
    [45, 48, 52, 55, 59],  # Am9
    [41, 45, 48, 52, 55],  # Fmaj9
    [43, 47, 50, 52, 57],  # G6/9
    [41, 45, 48, 52, 55],  # Fmaj9
    [48, 52, 55, 59, 62],  # Cmaj9
]

def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= n:
        return
    seg = sig[: n - i]
    buf[i:i + len(seg)] += seg * gain

def env(length, a, r):
    t = np.arange(int(length * SR)) / SR
    e = np.minimum(1.0, t / a) * np.minimum(1.0, np.maximum(0.0, (length - t) / r))
    return e ** 1.5

def tone(f, length, detune=(0.0, 0.0), harm=0.18):
    t = np.arange(int(length * SR)) / SR
    s = np.zeros_like(t)
    for d in detune:
        s += np.sin(2 * np.pi * f * (1 + d) * t)
    s /= len(detune)
    return s + harm * np.sin(2 * np.pi * 2 * f * t) / len(detune)

pad = np.zeros((n, 2))
pluck = np.zeros((n, 2))

for b, chord in enumerate(CHORDS):
    start = b * bar
    if start >= SECS:
        break
    length = bar + 1.4
    e = env(length, 0.9, 1.4)
    for k, m in enumerate(chord):
        f = mtof(m + (12 if k else 0))
        s = tone(f, length, detune=(-0.0035, 0.0, 0.0035)) * e
        pan = 0.25 + 0.5 * (k / (len(chord) - 1))
        buf = np.zeros(n); add(buf, start, s, 0.11)
        pad[:, 0] += buf * (1 - pan); pad[:, 1] += buf * pan
    root = tone(mtof(chord[0] - 12), length, harm=0.05) * env(length, 0.6, 1.2)
    buf = np.zeros(n); add(buf, start, root, 0.20)
    pad[:, 0] += buf; pad[:, 1] += buf

    # quiet arpeggio, eighth notes, starting on beat 2 so each bar breathes in first
    up = [chord[i] + 24 for i in range(len(chord))]
    pattern = [0, 2, 4, 3, 2, 3, 1, 2]
    for j, idx in enumerate(pattern):
        t0 = start + beat + j * beat / 2
        if j >= 6 or t0 >= SECS:
            continue
        f = mtof(up[idx])
        tt = np.arange(int(1.1 * SR)) / SR
        s = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt * 4.2)
        s *= np.minimum(1.0, tt / 0.006)
        g = 0.075 if j % 2 == 0 else 0.05
        buf = np.zeros(n); add(buf, t0, s, g)
        pan = 0.3 if (b + j) % 2 == 0 else 0.7
        pluck[:, 0] += buf * (1 - pan); pluck[:, 1] += buf * pan

# ping-pong echo on the plucks (dotted eighth)
d = int(beat * 0.75 * SR)
echo = np.zeros_like(pluck)
for tap, g in enumerate([0.45, 0.28, 0.17, 0.10], start=1):
    o = d * tap
    if o < n:
        echo[o:, 0] += pluck[: n - o, 1] * g
        echo[o:, 1] += pluck[: n - o, 0] * g
mix = pad + pluck + echo

# simple reverb: convolve with a decaying noise tail (FFT)
ir_len = int(1.6 * SR)
ir_t = np.arange(ir_len) / SR
for ch in (0, 1):
    ir = rng.standard_normal(ir_len) * np.exp(-ir_t * 3.2)
    ir[0] = 0
    ir /= np.sqrt((ir ** 2).sum())
    size = 1 << int(np.ceil(np.log2(n + ir_len)))
    wet = np.fft.irfft(np.fft.rfft(mix[:, ch], size) * np.fft.rfft(ir, size), size)[:n]
    mix[:, ch] = 0.72 * mix[:, ch] + 0.45 * wet

# gentle low-pass at about 6.5 kHz so it stays soft
for ch in (0, 1):
    sp = np.fft.rfft(mix[:, ch])
    fr = np.fft.rfftfreq(n, 1 / SR)
    sp *= 1 / (1 + (fr / 6500.0) ** 4)
    mix[:, ch] = np.fft.irfft(sp, n)

# level: quiet bed, about -22 LUFS, peaks well under -10 dBFS
mix *= 0.08 / np.sqrt((mix ** 2).mean())
peak = np.abs(mix).max()
if peak > 0.32:
    mix *= 0.32 / peak

pcm = (np.clip(mix, -1, 1) * 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f'wrote {out}: {SECS:.1f}s @ {BPM:.0f} bpm, peak {20*np.log10(max(np.abs(mix).max(),1e-9)):.1f} dBFS')
