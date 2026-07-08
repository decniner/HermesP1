# Win95 Desktop Shell + Embedded Games + Drag-Drop Solitaire

Design patterns from building a Windows 95 desktop simulator with embedded games as single-file HTML.

## Win95 Desktop Shell Pattern

### Architecture
- Teal desktop (#008080) with draggable windows
- Start menu → launches embedded games inline
- Taskbar with running app buttons + system tray clock
- Window manager: create, drag, minimize, maximize, close, focus (z-index stacking)
- Easter eggs: BSOD, Pipe screensaver

### Window Manager
- `createWindow(title, w, h, bodyHTML, onInit)` — creates a draggable, closable window with title bar
- Maximize toggle MUST set `dataset.maxed = true` on maximize, otherwise restore is broken (BUG)
- Maximize button icon should change: `□` → `🗗` on maximize, back to `□` on restore
- Focus system must deactivate ALL other windows (gray title bar via .inactive class) when one is clicked
- Taskbar buttons reflect window state: clicking a minimized window restores it, clicking an active window minimizes it
- Win95 aesthetic: `border-color: #fff #808080 #808080 #fff` for raised, inset borders for sunken

### Embedded Games (Two Approaches)

**A) iframe** — blocked on `file://` protocol. Only works via HTTP server.

**B) Inline JS function** (recommended) — game code is a function inside Win95.html. The window body contains a `<canvas>` or `<div>` with a unique ID. The `onInit` callback calls the game's init function which sets up on that element.

```javascript
// In openWin():
else if(type==='minesweeper') createWindow('Minesweeper',250,280,`<div id="ms-game"></div>`,()=>initMS());
else if(type==='spaceInvaders') createWindow('Space Invaders',480,520,`<div>...<canvas id="siCanvas">...</div>`,()=>initSpaceInvaders());
else if(type==='solitaire') createWindow('Solitaire',550,440,`<div id="solGame" style="overflow:auto;">`,()=>initSolitaire());
```

### Common Pitfalls
1. Maximize toggle broken if `dataset.maxed` not set after saving original dimensions
2. Focus system needs to loop ALL windows to deactivate, not just target
3. iframe src blocked on file:// — always use inline JS function approach
4. Window drag events must handle both mouse AND touch events on the title bar element
5. Closing a window must also remove its taskbar button

## Solitaire (Klondike) — DOM-Based Drag & Drop

Two approaches exist. The first (canvas + tap-to-select) is simpler but lacks drag feedback. The second (DOM + drag-and-drop) is more authentic to Win95.

### DOM Approach (Recommended for Authenticity)

#### Card Rendering
Cards are `<div>` elements with:
- White background + raised 3D border for face-up cards
- Blue diagonal stripe pattern for face-down cards (CSS `linear-gradient` + `background-size: 8px 8px`)
- Rank and suit displayed at top-left and mirrored at bottom-right (rotated 180deg)
- Large center suit symbol

```javascript
const CARD_W = Math.min(50, Math.floor((container.clientWidth||550)/8));
const CARD_H = Math.floor(CARD_W * 1.4);
const STACK = Math.floor(CARD_W * 0.3); // vertical overlap for face-up cards
```

#### Drag & Drop System

Three-phase approach:
1. **mousedown/touchstart** on a card → create floating ghost element (`position:fixed;pointer-events:none`), remove cards from source pile, dim source
2. **mousemove/touchmove** → update ghost position relative to cursor/finger
3. **mouseup/touchend** → detect drop target by checking bounding rects, execute move or revert

```javascript
function enableDrag(el, pile, idx) {
    const down = function(e) {
        e.preventDefault();
        const pos = e.type==='touchstart' ? e.touches[0] : e;
        
        // Remove cards from source (splice from tableau, pop from waste/foundation)
        if (pile === 'waste') { dragCards = [waste.pop()]; dragSrc = 'waste'; }
        else if (typeof pile === 'number') { dragCards = tableau[pile].splice(idx); dragSrc = 't'+pile; }
        
        // Create floating ghost
        const ghost = document.createElement('div');
        ghost.style.cssText = 'position:fixed;pointer-events:none;z-index:99999;';
        dragCards.forEach(c => ghost.appendChild(createCardEl(c, true)));
        document.body.appendChild(ghost);
        ghost.style.left = (pos.clientX - offsetX) + 'px';
        ghost.style.top = (pos.clientY - offsetY) + 'px';
        source.style.opacity = '0.6'; // dim background while dragging
    };
    el.addEventListener('mousedown', down);
    el.addEventListener('touchstart', down);
}
```

#### Drop Target Detection

After releasing, check bounding rects of all foundation and tableau containers:

```javascript
function getDropTarget(mx, my) {
    // Check foundations (right side, top row)
    for (let f = 0; f < 4; f++) {
        const el = document.getElementById('solF'+f);
        const r = el.getBoundingClientRect();
        if (pointInRect(mx, my, r)) return { type: 'foundation', f };
    }
    // Check tableau (bottom rows)
    for (let t = 0; t < 7; t++) {
        const el = document.getElementById('solT'+t);
        const r = el.getBoundingClientRect();
        if (mx >= r.left && mx <= r.left + CARD_W && my >= r.top) return { type: 'tableau', t };
    }
    return null;
}
```

#### Move Validation Rules

```javascript
// Foundation: card.suit === foundation[f].suit && card.rank === foundation[f].length
// Tableau (to non-empty): card.color !== topCard.color && card.rank === topCard.rank - 1
// Tableau (to empty): card.rank === 12 (King only)
```

#### Revert on Invalid Drop

If the drop target is invalid or doesn't exist, return cards to their source:

```javascript
if (!target || !isValidMove(dragCards[0], target)) {
    // Push cards back to original source pile
    if (dragSrc === 'waste') waste.push(...dragCards);
    else if (dragSrc[0] === 't') tableau[parseInt(dragSrc[1])].push(...dragCards);
}
// Flip/re-flip top card as needed
if (tableau[t].length > 0 && !tableau[t][tableau[t].length-1].up)
    tableau[t][tableau[t].length-1].up = true;
layout();
```

### Canvas Approach (Simpler, No Drag)

Use two-tap interaction: tap card to select (yellow border), tap target to move. See previous version of this reference for code.

### Mobile Considerations
- Cards must be responsive: `CARD_W = Math.min(50, Math.floor(containerWidth/8))`
- Container MUST have `overflow: auto` and a `minWidth` set in layout():
  ```javascript
  G.style.minWidth = (7 * (CARD_W + 8) + 16) + 'px';
  ```
- Card backs should use CSS gradients (not canvas drawing) for performance
- Touch events must call `preventDefault()` to avoid scrolling conflicts

## Key Solitaire Bugs

1. **Foundation move validation** must check `card.n === foundation[target.f].length` (0-indexed: Ace=0, King=12)
2. **Empty tableau** only accepts Kings (`card.n === 12`)
3. **Drag cards not reverting** on invalid drop — always test revert logic
4. **Top card not flipping** after moving cards from a tableau pile
5. **Win check** — `foundation.every(f => f.length === 13)`
6. **Stock recycle** — when stock is empty, reverse waste array and flip all cards face-down
