# Music Box Web Audio Synthesis

Technique for synthesizing classical music box / jewelry box sounds using the Web Audio API, without any external audio files.

## Core Sound

A music box uses tuned steel tines plucked by pins on a rotating drum. The sound is:

- **Pure tone** (sine wave) — like a tuning fork
- **Fast attack** (5-10ms) — the pin plucks the tine
- **Long, gentle decay** — the tine rings freely for 1-2 seconds
- **Slight mechanical click** at the start — the pin releasing
- **Subtle harmonics** for warmth and shimmer

## Implementation

### Main Tine (osc1)
```javascript
const osc1 = audioCtx.createOscillator();
const gain1 = audioCtx.createGain();
osc1.type = 'sine';
osc1.frequency.setValueAtTime(freq, now);
gain1.gain.setValueAtTime(0, now);
gain1.gain.linearRampToValueAtTime(0.30, now + 0.006); // Fast attack
gain1.gain.exponentialRampToValueAtTime(0.001, now + duration * 1.2); // Long decay
```

### Octave Shimmer (osc2) — slightly detuned for ethereal warmth
```javascript
const osc2 = audioCtx.createOscillator();
osc2.type = 'sine';
osc2.frequency.setValueAtTime(freq * 2.01, now); // +1 cent detune
```

### Fifth Harmonic (osc3) — metallic tine ring
```javascript
const osc3 = audioCtx.createOscillator();
osc3.type = 'sine';
osc3.frequency.setValueAtTime(freq * 3.02, now);
```

### Mechanical Pluck (noise burst)
```javascript
const bufferSize = audioCtx.sampleRate * 0.012;
const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
const data = buffer.getChannelData(0);
for (let i = 0; i < bufferSize; i++) {
  data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufferSize, 10);
}
// High-pass filter at 4000Hz to keep only the click
```

## Tempo & Feel

- Classical music box: **0.35-0.40s per beat** — slow, graceful
- Notes should overlap (the decay extends past the next note's attack)
- Higher octave (C5-C6 range) sounds most authentic

## Accompaniment Layers

For a richer arrangement when no audio file is available:

1. **Chime chords** — soft celesta-like chord accompaniment (C, F, G, G7)
2. **Descant sparkles** — twinkling high counter-melody notes on select beats
3. **Sustained pad** — warm, breathy low chord that sustains throughout

## Audio Iteration Flow (for reference)

This is the progression users often request:
1. Synthesized sine → "make it sound like a jewelry box"
2. Music box with harmonics → "make it sound like a xylophone"
3. Xylophone → "make it sound like a classical music box"
4. Music box → "slower, higher notes"
5. Music box → "add more instruments"
6. Any synthesized → "use this audio file instead" (switch to HTML5 Audio)

Keep the `playMusic()` / `stopMusic()` interface modular so the audio source can be swapped without changing the card logic.
