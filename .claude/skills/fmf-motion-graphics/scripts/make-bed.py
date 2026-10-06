#!/usr/bin/env python3
"""Synthesise an original music bed (no samples, so no licensing issues).

Usage: python3 make-bed.py out.wav [--seconds 30] [--bpm 96] [--style steady|arc]

steady (default): ONE groove at a constant density from the first bar to the last; only gain and chords move, so the
  track never feels like it speeds up. A gentle level lift at the reveal bar (default 15 s). Use this for ads.
arc: the older tension-to-lift plan described below (density builds; can feel like it accelerates).

Feel: positive, premium, confident. 2.5 s bars at 96 bpm, planned bar by bar (PLAN below) as a tension-to-lift arc:
  heart  / heart+  held-back heartbeat kick on every beat, low pulse, sparse piano (the hook)
  build  / build+  kick, snap, offbeat hats, electric-piano stabs; a riser leads into the drop
  lift             the reveal: soft impact, open chords, 16th hats, plucked arpeggio with ping-pong echo
  outro            groove thins and resolves on the tonic for the call to action
Electric piano (FM), sub bass, soft kick/snap/hats, sidechain-style ducking on keys and pad, light reverb.

Deterministic. Needs numpy. About -22 LUFS; the renderer adds fades. Beats fall on multiples of 60/bpm (0.625 s at 96 bpm);
put scene cuts and hits on that grid. The default PLAN is for 25 s (10 bars): hook bars 0-2, turn 3-4, lift from bar 5 (12.5 s).
"""
import sys, wave
import numpy as np

SR = 44100
out = sys.argv[1]
arg = lambda n, d: float(sys.argv[sys.argv.index(f'--{n}') + 1]) if f'--{n}' in sys.argv else d
SECS, BPM = arg('seconds', 30.0), arg('bpm', 96.0)
STYLE = sys.argv[sys.argv.index('--style') + 1] if '--style' in sys.argv else 'steady'
REVEAL = arg('reveal', 15.0)  # steady style: the bar where the level lifts
beat = 60.0 / BPM
bar = 4 * beat
step = beat / 4
n = int(SR * SECS)
rng = np.random.default_rng(11)
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)
T = lambda d: np.arange(int(d * SR)) / SR

def bus():
    return np.zeros((n, 2))

def put(b, t, sig, gain=1.0, pan=0.5):
    i = int(round(t * SR))
    if i >= n or i < 0:
        return
    seg = sig[: n - i] * gain
    b[i:i + len(seg), 0] += seg * np.cos(pan * np.pi / 2)
    b[i:i + len(seg), 1] += seg * np.sin(pan * np.pi / 2)

# ---- instruments -------------------------------------------------------------------------------
def kick():
    t = T(0.4)
    ph = 2 * np.pi * np.cumsum(48 + 110 * np.exp(-t * 28)) / SR
    return np.sin(ph) * np.exp(-t * 8) * np.minimum(1, t / 0.002)

def snap():
    t = T(0.2)
    nz = np.diff(rng.standard_normal(len(t)), prepend=0)
    return nz * np.exp(-t * 26) * 0.45 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 32) * 0.5

def hat(open_=False):
    t = T(0.18 if open_ else 0.05)
    nz = np.diff(rng.standard_normal(len(t)), n=2, prepend=[0, 0])
    return nz * np.exp(-t * (22 if open_ else 90)) * 0.5

def ep(f, dur, vel=1.0):
    """FM electric piano: warm tine with a short bell."""
    t = T(dur)
    mod = np.sin(2 * np.pi * f * t)
    car = np.sin(2 * np.pi * f * t + (1.5 * vel * np.exp(-t * 6) + 0.15) * mod)
    bell = 0.22 * np.sin(2 * np.pi * f * 7 * t) * np.exp(-t * 18)
    e = np.exp(-t * 2.4) * np.minimum(1, t / 0.004) * np.minimum(1, np.maximum(0, (dur - t) / 0.15))
    return (car + bell) * e * (1 + 0.05 * np.sin(2 * np.pi * 5 * t)) * vel

