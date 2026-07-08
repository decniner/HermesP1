---
name: retro-arcade-game-development
description: "Build retro-style arcade games in single-file HTML (Canvas + Web Audio API) — space shooters, flappy bird clones, platformers, pachislot machines, and other 80s/90s-style games with pixel art, PC speaker sound effects, and mobile touch controls."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [retro, arcade, game-dev, canvas, html5, javascript, pixel-art]
    related_skills: [web-app-audit, delegated-qa-workflow]
---

# Retro Arcade Game Development

Build classic 80s/90s-style arcade games as single-file HTML applications using HTML5 Canvas, JavaScript, and the Web Audio API. Games run in any browser, support mobile touch controls, and feature retro PC speaker-style sound effects.

Reference files: [`references/juggler-pachislot-cabinet-design.md`](references/juggler-pachislot-cabinet-design.md)  [`references/win95-desktop-and-solitaire.md`](references/win95-desktop-and-solitaire.md) — pachislot cabinet layout, GOGO lamp mechanics, and common bugs.  [`references/js-syntax-pitfalls.md`](references/js-syntax-pitfalls.md) — JS computed property name syntax, `roundRect` compatibility, brace balance check, and Node.js pre-delivery syntax verification.  [`references/yamasa-king-pulsar-cabinet.md`](references/yamasa-king-pulsar-cabinet.md) — Yamasa King Pulsar cabinet style, build order, and green/gold frame drawing code.

## Critical Pre-Step: Ask Clarifying Questions

BEFORE writing any code, ask clarifying questions to fully understand what the user wants. Do NOT jump into solutions.

Questions to ask:
- **Genre:** What kind of game? (shooter, platformer, puzzle, runner, pachislot)
- **Platform:** Browser? Mobile? Both?
- **Style:** Retro pixel art? Modern? Specific reference game?
- **Controls:** Keyboard? Touch? Both? Specific control scheme?
- **Features:** Multiplayer? Power-ups? Bosses? Score tracking?
- **Audio:** Retro beeps? Music?
- **Specific references:** "Like X game from Y era" — ask for screenshot/description

Failure to ask these questions first will result in the user correcting you mid-build, wasting time.

## Core Architecture

Every retro arcade game follows this pattern:

```
Single HTML file with:
├── <style>     — Retro theme, CRT scanline effect, responsive sizing
├── <canvas>    — All game graphics rendered here
├── <div id="ui"> — Menu overlay, game-over screen
└── <script>
    ├── Audio system (Web Audio API)
    ├── Game state (menu → playing → gameover)
    ├── Game loop (requestAnimationFrame)
    ├── Player entity
    ├── Enemies / obstacles
    ├── Collision detection
    ├── Scoring + lives
    └── Touch/mouse input
```

## Step 1: Audio System — PC Speaker Sounds

Use the Web Audio API to generate retro beeps, explosions, and jingles without any audio files:

```javascript
let audioCtx = null;
function initAudio() {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
}

// Simple beep
function beep(freq, dur, type='square', vol=0.06) {
    if (!audioCtx) return;
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.type = type;        // 'square' = classic PC speaker, 'sawtooth' = harsher
    o.frequency.setValueAtTime(freq, audioCtx.currentTime);
    g.gain.setValueAtTime(vol, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + dur);
    o.connect(g); g.connect(audioCtx.destination);
    o.start(); o.stop(audioCtx.currentTime + dur);
}

// Noise explosion
function explosion() {
    if (!audioCtx) return;
    const buf = audioCtx.createBuffer(1, audioCtx.sampleRate * 0.2, audioCtx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 3);
    const s = audioCtx.createBufferSource(); s.buffer = buf;
    const g = audioCtx.createGain(); g.gain.setValueAtTime(0.08, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.2);
    s.connect(g); g.connect(audioCtx.destination); s.start();
}

// Play melody (array of frequencies) for power-ups or level start
function playMelody(notes) {
    notes.forEach((n, i) => setTimeout(() => beep(n, 0.1), i * 100));
}
```

### Sound Effect Reference

| Effect | Technique |
|--------|-----------|
| Shoot | Two rapid beeps descending (880→660 Hz) |
| Explosion | Noise buffer with exponential decay |
| Player hit | Sawtooth wave descending (220→150 Hz) |
| Game over | Four descending notes (440→370→330→220 Hz) |
| Power-up | Three ascending notes (660→880→1100 Hz) |
| Level start | Four ascending notes (220→330→440→660 Hz) |
| Music box melody (simple) | Triangle wave + octave + 3rd harmonic + noise tail (see section below) |
| Music box melody (classical) | Sine wave tines + detuned octave + 5th harmonic + mechanical pluck + chord accompaniment + descant + pad (see section below) |

