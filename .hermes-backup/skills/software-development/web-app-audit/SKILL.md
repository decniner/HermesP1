---
name: web-app-audit
description: "Systematic audit of a frontend web app for bugs — combine static source analysis with live browser testing. Covers JS errors, game logic (collision, state machines, scaling), drag-and-drop, localStorage, XSS, edge cases, and UX issues."
version: 3.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [audit, code-review, frontend, bug-hunt, qa, web, testing, canvas, game, collision-detection, state-machine, drag-and-drop, localStorage, xss]
    related_skills: [requesting-code-review, systematic-debugging, delegated-qa-workflow]
---

# Web App Audit

Systematic bug-hunting in frontend web apps. Combines static source code analysis with live browser testing to find JavaScript errors, drag-and-drop bugs, data-persistence issues, XSS vectors, edge cases, and UX problems.

**Core principle:** Don't just read the code — exercise every interaction path in the browser. Code reads cleanly but breaks at runtime; runtime looks fine but hides data bugs.

## When to Use

- User asks you to "check for bugs," "review this app," "audit this page," or "find all issues" in a frontend HTML/JS/CSS application
- Before shipping a standalone `.html` file, dashboard, or single-page app
- When investigating reported issues in a web UI where the root cause is unknown
- During code review of a frontend-heavy project (complements `requesting-code-review`)

**Skip for:** server-side/API code (use `requesting-code-review` instead), debugging a specific known bug (use `systematic-debugging` instead), subagent-driven testing (use `delegated-qa-workflow` instead).

**This skill vs requesting-code-review:** `requesting-code-review` reviews diffs/changesets before committing. This skill audits a complete codebase file for latent bugs regardless of whether it's new or changed. Use both: this one for the full app, the other for incremental changes.

**When to use for games:** HTML5 Canvas games with `requestAnimationFrame` loops, collision detection, state machines, and Web Audio API follow different failure patterns than CRUD apps. The standard layers cover initialization, but Layers 3–5 are CRUD-specific (add/delete/persist/drag). Replace those with the **Game-Specific Audit** section below when the target is a game.

**When to use for desktop simulators:** HTML-based desktop environment emulators (Win95, macOS, widget dashboards) mix UI simulation, game logic, and cosmetic stubs. They follow different failure patterns: many visual elements exist purely for decoration, features have UI entry points but empty implementations, and the "desktop" chrome (taskbar, window manager, start menu) has its own class of bugs independent of any app running inside it. When the target is a desktop-environment simulator, swap in the **Desktop Simulator Audit** section for Layers 3–5. See `references/win95-desktop-audit.md` and `references/solitaire-audit.md` for worked examples.

## Methodology

The audit proceeds through six layers plus a game-specific section. Each layer has a checklist of things to inspect. Work through them in order — for games, swap in the Game-Specific Audit section where indicated.

```
Layer 1: Static Source Analysis
Layer 2: Initialization & Load Path
Layer 3: User Interaction Paths       ───┐
Layer 4: Data Persistence                 ├── For CRUD apps
Layer 5: Drag-and-Drop (if present)    ───┘
Layer 6: Edge Cases & Security
          ↓
Game-Specific Audit (for Canvas/Web API games) — swap in for Layers 3–5 when auditing games
```

---

## Layer 1 — Static Source Analysis

Read the source code start to finish. Do not skim. Look for these patterns:

### Event Handler Closure Bugs
- Are event handlers created inside a loop (`forEach`, `for`)?
- Does the handler close over a loop variable (`index`, `i`) that changes by the time it fires?
- **Fix pattern:** Use `let` in `for` loops, or capture the value per-iteration in `forEach`

### DOM Reference Staleness
- After `render()` or `innerHTML = ''`, are old DOM references still being used?
- Is the DOM being mutated while drag operations are in-flight?

### Data Flow Issues
- Trace the full lifecycle: load → render → user action → save → re-render
- Does `render()` destroy old event listeners? (If it uses `innerHTML`, yes — but code that adds listeners on existing elements could accumulate duplicates.)
- Are `dataset` attributes kept in sync with actual data?

### Error Handling Gaps
- `JSON.parse` without try-catch
- `e.dataTransfer.getData()` without fallback for unexpected formats
- Missing null/undefined checks on parsed data

### Unnecessary Code
- `e.stopPropagation()` with no parent handlers
- `dataset` attributes that are written but never read
- Dead code paths

---

## Layer 2 — Initialization & Load Path

Run the app in a browser and check the console:

```bash
# Start a local server
python3 -m http.server 8080
```

