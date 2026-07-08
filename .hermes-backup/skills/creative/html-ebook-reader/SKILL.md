---
name: html-ebook-reader
description: Build publication-grade digital books as single HTML files — supports both classic minimal and modern immersive reading interfaces with chapter navigation, page transitions, and responsive design.
version: 2.0.0
author: agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ebook, book, kindle, reader, html, publication, creative, ui, dark-mode, 3d-flip]
    related_skills: [claude-design]
---

# HTML Ebook / Digital Book Reader

Use this skill when the user asks you to create a digital book, ebook, publication, or reading interface as an HTML file. This covers Kindle-style readers, immersive page-flip books, documentation guides, and any long-form content designed for reading in a browser.

## When To Use

- User asks for a "book", "guide", "ebook", "publication", "digital book"
- User wants a Kindle-style or Kindle-like reading experience
- User wants to convert documentation/markdown into a readable book format
- User wants to share a long document with friends via URL
- User wants a "modern", "redesigned", "polished", "dark-first" reading experience

This skill does NOT cover:
- Presentations/decks (use claude-design with Deck Rules)
- Single landing pages or mockups (use claude-design)

## Design Variants

The skill supports two distinct design aesthetics. **Let the user's language guide your choice**, or ask explicitly if they give no signal.

### Variant A: Classic / Minimal (Kindle-style)
Best for: pure readability, text-forward content, users who say "kindle", "simple", "clean", "minimal"