### Music Box / Jewelry Box Synthesis

Two approaches depending on the desired feel. The **simple** version works for short jingles and menu themes. The **classical** version produces a richer, multi-layered arrangement suitable for greeting cards, level-complete fanfares, or any context where a traditional music box sound is desired.

#### Simple Music Box (Triangle-wave tine)

Use for short jingles, menu themes, and game sound effects:

```javascript
function playMusicBoxNote(freq, duration) {
  if (!audioCtx) return;
  const now = audioCtx.currentTime;

  // Main tone — bright triangle wave (plucked tine feel)
  const osc1 = audioCtx.createOscillator();
  const gain1 = audioCtx.createGain();
  osc1.type = 'triangle';
  osc1.frequency.setValueAtTime(freq, now);
  gain1.gain.setValueAtTime(0.35, now);
  gain1.gain.exponentialRampToValueAtTime(0.001, now + duration * 0.6);
  osc1.connect(gain1);
  gain1.connect(audioCtx.destination);
  osc1.start(now);
  osc1.stop(now + duration);

  // Octave harmonic — delicate bell shimmer
  const osc2 = audioCtx.createOscillator();
  const gain2 = audioCtx.createGain();
  osc2.type = 'sine';
  osc2.frequency.setValueAtTime(freq * 2, now);
  gain2.gain.setValueAtTime(0.08, now);
  gain2.gain.exponentialRampToValueAtTime(0.001, now + duration * 0.4);
  osc2.connect(gain2);
  gain2.connect(audioCtx.destination);
  osc2.start(now);
  osc2.stop(now + duration);

  // 3rd harmonic ring for extra sparkle
  const osc3 = audioCtx.createOscillator();
  const gain3 = audioCtx.createGain();
  osc3.type = 'sine';
  osc3.frequency.setValueAtTime(freq * 3, now);
  gain3.gain.setValueAtTime(0.03, now);
  gain3.gain.exponentialRampToValueAtTime(0.001, now + duration * 0.25);
  osc3.connect(gain3);
  gain3.connect(audioCtx.destination);
  osc3.start(now);
  osc3.stop(now + duration);

  // Reverb-like noise tail (mechanical echo)
  const bufferSize = audioCtx.sampleRate * 0.08;
  const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < bufferSize; i++) {
    data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufferSize, 3);
  }
  const noise = audioCtx.createBufferSource();
  noise.buffer = buffer;
  const gainN = audioCtx.createGain();
  gainN.gain.setValueAtTime(0.04, now);
  gainN.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
  noise.connect(gainN);
  gainN.connect(audioCtx.destination);
  noise.start(now);
}
```

**Key parameters for simple music box feel:**
- **Tempo**: ~0.30s per beat (slow, delicate winding pace)
- **Triangle wave** for the bell-like plucked tine
- **Fast decay** — notes decay within ~60% of nominal duration
- **Low harmonic volumes** — octave at ~0.08, 3rd at ~0.03 (shimmer without overpowering)
- **Noise reverb tail** — very quiet (0.04 gain), very short (0.08s), subtle mechanical echo

#### Classical Music Box (Sine-wave steel tine + multi-layer arrangement)

Use for greeting cards, fanfares, title screens, and any context needing a richer, more authentic sound. This version uses plucked steel tines (sine wave with fast attack + long sustain) plus three supporting layers.