- [ ] **Console errors on load?** Check `browser_console()` immediately after navigation
- [ ] **localStorage corruption handling:** If the stored data is missing a key or has wrong types, does the app crash or recover gracefully?
- [ ] **Empty state renders correctly:** Default layout without any stored data
- [ ] **No 404s or missing assets** in the console

---

## Layer 3 — User Interaction Paths

Test every action the user can take:

### Add Task
- Normal text → rendered correctly, appears in DOM
- Empty string → rejected (app should refuse or show a message)
- Whitespace-only → rejected AND input field cleared (UX: leaving whitespace in the field looks broken)
- Long strings → no layout breakage (`word-break` / `overflow` handling)
- Special characters → `textContent` vs `innerHTML` test (XSS check)

### Delete Task
- Delete single task → removed from DOM and data
- Delete last task → empty state message appears
- Rapid delete of multiple tasks → no stale-index crash
- Delete after drag mutation → correct item removed

### Clear All
- Confirm dialog appears (use `browser_click` and handle the modal)
- Cancel → no data lost
- Confirm → all columns cleared, empty states shown, localStorage reset

### Enter Key
- Press Enter in input → same as clicking Add
- Works when input is focused

---

## Layer 4 — Data Persistence (localStorage)

### Save/Load Round-Trip
- Add tasks → reload page → tasks should reappear
- Delete tasks → reload → deletions should persist
- Move tasks (drag) → reload → positions should persist
- Clear all → reload → all columns empty

### Corruption Handling
- Manually set invalid JSON in localStorage → app should fall back gracefully
- Manually set wrong shape (e.g. `{new: "not-an-array"}`) → no `forEach` crash

### Page Visibility
- Open two tabs with the app. Add in tab A, switch to tab B → data is stale (known limitation of localStorage without `storage` event listener — note as a gap)

---

## Layer 5 — Drag-and-Drop (if present)

HTML5 drag and drop has well-known browser quirks. Check each:

### Visual Feedback
- [ ] `dragstart` adds visual class (opacity, rotation)
- [ ] `dragover` on target adds visual class (dashed border, highlight)
- [ ] `dragleave` removes visual class
- [ ] `dragend` (on source) removes visual class
- [ ] `drop` removes visual class from target

**Common bug:** `dragleave` fires when entering a child element inside the drop target. Result: the dashed border flickers on/off as the cursor passes over individual task cards.

**Fix:** In `dragleave`, check `e.relatedTarget` is not a descendant:
```js
list.addEventListener('dragleave', (e) => {
    if (!list.contains(e.relatedTarget)) {
        list.classList.remove('drag-over');
    }
});
```

### Stuck Visual State (Escape)
- Start drag → enter target (dashed border appears) → press Escape → border should disappear
- **Common bug:** Chrome doesn't fire `dragleave` when Escape cancels drag; only `dragend` fires on the source. The target's visual state leaks.

**Fix:** In `dragend`, remove `drag-over` from all drop targets:
```js
document.querySelectorAll('.task-list').forEach(el => el.classList.remove('drag-over'));
```

### Drop to Same Column
- Dragging and dropping back into the same column: should this be a no-op (silent) or show feedback (animation, message)?
- If silent, note it as a UX gap

### External Drops
- Drag a file, bookmark, or selected text from another page/app onto a drop target
- **Common bug:** `JSON.parse` in the drop handler crashes on non-JSON payload
- **Fix:** Wrap drop handler data extraction in try-catch

### Stale Index on Drag Start
- `dragstart` captures `{column, index}` at the moment drag starts
- If the underlying data changes between dragstart and drop, the index may refer to the wrong item
- In synchronous single-page apps this is unlikely; if any async operation is added, this becomes a real bug

---

## Layer 6 — Edge Cases & Security

### XSS Vectors
- Does the app use `innerHTML`, `insertAdjacentHTML`, or `outerHTML` anywhere?
- If `textContent` is used, XSS is mitigated
- Test: try `<script>alert('xss')</script>` as task text
- Test: `<img src=x onerror=alert(1)>` as task text
- Even with `textContent`, check if task text is rendered through any template HTML

### Keyboard Accessibility
- Input field: keyboard-friendly? (should work with Enter)
- Delete buttons: are they `<button>` elements (focusable) or `<div>`/`<span>` (not focusable)?
- Drag-and-drop: any keyboard fallback for users who can't use a mouse? (Reordering and column moves)
- Tab order: logical flow from input → add → tasks → clear-all

### Empty State Messages
- Each column shows a helpful message when empty
- Messages are consistent with column purpose (e.g. "Add a task above ✏️" for "New")
- Messages don't interfere with drag-and-drop (they should be non-interactive placeholders)

### Performance
- Apps re-rendering the entire list on every mutation: fine for < 100 tasks
- No event delegation on the task list (one listener per task) — memory concern at scale
- Note as a scalability limitation, not a bug for small apps