def bass(f, dur=0.55):
    t = T(dur)
    s = np.sin(2 * np.pi * f * t) + 0.28 * np.sin(2 * np.pi * 2 * f * t)
    return s * np.minimum(1, t / 0.006) * np.exp(-t * 4.2) * np.minimum(1, np.maximum(0, (dur - t) / 0.05))

def pad_tone(f, dur):
    t = T(dur)
    s = sum(np.sin(2 * np.pi * f * (1 + d) * t) for d in (-0.0035, 0, 0.0035)) / 3
    s += 0.15 * np.sin(2 * np.pi * 2 * f * t)
    e = np.minimum(1, t / 0.9) * np.minimum(1, np.maximum(0, (dur - t) / 1.3))
    return s * e ** 1.5

def riser(d):
    t = T(d)
    nz = rng.standard_normal(len(t))
    a = 0.02 + 0.9 * (t / d) ** 2
    y = np.zeros_like(nz); acc = 0.0
    for i in range(len(nz)):
        acc += a[i] * (nz[i] - acc); y[i] = acc
    sweep = np.sin(2 * np.pi * np.cumsum(180 * np.exp(np.log(8) * t / d)) / SR) * 0.3
    return (y * 3 + sweep) * (t / d) ** 2

def impact():
    t = T(1.8)
    boom = np.sin(2 * np.pi * np.cumsum(52 + 40 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.2)
    air = np.diff(rng.standard_normal(len(t)), prepend=0) * np.exp(-t * 5) * 0.12
    return boom + air

# ---- score -------------------------------------------------------------------------------------
CHORDS = {  # name: (rootless voicing, bass root)
    'Am7': ([52, 55, 60, 64], 45), 'Fmaj7': ([52, 57, 60, 65], 41), 'Cmaj9': ([55, 59, 62, 64], 48),
    'G69': ([57, 59, 62, 64], 43), 'Fmaj9': ([55, 57, 60, 64], 41),
}
PLAN = [('Am7', 'heart'), ('Am7', 'heart+'), ('Fmaj7', 'heart+'), ('Fmaj7', 'build'), ('G69', 'build+'),
        ('Cmaj9', 'lift'), ('Fmaj9', 'lift'), ('G69', 'lift'), ('Fmaj9', 'lift'), ('Cmaj9', 'outro')]
NB = int(np.ceil(SECS / bar))
if STYLE == 'steady':
    LOOP = ['Am7', 'Fmaj7', 'Cmaj9', 'G69', 'Am7', 'Fmaj7', 'Cmaj9', 'G69', 'Fmaj9', 'G69', 'Cmaj9', 'Cmaj9']
    PLAN = [(LOOP[i % len(LOOP)], 'groove') for i in range(NB)]
    PLAN[-1] = (PLAN[-1][0], 'groove_end')
else:
    PLAN = (PLAN * 4)[:NB] if NB != len(PLAN) else PLAN
ARP = [0, 2, 3, 1, 3, 2, 1, 0]
FIRST_LIFT = next((i for i, (_, k) in enumerate(PLAN) if k == 'lift'), None)

drums, kicks_b, keys, arp, padb, bassb, fx = bus(), bus(), bus(), bus(), bus(), bus(), bus()
kick_times = []

def K(t, v=1.0):
    kick_times.append(t); put(kicks_b, t, kick(), 0.55 * v)

for b, (name, kind) in enumerate(PLAN):
    t0 = b * bar
    if t0 >= SECS:
        break
    v, root = CHORDS[name]
    at = lambda s, t0=t0: t0 + s * step

    for k, m in enumerate(v):  # pad, sustained into the next bar
        put(padb, t0, pad_tone(mtof(m), bar + 1.4), 0.07, 0.25 + 0.5 * k / 3)

    if kind in ('groove', 'groove_end'):
        # identical pattern every bar: kick 1 and 3, snap 2 and 4, even eighth hats, bass, stabs, a soft eighth arpeggio
        for s_ in (0, 8):
            K(at(s_))
        for s_ in (4, 12):
            put(drums, at(s_), snap(), 0.20)
        for s_ in range(0, 16, 2):
            put(drums, at(s_), hat(), 0.08 if s_ % 4 == 2 else 0.05, 0.62)
        for s_, g in ((0, 0.32), (6, 0.24), (10, 0.24), (14, 0.18)):
            put(bassb, at(s_), bass(mtof(root)), g)
        for s_ in (0, 6, 10):
            for k, m in enumerate(v):
                put(keys, at(s_) + k * 0.012, ep(mtof(m), 0.9, 0.65), 0.07, 0.3 + 0.4 * k / 3)
        for j, s_ in enumerate(range(0, 16, 2)):
            put(arp, at(s_) + step, ep(mtof(v[ARP[j] % 4] + 12), 0.6, 0.5), 0.05, 0.3 if j % 2 == 0 else 0.7)
        if kind == 'groove_end':
            for k, m in enumerate(v):
                put(keys, at(8) + k * 0.012, ep(mtof(m), 2.6, 0.7), 0.06, 0.3 + 0.4 * k / 3)
    elif kind in ('heart', 'heart+'):
        for j, vel in enumerate([1.0, 0.8, 0.8, 0.95]):
            K(t0 + j * beat, vel * (0.8 if kind == 'heart' else 0.9))
        put(bassb, at(0), bass(mtof(root)), 0.30)
        put(bassb, at(10), bass(mtof(root)), 0.22)
        if kind == 'heart+':
            put(bassb, at(6), bass(mtof(root)), 0.18)
            for s_ in (2, 6, 10, 14):
                put(drums, at(s_), hat(), 0.05, 0.62)
        put(keys, at(0), ep(mtof(v[0]), 1.2, 0.6), 0.10, 0.4)
        put(keys, at(8), ep(mtof(v[3] + 12), 1.2, 0.5), 0.10, 0.6)
    elif kind in ('build', 'build+'):
        for s_ in (0, 8):
            K(at(s_))
        if kind == 'build+':
            K(at(10), 0.6); K(at(14), 0.4)
        for s_ in (4, 12):
            put(drums, at(s_), snap(), 0.22)
        for s_ in ([2, 6, 10, 14] if kind == 'build' else range(0, 16, 2)):
            put(drums, at(s_), hat(), 0.10 if s_ % 4 == 2 else 0.06, 0.62)
        for s_, g in ((0, 0.34), (6, 0.26), (10, 0.26), (14, 0.20)):
            put(bassb, at(s_), bass(mtof(root)), g)
        for s_ in (0, 6, 10, 14):
            for k, m in enumerate(v):
                put(keys, at(s_) + k * 0.012, ep(mtof(m), 0.9, 0.7), 0.075, 0.3 + 0.4 * k / 3)
    elif kind == 'lift':
        for s_ in (0, 8):
            K(at(s_))
        K(at(10), 0.6)
        for s_ in (4, 12):
            put(drums, at(s_), snap(), 0.24)
        for s_ in range(0, 16, 2):
            put(drums, at(s_), hat(), 0.10 if s_ % 4 == 2 else 0.06, 0.62)
        put(drums, at(14), hat(True), 0.07, 0.4)
        for s_, g in ((0, 0.34), (6, 0.26), (10, 0.26), (14, 0.20)):
            put(bassb, at(s_), bass(mtof(root)), g)
        for s_ in (0, 6, 10):
            for k, m in enumerate(v):
                put(keys, at(s_) + k * 0.012, ep(mtof(m), 0.9, 0.7), 0.075, 0.3 + 0.4 * k / 3)
        for j, s_ in enumerate(range(0, 16, 2)):  # plucked arpeggio, an octave up
            put(arp, at(s_) + step, ep(mtof(v[ARP[j] % 4] + 12), 0.6, 0.55), 0.07, 0.3 if j % 2 == 0 else 0.7)
    else:  # outro: thin out and resolve
        K(at(0)); K(at(8), 0.8)
        for s_ in (2, 6, 10, 14):
            put(drums, at(s_), hat(), 0.06, 0.62)
        put(bassb, at(0), bass(mtof(root), 1.2), 0.30)
        for k, m in enumerate(v):
            put(keys, at(0) + k * 0.012, ep(mtof(m), 2.4, 0.75), 0.085, 0.3 + 0.4 * k / 3)
        for j, s_ in enumerate(range(0, 16, 4)):
            put(arp, at(s_) + step, ep(mtof(v[ARP[j * 2] % 4] + 12), 0.8, 0.5), 0.06, 0.3 if j % 2 == 0 else 0.7)

# riser into the first lift, soft impact on it
if FIRST_LIFT is not None and STYLE != 'steady':
    lt = FIRST_LIFT * bar
    put(fx, lt - 1.25, riser(1.25), 0.10)
    put(fx, lt, impact(), 0.55)
    put(fx, lt, hat(True), 0.25)

# ---- mix ---------------------------------------------------------------------------------------
def duck_curve():
    t = np.arange(n) / SR
    d = np.ones(n)
    for k in kick_times:
        m = t >= k
        d[m] = np.minimum(d[m], 1 - 0.4 * np.exp(-(t[m] - k) / 0.12))
    return d[:, None]

def reverb(x, wet, secs=1.5, decay=3.4):
    ir_t = np.arange(int(secs * SR)) / SR
    res = x * (1 - wet)
    size = 1 << int(np.ceil(np.log2(n + len(ir_t))))
    for ch in (0, 1):
        ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * decay); ir[0] = 0
        ir /= np.sqrt((ir ** 2).sum())
        w = np.fft.irfft(np.fft.rfft(x[:, ch], size) * np.fft.rfft(ir, size), size)[:n]
        res[:, ch] += wet * 1.6 * w
    return res