**Layer 1 — Main music box tine:**
```javascript
function playMusicBoxTine(freq, duration) {
  if (!audioCtx) return;
  const now = audioCtx.currentTime;

  // Main steel tine — pure sine
  const osc1 = audioCtx.createOscillator();
  const gain1 = audioCtx.createGain();
  osc1.type = 'sine';
  osc1.frequency.setValueAtTime(freq, now);
  gain1.gain.setValueAtTime(0, now);
  gain1.gain.linearRampToValueAtTime(0.30, now + 0.006);
  gain1.gain.exponentialRampToValueAtTime(0.001, now + duration * 1.2);
  osc1.connect(gain1);
  gain1.connect(audioCtx.destination);
  osc1.start(now);
  osc1.stop(now + duration + 0.3);

  // Detuned octave shimmer (ethereal warmth)
  const osc2 = audioCtx.createOscillator();
  const gain2 = audioCtx.createGain();
  osc2.type = 'sine';
  osc2.frequency.setValueAtTime(freq * 2.01, now);
  gain2.gain.setValueAtTime(0, now);
  gain2.gain.linearRampToValueAtTime(0.06, now + 0.008);
  gain2.gain.exponentialRampToValueAtTime(0.001, now + duration * 0.8);
  osc2.connect(gain2);
  gain2.connect(audioCtx.destination);
  osc2.start(now);
  osc2.stop(now + duration + 0.3);

  // 5th harmonic metallic ring
  const osc3 = audioCtx.createOscillator();
  const gain3 = audioCtx.createGain();
  osc3.type = 'sine';
  osc3.frequency.setValueAtTime(freq * 3.02, now);
  gain3.gain.setValueAtTime(0, now);
  gain3.gain.linearRampToValueAtTime(0.025, now + 0.005);
  gain3.gain.exponentialRampToValueAtTime(0.001, now + duration * 0.5);
  osc3.connect(gain3);
  gain3.connect(audioCtx.destination);
  osc3.start(now);
  osc3.stop(now + duration + 0.2);

  // Mechanical pluck (pin releasing the tine)
  const bufSize = audioCtx.sampleRate * 0.012;
  const buffer = audioCtx.createBuffer(1, bufSize, audioCtx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < bufSize; i++) {
    data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufSize, 10);
  }
  const noise = audioCtx.createBufferSource();
  noise.buffer = buffer;
  const gainN = audioCtx.createGain();
  gainN.gain.setValueAtTime(0.04, now);
  gainN.gain.exponentialRampToValueAtTime(0.001, now + 0.012);
  const filter = audioCtx.createBiquadFilter();
  filter.type = 'highpass';
  filter.frequency.setValueAtTime(4000, now);
  noise.connect(filter);
  filter.connect(gainN);
  gainN.connect(audioCtx.destination);
  noise.start(now);
}
```

**Layer 2 — Celesta/chime chord accompaniment** (soft bell-like harmony):
```javascript
const chordIntervals = {
  'C':  [0, 4, 7],
  'F':  [0, 4, 7],
  'G':  [0, 4, 7],
  'G7': [0, 4, 7, 10]
};

function playChordChord(rootFreq, chordType, duration) {
  if (!audioCtx) return;
  const now = audioCtx.currentTime;
  const intervals = chordIntervals[chordType];
  if (!intervals) return;
  intervals.forEach((semitone, idx) => {
    const freq = rootFreq * Math.pow(2, semitone / 12);
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, now);
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.035 - idx * 0.007, now + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.001, now + duration * 0.7);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + duration);
  });
}
```

**Layer 3 — Celesta descant** (twinkling high counter-melody):
```javascript
function playDescant(beatIndex, time) {
  if (!audioCtx) return;
  const descantNotes = {
    1:  [1046, 0.12], 4:  [1174, 0.12], 7:  [1398, 0.12],
    10: [1244, 0.12], 13: [1568, 0.12], 16: [1398, 0.12],
    19: [1046, 0.12], 22: [1174, 0.12], 25: [1398, 0.12],
  };
  if (descantNotes[beatIndex]) {
    const [freq, dur] = descantNotes[beatIndex];
    const now = audioCtx.currentTime + time / 1000;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, now);
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.025, now + 0.005);
    gain.gain.exponentialRampToValueAtTime(0.001, now + dur);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + dur);
  }
}
```

**Layer 4 — Sustained warm pad** (gentle breath underneath):
```javascript
function playPad(rootFreq, duration) {
  if (!audioCtx) return;
  const now = audioCtx.currentTime;
  // Soft sustained major chord one octave below
  const notes = [
    rootFreq * 0.5,
    rootFreq * 0.5 * Math.pow(2, 4/12),
    rootFreq * 0.5 * Math.pow(2, 7/12)
  ];
  notes.forEach((freq) => {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, now);
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.02, now + 0.5);
    gain.gain.setValueAtTime(0.02, now + duration * 0.6);
    gain.gain.exponentialRampToValueAtTime(0.001, now + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + duration);
  });
}
```

**Playing the full arrangement together:**

```javascript
const chordProgression = [
  [262, 'C', 0, 2],  [262, 'C', 2, 1], [349, 'F', 3, 1], [262, 'C', 4, 1],
  [392, 'G', 5, 1],  [392, 'G7', 6, 1],
  // ... map remaining chords to melody beat positions
];

function playAll() {
  const tempo = 0.38; // slow, dreamy pace
  let time = 0;
  let chordIdx = 0;
  let beatCount = 0;

  // Start the pad (sustains entire song)
  playPad(262, totalDuration);

  melody.forEach(([freq, dur]) => {
    const noteDur = dur * tempo;

    // Layer 1: Main tine
    setTimeout(() => playMusicBoxTine(freq, noteDur), time * 1000);

    // Layer 2: Chords
    if (chordIdx < chordProgression.length) {
      const [rFreq, cType, cStart, cLen] = chordProgression[chordIdx];
      if (beatCount === cStart) {
        const chordDur = cLen * 0.5 * tempo + 0.4;
        setTimeout(() => playChordChord(rFreq, cType, chordDur), time * 1000);
        chordIdx++;
      }
    }

    // Layer 3: Descant
    playDescant(beatCount, time * 1000);

    time += noteDur + 0.05;
    beatCount++;
  });
}
```