### Race Conditions
- Click handlers that trigger `render()` can cause issues if `render()` is async in the future
- Current synchronous code is safe

---

## Desktop Simulator Audit (HTML Desktop Environment Emulators)

For apps that simulate a desktop operating system (Win95, macOS Classic, widget dashboards, desktop-in-browser), swap this section in for Layers 3–5 above. These apps have a unique failure profile: they look like full-featured desktops but many UI elements exist purely for decoration, features have entry points but empty implementations, and the "chrome" (window manager, taskbar, start menu) has its own class of bugs separate from any app running inside it.

### D1 — Feature Completeness & Cosmetic Stub Detection

The #1 source of bugs in desktop simulators: **features that have UI entry points but no (or broken) implementation behind them.**

**Checklist:**
- [ ] **Every start menu item** opens a real window or triggers a real action — not just closes the menu silently
- [ ] **Every window button** (close, minimize, maximize) actually performs its function — not just flashes or does nothing
- [ ] **Every "running app"** (Minesweeper, Notepad, Paint, etc.) has at least basic gameplay or interaction — not a static placeholder with a title bar
- [ ] **Clock/tray displays** update on a reasonable interval (every 1 min max for time) — not a static string or 10-minute interval
- [ ] **Screensaver/idle features** have an auto-activation timer, not just a manual toggle
- [ ] **BSOD / error screens** respond to keyboard input consistently with the on-screen instructions (text says "press any key" but only clicks work)
- [ ] **Context menus** (right-click on desktop, taskbar) exist and have real entries
- [ ] **Recycle Bin / Trash** actually stores deleted items — not just a "this folder is empty" placeholder
- [ ] **Dialogs** (Shut Down, Run, Find) show actual modal dialogs with real controls

**How to test:** For every UI element with an `onclick` or event listener, trace what it does:
1. Find all elements that appear interactive (buttons, menu items, taskbar icons)
2. Click each one
3. If nothing visible happens (no window opens, no state change, no animation), it's a cosmetic stub
4. If a window opens but the content is a placeholder message ("Coming soon", "This folder is empty"), note it as an incomplete feature

### D2 — Window Manager Bugs

Desktop simulators have a custom window manager. Window managers have their own class of bugs.

**Checklist:**
- [ ] **Open → Close → Re-open** a window works (close removes from DOM, re-open creates fresh instance)
- [ ] **Multiple windows** can coexist; clicking one focuses it and unfocuses others (title bar color changes)
- [ ] **Minimize** hides the window; taskbar button click restores it; subsequent click re-minimizes
- [ ] **Maximize** toggles correctly — second click restores original position/size. **BUG PATTERN:** `w.dataset.maxed` flag is never set to `true` in the maximize path, making restore impossible.
- [ ] **Maximize button icon changes** — when maximized, the button icon should change from a single square (□) to overlapping squares (restore icon)
- [ ] **Close button** actually removes the window (not just hides it), and the taskbar button is removed
- [ ] **Taskbar buttons** reflect active vs minimized state with visual difference (pressed/raised appearance)
- [ ] **Z-order (focus) stacking** works — most recently clicked window is on top
- [ ] **Drag to reposition** works for both mouse and touch; boundaries prevent window from going entirely off-screen
- [ ] **Window state preserved across maximize/restore cycles** — original position, size, and content are restored correctly

### D3 — Game Logic Within the Simulator

Many desktop simulators include classic games (Minesweeper, Solitaire, Pinball). These are simple but have specific failure patterns.

**Minesweeper — Checklist:**
- [ ] **Timer starts on first click** (Minesweeper convention) and increments every second
- [ ] **Mine counter decrements** when flags are placed, increments when flags are removed
- [ ] **Flood-fill (zero-cell expansion)** correctly reveals connected empty cells and stops at numbered cells
- [ ] **Flagging** works via right-click (desktop) and via long-press or two-finger tap (touch)
- [ ] **Game-over** reveals all mines, disables further clicks, shows death icon
- [ ] **Win condition** is detected: all non-mine cells revealed
- [ ] **Reset button** fully resets board, mine counter, and timer
- [ ] **Reset after loss** fully resets (not just visually — internal state too)
- [ ] **No game-state bleed between resets** — stale references from previous round don't carry over

