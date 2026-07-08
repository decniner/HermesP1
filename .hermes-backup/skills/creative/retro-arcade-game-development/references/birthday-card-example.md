# Animated HTML Birthday Card Example

A complete single-file HTML greeting card with 3D flip, confetti, floating animations, and music box audio.

## Core Techniques

### 1. Card Flip (3D Perspective)

```css
.card-container {
  perspective: 1200px;
}
.card {
  transform-style: preserve-3d;
  transition: transform 1.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.card.open {
  transform: rotateY(-180deg);
}
.card-front, .card-inside {
  backface-visibility: hidden;
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
}
.card-inside {
  transform: rotateY(180deg); /* hidden by default, shown when card is flipped */
}
```

### 2. Confetti on Open

Create confetti elements dynamically, style them with random colors/sizes, and animate them falling:

```javascript
function spawnConfetti(count) {
  const colors = ['#ff6b9d', '#ffd700', '#ff8c42', '#ff4757', '#7bed9f', '#70a1ff'];
  for (let i = 0; i < count; i++) {
    const el = document.createElement('div');
    el.className = 'confetti-piece';
    const size = Math.random() * 8 + 6;
    el.style.width = size + 'px';
    el.style.height = size * (Math.random() * 0.6 + 0.5) + 'px';
    el.style.background = colors[Math.floor(Math.random() * colors.length)];
    el.style.left = Math.random() * 100 + '%';
    el.style.setProperty('--fall-dur', (Math.random() * 2 + 2) + 's');
    document.body.appendChild(el);
    requestAnimationFrame(() => el.classList.add('fall'));
    setTimeout(() => el.parentNode.removeChild(el), 5000);
  }
}
```

### 3. Floating Emojis (Hearts, Stars, Balloons)

CSS animation with duration and delay custom properties:

```css
.floater {
  position: absolute;
  font-size: 20px;
  opacity: 0;
  animation: floater-float var(--fd) ease-in-out var(--fdelay) infinite;
}
@keyframes floater-float {
  0% { transform: translateY(100vh) scale(0); opacity: 0; }
  20% { opacity: 0.6; transform: translateY(80vh) scale(1); }
  100% { transform: translateY(-10vh) scale(0.5); opacity: 0; }
}
```

### 4. Balloons Rising Inside the Card

```css
.balloon {
  position: absolute;
  font-size: 30px;
  opacity: 0;
  animation: balloon-rise var(--dur) ease-in var(--delay) infinite;
}
@keyframes balloon-rise {
  0% { transform: translateY(100px) rotate(0deg); opacity: 0; }
  10% { opacity: 0.8; }
  90% { opacity: 0.8; }
  100% { transform: translateY(-250px) rotate(10deg); opacity: 0; }
}
```

### 5. Music Box Audio (via Web Audio API)

See the main SKILL.md section "Music Box / Jewelry Box Synthesis" for the `playMusicBoxNote()` function.

#### Melody Data (Happy Birthday)

```javascript
const birthdayMelody = [
  [262, 0.3], [262, 0.3], [294, 0.5], [262, 0.5], [349, 0.5], [330, 0.8],
  [262, 0.3], [262, 0.3], [294, 0.5], [262, 0.5], [392, 0.5], [349, 0.8],
  [262, 0.3], [262, 0.3], [523, 0.5], [440, 0.5], [349, 0.5], [330, 0.5], [294, 0.5],
  [494, 0.3], [494, 0.3], [440, 0.5], [349, 0.5], [392, 0.5], [349, 0.8]
];
```

#### AudioContext Autoplay Policy

Must init on first user interaction — use event listener that fires once:

```javascript
document.addEventListener('touchstart', function init() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
}, { once: true });
```

Star field, music toggle button, and tap-to-open/close card are the remaining UI elements.

## Advanced Techniques

### 5. Gold Glittery Text Effects

Use CSS background gradients with `background-clip: text` to simulate gold foil text:

```css
.gold-text {
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 42px;
  font-weight: bold;
  font-style: italic;
  background: linear-gradient(180deg, #d4af37 0%, #c9a030 30%, #b8942e 60%, #d4af37 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 1px 2px rgba(212,175,55,0.2));
}
```

Add a glow effect with `text-shadow`:
```css
text-shadow: 0 0 20px rgba(212,175,55,0.3), 0 0 40px rgba(212,175,55,0.1);
```