**Key parameters for classical music box feel:**
- **Tempo**: ~0.35-0.38s per beat (even slower than simple version — notes overlap for a dreamy cascade)
- **Sine wave** (not triangle) for the main tine — gives a purer, more delicate steel tone
- **Slightly detuned harmonics** — octave at 2.01× (not exactly 2×), 5th at 3.02× — creates authentic mechanical imperfection
- **Long sustain** — notes ring for 1.2× their nominal duration (overlap creates the iconic music box cascade)
- **Fast attack** (0.006s) with linear ramp — mimics the instantaneous pluck of a pin on a steel tine
- **Mechanical pluck sound** — a filtered noise burst (very quiet, very short) simulating the pin releasing
- **Higher octave** — transpose melody up one octave (C5-C6 range) for a more delicate, authentic pitch

#### Playing a melody at higher octave

For a more delicate music box sound, transpose the melody frequencies up one octave (multiply by 2):

```javascript
// Happy Birthday in higher octave (C5-C6)
const birthdayMelody = [
  [524, 0.3], [524, 0.3], [588, 0.5], [524, 0.5], [698, 0.5], [660, 0.8],
  [524, 0.3], [524, 0.3], [588, 0.5], [524, 0.5], [784, 0.5], [698, 0.8],
  [524, 0.3], [524, 0.3], [1046, 0.5], [880, 0.5], [698, 0.5], [660, 0.5], [588, 0.5],
  [988, 0.3], [988, 0.3], [880, 0.5], [698, 0.5], [784, 0.5], [698, 0.8]
];
```

Tempo for classical music box: 0.38s per beat. The chord progression must stay at lower octave (C4 around 262Hz) while the melody sings at C5-C6.

See `references/birthday-card-example.md` for a complete working single-file HTML greeting card with the classical multi-layer music box technique.

## Step 2: Game Loop

```javascript
let state = 'menu';  // 'menu' | 'playing' | 'gameover'
let frame = 0;

function update() {
    if (state !== 'playing') return;
    frame++;
    // Update player position, enemies, bullets, collisions, scoring
}

function draw() {
    // Clear canvas
    // Draw background (stars, sky gradient, scanlines)
    // Draw game elements (player, enemies, bullets, particles)
    // Draw HUD (score, lives)
}

function gameLoop() {
    update();
    draw();
    requestAnimationFrame(gameLoop);
}
```

## Step 3: Mobile Touch Controls

Essential for Android play. Two patterns:

### Pattern A: Drag to Move + Auto-Fire (Shooter)
```javascript
let touching = false;
let touchX = 0, touchY = 0;

canvas.addEventListener('touchstart', (e) => {
    e.preventDefault();
    initAudio();
    const t = e.touches[0];
    touchX = t.clientX; touchY = t.clientY;
    touching = true;
    // Start/menu/restart logic
});

canvas.addEventListener('touchmove', (e) => {
    e.preventDefault();
    const t = e.touches[0];
    touchX = t.clientX; touchY = t.clientY;
});

canvas.addEventListener('touchend', (e) => {
    e.preventDefault();
    touching = false;
});

// In update():
if (touching) {
    const dx = touchX - player.x;
    const dy = touchY - player.y;
    const dist = Math.sqrt(dx*dx + dy*dy);
    if (dist > 5) {
        player.x += (dx / dist) * player.speed * 6;
        player.y += (dy / dist) * player.speed * 6;
    }
    // Auto-fire
    if (fireCD <= 0) {
        bullets.push({ x: player.x, y: player.y - 14 });
        fireCD = fireRate;
        shootSound();
    }
}
```

### Pattern B: Tap to Flap (Flappy Bird style)
```javascript
canvas.addEventListener('click', handleFlap);
canvas.addEventListener('touchstart', (e) => { e.preventDefault(); handleFlap(); });
```

### Viewport Meta
Always include for mobile:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<style>
    * { touch-action: none; -webkit-user-select: none; user-select: none; }
    canvas { width: 100vw; height: 100vh; object-fit: contain; }
