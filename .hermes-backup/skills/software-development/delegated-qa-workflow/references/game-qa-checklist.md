# Game QA Checklist

HTML/JS game testing template for use with `delegated-qa-workflow`.

## Template Prompt for QA Subagent

```
Review the HTML/JS game at [file path] for bugs.

Check:
1. JS syntax errors, undefined variables, missing functions
2. Game logic: movement, collision detection, spawning, scoring
3. Touch controls: touchstart/touchmove/touchend handlers
   - clientY must pair with sy (saved Y), NOT sx (saved X)
   - swipe reset after direction change
4. Audio: Web Audio API initializes on user interaction (touchstart/click, not on page load)
5. Game state: menu -> playing -> gameover -> restart transitions
6. Edge cases: boundaries, empty states, rapid inputs
7. Canvas scaling: viewport meta, resize handler, orientation change listener
   - Uses 100dvh not 100vh
   - Container div wrapping canvas
8. Braces balanced (count '{' vs '}')
9. No DOM/JS console errors
10. Entity collision flags: if maze game (Pac-Man), isGhost flag must be passed through isWall/canMove/moveEntity
```

## Pre-Delivery Validation (Run Before Giving to User)

Always run these checks before sending the file to the user:

```
node -e "
const fs = require('fs');
let html = fs.readFileSync('[filepath]', 'utf8');
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.log('No script found'); process.exit(1); }
try { new Function(m[1]); console.log('✅ JS syntax OK'); }
catch(e) { console.log('❌', e.message); }
"
```

## Pachislot Game QA (Juggler / King Pulsar)

### State Machine Checks
| State | Expected Behavior |
|-------|------------------|
| `idle` | Reels stopped, PULL LEVER visible, STOP buttons hidden |
| `sp` | All 3 reels spinning, STOP_READY after MIN_SPIN_MS, STOP buttons visible under each reel |
| `gogo` | GOGO lamp flashing, top lamps blinking, bonus countdown |
| `bonus` | User can pull again, BG decrements, reels spin normally |

### Common State Machine Bugs
- **Bonus mode never sets `state='sp'`** — after bonus deduction, state stays 'bonus' instead of 'sp', causing the spin loop to not process. Fix: ensure `state='sp'` is set regardless of path through startSpin.
- **Re-spin blocked after first round** — STOP_CNT is 3 after completion but never reset. The PULL LEVER area check must be separate from the `STOP_CNT===0` fallback.
- **Spinning check blocks re-spin** — `if(!SPINNING[0]&&!SPINNING[1]&&!SPINNING[2])` must guard the lever check so the user can't start a new spin while reels are still turning.

### Button/Click Area Mapping
- Visual positions and click hitboxes must match
- On mobile, touch coordinates are relative to the canvas — use `e.touches[0].clientX` and `e.touches[0].clientY` with the canvas bounding rect
- Offset calculation: `const r = C.getBoundingClientRect(); const s = C.width / r.width; const mx = (clientX - r.left) * s; const my = (clientY - r.top) * s;`

### Reel Mechanics
- Result is predetermined at spin start (`RESULT_SLOT`)
- Each reel stops to its predetermined symbol when STOP button pressed
- STOP buttons must have minimum active delay (~800ms) before they become clickable
- Reels shown as spinning: randomly advance symbol position each frame while SPINNING[idx] is true
- On stop: set `RS[idx][RP[idx]] = RESULT_SLOT[idx]` to snap to predetermined value

### Click Target Priorities (handleClick order)
1. Check bonus state → startSpin
2. Check STOP button areas (only visible when SPINNING)
3. Check PULL LEVER button area (only when idle)
4. Fallback: if idle and STOP_CNT===0, startSpin from anywhere

### Computed Property Name Syntax (Common JS Bug)

When using numeric keys in JavaScript object literals, computed property names (`[1]`) are valid ES6 but cause confusion:

```javascript
// ❌ BROKEN — `[5:` opens a computed property bracket that clashes with `:`
const m = { 0: 'a', [1]: 'b', [5:[60,'STAR×3']] };  // SyntaxError: Unexpected token ':'

// ✅ FIX — Numeric keys don't need brackets
const m = { 0: 'a', 1: 'b', 5: [60, 'STAR×3'] };
```

**Rule of thumb:** Use bare numbers for literal numeric keys (`0:`, `1:`, `5:`). Only use `[expr]:` when the key itself is an expression (variable, computed value). When in doubt, drop the brackets.

### Patch Cleanup After Multiple Fixes

After applying 3+ patches to a file in rapid succession, the file can accumulate orphaned brackets, duplicate lines, or nested-block artifacts from partial old_string matches. Run this validation after the last patch:

```bash
node -e "
const fs = require('fs');
const html = fs.readFileSync('path/to/file.html', 'utf8');
const m = html.match(/<script>([\\s\\S]*?)<\\/script>/);
if (!m) { console.log('No script'); process.exit(1); }
const js = m[1];
const opens = js.split('{').length - 1;
const closes = js.split('}').length - 1;
console.log('Braces:', opens, 'open,', closes, 'close, balanced=' + (opens === closes));
try { new Function(js); console.log('✅ Syntax OK'); }
catch(e) { console.log('❌', e.message); }
"
```

## Quick Checks

| Check | Guided Procedure |
|-------|-----------------|
| JS syntax | Run through Node.js `new Function(js)` — catches computed property name bugs like `[5:[60,...]]` (should be `5:[60,...]`) |
| Touch Y-axis | Search for `clientY-sx` — this is a BUG (uses X as Y). Should be `clientY-sy` |
| Brace balance | `opens = js.count('{')`, `closes = js.count('}')`, verify equal |
| Audio init | Search for `AudioContext` — must be inside touchstart/click handler, not at top level |
| Viewport | Search for `100vh` — should be `100dvh` for mobile |
| Ghost house | If maze game: search for `isWall` function signature — must accept `isGhost` parameter |
| Canvas renders | Open in browser, check no 404 on file, verify title matches game name |
| State reset | After gameover → restart → play again: verify all counters reset, MEDALS restored, reels reset |
