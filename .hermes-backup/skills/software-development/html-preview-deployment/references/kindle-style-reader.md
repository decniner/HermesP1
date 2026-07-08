# Kindle-Style HTML Reading Interface

A standalone HTML file that renders book content with a mobile-friendly reading interface. Single-page view with opacity fade transition — NOT a 3D page-flip or two-page spread.

## Core Architecture

```
<body>
  ├── #top (hidden, shown on center-tap)
  │   ├── Title ("Book Title")
  │   ├── Contents button (opens TOC sidebar)
  │   ├── Aa button (font size controls)
  │   └── Theme toggle (☀ sun icon)
  ├── #pg (content area, overflow:hidden, click-to-toggle-menu only)
  ├── #bot (hidden, shown on center-tap)
  │   ├── Chapter title + page info
  │   └── Progress bar (.fill, width %)
  ├── #toc (slide-out sidebar, left: -300px → 0)
  └── #font (Aa+ / Aa- buttons, absolute positioned)
```

**Navigation: ◀ Prev / Next ▶ buttons only.** No swipe detection, no tap zones, no left/right 30% click zones. All page navigation goes through the bottom arrow buttons.

**Tap on page content** only toggles the menu bars (top + bottom). It does NOT navigate pages.

## Key Design Rules (from user corrections)

### Navigation — Arrows Only (CORRECTED THIS SESSION)
The user explicitly rejected two approaches before settling on arrows-only:
1. ❌ CSS 3D page-flip animation → "it does not work"
2. ❌ Two-page spread layout → "it does not work"
3. ❌ Tap zones (left/right 30% click zones) → "rely on arrow at the bottom"
4. ❌ Touch swipe detection → "scrolling up or down should not switch to next page"
5. ✅ **Prev / Next buttons at the bottom** — this is the ONLY approved navigation method

HTML for the buttons:
```html
<div id="nav">
  <button onclick="p(-1)">◀ Prev</button>
  <span class="pi" id="pi">1 / 1</span>
  <button onclick="p(1)">Next ▶</button>
</div>
```

### Page Content — No Scroll (CORRECTED THIS SESSION)
Content must fit entirely on the page without scrolling:
```css
#pg{position:fixed;top:0;left:0;right:0;bottom:0;overflow:hidden;padding:40px 10% 50px;}
```
- `overflow: hidden` — not `overflow-y: auto`
- Compact font sizes (14px default, headings at 20px/15px)
- Tight spacing (paragraphs: 1.5 line-height, code: 1.35, compact margins)
- Use `Aa` button for font size adjustment if text is too small

### Font Size Defaults
```css
:root{ --fs:14px; }
#pg h1{font-size:20px;margin-bottom:8px;}
#pg h2{font-size:15px;margin:12px 0 5px;}
#pg p{margin:0 0 8px;font-size:var(--fs);line-height:1.5;}
#pg pre{padding:8px 10px;font-size:calc(var(--fs) - 5px);line-height:1.35;}
#pg ul{margin:0 0 6px 18px;line-height:1.45;}
#pg li{margin:2px 0;}
```

### Minimum Font Size Control Range
`Math.max(11, Math.min(28, fs + d))` — allows 11px to 28px

### Mobile Responsiveness
```css
@media(max-width:700px){
  #pg{padding:36px 10px 44px;}
  #pg h1{font-size:17px;}
  #pg h2{font-size:13px;}
  #toc{width:250px;left:-260px;}
}
```

## Page Transition

Use opacity fade (0.2s) rather than 3D transforms for reliability:

```javascript
const el = document.getElementById('pg');
el.classList.add('fade');
setTimeout(() => { /* update content */ el.classList.remove('fade'); }, 200);
```

## Navigation Logic (via Prev/Next buttons)

```javascript
function n(dir){
  const c = C[ch];
  const nxt = pg + dir;
  if(nxt >= 0 && nxt < c[1].length){
    // Same chapter, different page
    pg = nxt;
    show();
  } else if(dir > 0 && ch < lastCh && C[ch+1]){
    // Next chapter
    ch++; pg = 0;
    show();
  } else if(dir < 0 && ch > 1 && pg === 0){
    // Previous chapter (last page of previous)
    ch--; pg = C[ch][1].length - 1;
    show();
  }
}
```

## Chapter Jump via TOC