d_ = int(beat * 0.75 * SR)  # ping-pong echo (dotted eighth) on the arpeggio only
echo = np.zeros_like(arp)
for tap, g in enumerate([0.42, 0.26, 0.15], start=1):
    o = d_ * tap
    if o < n:
        echo[o:, 0] += arp[: n - o, 1] * g
        echo[o:, 1] += arp[: n - o, 0] * g

duck = duck_curve()
tonal = reverb((keys + arp + echo + padb) * duck, 0.38)
mix = tonal + kicks_b + drums + bassb + reverb(fx, 0.2)

# energy arc: held back for the hook, building through the turn, a clear lift on the reveal, settling for the CTA
ARCV = {'heart': 0.62, 'heart+': 0.72, 'build': 0.84, 'build+': 0.94, 'outro': 1.0, 'groove': 1.0, 'groove_end': 1.0}
LIFTS = [1.30, 1.20, 1.14, 1.10]
arc, li = [], 0
for _, k in PLAN:
    if k == 'lift':
        arc.append(LIFTS[min(li, 3)]); li += 1
    else:
        arc.append(ARCV[k])
if STYLE == 'steady':  # flat level, a gentle lift from the reveal bar onwards
    rb = int(REVEAL / bar)
    arc = [0.92 if i < rb else 1.08 for i in range(len(PLAN))]
    FIRST_LIFT = None
