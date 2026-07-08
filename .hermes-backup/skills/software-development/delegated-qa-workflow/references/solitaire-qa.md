# Solitaire (DOM Drag-and-Drop) QA Checklist

Specific QA patterns for DOM-based card games with drag-and-drop, particularly relevant to Win95 Solitaire clone.

## Critical Game Logic Checks

### 1. Suit Color Parity
Suits are indexed [♠=0, ♥=1, ♦=2, ♣=3]. Black = ♠(0)+♣(3). Red = ♥(1)+♦(2).

**WRONG:** `card.s % 2 !== topCard.s % 2` — groups ♠(0)+♦(2) together and ♥(1)+♣(3) together, allowing black-on-black and red-on-red.

**CORRECT:** `isRed(card.s) !== isRed(topCard.s)` where `isRed = s => s===1||s===2`

### 2. Foundation Validation
Must check BOTH suit AND rank:
```javascript
(dragCards.length === 1) &&
(fPile.length === 0 || fPile[0].s === card.s) &&
(card.n === fPile.length)
```
- Missing suit check: any suit can go on any foundation (game can be "won" illegally)
- Missing length check: cards placed in wrong order

### 3. Stack-to-Foundation Rejection
Only single cards can go to foundation. If a multi-card stack is dragged to foundation, the ENTIRE drag must be rejected with full revert — not just the first card placed.

### 4. Empty Tableau — King Only
Empty tableau piles only accept Kings (card.n === 12). No other card can start a new pile.

### 5. Card Revert on Invalid Drop
When a drag is dropped on an invalid target, ALL cards must be returned to their source pile with no data loss.

### 6. Top Card Flip
After moving cards FROM a tableau pile, if the new top card is face-down, it must be flipped face-up.

## Drag-and-Drop Tests

1. Mouse drag from tableau to another tableau (valid and invalid)
2. Mouse drag from tableau to foundation
3. Mouse drag from waste to tableau
4. Mouse drag from waste to foundation
5. Mouse drag from foundation to tableau (should be valid for King on empty)
6. Touch drag (same as above via touch events)
7. Release outside any valid target → revert
8. Stack drag (multiple face-up cards) to tableau
9. Stock click → draws card to waste
10. Empty stock click → recycles waste

## Event Listener Leaks

Each `initSolitaire()` call adds new document-level event listeners (mousemove, mouseup, touchmove, touchend). If the user reopens Solitaire, old listeners accumulate. **Fix:** Remove old listeners before adding new ones:
```javascript
document.removeEventListener('mousemove', moveHandler);
document.removeEventListener('mouseup', upHandler);
// ... then re-add
```

## Visual Checks

1. Card backs: blue diagonal pattern (CSS linear-gradient, NOT canvas)
2. Face-up cards: white background, raised 3D border, rank+suite at top-left + mirrored bottom-right
3. Ghost drag element: follows cursor/finger with no lag
4. Stack ghost: cards in ghost should match the spacing of the tableau (same STACK value)
5. Empty pile drop zones: dashed border outline
6. Stock empty state: dashed border
7. Window scrolling on overflow (horizontal scroll when cards don't fit)