</style>
```

## Step 4: Retro Visuals

### CRT Scanline Effect
```javascript
function drawScanlines() {
    ctx.fillStyle = 'rgba(0,0,0,0.06)';
    for (let y = 0; y < H; y += 3) ctx.fillRect(0, y, W, 1);
}
```

### 3-Color Palette
Limit to the classic CGA palette: black, green, white, red, yellow, orange:
```
#000 — Background space
#0f0 — Player, friendly bullets, HUD (green)
#fff — Bright bullets, score text
#f44 — Red enemies (top tier)
#fa0 — Orange enemies (mid tier)
#ff0 — Engine glow, powerups
#f00 — Damage, game over text
```

### Pixel Art Ships
Draw with `fillRect()` calls, not images:
```javascript
// Player ship example
ctx.fillStyle = '#0f0';
ctx.beginPath();
ctx.moveTo(x, y - 10);        // nose
ctx.lineTo(x - 12, y + 6);    // left wing
ctx.lineTo(x + 12, y + 6);    // right wing
ctx.closePath();
ctx.fill();

// Engine glow
ctx.fillStyle = '#ff0';
ctx.fillRect(x - 2, y + 6, 2, 3);
```

### Scanner / Blink Effect for Menu
```css
@keyframes blink { 50% { opacity: 0; } }
.blink { animation: blink 1s step-end infinite; }
```

## Step 5: Retro Game Types & Their Patterns

### Space Shooter (Star Fury, Space Invaders)
- Player at bottom, enemies descending from top
- Auto-fire on touch drag, collision detection
- Wave-based progression, increasing difficulty
- Power-ups (rapid fire)
- Particles on explosion
- `references/shooter-patterns.md` for detailed implementation

### Flappy Bird
- Side-scrolling with gravity-based physics
- Tap to flap (upward velocity impulse)
- Pipe obstacles with gaps
- Score increments on passing each pipe
- Ground collision + pipe collision = death

### Runner
- Auto-scrolling, player jumps over obstacles
- Gravity + jump physics
- Increasing speed over time

## Step 6: Canvas Scaling (Two Approaches)

### Approach A: Dynamic (Simple Shooter/Runner)
Canvas fills the screen, all coordinates relative to W/H:

```javascript
function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
}
resize();
window.addEventListener('resize', resize);
window.addEventListener('orientationchange', () => setTimeout(resize, 300));
```

Use this for games where you can express positions as fractions of W/H (e.g., `W*0.5` for center).

### Approach B: Fixed Design Size (Complex Layouts — Pachislot, Maze)

Use a fixed canvas buffer with CSS scaling. This preserves exact pixel positions for complex layouts:

```javascript
const W = 400, H = 580;  // DESIGN SIZE (not screen size)
function resize() {
    const fitW = window.innerWidth - 4;
    const fitH = window.innerHeight - 4;
    const s = Math.min(fitW/W, fitH/H, 1.5);
    C.width = W;        // Canvas buffer = design size
    C.height = H;
    C.style.width = Math.floor(W * s) + 'px';  // CSS size = scaled
    C.style.height = Math.floor(H * s) + 'px';
}
window.addEventListener('orientationchange', () => setTimeout(resize, 300));
```

**CSS:** `html, body { width:100%; height:100%; overflow:hidden; }`  
**HTML:** `<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, user-scalable=no\">`  
**Wrap:** `<div id=\"wrap\"><canvas id=\"c\"></canvas></div>`

Use this for pachislot, Pac-Man, or any game where elements are at absolute pixel positions.

### Reel-style Slot (Juggler / King Pulsar Pachislot)

3 spinning reels with **player-controlled stop** (not auto-stop), weighted symbol distribution, GOGO lamp bonus detection, and bonus game rounds.

#### Overview

Pachislot games like Juggler and King Pulsar use a distinctive pattern:
1. Player pulls lever → all 3 reels spin simultaneously
2. **Player presses STOP buttons one at a time** (any order)
3. Each STOP has a minimum spin time (~0.8s) before it becomes active
4. After all 3 stops, result is evaluated
5. Bonus symbols trigger the GOGO lamp → bonus game round

#### Predetermined Result Pattern

CRITICAL: The result is determined BEFORE the reels stop, then each reel snaps to the predetermined symbol when the player presses STOP:

```javascript
// At spin start, predetermine the outcome
function startSpin() {
    const r = Math.random();
    if (r < 0.005) { // ~1/200 BIG bonus
        GF = true;
        RESULT_SLOT = [6,6,6]; // 777 across the board
        PL = 300; WN = '777';
    } else {
        for (let i = 0; i < 3; i++) {
            RESULT_SLOT[i] = pickWeighted(); // normal result
        }
    }
    // Start all reels spinning simultaneously
    SPINNING = [true, true, true];
    STOP_READY = [false, false, false];
    SPIN_START = Date.now();
}
```

#### Reel Strip