Gold sparkle dots scattered around the card:
```css
.gold-dot {
  position: absolute;
  width: 4px; height: 4px;
  background: #d4af37;
  border-radius: 50%;
  animation: dot-twinkle 2.5s ease-in-out infinite alternate;
}
@keyframes dot-twinkle {
  0% { opacity: 0.1; transform: scale(0.5); }
  100% { opacity: 0.9; transform: scale(1.3); }
}
```

### 6. SVG Floral Wreath (Hallmark Style)

Create a floral wreath using inline SVG. The wreath sits behind the text on the card front.

**Structure:**
```svg
<svg viewBox="0 0 300 400" fill="none">
  <!-- Double gold ring frame -->
  <circle cx="150" cy="210" r="120" stroke="#d4af37" stroke-width="0.8" opacity="0.3"/>
  <circle cx="150" cy="210" r="116" stroke="#d4af37" stroke-width="1.5" opacity="0.5"/>

  <!-- Flower: layered ellipses at angles for petals, circle for center -->
  <g transform="translate(215, 130)">
    <ellipse cx="-6" cy="-4" rx="10" ry="7" fill="#9b59b6" transform="rotate(-30)" opacity="0.9"/>
    <ellipse cx="6" cy="-4" rx="10" ry="7" fill="#8e44ad" transform="rotate(30)" opacity="0.9"/>
    <circle cx="0" cy="0" r="4" fill="#f1c40f"/>
  </g>

  <!-- Leaf: rotated ellipse -->
  <ellipse cx="0" cy="0" rx="12" ry="4" fill="#48d1cc" transform="rotate(-60)" opacity="0.6"/>

  <!-- Butterfly: path-based outline -->
  <g transform="translate(55, 155)" opacity="0.7">
    <path d="M0,0 Q-8,-6 -10,-12 Q-6,-8 0,-4 Q6,-8 10,-12 Q8,-6 0,0Z" fill="none" stroke="#d4af37" stroke-width="0.8"/>
    <path d="M0,0 Q-6,3 -8,8 Q-4,5 0,2 Q4,5 8,8 Q6,3 0,0Z" fill="none" stroke="#d4af37" stroke-width="0.8"/>
  </g>
</svg>
```

**Flower color palette:**
- Purple pansy: `#9b59b6`, `#8e44ad`, yellow center `#f1c40f`
- Magenta hibiscus: `#c2185b`, `#d81b60`, dark center `#4a0e2e`
- White anemone: `#fff`, `#f5f5f5`, dark center `#2c3e50`, gold stamens `#d4af37`
- Red berries: `#dc143c`, `#e74c3c`
- Teal leaves: `#48d1cc`, `#40c4c0`
- Gold leaves: `#c9a030`, `#b8942e`
- Green leaves: `#7cb342`

### 7. Multi-Layer Classical Music Box Audio

See the main SKILL.md section "Classical Music Box (Sine-wave steel tine + multi-layer arrangement)" for the full implementation. Key differences from the simple version:

- **Sine waves** (not triangle) — purer, more delicate steel tine tone
- **Detuned harmonics** — octave at 2.01×, 5th at 3.02× for authentic mechanical imperfection
- **Long sustain** — notes ring for 1.2× their nominal duration (overlap creates cascading effect)
- **Higher octave** — melody at C5-C6 range for delicate pitch
- **Four layers** — main tines + chord accompaniment + descant + sustained pad

### 8. Hallmark-Style Card Layout (Front Cover)

```
┌──────────────────────────────────┐
│                                  │
│     to a fantastic               │  ← small dark serif
│        Angel                     │  ← large gold glittery cursive
│        on your                   │  ← small dark serif
│       Birthday                   │  ← large gold glittery cursive
│                                  │
│  ╔══════════════════════╗        │
│  ║   Floral Wreath      ║        │  ← SVG wreath with flowers,
│  ║   (flowers, leaves,  ║        │     leaves, butterflies
│  ║    butterflies)      ║        │
│  ╚══════════════════════╝        │
│                                  │
│       ✦ tap to open ✦           │  ← animated hint
└──────────────────────────────────┘
```

Background: pale pink gradient `linear-gradient(160deg, #fce4ec, #fce8ee, #fce4ec)` with watercolor texture overlay.

### 9. GitHub + htmlpreview Deployment

Share the card via GitHub without setting up Pages:

```
https://htmlpreview.github.io/?https://github.com/USER/REPO/blob/main/path/to/card.html
```

If GitHub Pages is enabled: `https://USER.github.io/REPO/path/to/card.html`

Enable Pages: repo Settings → Pages → Source: "Deploy from branch: main, / (root)".

### Full Example

Complete source available at the HermesP1 repo:
`https://github.com/decniner/HermesP1/blob/main/birthday-card/index.html`