**Solitaire (Klondike) — Checklist:**
- [ ] **New deal** produces a valid layout: 7 tableau columns (1–7 cards), 24-card stock
- [ ] **Stock click** draws the top card to waste (or recycles waste when stock empty)
- [ ] **Card drag creates ghost** — a floating copy follows the cursor; source pile's cards are removed from the DOM during drag
- [ ] **Drop on empty tableau** only accepts a King (n=12), rejects any other card
- [ ] **Drop on non-empty tableau** checks alternating color + descending rank — verify the suit-color parity logic is correct (common bug: `s%2` groups ♠+♦ and ♥+♣ instead of the correct black=♠♣ / red=♥♦ grouping)
- [ ] **Drop on foundation** checks same suit + ascending rank — verify both suit AND rank are validated (common bug: only rank checked, allowing mixed-suit foundations)
- [ ] **Drop on foundation from a stack** doesn't lose trailing cards — verify only single cards (waste, tableau top, or other foundation top) can be placed; stack-drag to foundation must reject or handle all cards (not just `dragCards[0]`)
- [ ] **Invalid drop reverts** — card returns to its source pile; source pile's face-down top card remains correctly flipped/covered
- [ ] **Stock recycling** — when stock is exhausted, clicking it reverses waste back to stock (cards flipped face-down)
- [ ] **Foundation-to-tableau moves** work for top card of a foundation pile
- [ ] **Tableau stack drag** — dragging multiple face-up cards moves them as a group, preserving order and visual stacking
- [ ] **Win detection** — `alert()` fires when all 4 foundations reach 13 cards
- [ ] **No duplicate event listeners** after close→reopen — each `initSolitaire()` call should not add extra `mousemove`/`mouseup`/`touchmove`/`touchend` listeners to `document`
- [ ] **Waste pointer** — after drawing from stock, the new waste card is clickable/draggable (not just visually present)
- [ ] **Touch drag support** — `touchstart` initiates drag, `touchmove` follows finger, `touchend` drops; `{passive: false}` prevents scroll interference

### D4 — Desktop Event System

Desktop simulators may intercept clicks differently than normal web apps.

**Checklist:**
- [ ] **Click outside start menu** closes it (common bug: click handler is on `document` but start menu items inside trigger `toggleStart()`, then the document listener fires and toggles it back closed)
- [ ] **Double-click** on desktop icons opens window (not single-click — or if single-click is the convention, be consistent)
- [ ] **Touch events don't fire twice** — if the app has both `ontouchstart` and `onclick`, ensure `e.preventDefault()` is called in touch handler to suppress the synthetic mouse event
- [ ] **Window chrome (title bar buttons) works on mobile** — small 16×14px buttons are hard to tap; check if they have adequate touch target size
- [ ] **BSOD / overlays with 100% z-index** don't trap future interactions — after dismissing, all previously open windows remain functional

### D5 — Clock, Timer, and Interval Features

**Checklist:**
- [ ] **Clock update interval** is reasonable (≤ 60s, ideally 30s for a simulator). A 10-second interval is acceptable but not realistic — clock in real Win95 updated every minute from the system timer
- [ ] **All intervals are cleaned up** on window close / simulator reset — stale `setInterval` handles don't keep referencing dead DOM nodes
- [ ] **requestAnimationFrame loops** (screensaver, animations) use `cancelAnimationFrame` when stopped to avoid runaway rendering
- [ ] **Event listeners on `document`** for idle detection (mousemove/touchstart) are not attached multiple times

---

## Game-Specific Audit (HTML Canvas / Web API Games)

For games built with `<canvas>`, `requestAnimationFrame`, and Web Audio API, swap this section in for Layers 3–5 above. Games run on **state machines + per-frame update loops**, not event-driven CRUD workflows. The bugs are fundamentally different: collision logic, state-transition gaps, scaling curves, and animation-frame ordering.

### G1 — State Machine Transitions

HTML games typically have 3–4 states:

```
menu → playing → gameover → menu (or restart)
        ↑_____________________|
```

**Checklist:**
- [ ] Each transition resets **all** relevant state variables (lives, score, wave, bullets, enemyBullets, cooldowns, respawn timers)
- [ ] Mid-update transitions don't leave stale state — if `gameState` changes during `update()`, does remaining code in that frame still execute? (Common: wave-advance code runs after `playerHit()` sets `gameover`, because the wave-clear check comes after collision detection in the same frame.)
- [ ] Restart from gameover clears the previous round's enemy bullets AND old enemy references completely (not just `alive` flags)
- [ ] The menu/start overlay hides on play and reappears on gameover
- [ ] Animation timers/frame counters that freeze after game-over: if `update()` returns early when `gameState !== 'playing'` and the frame counter is incremented inside `update()`, any blink/flash effects in `draw()` that depend on that counter become frozen — permanently visible or permanently hidden. **Fix:** use a separate death-screen counter or advance it in `draw()`.

**How to test:** Probe runtime state between transitions via `browser_console`:

```js
// One-shot probe after a specific event
`gameState=${gameState}, lives=${lives}, wave=${wave}, enemiesAlive=${enemiesAlive}, enemyBullets=${enemyBullets.length}`
```

### G2 — Collision Detection

This is the #1 source of bugs in HTML games. Two high-risk patterns to look for:

#### Pattern A: Nested `for` loops + `splice` + `break` (skipped elements)

```js
// BUG: bullets.splice(i,1) shifts elements, then i-- skips the shifted bullet
for (let i = bullets.length - 1; i >= 0; i--) {
    for (let j = enemies.length - 1; j >= 0; j--) {
        if (rectCollide(bullets[i], enemies[j])) {
            bullets.splice(i, 1);  // elements at i+1+ shift to index i
            enemies[j].alive = false;
            break;                 // exits inner loop
        }
    }
    // for-loop i-- then skips the element that shifted into index i
}
```

Trace: bullets = [b0, b1, b2], i=1 hits → `splice(1,1)` → [b0, b2]; b2 now at index 1. `break` → `i--` → i=0. **b2 at index 1 is never checked.**

**Fix pattern:** Track hit with a flag, splice after the inner loop:

```js
for (let i = bullets.length - 1; i >= 0; i--) {
    let hit = false;
    for (let j = enemies.length - 1; j >= 0; j--) {
        if (!enemies[j].alive) continue;
        if (rectCollide(bullets[i], enemies[j])) {
            enemies[j].alive = false;
            enemiesAlive--;
            hit = true;
            break;
        }
    }
    if (hit) bullets.splice(i, 1);
    // No second decrement — nothing is skipped
}
```

#### Pattern B: Multiple collision checks calling `playerHit()` in one frame

```js
// Enemy bullet vs player (break = safe, at most 1 hit per frame)
for each enBullet:
    if collision(player): playerHit(); break

// Enemy body vs player (forEach, no break — can call playerHit N times)
enemies.forEach(e => {
    if collision(player): playerHit()  // N calls!
});
```

**Checklist:**
- [ ] Does every collision path have a guard, `break`, or early-return to prevent multi-hits?
- [ ] Is the `alive` flag pattern used correctly? Dead entities skipped with `continue`/`return`?
- [ ] Can the kill counter (`enemiesAlive`) go negative via double-counting?
- [ ] After `playerHit()` respawns the player, is `enemyBullets` cleared so the player doesn't die again from in-flight bullets?

### G3 — Game Loop Ordering

The `update()` sequence matters. Player death can happen mid-frame, but code after that call still runs.

```js
function update() {
    // 1. Player input & movement
    // 2. Bullet state update
    // 3. Enemy update (position, shooting)
    // 4. Collision detection     ← player can die here
    // 5. Wave clear check        ← but this still runs after death!
}
```

**Checklist:**
- [ ] Are all operations after a death-triggering call guarded by `gameState`?
- [ ] Does `updateEnemies()` run on every frame or only on move ticks? Per-frame fire with 40+ enemies at 60fps = 2400 random trials/second. Even a 0.5% probability produces ~12 bullets/second.
- [ ] When a wave is cleared mid-frame, are old enemy bullets cleared BEFORE the next `draw()` call?
- [ ] What happens if `enemiesAlive` reaches 0 in the same frame the player dies? (Wave-advance code may still spawn fresh enemies on the gameover screen.)

### G4 — Respawn & Invulnerability

**Checklist:**
- [ ] Is `enemyBullets` (or equivalent in-flight projectile array) cleared on respawn?
- [ ] Is there an invulnerability window (iframe countdown) preventing instant re-death?
- [ ] Are enemy ships cleared or repositioned on respawn? Ships that have descended close to spawn can re-kill instantly.
- [ ] Is `player.cooldown` (fire rate limiter) reset on death/restart so the first shot isn't delayed or burst?

### G5 — Scaling Curves

Difficulty-scaling formulas that look fine at wave 1 can explode at higher waves.

**Checklist:**
- [ ] Identify every scaling formula: `base + wave * increment`. Is it linear, capped, or bounded?
- [ ] Compute the rate at wave 1, 10, 25, 50. Does it become unplayable?
- [ ] Is the fire-rate probability **per frame** or **per move tick**? Per-frame with 40 enemies is much deadlier than the author likely intended.
- [ ] Are there any caps? (`Math.max(min, x)`, `Math.min(x, max)`, or a clamp)
- [ ] Does any other per-enemy-per-frame operation scale the same way? (movement speed, bullet speed, enemy count)

### G6 — Visual / Animation Consistency