```javascript
const WGT = [14, 18, 16, 10, 12, 16, 8, 6]; // symbol weights
function ps() { const t = WGT.reduce((a,b)=>a+b,0); let r = Math.random()*t;
    for (let i = 0; i < WGT.length; i++) { r -= WGT[i]; if (r <= 0) return i; } return 0; }
function mr() {
    let r = [];
    for (let i = 0; i < 12; i++) r.push(ps());
    r[0] = 6; r[1] = 5; // Guarantee at least one 7 and BAR on strip
    for (let i = r.length-1; i > 0; i--) { const j = Math.floor(Math.random()*(i+1)); [r[i],r[j]]=[r[j],r[i]]; }
    return r;
}
let RS = [mr(), mr(), mr()]; // 3 reels, each with independent 12-position strip
```

#### Player-Controlled Stop (Manual STOP buttons)

```javascript
// On each frame while spinning, advance reel position
function update() {
    if (state === 'sp') {
        const elapsed = Date.now() - SPIN_START;
        for (let i = 0; i < 3; i++) {
            // Activate STOP button after minimum spin time
            if (SPINNING[i] && !STOP_READY[i] && elapsed > 800) STOP_READY[i] = true;
            // Animate reel spinning
            if (SPINNING[i]) RP[i] = (RP[i] + 1 + Math.floor(Math.random() * 2)) % RS[i].length;
        }
    }
}

// Called when player presses a STOP button
function pressStop(idx) {
    if (!SPINNING[idx] || !STOP_READY[idx]) return;
    SPINNING[idx] = false;
    RS[idx][RP[idx]] = RESULT_SLOT[idx]; // Snap to predetermined result
    STOP_CNT++;
    sound('stop');
    
    if (STOP_CNT >= 3) { // All reels stopped
        state = 'idle';
        if (GF) { state = 'gogo'; // Enter gogo lamp animation
        } else if (PL > 0) { /* payout */ }
    }
}
```

#### BONUS State Machine (CRITICAL — handle correctly)

Common bug: forgetting to set `state='sp'` during bonus games. The state transitions must be:

```
idle → spin() → sp → pressStop×3 → idle → gogo (if bonus) → idle → bonus
```

```javascript
function startSpin() {
    if (state === 'sp' || state === 'gogo') return;
    if (MED < BET && !IB) return;
    // Handle bonus game spin (state === 'bonus')
    if (IB) { BG--; if (BG <= 0) { state = 'idle'; IB = false; } else MED -= BET; }
    else MED -= BET;
    state = 'sp'; // ← MUST set state='sp' for both normal AND bonus spins
    STOP_CNT = 0;
    SPINNING = [true, true, true];
    STOP_READY = [false, false, false];
    // ... determine result
}
```

Bonus game transitions:
```javascript
// In game loop:
if (state === 'gogo') {
    GT--; // gogo timer countdown
    if (GT <= 0) {
        state = 'bonus'; // ← NOT 'idle', NOT 'sp'
        IB = true;
        if (RESULT[0] === 7 || RESULT[0] === 'BAR') { BG = 30; BT = 'big'; }
        else { BG = 8; BT = 'reg'; }
        MED += PL;
        RD = 'BIG BONUS!!';
    }
}

// In handleClick:
if (state === 'bonus') { startSpin(); return; }
```

#### GOGO Lamp Visual Effect

The GOGO lamp should be a prominent visual element based on the reference:

```
┌──────────────────────────────┐
│ 🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴  ← Red lamp row (flashes on bonus)
│          GOGO!               ← Text lights up below
├──────────────────────────────┤
│   🟪 GOGO! CHANCE overlay   ← Pop-art lamp over reels:
│   • Pink #FF1493 background  │   • Blue starburst with black outline
│   • "GOGO!" in glossy pink   │   • "CHANCE" white with black shadow
│   • Pulsing glow effect      │
└──────────────────────────────┘
```

```javascript
const gflash = (state === 'gogo' || GF);
// Top lamp row (12 red lamps)
for (let i = 0; i < 12; i++) {
    const fl = gflash && Date.now() % 250 < 125;
    ctx.fillStyle = fl ? '#f44' : '#300';
    ctx.shadowColor = fl ? '#f00' : 'transparent';
    ctx.shadowBlur = fl ? 15 : 0;
    ctx.beginPath(); ctx.arc(x, 18, 7, 0, Math.PI*2); ctx.fill();
}

// Overlay lamp on reels
if (gflash || state === 'gogo' || state === 'bonus') {
    ctx.globalAlpha = 0.85 + Math.sin(Date.now() * 0.008) * 0.15;
    // Pink background
    ctx.fillStyle = '#FF1493';
    ctx.fillRect(lx, ly, lw, lh);
    ctx.strokeStyle = '#000'; ctx.lineWidth = 3;
    ctx.strokeRect(lx, ly, lw, lh);
    // Blue starburst
    ctx.fillStyle = '#1a0050';
    ctx.beginPath();
    for (let i = 0; i < 8; i++) {
        const a = i*Math.PI/4 - Math.PI/2;
        const r2 = i%2 === 0 ? 30 : 18;
        if (i === 0) ctx.moveTo(...coords);
        else ctx.lineTo(...coords);
    }
    ctx.closePath(); ctx.fill(); ctx.stroke();
    // GOGO text (glossy pink)
    ctx.fillStyle = '#FFB6C1';
    ctx.font = 'bold 28px "Courier New",sans-serif';
    ctx.fillText('GOGO!', cx, cy);
    // CHANCE text (white with black shadow)
    ctx.shadowColor = '#000';
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 20px "Impact","Courier New",sans-serif';
    ctx.fillText('CHANCE', cx, cy + 30);
}
```

