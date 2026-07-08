# Solitaire (Klondike) — Win95 HTML Simulator Audit

**Source:** Single-file HTML/JS/CSS app (~800 lines). Solitaire lives inside a Win95 desktop simulator with window manager, start menu, taskbar, and other classic games.

**Scope:** The `initSolitaire()` function was rewritten and reported broken. Audit covered code reading, browser testing, and programmatic state inspection.

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | 2 |
| 🟠 High | 2 |
| 🟡 Medium | 1 |
| 🔵 Low | 3 |

## Bugs Found

### 🔴 Critical 1 — Suit color parity uses wrong arithmetic

**Code:** `initSolitaire()` line 768 — `dragCards[0].s%2 !== topCard.s%2`

**Suits are indexed** `['♠'=0, '♥'=1, '♦'=2, '♣'=3]`. The `s%2` operation groups:
- **s%2=0:** ♠(0) + ♦(2)
- **s%2=1:** ♥(1) + ♣(3)

But the correct black/red grouping is:
- **Black:** ♠(0) + ♣(3)
- **Red:** ♥(1) + ♦(2)

**Effect:** Black ♠ can be placed on black ♣ (both black! `0%2=0 !== 3%2=1` → `true`), and red ♥ can be placed on red ♦ (both red!). Verified via `browser_console`: `♠(0)%2=0, ♣(3)%2=1 → 0 !== 1 → true` — allows black-on-black.

**Fix:** Replace with a proper red-suit check:
```js
function isRed(s) { return s === 1 || s === 2; }
// Then: isRed(dragCards[0].s) !== isRed(topCard.s)
```

### 🔴 Critical 2 — No suit check for foundation drops

**Code:** Lines 743–745
```js
if(!card||card.n===foundation[target.f].length){
    foundation[target.f].push(card);
```
Only `card.n` (rank) is checked against `foundation[target.f].length` (pile height). No suit validation.

**Effect:** Any suit can go on any foundation. ♠A on foundation[0], then ♥2 on the same pile — both succeed. The game can be "won" with mixed-suit foundations, which is not valid Klondike.

**Fix:** Add a suit check:
```js
if((foundation[target.f].length===0 || foundation[target.f][0].s===card.s)
    && card.n===foundation[target.f].length)
```

### 🟠 High 3 — Stack drag to foundation loses trailing cards

**Code:** Lines 743–745 (same code as bug 2). When a multi-card stack from tableau is dragged to a foundation:
1. `dragCards = tableau[t].splice(idx)` — all cards removed from tableau
2. Only `dragCards[0]` is checked against foundation validation
3. If it passes, only `dragCards[0]` is pushed to foundation — the rest vanish

**Effect:** Dragging a 3-card stack (e.g., 9♠-8♥-7♠) to a foundation that accepts the 9 loses the 8♥ and 7♠ permanently.

**Fix:** Reject stack drops to foundation entirely (solitaire convention), or handle revert of trailing cards if only the top card qualifies.

### 🟠 High 4 — Document event listeners accumulate on reopen

**Code:** Lines 786–787 — `document.addEventListener('mousemove',move)` etc. inside `initSolitaire()`

**Problem:** `initSolitaire()` is called every time the Solitaire window opens. Each call adds 4 new `document` event listeners (`mousemove`, `mouseup`, `touchmove`, `touchend`). The old listeners are never removed.

**Effect:** After 5 open/close cycles, there are 20 event listeners. The last-registered handler wins since only the shared closure variable `drag` matters, but memory still leaks and performance degrades.

**Fix:** Store listener references, or wrap in a helper that removes old listeners first, or use an AbortController to scope listeners to the window's lifecycle.

### 🟡 Medium 5 — Duplicate "King on empty tableau" check

**Code:** Lines 758–768 — two nearly identical `if` blocks
```js
if(dragCards.length===1 && !topCard && dragCards[0].n===12){
    foundation.forEach(...);   // useless loop body
    pile.push(...dragCards);
}else if(!topCard && dragCards[0].n===12){
    pile.push(...dragCards);   // same push
```

**Effect:** Dead `foundation.forEach(...)` does nothing. Code is confusing but functionally correct — both branches push to the tableau pile identically.

### 🔵 Low 6 — Ghost drag stack offset doesn't match tableau

**Code:** Line 670 (`STACK-8`) vs line 618 (`STACK`)

**Effect:** The floating drag ghost uses a tighter vertical offset (`STACK-8` = 7px when CARD_W=50) than the actual tableau pile (`STACK` = 15px). The ghost looks compressed compared to source.

### 🔵 Low 7 — Waste revert only pushes `dragCards[0]`

**Code:** Line 772 — `waste.push(dragCards[0])`

**Effect:** Safe in practice (waste always pops 1 card → dragCards always length 1), but fragile if code is refactored. Should use `waste.push(...dragCards)`.

### 🔵 Low 8 — Foundation revert only pushes `dragCards[0]`

**Code:** Line 749 — `foundation[parseInt(dragSrc[1])].push(dragCards[0])`

**Effect:** Same pattern as bug 7. Safe in practice since foundation only ever pops 1 card, but fragile.

## Techniques Used

1. **Static code analysis first** — Read all ~260 lines of `initSolitaire()` before any browser interaction. Identified 6 potential bugs from code alone.
2. **Local HTTP server** (`python3 -m http.server 8765`) — `file://` protocol is blocked by the browser automation tool.
3. **Probe game state via `browser_console` with `dataset` attributes** — Card elements carry `data-s` (suit 0–3) and `data-n` (rank 0–12). Reading `firstChild.dataset.s` and `firstChild.dataset.n` reveals exact card identity that vision can't reliably confirm.
4. **Snapshot for ref IDs, vision for visual layout** — Snapshot shows interactive element refs; vision confirms card placement, stock presence, and layout geometry.
5. **Suit parity verification via expression** — `'0%2='+(0%2)+' 3%2='+(3%2)` confirmed the wrong grouping.
6. **`getBoundingClientRect()` for coordinate mapping** — Used to map game element positions relative to the game container for drop-target logic analysis.
7. **JavaScript `var` for browser_console expressions** — `let`/`const` inside `browser_console(expression=...)` caused SyntaxErrors with multi-line expressions. `var` works reliably in single-line expressions.

## Also Working Correctly

- Stock click draws card to waste (verified 2♦, 6♦, then 9♠ appeared)
- Stock click recycles exhausted stock from waste
- Face-up card appears in waste with correct suit/rank text
- Card backs render with blue diagonal pattern
- Tableau columns show correct card counts (1–7)
- No JS console errors on load or after any interaction
- Layout recalculates card width based on container (`Math.min(50, Math.floor(width/8))`)