- Cream/off-white default (#f9f6ef) with dark mode inverse (#1a1a1a)
- Serif body font (Georgia, Palatino) — readability first
- **Navigation via bottom ◀ Prev / Next ▶ buttons only** — no tap zones on page, no swipe detection
- Simple opacity fade for page turns (`.fade` class, 200ms timeout)
- **Content fits without scrolling** (`overflow:hidden` on #pg, compact text)
- **NO swipe detection at all** — do NOT include dx/dy swipe calculation code. Swipe detection causes accidental page turns during vertical scroll on mobile. Remove it entirely.
- **Touch handling only tracks `touchMoved` flag**: `touchstart→tm=false`, `touchmove→tm=true`, `touchend→no-op`
- **Click handler only toggles menu bars** — never navigates pages. Checks `touchMoved` flag; if scrolled, click is suppressed.
  ```javascript
  let tm=false;
  document.addEventListener('touchstart',()=>{tm=false;});
  document.addEventListener('touchmove',()=>{tm=true;});
  document.addEventListener('touchend',()=>{});
  document.getElementById('pg').addEventListener('click',function(e){
    if(tm){tm=false;return;}
    if(e.target.closest('a'))return;
    if(window.getSelection().toString().length>0)return;
    tB(); // menu toggle only
  });
  ```
- **Default font size: 14px** (compact, fits content in viewport)
- **Compact sizing**: h1=20px h2=15px h3=13px, code padding=8px line-height=1.35, ul margin=6px line-height=1.45, table padding=4px 6px margin=6px
- Gold accent (#c4782a), flat/matte surfaces, minimal shadows

### Variant B: Modern / Immersive (Dark-first)
Best for: visually striking, demo-worthy, users who say "redesign", "modern", "polished", "dark", "3D", "glass"

- **Dark-first default**: deep navy/slate background (#0f1117), gold/caduceus accents (#c4782a)
- **Warm light mode** as accessible toggle (#f5f0eb paper)
- **Glass-morphism top bar**: semi-transparent background with `backdrop-filter: blur(20px) saturate(1.4)` and `border-bottom: 1px solid rgba(255,255,255,0.08)`
- **3D page flip** using CSS perspective transforms:
  - Forward: `perspective(1200px) rotateY(-8deg) translateX(20px)` with origin left center
  - Backward: `perspective(1200px) rotateY(8deg) translateX(-20px)` with origin right center
  - Cubic-bezier easing: `cubic-bezier(.22,.61,.36,1)` over ~450ms
- **Page curl effect**: fixed `::after` pseudo-element on `#pg` — 60px gradient corner (transparent → accent-dim → accent), opacity 0.4 idle → 0.7 on hover
- **Animated gradient background**: 3 radial gradient blobs (gold, blue, purple) with `filter: blur(80px)` drifting via `transform: translate` over 20s infinite
- **Click zones**: left 30% → previous page, right 30% → next page, center 40% → toggle menu bars
- **Touch/swipe support**: track `touchstart X/Y`, compare with `touchend`, 40px threshold, only horizontal swipes with `Math.abs(dx) > Math.abs(dy)`
- **Auto-hide bars**: top/bottom bars auto-hide after 3s of inactivity, shown on any click or touch, timer resets on interaction
- **Hover nav arrows**: left/right navigation zones (`.nav-zone`) are 30% wide, hidden by default (`opacity: 0`), appear on hover with scale + glow
- **Loading screen**: full-screen overlay with spinner animation + pulsing text ("⟐ Opening the Codex") that fades out after ~600ms
- **Animated progress bar**: gradient fill (`#c4782a → #e8a34a → #f0c060`) with shimmer overlay animation
- **Page badge**: floating pill at bottom-center showing "Page X.Y" with gold chapter number
- **Clean font stack**: Inter/system-ui for UI, Georgia/serif for content, JetBrains Mono for code
- **Responsive**: 3 breakpoints (768px tablet, 480px mobile) scaling header, padding, TOC width, nav zone width

## Core Architecture

### Reader Layout
1. **Single-page view** — One page at a time, full width.
2. **Page content (#pg)** — fixed position, full viewport, `overflow-y: auto` (Variant A: hidden, Variant B: auto — user scrolls inside page).
3. **Text selectable** — `user-select: text` on `#pg`. Links must be clickable with `e.target.closest('a')` guard.
4. **Font size controls** — Aa button toggles a floating menu with `A−` / `A+` buttons. Clamp: 11px–28px, step: 2px.
5. **Dark/Light mode toggle** — 🌙/☀ button toggles `.light` class on `<body>`, switching CSS custom properties.
6. **Slide-out TOC sidebar** — 📖 button slides panel from left, overlaid backdrop for tap-to-close.
7. **Progress bar** — bottom bar showing chapter name, page count, and gradient fill progress bar.

### Content Structure
```
const C = [
  null,  // index 0 reserved
  ['Chapter Title', [
    `<p>Page 1 content...</p>`,
    `<p>Page 2 content...</p>`
  ]],
  ...
];
```

Each chapter: `[title, [page1, page2, ...]]`. Pages are raw HTML template literals (backtick strings).

### Variant A CSS Constants
```css
:root{
  --page-bg:#f9f6ef;
  --page-text:#1a1a1a;
  --header-bg:#f0ede6;
  --header-text:#555;
  --accent:#c4782a;
  --bar-bg:#e8e4da;
  --dim:#999;
  --font:'Georgia','Palatino Linotype','Book Antiqua',Palatino,serif;
  --mono:'Courier New',monospace;
  --fs:14px;
}
```

### Variant B CSS Constants
```css
:root{
  --bg:#0f1117;
  --surface:#1c1e26;
  --surface-hover:#262833;
  --text:#e1e4e8;
  --text-dim:#8b8fa3;
  --accent:#c4782a;
  --accent-glow:rgba(196,120,42,0.25);
  --accent-dim:rgba(196,120,42,0.12);
  --blue:#58a6ff;
  --glass:rgba(255,255,255,0.04);
  --glass-border:rgba(255,255,255,0.08);
  --shadow:rgba(0,0,0,0.45);
  --font-ui:'Inter','system-ui',-apple-system,sans-serif;
  --font-content:'Georgia','Palatino Linotype',serif;
  --font-mono:'JetBrains Mono','Fira Code','Courier New',monospace;
  --fs:16px;
  --header-h:52px;
  --bot-h:48px;
  --radius:12px;
  --radius-sm:6px;
}
.light{
  --bg:#f5f0eb;
  --surface:#fff;
  --text:#1a1a1a;
  --text-dim:#7a7570;
  --glass:rgba(0,0,0,0.03);
  --glass-border:rgba(0,0,0,0.08);
  --shadow:rgba(0,0,0,0.12);
}
```

### Navigation Engine

Shared state for both variants:
```javascript
let ch=1, pg=0, ui=false, fs=16;
```

**Core functions:**
- `n(dir)` — Navigate `dir` pages (+1 forward, -1 back). Handles page boundaries within a chapter. Advances/retreats chapters at boundaries. Calls `show(dir)` for animation direction.
- `show(dir)` — Render current `ch`/`pg`. Apply animation class based on `dir`. Inner HTML = `<h1>{ch}. {title}</h1>` + page content.
- `go(n)` — Jump to chapter `n`, reset to page 0. Close TOC.
- `update()` — Recalculate progress: sum pages of completed chapters + current page offset, divided by total. Set `#pf` width and `#pi` text.
- `tocU()` — Remove `.cur` from all TOC links; add to current chapter. Call `scrollIntoView({block:'center',behavior:'smooth'})`.
- `tB()` / `resetHideTimer()` — Toggle bar visibility. Start 3s auto-hide timer (Variant B only; Variant A keeps bars always visible or toggles explicitly).

**Keyboard shortcuts** (both variants):
- ArrowRight → `n(1)`
- ArrowLeft → `n(-1)`
- Space → `n(1)` with `e.preventDefault()`
- `t` or Escape → `tT()` (toggle TOC)

**Touch handling** — Variant B only (Variant A has no swipe/tap-zone nav):
```javascript
let touchStartX=0, touchStartY=0, touchMoved=false;
document.addEventListener('touchstart',e=>{/* record start */},{passive:true});
document.addEventListener('touchmove',e=>{touchMoved=true;},{passive:true});
document.addEventListener('touchend',e=>{
  if(touchMoved){
    let dx=e.changedTouches[0].screenX-touchStartX;
    let dy=e.changedTouches[0].screenY-touchStartY;
    if(Math.abs(dx)>Math.abs(dy) && Math.abs(dx)>40)
      dx<0 ? n(1) : n(-1);
  }
},{passive:true});
```

**Click navigation** — Variant B only (Variant A uses buttons only):
```javascript
document.getElementById('pg').addEventListener('click',function(e){
  if(touchMoved){touchMoved=false;return;}
  if(e.target.closest('a'))return;
  if(window.getSelection().toString().length>0)return;
  let x=e.clientX-this.getBoundingClientRect().left;
  let w=this.getBoundingClientRect().width;
  let third=w*0.3;
  if(x<third) n(-1);
  else if(x>w-third) n(1);
  else tB();  // center tap toggles bars
});
```

## Best Practices

- Chapter data goes in a `const C = [...]` array at the top of the `<script>` block — easy to maintain, easy to verify.
- Use `null` at index 0 so `ch` starts at 1 (1-indexed chapters).
- Generate TOC dynamically from `C` — never hardcode it.
- Always verify with `new Function()` or browser console that the JS parses without errors.
- For long chapter data (>1000 lines), use template literal backticks inside the array — they preserve whitespace and embedded quotes.

## Pitfalls

1. **Don't hardcode the chapter list** in TOC — generate from `C` array.
2. **Don't forget the `null` at index 0** — chapters start at 1.
3. **Don't use single-quote strings for page content** containing apostrophes — use backtick template literals.
4. **Don't break the chapter boundary logic** — `n(dir)` must check both `pg` boundaries AND `ch` boundaries.
5. **Don't forget `e.preventDefault()`** on Space/Arrow keyboard handlers — prevents unwanted page scroll.
6. **Don't miss the `touchMoved` reset** in the click handler — without it, a swipe that doesn't meet the 40px threshold will trigger a page turn on touchend's synthetic click.
7. **Click zones work poorly on long pages** where users want to scroll — only use them (Variant B) when pages are short enough to fit the viewport.
8. **Backdrop-filter performs poorly on low-end mobile** — test on real devices or fall back to solid backgrounds.
9. **TOC overlay must have `pointer-events: none` when closed** and `pointer-events: auto` when open — otherwise it blocks clicks on the page.

## Verification Checklist

- [ ] File loads without JS errors (check with browser console)
- [ ] Page turns work via keyboard, buttons, and click zones (if Variant B)
- [ ] TOC sidebar opens, lists all chapters, links work
- [ ] TOC active chapter highlight updates on navigation
- [ ] Dark/light toggle works
- [ ] Font size controls work (11–28px range)
- [ ] Links are clickable (test by clicking)
- [ ] Text is selectable (test by dragging)
- [ ] Progress bar tracks correctly (last page = 100%)
- [ ] Chapter boundaries work (last page → next chapter, first page → prev chapter)
- [ ] Swipe gestures work (Variant B) — swipe left = next, swipe right = prev
- [ ] Auto-hide timer works (Variant B) — bars disappear after 3s idle
- [ ] Responsive on mobile (check 768px and 480px breakpoints)
- [ ] Animated background doesn't cause jank (Variant B)
- [ ] **Variant A only: Scrolling vertically does NOT trigger page turn** (test by scrolling on mobile)
- [ ] **Variant A only: Only ◀ Prev and Next ▶ buttons navigate** (tap center, links, and text select should not trigger navigation)

## Share URL Pattern

After pushing to GitHub, provide:
```
https://htmlpreview.github.io/?https://github.com/USER/REPO/blob/main/PATH/TO/FILE.html
```