```javascript
function go(n){
  if(n < 1 || n >= C.length || !C[n]) return;
  ch = n; pg = 0;
  show();
  document.getElementById('toc').classList.remove('open');
  tocU();
}
```

## Progress Calculation

Cumulative page count across all chapters for the progress bar:

```javascript
function update(){
  let done = 0, total = 0;
  for(let i = 1; i < C.length; i++){
    if(!C[i]) continue;
    if(i < ch) done += C[i][1].length;
    else if(i === ch) done += pg + 1;
    total += C[i][1].length;
  }
  document.getElementById('pi').textContent = `${C[ch][0]} — Page ${pg+1} of ${C[ch][1].length}`;
  document.getElementById('pf').style.width = `${(done/total)*100}%`;
}
```

## Click Handler — Menu Toggle Only (not navigation)

```javascript
document.getElementById('pg').addEventListener('click', function(e){
  if(tm){ tm = false; return; }  // Skip if user was scrolling
  if(e.target.closest('a')) return;  // Let links work
  if(window.getSelection().toString().length > 0) return;  // Skip text selection
  tB();  // Toggle menu bars — no page nav
});
```

**Note:** The `tm` flag differentiates taps from scrolls:
```javascript
let tm = false;
document.addEventListener('touchstart', () => { tm = false; });
document.addEventListener('touchmove', () => { tm = true; });
document.addEventListener('touchend', () => {});
```

On mobile, `touchstart` → `touchmove` → `touchend` fires during a scroll. The `touchmove` handler sets `tm = true`. Then when `click` fires (~300ms after touchend), the handler sees `tm = true` and ignores the click. Only taps (touchstart → touchend with no touchmove) pass through.

## Links & Text Selection

```css
#pg{user-select:text;-webkit-user-select:text;}
#pg a{color:var(--accent);text-decoration:underline;cursor:pointer;}
#pg a:hover{opacity:0.8;}
::selection{background:var(--accent);color:#fff;}
```

## Data Structure

```javascript
// Each chapter: [title, [page1_content, page2_content, ...]]
const C = [
  null,
  ['Chapter 1 Title', [`<p>page 1 text</p>`, `<p>page 2 text</p>`]],
  ['Chapter 2 Title', [`<p>page 1 text</p>`]],
];
```

Each page is raw HTML. The `show()` function prepends a `<h1>` heading and renders.

## Dark/Light Mode

```css
.dark{
  --page-bg:#1a1a1a;
  --page-text:#ccc;
  --header-bg:#222;
  --bar-bg:#2a2a2a;
}
```

Toggle: `document.body.classList.toggle('dark');`

## Common Pitfalls

1. **DO NOT build 3D page-flip or spread layouts.** Start with Kindle-style single-page opacity fade immediately. The user has rejected alternatives twice.

2. **DO NOT use overlay tap zone divs for navigation.** No fixed-position `<div class="prev">` / `<div class="next">` overlays. They block links and text selection. Navigation is exclusively through Prev/Next buttons.

3. **DO NOT implement swipe detection for page turning.** The user scrolls vertically on mobile and any diagonal movement triggers unwanted page turns. Remove all swipe logic — use only the `tm` flag to detect taps vs scrolls for menu toggling.

4. **DO NOT allow scrolling on the page content.** Use `overflow: hidden`. Font size defaults must be small enough that content fits on one screen. The `Aa` button allows the user to enlarge text if needed.

5. **Every use case in a book/guide MUST include concrete, copy-pasteable commands.** Cron job configs, skill blocks, and prompts — not just descriptions. The user has explicitly rejected "just descriptions" multiple times.

6. **GitHub sharing via htmlpreview.github.io** — Do not ask the user to enable GitHub Pages. Just push to GitHub and provide the htmlpreview URL:
   ```
   https://htmlpreview.github.io/?https://github.com/decniner/HermesP1/blob/main/hermes-book/HermesAgentBook.html
   ```

7. **Menu auto-hide** — When the user navigates to a new page, auto-hide the top/bottom bars. Don't persist the menu state across page turns.

8. **TOC sidebar width** — On desktop 280-300px, on phone 240-250px. Must close after clicking a chapter link.

9. **Font size changes via Aa** — Reset the font menu to hidden after the user picks a size. Don't leave the Aa menu open.