tt = np.arange(n) / SR
anchors = [i * bar + bar / 2 for i in range(len(arc))]
gain = np.interp(tt, anchors, arc)
if FIRST_LIFT is not None:  # land the lift on beat 1 of the first lift bar
    lt = FIRST_LIFT * bar
    gain = np.where((tt > lt - 0.05) & (tt < lt + 0.05), np.interp(tt, [lt - 0.05, lt + 0.05], [0.85, arc[FIRST_LIFT]]), gain)
mix *= gain[:, None]

# soften the top end, normalise, limit gently
for ch in (0, 1):
    sp = np.fft.rfft(mix[:, ch]); fr = np.fft.rfftfreq(n, 1 / SR)
    mix[:, ch] = np.fft.irfft(sp / (1 + (fr / 9000.0) ** 4), n)
mix *= 0.12 / np.sqrt((mix ** 2).mean())
mix = np.tanh(mix * 1.4) / 1.4
peak = np.abs(mix).max()
if peak > 0.40:
    mix *= 0.40 / peak

pcm = (np.clip(mix, -1, 1) * 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f'wrote {out}: {SECS:.1f}s @ {BPM:.0f} bpm, {NB} bars, peak {20*np.log10(max(np.abs(mix).max(),1e-9)):.1f} dBFS')
