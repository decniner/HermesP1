---
name: birthday-card
description: Build animated HTML greeting cards with 3D flip, music, confetti, and photo frames. Hallmark-style e-cards with background audio.
---

# Animated HTML Greeting Cards (Birthday / E-Card)

Build interactive HTML greeting cards that feel like Hallmark e-cards — tap to open with 3D flip animation, background music, confetti, photo frames, and personalized messages.

## When to Use

- User asks for an animated birthday / greeting card in HTML
- Wants a "tap to open" card with sound, confetti, or photo
- Wants the card hosted on GitHub for sharing via link

## Structure

```
birthday-card/
├── index.html          # The card itself
├── angel-photo.jpeg    # Photo on front cover (optional)
└── birthday-music.mp3  # Background music (optional, replaces Web Audio)
```

## Key Techniques

### 1. Card Flip (3D Perspective)
```css
.card-container { perspective: 1200px; }
.card { transform-style: preserve-3d; transition: transform 1.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
.card.open { transform: rotateY(-180deg); }
.card-front, .card-inside { backface-visibility: hidden; }
.card-inside { transform: rotateY(180deg); }
```
The `.open` class toggles to reveal the inside message. Use `backface-visibility: hidden` on both faces.

### 2. Gold Glittery Text
Use CSS gradients with `background-clip: text` for gold text:
```css
background: linear-gradient(180deg, #d4af37 0%, #c9a030 30%, #b8942e 60%, #d4af37 100%);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
filter: drop-shadow(0 1px 2px rgba(212,175,55,0.2));
```

### 3. Circular Photo Frame
Wrap `<img>` in a `border-radius: 50%; overflow: hidden` div. Overlay an SVG gold ring with:
- Double gold circles (solid + dashed)
- Small diamond decorations at cardinal points
- `pointer-events: none` so clicks pass through to the card

### 4. Background Music
**Prefer HTML5 Audio** over Web Audio synthesis — the user will likely provide their own audio file.

```javascript
let audioEl = new Audio('birthday-music.mp3');
audioEl.loop = true;
audioEl.volume = 0.7;
audioEl.play(); // Must be triggered by user gesture
```

If synthesizing music box tones with Web Audio:
- Use sine wave for main tone (like a tuned steel tine)
- Add slightly detuned octave harmonic (+1 cent) for shimmer
- Add 5th harmonic at low volume for metallic ring
- Quick attack (5-8ms), long gentle decay (notes should overlap)
- High-pass filtered noise burst at start for mechanical "pluck"

### 5. Confetti
Use absolute-positioned colored divs with random sizes, colors, and `animation: confetti-fall`:
```css
@keyframes confetti-fall {
  0% { transform: translateY(0) rotate(0deg); opacity: 1; }
  100% { transform: translateY(110vh) rotate(720deg); opacity: 0; }
}
```
Spawn bursts on card open with staggered delays.

