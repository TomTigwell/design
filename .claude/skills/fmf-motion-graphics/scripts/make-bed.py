#!/usr/bin/env python3
"""Synthesise an original music bed (no samples, so no licensing issues).

Usage: python3 make-bed.py out.wav [--seconds 15] [--bpm 96]

Feel: positive, premium, confident. A tension-to-lift arc over 2.5 s bars at 96 bpm:
  bar 1  Am7   heartbeat kick on every beat + low pulse (a hook that lands one hit per beat)
  bar 2  Fmaj7 groove builds: kick, snap, offbeat hats, electric-piano stabs, riser into the drop
  bar 3  Cmaj9 the lift: soft impact, open chords, 16th hats, plucked arpeggio with ping-pong echo
  bars 4-6     G6/9, Fmaj9, Cmaj9: the groove carries and resolves on the tonic
Electric piano (FM), sub bass, soft kick/snap/hats, sidechain-style ducking on the keys and pad, light reverb.

Deterministic. Needs numpy. The mix is kept under captions-free visuals at about -21 LUFS; the renderer adds fades.
Beats fall on multiples of 60/bpm (0.625 s at 96 bpm); put scene cuts and hits on that grid.
"""
import sys, wave
import numpy as np

SR = 44100
out = sys.argv[1]
arg = lambda n, d: float(sys.argv[sys.argv.index(f'--{n}') + 1]) if f'--{n}' in sys.argv else d
SECS, BPM = arg('seconds', 15.0), arg('bpm', 96.0)
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
BASS = [45, 41, 48, 43, 41, 48]  # A F C G F C
VOICE = [  # rootless voicings
    [52, 55, 60, 64],  # Am7
    [52, 57, 60, 65],  # Fmaj7
    [55, 59, 62, 64],  # Cmaj9
    [57, 59, 62, 64],  # G6/9
    [55, 57, 60, 64],  # Fmaj9
    [55, 59, 62, 64],  # Cmaj9
]
ARP = [0, 2, 3, 1, 3, 2, 1, 0]

drums, kicks_b, keys, arp, padb, bassb, fx = bus(), bus(), bus(), bus(), bus(), bus(), bus()
kick_times = []

def K(t, v=1.0):
    kick_times.append(t); put(kicks_b, t, kick(), 0.55 * v)

for b in range(int(np.ceil(SECS / bar))):
    t0 = b * bar
    ch, v = VOICE[min(b, 5)], VOICE[min(b, 5)]
    root = BASS[min(b, 5)]
    at = lambda s: t0 + s * step

    # pad: sustained, overlaps into the next bar
    for k, m in enumerate(v):
        put(padb, t0, pad_tone(mtof(m), bar + 1.4), 0.07, 0.25 + 0.5 * k / 3)

    if b == 0:  # hook: a heartbeat, one hit per beat, matching one question card per beat
        for j, vel in enumerate([1.0, 0.8, 0.8, 1.0]):
            K(t0 + j * beat, vel)
        put(bassb, at(0), bass(mtof(root)), 0.30)
        put(bassb, at(10), bass(mtof(root)), 0.22)
        put(keys, at(0), ep(mtof(v[0]), 1.2, 0.6), 0.10, 0.4)
        put(keys, at(8), ep(mtof(v[3] + 12), 1.2, 0.5), 0.10, 0.6)
    else:
        for s_ in ([0, 8] if b != 1 else [0, 8]):
            K(at(s_))
        if b >= 2:
            K(at(10), 0.6)
        for s_ in (4, 12):
            put(drums, at(s_), snap(), 0.24)
        hat_steps = [2, 6, 10, 14] if b == 1 else list(range(0, 16, 2))
        for s_ in hat_steps:
            put(drums, at(s_), hat(), 0.10 if s_ % 4 == 2 else 0.06, 0.62)
        put(drums, at(14), hat(True), 0.07, 0.4)
        for s_, g in ((0, 0.34), (6, 0.26), (10, 0.26), (14, 0.20)) if b < 5 else ((0, 0.34), (10, 0.22)):
            put(bassb, at(s_), bass(mtof(root)), g)
        stabs = (0, 6, 10, 14) if b == 1 else (0, 6, 10)
        for s_ in stabs:
            for k, m in enumerate(v):
                put(keys, at(s_) + k * 0.012, ep(mtof(m), 0.9, 0.7), 0.075, 0.3 + 0.4 * k / 3)
        if b >= 2:  # plucked arpeggio, one octave up
            for j, s_ in enumerate(range(0, 16, 2)):
                if b == 5 and s_ >= 8:
                    continue
                m = v[ARP[j] % 4] + 12
                put(arp, at(s_) + step, ep(mtof(m), 0.6, 0.55), 0.07, 0.3 if j % 2 == 0 else 0.7)

# transitions: riser into the lift, soft impact on it
riser_len = 1.25
put(fx, 2 * bar - riser_len, riser(riser_len), 0.10)
put(fx, 2 * bar, impact(), 0.55)
put(fx, 2 * bar, hat(True), 0.25)

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

# ping-pong echo (dotted eighth) on the arpeggio only
d_ = int(beat * 0.75 * SR)
echo = np.zeros_like(arp)
for tap, g in enumerate([0.42, 0.26, 0.15], start=1):
    o = d_ * tap
    if o < n:
        echo[o:, 0] += arp[: n - o, 1] * g
        echo[o:, 1] += arp[: n - o, 0] * g

duck = duck_curve()
tonal = reverb((keys + arp + echo + padb) * duck, 0.38)
mix = tonal + kicks_b + drums + bassb + reverb(fx, 0.2)

# energy arc: held-back hook, build, then a clear lift on the reveal (bar 3), settling for the call to action
ARC = [0.62, 0.80, 1.30, 1.15, 1.15, 1.0]
tt = np.arange(n) / SR
anchors = [(i * bar + bar / 2) for i in range(len(ARC))]
gain = np.interp(tt, anchors, ARC)
gain[tt >= 2 * bar] = np.interp(tt[tt >= 2 * bar], anchors, ARC) * 1.0
# a short ramp up into the drop so the lift lands on beat 1 of bar 3 rather than before it
jump = (tt > 2 * bar - 0.05)
gain = np.where(jump & (tt < 2 * bar + 0.05), np.interp(tt, [2 * bar - 0.05, 2 * bar + 0.05], [0.85, 1.30]), gain)
mix *= gain[:, None]

# soften the top end (keeps hats airy but never harsh), then limit gently
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
print(f'wrote {out}: {SECS:.1f}s @ {BPM:.0f} bpm, peak {20*np.log10(max(np.abs(mix).max(),1e-9)):.1f} dBFS')