**Checklist:**
- [ ] Does the animation frame advance on every logical move? Check both the normal-move and edge-hit/reverse-direction branches.
- [ ] Are canvas elements drawn during `gameover`? (Enemies/bullets behind the overlay — intentional or not?)
- [ ] Is the draw state congruent with the game state? (Player hidden when dead, enemies hidden when gameover, etc.)
- [ ] Do engine-glow or particle effects use `Math.random()` per frame? (Causes flicker — deterministic seed or clamped range preferred.)
- [ ] Does any blink/pulse/flash effect depend on the main `frame` counter that freezes when `update()` stops incrementing it after game-over? The effect will be permanently on or off instead of oscillating. **Check:** is the counter read in `draw()` but incremented only in `update()`?

### G7 — Audio (Web Audio API)

**Checklist:**
- [ ] `AudioContext` created inside a user gesture handler (`keydown`, `click`) — required by autoplay policies
- [ ] `initAudio()` guarded by `if (!audioCtx)` so context is created exactly once
- [ ] `audioCtx.resume()` is called explicitly after creation or on each user gesture, not just `new AudioContext()` — browsers may leave the context suspended even after creation inside a gesture handler
- [ ] All `playBeep`/`playSound` functions guarded by `if (!audioCtx) return` for silent-safe operation before first interaction
- [ ] `exponentialRampToValueAtTime` target is > 0 (spec requires > 0; 0.001 is safe)
- [ ] No `osc.start()` / `osc.stop()` called while `AudioContext.state !== 'running'`
- [ ] `playExplosion`-style buffer noise doesn't leak memory by creating new buffers on every call

### G8 — Runtime State Probing

Canvas games can't be inspected via DOM. Use `browser_console(expression=...)` to read internal state — but note that `let` and `const` at the top level of a `<script>` do **not** create properties on `window`, so `window.gameState` returns `undefined` even when `gameState` exists in scope. Use the raw variable name directly in the expression instead.

```js
// Typical probe — all key state in one expression
`lives=${lives}, score=${score}, wave=${wave}, gameState=${gameState}, enemiesAlive=${enemiesAlive}, enemyBullets=${enemyBullets.length}`
```

**Multi-line expressions:** `browser_console(expression=...)` accepts JavaScript expressions, not statement blocks. Compose multi-line probes with template literals or semicolons:

```js
var cx=document.getElementById('gameCanvas').getContext('2d'); var d=cx.getImageData(0,0,320,480).data; 'r='+d[0]+' g='+d[1]+' b='+d[2]
```