### 6. Hallmark-Style Design Palette
- Background: Pale pink gradient (#FADADD → #F8C8DC)
- Text: Serif font (Georgia) in dark grey (#4a4a4a) for body, gold gradient for names/titles
- Gold accents: #d4af37, #c9a030
- Wreaths: SVG-based flowers (pansies, anemones, hibiscus), teal leaves, gold ferns, butterflies

### 7. Swipeable Message Carousel

After opening the card, show a horizontal swipeable carousel of messages. Each slide shows one sender's message with an avatar emoji, name, and message text.

**⚠️ CAROUSEL APPROACH SELECTION — CRITICAL:**

CSS `overflow-x: auto` + `scroll-snap-type: x mandatory` works on direct browser access (local server, GitHub Pages) but **DOES NOT work inside htmlpreview's iframe**. htmlpreview re-renders the HTML in a sandboxed DOM that strips overflow-scroll behavior.

For htmlpreview compatibility, use **JS touch/mouse event detection** instead:

```css
.carousel-track-wrap {
  overflow: hidden; /* clips the sliding content */
}
.carousel-track {
  display: flex;
  height: 100%;
  transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
}
.carousel-slide {
  flex: 0 0 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 20px 18px;
  text-align: center;
}
```

#### JS Touch/Mouse Swipe Implementation

```javascript
var tr = document.getElementById('carouselTrack');
var dc = document.getElementById('carouselDots');
var D = dc ? dc.children : [];
var si = 0;           // current slide index
var tl = D.length;    // total slides
var sx = 0;           // start X position
var cx = 0;           // current X position
var dr = false;       // is dragging?

function go(n) {
  si = Math.max(0, Math.min(n, tl - 1));
  tr.style.transform = 'translateX(-' + (si * 100) + '%)';
  for (var j = 0; j < D.length; j++) {
    D[j].className = j === si ? 'carousel-dot active' : 'carousel-dot';
  }
}

function ss(e) {
  sx = e.touches ? e.touches[0].clientX : e.clientX;
  dr = true;
  tr.style.transition = 'none';
  e.stopPropagation();
}

function sm(e) {
  if (!dr) return;
  cx = e.touches ? e.touches[0].clientX : e.clientX;
  var df = cx - sx;
  var p = (-si * tr.clientWidth + df) / tr.clientWidth * 100;
  tr.style.transform = 'translateX(' + p + '%)';
}

function se(e) {
  if (!dr) return;
  dr = false;
  tr.style.transition = 'transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
  var df = cx - sx;
  if (df < -40) go(si + 1);
  else if (df > 40) go(si - 1);
  else go(si);
}

if (tr) {
  tr.addEventListener('touchstart', ss);
  tr.addEventListener('touchmove', sm);
  tr.addEventListener('touchend', se);
  tr.addEventListener('mousedown', ss);
  tr.addEventListener('mousemove', sm);
  tr.addEventListener('mouseup', se);
  tr.addEventListener('mouseleave', se);
}
go(0); // Initialize first slide
```

Key points:
- Both `touch` and `mouse` event handlers are needed for mobile + desktop
- `e.stopPropagation()` on `ss()` (touchstart/mousedown) prevents swipes from reaching the card-container's click handler (which would close the card)
- The `mouseleave` listener ensures cleanup if the cursor leaves the track mid-drag
- A 40px threshold prevents accidental micro-swipes from advancing the slide
- `touch-action: none` on the track prevents browser from intercepting touch gestures

#### Dot Indicators

```html
<div class="carousel-dots" id="carouselDots">
  <span class="carousel-dot active"></span>
  <span class="carousel-dot"></span>
  ...
</div>
```

```css
.carousel-dots {
  position: absolute;
  bottom: 16px; left: 0; right: 0;
  display: flex;
  justify-content: center;
  gap: 6px;
  z-index: 5;
  pointer-events: none; /* prevent dots from intercepting touches */
}
.carousel-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: rgba(196,78,138,0.25);
  transition: all 0.3s ease;
}
.carousel-dot.active {
  background: #c44e8a;
  width: 18px;
  border-radius: 4px;
}
```

Dots update via the `go()` function above — no separate scroll listener needed.

### 8. Touch Event Conflict Resolution

When the card container has a click handler (to open/close), swiping the carousel can accidentally trigger the close. Three mechanisms work together:

1. **CSS**: `touch-action: none` on the carousel track prevents the browser from handling touch events
2. **JS stopPropagation**: The swipe `ss()` handler calls `e.stopPropagation()` on touchstart/mousedown
3. **Architecture**: Add a dedicated ✕ close button so the only way to close the card is intentional

```javascript
var cb = document.getElementById('closeBtn');
if (cb) {
  cb.addEventListener('click', function(e) {
    e.stopPropagation();
    // Close card logic: remove 'open' class, reset state
  });
}
```

### 9. Close Button

The close button is the only way to close the card when the carousel is being swiped:

```html
<div class="close-btn" id="closeBtn">✕</div>
```

```css
.close-btn {
  position: absolute; top: 16px; right: 16px;
  width: 28px; height: 28px;
  border-radius: 50%;
  background: rgba(196,78,138,0.15);
  border: 1px solid rgba(196,78,138,0.2);
  color: #c44e8a; font-size: 14px;
  display: flex; align-items: center; justify-content: center;
  z-index: 10; cursor: pointer;
  opacity: 0; transition: opacity 0.6s ease 0.8s;
  touch-action: manipulation;
}
.card.open .close-btn { opacity: 1; }
.close-btn:active { background: rgba(196,78,138,0.3); }
```

Also consider allowing close by tapping the card-front area (the outer face visible when card is open) via the card-container click handler.

### 9b. Arrow Button Navigation

When users find swipe gestures difficult or unreliable (especially inside htmlpreview iframes), add animated ▶ ◀ buttons as an alternative:

```html
<button class="arrow arrow-next" id="arrowNext">▶</button>
<button class="arrow arrow-prev" id="arrowPrev">◀</button>
```

```css
.arrow {
  position: absolute; top: 50%; transform: translateY(-50%);
  z-index: 20; width: 40px; height: 40px;
  border-radius: 50%;
  background: rgba(196,78,138,0.15);
  border: 2px solid rgba(196,78,138,0.3);
  color: #c44e8a; font-size: 20px;
  cursor: pointer; display: flex;
  align-items: center; justify-content: center;
  touch-action: manipulation;
  transition: all 0.2s; opacity: 0.7;
}
.arrow:active { background: rgba(196,78,138,0.3); opacity: 1; }
.arrow-next { right: 8px; animation: bounce-right 1.5s ease-in-out infinite; }
.arrow-prev { left: 8px; animation: bounce-left 1.5s ease-in-out infinite; display: none; }

@keyframes bounce-right {
  0%, 100% { transform: translateY(-50%) translateX(0); }
  50% { transform: translateY(-50%) translateX(4px); }
}
@keyframes bounce-left {
  0%, 100% { transform: translateY(-50%) translateX(0); }
  50% { transform: translateY(-50%) translateX(-4px); }
}
```

JS click handlers:

```javascript
var an = document.getElementById('arrowNext');
var ap = document.getElementById('arrowPrev');
// In go() function, add show/hide logic:
function go(n) {
  si = Math.max(0, Math.min(n, tl - 1));
  tr.style.transform = 'translateX(-' + (si * 100) + '%)';
  // ... update dots ...
  if (an) { an.style.display = si < tl - 1 ? 'flex' : 'none'; }
  if (ap) { ap.style.display = si > 0 ? 'flex' : 'none'; }
}
if (an) { an.addEventListener('click', function(e) { e.stopPropagation(); go(si + 1); }); }
if (ap) { ap.addEventListener('click', function(e) { e.stopPropagation(); go(si - 1); }); }
```

Arrow buttons **coexist with swipe** — both work simultaneously. The animated bounce draws the user's eye to the next-page arrow.

### 9c. Flipbook Pattern (No Tap, Pure Page Navigation)

**Use this when the user wants a book-like experience** — no tap-to-open, just swipe/arrow through pages from the cover.

**Structural changes from the flip-card pattern:**

1. Remove the 3D card flip entirely (no `.card-front`/`.card-inside`/`.card.open`/`rotateY`)
2. The cover IS page 0 of a single carousel track
3. No tap handler needed — arrow buttons and swipe work immediately
4. Music starts automatically when the user leaves page 0
5. Confetti bursts on each page turn

```html
<div class="book" id="book">
  <div class="pages-wrap">
    <div class="pages" id="pages">
      <!-- PAGE 0: Cover -->
      <div class="page page-cover">
        ... cover content (photo, gold text, "tap ▶ to open" hint) ...
      </div>
      <!-- PAGE 1..N: Messages -->
      <div class="page page-msg">
        ... avatar, sender, message text ...
      </div>
    </div>
  </div>
</div>
```

**Key CSS:**
```css
.book { position: relative; border-radius: 16px; overflow: hidden; }
.pages { display: flex; height: 100%; transition: transform 0.5s cubic-bezier(0.25,0.46,0.45,0.94); }
.page { flex: 0 0 100%; display: flex; flex-direction: column; }
/* Page shadow for book feel */
.page::after {
  content: ''; position: absolute; top: 0; left: 0; bottom: 0;
  width: 8px;
  background: linear-gradient(to right, rgba(0,0,0,0.06), transparent);
  pointer-events: none;
}
.page:first-child::after { display: none; }
```

**JS changes from flip card:**
```javascript
// REMOVE: var o=false; (isOpen state)
// REMOVE: ct.addEventListener('click', ...) (card flip handler)
// REMOVE: close button and its handler

// The go() function becomes primary navigation:
function go(n) {
  si = Math.max(0, Math.min(n, tl - 1));
  tr.style.transform = 'translateX(-' + (si * 100) + '%)';
  for (var j = 0; j < D.length; j++) {
    D[j].className = j === si ? 'dot on' : 'dot';
  }
  // Auto-start music on first page turn:
  if (si > 0 && !p) { pM(); mb.classList.remove('muted'); }
  // Confetti on each page turn:
  if (si > 0) { sC(20); }
  // Show/hide arrows:
  if (an) { an.style.display = si < tl - 1 ? 'flex' : 'none'; }
  if (ap) { ap.style.display = si > 0 ? 'flex' : 'none'; }
}

go(0); // Start on cover page
```

**User flow:**
1. Lands on the cover page (photo + "to a fantastic Angel on your Birthday")
2. Taps the animated ▶ button → flips to page 1 (first message)
3. Music starts automatically, confetti bursts
4. Continues tapping ▶ through all message pages
5. ▶ hides on the last page, ◀ shows on pages after the first
6. Swipe still works as a secondary interaction

**When to use flipbook vs flip-card:**
| Pattern | When | Key Characteristics |
|---------|------|-------------------|
| Flip-card | User says "tap to open like Hallmark card" | 3D rotateY flip, front/inside, close button needed |
| Flipbook | User says "like a book, no tap, just flip pages" | Single carousel, cover = page 0, no close button, arrows + swipe |

#### Push to GitHub
```bash
git add birthday-card/
git commit -m "Add animated birthday card"
git push
```

#### Share via htmlpreview
```
https://htmlpreview.github.io/?https://github.com/{user}/{repo}/blob/main/{path}/index.html
```

No GitHub Pages setup needed — htmlpreview renders raw HTML directly from the repo.

---

#### ⚠️ CRITICAL: htmlpreview Inline JS Truncation Limit

`htmlpreview.github.io` **silently truncates inline `<script>` blocks at ~3,400 characters.** The truncated portion is lost, causing the card to fail silently: no flip, no audio, no click handlers. This is the #1 cause of "works on my machine but not when shared."

**Symptom:** Card renders visually (HTML+CSS loads fine) but nothing happens when tapped. Console shows no errors because the truncated JS simply doesn't execute.

**The fix: keep inline JavaScript under ~3,300 characters** (leave a 100-char buffer).

#### Minification Strategy

1. **Short variable names** — `a` for audioEl, `p` for isPlaying, `o` for isOpen, `cd` for card, `ct` for container, `mb` for musicBtn
2. **Remove all comments and whitespace** — every character counts
3. **Use `var` instead of `let/const`** — saves chars
4. **Shorten console.log** — `console.log('🎂')` instead of full messages
5. **Reduce confetti colors** — 5-6 hex codes instead of 8
6. **Inline single-use helpers** — don't define functions that are only called once
7. **Combine variable declarations** — `var a=null;var p=false` → `var a=null,p=false`

Example savings: 8 confetti colors with `Math.floor(Math.random()*C.length)` → 6 colors with `C[i%C.length]` saves ~40 chars.

**Note:** The truncation is by TOTAL script content, not per-line. But splitting very long lines (~700+ chars) may help with htmlpreview's DOM-injection pipeline.

#### What Does NOT Work

| Approach | Why It Fails |
|---|---|
| External `<script src="script.js">` | htmlpreview rewrites src to `raw.githubusercontent.com` which serves as `text/plain` — browsers block execution |
| Multiple inline `<script>` tags | Each may be independently truncated |
| `file://` protocol | Blocks audio playback, CORS for images |
| `raw.githubusercontent.com` directly | Wrong Content-Type header, browser refuses to render as HTML |

#### When JS Won't Fit (Alternative: GitHub Pages)

If the card's JS exceeds 3,400 chars after aggressive minification, enable **GitHub Pages** on the repo:

1. Go to repo → Settings → Pages
2. Set source to "Deploy from branch: main, folder: /(root)"
3. Card available at `https://{user}.github.io/{repo}/{path}/`
4. No JS size limit, no sandboxing, full interactivity

GitHub Pages also fixes:
- Touch events in carousel work natively (no iframe sandbox)
- Audio autoplay less restricted
- Larger JS files possible
- No truncation of any kind

## Audio Iteration Pitfalls

- User may cycle through several audio preferences (synthesized → music box → xylophone → classical → real audio file). Keep the code modular: one `playMusic()` / `stopMusic()` interface that can swap between Web Audio synthesis and HTML5 `<audio>`.
- Music box tempo should be slow (0.35-0.40s per beat) for a gentle, winding feel.
- For xylophone, use a faster tempo (~0.18s per beat) with bouncier feel.
- For real audio files, convert to MP3 (not WAV) for web compatibility and smaller file size. Use `ffmpeg -i input.wav -codec:a libmp3lame -b:a 64k output.mp3`.
- **⚠️ WAV-in-RIFF containers:** Some audio files (e.g., from messaging apps) have MP3 data wrapped in a WAV container (RIFF header + MPEG Layer 3 payload). `ffmpeg` can handle these, but plain browser `<audio>` may not. Always convert to proper MP3 with ffmpeg.

## touch-action: manipulation Pitfall

Setting `touch-action: manipulation` on the `<body>` (to remove 300ms tap delay on mobile) **silently prevents horizontal scrolling** on child elements. The setting tells the browser to handle ALL touch gestures as manipulation (zoom, tap), which overrides overflow-x scrolling behavior.

**Fix:** Override on the carousel track:
```css
.carousel-track { touch-action: pan-x; }
```

Or if using JS-based swipe (recommended for htmlpreview), set `touch-action: none` on the track and handle all touch events yourself.

## Line-Length Truncation

htmlpreview may truncate individual lines that are very long (~700+ chars), even if the total script is under 3,400 chars. Split minified JS across multiple lines (around 300-400 chars per line) as insurance:

```javascript
// Instead of one giant line:
var a=null;var p=false;function iA(){if(a)return;a=new Audio('x.mp3');...}

// Break at natural boundaries:
var a=null;var p=false;
function iA(){if(a)return;a=new Audio('x.mp3');a.loop=true;a.volume=0.7;a.preload='auto';a.load()}
function pM(){iA();if(!a)return;a.currentTime=0;a.play()['catch'](function(){});p=true}
```

## QA / Validation

Before handing off a birthday card, validate it systematically. See `references/qa-checklist.md` for the full checklist covering asset verification, responsive layout, animation behavior, audio playback, and common pitfalls.

## Photos on Front Cover

When the user provides a photo to place on the card front:
1. Copy the image into the repo folder alongside `index.html`
2. Reference it with a relative path: `src="angel-photo.jpeg"`
3. Use a circular crop: `border-radius: 50%; overflow: hidden; object-fit: cover;`
4. Add a gold ornamental ring via SVG overlay
5. Position it centered between the text header and the tap-hint footer