#### Click/Touch Coordinate Mapping

CRITICAL: Properly map screen coordinates to canvas coordinates:

```javascript
function handleClick(mx, my) {
    ia(); // initialize audio on first touch
    
    if (state === 'bonus') { startSpin(); return; }
    
    if (state === 'idle' || state === 'sp') {
        // Check STOP button areas
        for (let r = 0; r < 3; r++) {
            const bx = reelX + r * (reelW + gap) + reelW/2 - 24;
            const by = reelY + reelH + 4;
            if (mx >= bx && mx <= bx + 48 && my >= by && my <= by + 24) {
                pressStop(r); return;
            }
        }
        // Check PULL LEVER area
        if (mx >= W/2 - 60 && mx <= W/2 + 60 && my >= leverY && my <= leverY + 36) {
            if (state === 'idle') { startSpin(); return; }
        }
        // Fallback for initial spin
        if (state === 'idle' && STOP_CNT === 0) { startSpin(); return; }
    }
}

// Both click and touch must use getBoundingClientRect() for proper scaling:
C.addEventListener('click', e => {
    const r = C.getBoundingClientRect();
    const s = C.width / r.width; // scale = canvas buffer / CSS size
    handleClick((e.clientX - r.left) * s, (e.clientY - r.top) * s);
});
C.addEventListener('touchstart', e => {
    e.preventDefault();
    const t = e.touches[0];
    const r = C.getBoundingClientRect();
    const s = C.width / r.width;
    handleClick((t.clientX - r.left) * s, (t.clientY - r.top) * s);
});
```

#### King Pulsar Cabinet Style (Yamasa)

```
┌──────────────────────────────────────┐
│ YAMASA  YAMASA-NEXT                  │  ← White on black bar
│ 🔶🔶🔶🔶🔶 (orange honeycomb lamps) │  ← Flash on bonus
├──────────────────────────────────────┤
│ 🟢 Green background with gold filigree│
│ BIG BONUS / REGULAR BONUS (top left) │
│ 🟡 Golden sunburst with 🐸 frog face  │
│   ┌─────┐ ┌─────┐ ┌─────┐            │
│   │ 🐸  │ │ 🔔  │ │ 7   │            │  ← 3 reels
│   │ 🔔  │ │ 🐸  │ │ 🐸  │            │
│   │ BAR │ │ 🔔  │ │ 🔔  │            │
│   └─────┘ └─────┘ └─────┘            │
│ BAT TYPE - HAVE A GOOD TIME...        │
├──────────────────────────────────────┤
│ Controls:                            │
│ [PULL] button (oval, gold bordered)  │
│ 3 × [STOP] buttons under each reel    │
├──────────────────────────────────────┤
│ 👑 KING (red)                        │
│ PULSAR (gold 3D serif, massive)      │
│ The fuyu revolution                  │
├──────────────────────────────────────┤
│ 🔊 Speakers                          │
└──────────────────────────────────────┘
```

Symbol set for King Pulsar: 🐸 Frog, 🔔 Bell, 7, BAR, 🍒 Cherry

#### Forced First-Spin Demo

To demonstrate the GOGO lamp effect, force the first spin to always win:

```javascript
let FIRST_SPIN = true; // ← global flag

// Pre-determine result:
const r = FIRST_SPIN ? 0.001 : Math.random();
FIRST_SPIN = false;
if (r < 0.005) { GF = true; RESULT_SLOT = [6,6,6]; PL = 300; }
```

### Pac-Man / Maze Game

Tile-based movement on a 28x31 grid, ghost AI with chase/scatter/fright modes, power pellets, and ghost house mechanics.

**Map representation:**
```javascript
// 0=dot, 1=wall, 2=empty(inside ghost house), 3=ghost house door, 4=power pellet
const MAP_SRC = [
    [1,1,1,1,1,...],  // Row 0: solid wall border
    [1,0,0,0,0,1,...], // Row 1: dots
];
```