Note: if the canvas has never been painted (e.g. `requestAnimationFrame` hasn't fired in headless mode), `getImageData` returns stale initial pixel data. Draw a test pixel first to confirm the context is updating:

```js
var cx=document.getElementById('gameCanvas').getContext('2d'); cx.fillStyle='#ff00ff'; cx.fillRect(0,0,1,1); var d=cx.getImageData(0,0,1,1).data; 'test pixel: r='+d[0]+' g='+d[1]+' b='+d[2]
```

**What to probe at each state:**

| Game State  | What to verify |
|-------------|---------------|
| `menu`      | No enemies alive, no bullets, overlay visible, stars scrolling |
| `playing` (fresh) | All enemies alive, player at center, cooldown=0, no bullets |
| `playing` (mid) | Some enemies dead, score > 0, bullets traveling |
| `playing` (after respawn) | Lives decremented, player at center, enemy bullets cleared |
| `gameover`  | Lives = 0, overlay shows "GAME OVER", enemies/bullets visible behind |

### G9 — Running the Game

Games need an HTTP server (Canvas/Web Audio may not work from `file://`):

```bash
# From the game's directory
cd /path/to/game
python3 -m http.server 8080
```

Then `browser_navigate` to `http://localhost:8080/index.html`. Interact via `browser_press` (Space to start, Arrow keys to move, etc.) while checking `browser_console` for errors.

**If port 8080 is already in use** (another dev server is running), use a different port:
```bash
python3 -m http.server 8081
```

**Testing restart twice:** Run the full start→play→die→restart cycle twice. The second restart reveals state that wasn't properly reset (stale enemy references, uncleared arrays, wrong counter values).

---

## Reporting Findings

Structure the report with clear severity levels:

| Severity | Meaning |
|----------|---------|
| 🔴 Critical | Crash, data loss, or security vulnerability |
| 🟠 High | Broken feature, incorrect behavior, accessibility blocker |
| 🟡 Medium | Visual glitch, poor UX, edge-case crash |
| 🔵 Low | Code smell, missing polish, optimization opportunity |

For each finding include:
1. **Severity** label
2. **File and line reference**
3. **Exact code snippet** (the problematic lines)
4. **What goes wrong** (the symptom, observed or predicted)
5. **Suggested fix** (code or approach)
6. **Verification** (how to confirm the fix works)

Also list **what's correct** — balanced reporting shows the app has strengths too.

## Checklist Summary

```
[ ] Layer 1: Source scanned for closure bugs, stale references, error-handling gaps
[ ] Layer 2: App loads cleanly, console has no errors
[ ] — For CRUD apps: —
[ ] Layer 3: All user interactions tested (add, delete, clear, enter key)
[ ] Layer 4: localStorage save/load round-trip verified
[ ] Layer 5: Drag-and-drop visual feedback, edge cases, external drops tested
[ ] — For games: —
[ ] G1: State machine transitions tested (menu→playing→gameover→restart, mid-update guards)
[ ] G2: Collision loops traced for splice+break skipping and multi-hit frames
[ ] G3: Game loop ordering analyzed for post-death code execution
[ ] G4: Respawn invulnerability checked (bullet clear, iframes, enemy position)
[ ] G5: Scaling curves computed at waves 1, 10, 25, 50; caps verified
[ ] G6: Visual/animation consistency (both branches, gameover draw state)
[ ] G7: Audio context creation, gesture guard, ramp-to-zero safety
[ ] G8: Runtime state probed via browser_console expressions at each state
[ ] G9: HTTP server started; game played; restart twice to verify clean reset
[ ] — For desktop simulators: —
[ ] D1: Every UI entry point leads to a real feature, not a cosmetic stub
[ ] D2: Window manager fully tested (close/minimize/maximize/drag/focus/taskbar)
[ ] D3: Game logic (Minesweeper, Solitaire, etc.) tested: timer, counter, flood-fill, win/loss, reset, drag, card rules
[ ] D4: Event system tested: click-outside-close, double-click, touch, z-order
[ ] D5: Clock/timer intervals correct; animation loops cleaned up on stop
[ ] — All apps: —
[ ] Layer 6: XSS, keyboard accessibility, empty states, performance considered
[ ] Report structured with severity levels
[ ] Correct behavior noted alongside bugs
```

## Pitfalls

- **Don't test drag-and-drop by reading code alone** — `dragleave` behavior differs across browsers and is only observable at runtime
- **`confirm()` dialogs block browser_click** — the click times out. Use `browser_press('Enter')` or `browser_press('Escape')` to interact with the dialog, then re-navigate to see post-dialog state
- **`browser_console(expression=...)` may be blocked** — security guardrails may reject localStorage access via expression. Work around by testing persistence through navigation (add → reload → check if data survives)
- **Event listeners are recreated on every `render()`** — with `innerHTML = ''`, all old listeners are garbage collected. This is correct but look for listener accumulation in apps that use `appendChild` without clearing first
- **`stopPropagation()` on clicks is unnecessary unless parent click handlers exist** — it may block future event delegation; flag it as dead code
- **Don't conflate "pre-commit review" with "full-codebase audit"** — `requesting-code-review` covers diffs for security+build gates; this skill covers the entire application as a standalone artifact
- **Always note what works** — a report that only lists negatives is less credible than one that acknowledges correct patterns (XSS protection via textContent, correct count updates, etc.)

### Desktop-Simulator-Specific Pitfalls

- **Cosmetic stubs masquerade as features.** A start menu with 15 items does not mean 15 features exist. Click every single one. Simulators often have elaborate UI chrome with empty implementations behind it.
- **Maximize toggle is the most commonly broken window-manager feature.** Developers frequently forget `w.dataset.maxed = true;` in the maximize branch, making the second click a no-op. Always test maximize → restore.
- **Minesweeper timer is often missing entirely.** Despite having a timer display (`000`), many implementations never start it. Check with a few clicks + visual inspection.
- **Mine counter is often hardcoded.** The `💣 10` display may be a static string rather than `msMines - msFlagged`. Verify by placing a flag and checking if the counter decrements.
- **BSOD text says "press any key" but only handles click.** Simulators often forget to add `keydown` event listeners matching their on-screen instructions. Check for this mismatch.
- **Touch support often uses two-finger tap for flagging** instead of the more intuitive long-press. The multi-touch approach is platform-inconsistent and hard to trigger on small cells.
- **Taskbar button toggle cycling** (click to restore, click again to minimize) is often broken because the `minWin()` call doesn't also set the taskbar button state correctly.
- **Solitaire suit parity `s%2` is wrong.** Suits indexed `['♠'=0,'♥'=1,'♦'=2,'♣'=3]`. `s%2` groups ♠+♦ and ♥+♣, but the correct grouping is black=♠♣ / red=♥♦. The fix: a helper `isRed(s){return s===1||s===2;}` and check `isRed(card) !== isRed(topCard)`.
- **Solitaire foundation drops often skip suit validation.** Many implementations only check rank (`card.n === pile.length`) without verifying the card matches the foundation's suit. Test by dropping off-suit cards on a foundation that already has a card.

### Game-Specific Pitfalls

- **Game state changes mid-frame.** `checkCollisions()` inside `update()` can kill the player. Code executed after that call (wave advancement, HUD updates) still runs — and can corrupt state on the death frame. Always check what happens after a `playerHit()` call.
- **`splice` inside reverse `for` loops + `break` = skipped elements.** Always trace the loop with 3 elements to verify. The shifted element gets skipped by the `for` loop's `i--`.
- **Collision rects extending past meaningful bounds.** A bottom-pipe collision rect with `h: H` (full canvas height) technically works because the ground-collision check fires first, but this is fragile — removing the ground check would cause false positive collisions. Check whether collision rects are correctly sized to their visual bounds rather than sloppily oversized.
- **`let`/`const` variables are not on `window`.** At the top level of a `<script>`, `let` and `const` do not create `window` properties. `window.gameState` will be `undefined` even when `gameState` is in scope. Use the bare name in `browser_console(expression=...)` expressions.
- **`requestAnimationFrame` may not fire in headless browsers.** Canvas games that rely on `rAF` for their game loop will appear frozen (no game elements drawn) when tested in browser automation without a visible tab. Test the pixel data — if every `getImageData` sample is background gradient, the loop isn't progressing.
- **Enemy fire rate must be calculated per frame, not per move.** A probability of `0.008` per enemy per frame at 60fps with 40 enemies = ~19 bullets/second. At wave 50 with `0.058`, it's ~140 bullets/second. Most scaling formulas are designed for move-tick rates, not frame rates.
- **Animations that only advance in one branch of a conditional** create visual stutter. Check both the normal-move and edge-hit/reverse-direction branches.
- **`browser_console(expression=...)` state queries are asynchronous** — by the time your eval runs, several `requestAnimationFrame` callbacks may have fired. Account for 1–60 frames of delay in your interpretation.
- **Test restart twice in a row.** The first restart resets state; the second restart tests whether the reset was clean. This catches stale references, uncleared arrays, and missing re-initialization.
- **HTTP server on port 8080 may conflict** with an existing dev server. Use a different port (8081, 8082) if a different page loads than expected, or if `browser_navigate` shows the wrong app.
- **Touch input: wrong-axis start coordinate.** A common copy-paste bug: `touchmove` computes `dy = clientY - sx` but stores only `sx` (no `sy` variable in `touchstart`). Swiping vertically down from the right side of the screen produces `clientY - sx` < 0, registering an **upward** swipe instead of down. Always verify both `sx` and `sy` are stored and independently referenced.
- **Bounding-box zone checks that eat valid tiles.** When a special zone (ghost house, spawn room, no-fly zone) is a rectangle check like `if (r >= A && r <= B && c >= C && c <= D && map[r][c] !== EMPTY && map[r][c] !== ZONE_TYPE)`, it treats every non-zone tile value inside the rectangle as a wall — including legitimate dot/pellet tiles that overlap the rectangle. The bounding-box rows must be scoped to only the actual zone rows, or explicitly allow dot tiles (`=== 0`) through. Test by spawning an entity at each row in the zone and verifying `canMove` returns the expected value.
- **Spawn-point search scoped too broadly.** A function finding the first empty tile (`map[r][c] === EMPTY`) in row-major order can place an entity inside a restricted zone (ghost house interior, wall cavity, off-limits area) if empty tiles exist there before the intended spawn region. Fix by hardcoding the player spawn position, or scoping the search to valid rows/columns.
- **Exact-equality position checks for edge-wrapping / tunnel triggers.** Code like `if (ny === tunnelY && nx < 0)` uses strict `===` on a floating-point position. A 1-pixel Y drift (floating-point accumulation, entry from a slightly different row) silently fails the wrap; the entity stops at the wall. Use a range check: `if (Math.abs(ny - tunnelY) < 2 && nx < 0)`.
- **Missing direction reversal on mode transition.** When a power pellet is eaten (fright mode activates), ghosts should immediately reverse direction. If the transition sets `g.fright = true` but does not also reverse `g.dir`, ghosts continue toward Pac-Man instead of fleeing. State transitions that change movement behavior should also update the movement vector.
- **Configured-but-never-read data fields.** Objects initialized with fields like `scatter: 14` that are never referenced by any game logic are dead code — or a missing feature. If the data was intended for scatter/chase mode switching, its absence is an unimplemented mechanic that affects gameplay balance.
- **Empty if-block / dead bounce code.** An `if (!entity.move(...)) { /* comment */ }` block with no body after a collision is a placeholder that was never implemented. Collision-response stubs should be removed or completed before shipping.
