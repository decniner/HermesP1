# Structured Project Kickoff — Three-Phase Method

This reference records the exact process used for the Hermes Agent Digital Book project (2026-07-07), which the user explicitly defined as the required workflow for all future projects.

## The Three Phases

### Phase 1: Discovery & Requirements
- Ask questions ONE topic at a time. Label each by number (Topic 1, Topic 2, ...)
- Topics covered in this session's project:
  1. Source Material & Scope (official docs, community discussions)
  2. Real-World Use Cases Depth (conceptual vs tutorial, how many, cite sources)
  3. Visual Design & Styling (theme, page style, cover, TOC, brand colors)
  4. Book Structure & Length (chapters, core vs advanced, personal setup, SRE focus)
- Continue until you can describe the full project back to the user

### Phase 2: Project Vision Document
- Synthesize everything into a structured, AI-readable document
- Present to user for explicit approval before writing any code
- The document must cover: identity, visual design, chapter structure, sources, style
- Do NOT skip this step even if the user is impatient

### Phase 3: Build
- Only proceed after user confirms the vision document matches

## Book Interface Evolution (This Session)

The final deliverable evolved through 4 iterations based on user corrections:

1. **Book-style page-flip HTML** (CSS 3D transform on entire book container) — ❌ "I can't flip the pages"
2. **Per-spread rotateY** (CSS rotateY on individual spreads with flip div) — ❌ "it does not work"
3. **Kindle-style reader** (single-page view, tap zones for left/right nav, swipe detection, scrollable content) — ❌ multiple corrections:
   - "I can't click on URLs or copy text" → tap zone overlays removed, JS click handler added
   - "Scrolling should not go to the next page" → swipe detection fixed (dx/dy ratio check)
   - "Scrolling up or down should not switch to next page, it is strictly for scrolling" → swipe detection removed entirely, `tm` flag added
   - "Rely on arrow at the bottom" → tap navigation removed, only Prev/Next buttons
   - "It should just fit on the page so i don't have to scroll" → `overflow:hidden`, font reduced to 14px default, compact spacing
4. **Final approved version**: Arrows-only navigation, no scroll, compact text, menu toggle on tap

## Final (Approved) Interface Design

### Navigation
- **◀ Prev / Next ▶ buttons** at the bottom — the ONLY navigation method
- **No swipe detection** (removed after multiple user corrections)
- **No tap zones** (removed — user said "rely on arrow at the bottom")
- **Tap on page** toggles menu bars only (does NOT navigate)
- **Keyboard** arrow keys still work

### Content Display
- **`overflow: hidden`** — no scrolling. Everything fits on one page
- Default font: 14px body, 20px h1, 15px h2, compact line-height (1.5p, 1.35 pre)
- Usable can adjust via Aa button (11px–28px range)
- Links clickable, text selectable

### Touch Handling (Menu Toggle Only)
```javascript
let tm = false;
document.addEventListener('touchstart', () => { tm = false; });
document.addEventListener('touchmove', () => { tm = true; });
document.addEventListener('touchend', () => {});

document.getElementById('pg').addEventListener('click', function(e){
  if(tm){ tm = false; return; }  // was a scroll, skip
  if(e.target.closest('a')) return;
  if(window.getSelection().toString().length > 0) return;
  tB();  // toggle menu bars only
});
```

### Color Scheme
- Light mode: cream paper (#f5f0e1), dark text (#2a2a1a), gold accent (#CD7F32), teal (#4dd0e1)
- Dark mode: deep navy (#1a1a2e), light text (#ccc), same accents
- Selection highlight: accent bg with white text

### Sharing URL
```html
https://htmlpreview.github.io/?https://github.com/decniner/HermesP1/blob/main/hermes-book/HermesAgentBook.html
```

## When to Use This Pattern

Any project with significant scope — books, documentation sites, multi-page apps, or anything where the user wants to approve the design before building. Always start with the simplest possible approach (Kindle-style) and only add complexity if specifically requested. Never build a 3D page-flip animation first.

## User Preferences Captured

- Author name on cover: Den Sanchez
- Colors: Hermes gold (#CD7F32), teal (#4dd0e1), dark navy (#1a1a2e) and cream paper (#f5f0e1) for light mode
- Font: Georgia/Times New Roman serif for body, Courier New for code
- Responsive: must work on phone browsers
- Navigation: arrows only, no swipe, no tap zones, no page-flip animation
- Content: must fit without scrolling (use compact defaults, Aa button for adjustment)