**Entity-aware wall collision (CRITICAL — ghosts vs player need different rules):**
```javascript
function isWall(px, py, isGhost) {
    const c = Math.floor(px/T), r = Math.floor(py/T);
    if (r<0||r>=ROWS||c<0||c>=COLS) return true;
    // Ghost house interior — only ghosts can be here
    if (r>=11&&r<=14&&c>=11&&c<=17) {
        if (isGhost) return map[r][c] === 1;   // Ghosts: only walls
        return map[r][c] !== 2 && map[r][c] !== 3; // Player: blocked
    }
    return map[r][c] === 1;
}
```

**Ghost AI (simple chase):**
```javascript
function updateGhost(g) {
    const dirs = ['u','d','l','r'];
    const rev = {'u':'d','d':'u','l':'r','r':'l'};
    let bestDir = g.dir, bestDist = Infinity;
    const target = g.fright ? fleeTarget : playerPos;
    for (let d of dirs) {
        if (d === rev[g.dir]) continue; // No reversing
        const dist = Math.hypot(nx-target.x, ny-target.y);
        if (canMove(g.x, g.y, d, true) && dist < bestDist) {
            bestDist = dist; bestDir = d;
        }
    }
    g.dir = bestDir;
    moveEntity(g, g.dir, spd, true);
}
```

## Step 7: Touch Swipe Controls (for Directional Games)

```javascript
let sx = 0, sy = 0;
canvas.addEventListener('touchstart', e => {
    sx = e.touches[0].clientX;
    sy = e.touches[0].clientY;  // CRITICAL: track BOTH axes
});
canvas.addEventListener('touchmove', e => {
    e.preventDefault();
    const dx = e.touches[0].clientX - sx;
    const dy = e.touches[0].clientY - sy;  // BUG: clientY - sx = broken swipe
    if (Math.abs(dx) > 20 || Math.abs(dy) > 20) {
        if (Math.abs(dx) > Math.abs(dy))
            player.nextDir = dx > 0 ? 'r' : 'l';
        else
            player.nextDir = dy > 0 ? 'd' : 'u';
        sx = e.touches[0].clientX; // Reset after direction change
        sy = e.touches[0].clientY;
    }
});
```

## Step 9: QA Before Delivery (MANDATORY — DO NOT SKIP)

After writing game code, ALWAYS dispatch a `delegate_task` QA subagent immediately to review the code for bugs before delivering to the user. Do NOT deliver untested code.

### Pre-Delivery Syntax Check
Run the extracted JS through Node.js to catch syntax errors that would produce a blank page:

```bash
node -e "
const fs = require('fs');
let html = fs.readFileSync('path/to/game.html', 'utf8');
const m = html.match(/<script>([\s]*?])<\/script>/);
if (!m) { console.log('No script found'); process.exit(1); }
let js = m[1];
try { new Function(js); console.log('OK'); }
catch(e) { console.log('ERROR:', e.message); }
"
```

### QA Subagent Template

After building, verify:

- [ ] JavaScript console has no errors
- [ ] Game loop runs at 60fps (requestAnimationFrame)
- [ ] Touch controls work on mobile (drag/tap)
- [ ] Audio initializes on first user interaction (AudioContext resume)
- [ ] Game state transitions work: menu → play → gameover → restart
- [ ] Collision detection is accurate (no bullet piercing)
- [ ] Edge cases handled: enemies reaching bottom, all enemies killed, player death, power-ups
- [ ] Mobile viewport scales properly (no zoom, no scroll)
- [ ] Sound effects play (PC speaker beeps, explosions)
- [ ] Score/lives display update correctly
- [ ] Game over shows final score and restart option

## Common Pitfalls

1. **AudioContext blocked by browser autoplay policy** — Must create + resume AudioContext on first user interaction (touchstart/mousedown). Creating it on page load will fail silently.
2. **Touch controls conflict with scrolling** — Always add `touch-action: none` CSS and `e.preventDefault()` in touch handlers.
3. **Bullet index skipping during collision** — When splicing bullets inside a forward loop, the next element shifts down and gets skipped. Always iterate **backwards** (`for (let i = bullets.length - 1; i >= 0; i--)`) or use a separate "used" flag.
4. **Canvas not filling phone screen** — Canvas width/height attributes must be set to `window.innerWidth/innerHeight` on each resize event, not just on page load.
5. **Game state not resetting on restart** — When transitioning from gameover → playing, reset ALL state variables (score, lives, enemies, bullets, position). Create a `resetGame()` function called at the start of each new game.
6. **Invulnerability period after hit** — Players should get 60-90 frames of invulnerability after being hit (flashing effect), otherwise they can be killed multiple times by overlapping enemy bullets.
