# Case Study: Kanban To-Do HTML App Audit

**App:** Single-file HTML Kanban board with drag-and-drop, localStorage persistence, and three columns (New / In Progress / Done).

**Methods used:** Static source analysis + live browser testing (Chrome).

## Bugs Found

### 🔴 Critical (3)

| # | Bug | Code | Fix |
|---|-----|------|-----|
| 1 | Drop handler crashes on external drags (file, bookmark, text from other site) — `JSON.parse` has no try-catch | Line 360 | Wrap in try-catch |
| 2 | `fromIndex` is captured at dragstart — becomes stale if async mutations are added later | Lines 315–318, 366–367 | Read `dataset.index` at drop time, or use a stable ID |
| 3 | No type validation on localStorage data — `forEach` crashes if a column is not an array | Line 253 | Check `Array.isArray()` on each column |

### 🟠 High (3)

| # | Bug | Detail |
|---|------|--------|
| 4 | `dragleave` fires when hovering child `.task` elements — dashed border flickers | Use `contains()` check on `relatedTarget` in `dragleave` |
| 5 | `drag-over` visual state leaks when dragging is cancelled with Escape | Remove `.drag-over` from all targets in `dragend` |
| 6 | No `dragenter` handler — uses `dragover` for visual state (fires 60fps) | Add `dragenter` handler |

### 🟡 Medium (6)

| # | Bug | Detail |
|---|------|--------|
| 7 | Dropping into the same column is a silent no-op — no feedback | Show brief animation or "already in this column" |
| 8 | Whitespace-only input is rejected but input field is NOT cleared | Clear `input.value` on rejection too |
| 9 | `stopPropagation()` on delete click has no parent listeners — blocks future delegation | Remove unnecessary `stopPropagation` |
| 10 | `dataset.index` and `dataset.column` are written but never read | Dead code |
| 11 | No undo for Clear All — permanent data loss after confirm | Consider undo snackbar or trash column |
| 12 | No keyboard-accessible reordering — mouse-only drag-and-drop fails WCAG | Add keyboard handlers for move-up/move-down/move-column |

### ✅ Correct

| # | Pattern | Detail |
|---|---------|--------|
| 1 | XSS mitigation | Uses `textContent`, not `innerHTML` |
| 2 | Save/load round-trip | Works correctly across reloads |
| 3 | Column counts update | Recalculated from `tasks[col].length` every render |
| 4 | Empty state messages | Shown/hidden per-column correctly |
| 5 | Enter key submission | Delegates to Add button click |
| 6 | Drag visual | `.dragging` class set/removed correctly |

## Key Interaction Patterns Observed

- `confirm()` dialogs **block** `browser_click` — tool times out after 30s. Use `browser_press('Enter')` immediately after the click call to accept the dialog.
- `browser_console(expression=...)` is blocked for localStorage access by security guardrails — test persistence by navigating away and back, not by reading the API.
- Browser tool's `browser_type` encodes `<` and `>` as `&lt;` `&gt;` — XSS payloads in the toolbar appear as text, which matches what `textContent` would do anyway.
