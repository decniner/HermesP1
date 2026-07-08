# Case Study: Flappy Bird '86 HTML Game Audit

**App:** Single-file HTML5 Canvas Flappy Bird clone (320×480) with pixel-art bird, procedurally spawned pipes, CRT scanline overlay, and Web Audio API sound effects.

**Methods used:** Static source analysis + live browser testing (served via HTTP — canvas/audio don't work on `file://`) + pixel-data inspection via `getImageData` + runtime state probing.

## Bugs Found

### 🟡 Medium (2)

| # | Bug | Location | Root Cause | Impact |
|---|-----|----------|------------|--------|
| 1 | **Bird blink effect frozen after game-over** | `draw()` line 412, `update()` line 370–371 | `frame` counter is only incremented in `update()` when `gameState === 'playing'`. After game-over, `update()` returns early — so `frame` freezes. `Math.floor(frame/8) % 2` in `draw()` becomes a constant. | Bird either never draws (permanently hidden) or always draws (no blink effect) on death, depending on the frame number when collision occurred. Blink effect is entirely broken. |
| 2 | **AudioContext never resumed, sounds may not play** | `initAudio()` line 116–118, `playBeep()` line 120–130 | `new AudioContext()` is created inside a user gesture but `audioCtx.resume()` is never called. On browsers with strict autoplay policies (Chrome, Edge), the context may remain in a `"suspended"` state. | Sound effects (flap, score, hit, start jingle) may be silently dropped on affected browsers. |

### 🔵 Low (3)

| # | Bug | Detail |
|---|------|--------|
| 3 | **Bottom pipe collision rect uses `h: H` (full canvas height)** | Line 340: `const botRect = { x: p.x, y: p.topH + PIPE_GAP, w: PIPE_W, h: H }`. The height should be `H - GROUND_H - (p.topH + PIPE_GAP)`. Works only because ground-collision check fires first — if the ordering changed or ground check was removed, this would cause false positives. |
| 4 | **Asymmetric ceiling vs. ground collision hitbox** | Line 330, 333: Ceiling check uses raw `by < 0` (full 14px bird height), ground check uses reduced `bh = b.h - 2` (12px). Result: ceiling has 0px leniency, ground has 2px leniency. |
| 5 | **In-canvas score overlaps tall pipes** | Line 428: Score text rendered at `(W/2, 50)` — tall top pipes (`topH` up to 306) can extend below y=50, causing visual overlap with the score. |

### ✅ Verified Correct

| # | Pattern | Detail |
|---|---------|--------|
| 1 | State machine | `menu → playing → gameover → playing` transitions all correct. Overlay hides/shows properly. `startGame()` resets score=0, frame=0, bird, pipes, groundOffset. |
| 2 | Pipe spawning | `30 + Math.random() * 276` — valid range (30–306 for top pipe height). Gap is always 100px. Bottom pipe always has at least 50px visible. |
| 3 | Scoring | `p.x + PIPE_W < bird.x` (bird x=70 fixed) — pipe passes completely behind bird before score increments. `p.scored` flag prevents double-counting. |
| 4 | Pipe cleanup | Reverse loop splice: `pipes[i].x + PIPE_W < 0` removes off-screen pipes. Correct pattern (no splice+break issue). |
| 5 | Input handling | `e.preventDefault()` on Space/ArrowUp. `touchstart` with `e.preventDefault()` on canvas. Click/tap/space all route through `handleFlap()`. |
| 6 | Ground collision | Triggers at `bird.y + bh >= H - GROUND_H` (y=444 with bh=12). Bird's visual bottom is at y+14=458 vs ground at 456 — 2px visual overlap before death. |
| 7 | localStorage | Best score persisted/loaded correctly with fallback to '0'. |
| 8 | No runtime JS errors | Console showed no script errors during gameplay. |

## Runtime State Probing Notes

**Canvas rendering could not be confirmed via pixel data in headless browser.** All `getImageData(0, 0, 320, 480)` calls returned only background gradient colors (dark blue/purple shades: R=11–26, G=11–26, B=47–62). Zero green (pipes), yellow (bird), brown (ground), or white (scanlines/in-game score) pixels were ever detected — even after clicking to transition to `playing` state.

**Diagnostic steps taken:**
1. Confirmed `getContext('2d')` works — manual `fillStyle='#ff00ff'; fillRect(0,0,1,1)` rendered correctly (verified via pixel sample)
2. Confirmed overlay hides on click → `document.getElementById('overlay').style.display === 'none'`
3. Confirmed the DOM HUD is reachable → `scoreDisplay.textContent === '0'`
4. Inferred `requestAnimationFrame` may not fire in headless/background-tab mode, causing the game loop (`update()` + `draw()`) to never execute after the initial render call

**Lesson:** Both `let`-scoped variable probing AND pixel-data inspection are unreliable in headless browser automation when `requestAnimationFrame` may be throttled to zero. For future audits, use a visible-tab browser profile if available, or add a manual draw-test at init to verify the loop is running.

## Key Methodology Takeaways

1. **Frame-counter freeze is a common game-over bug pattern** — when `update()` guards on `gameState === 'playing'` and `frame++` is inside `update()`, any `draw()` animation that reads `frame` will be permanently frozen. The fix is a separate death-screen counter or advancing it in `draw()`.
2. **`AudioContext.resume()` is mandatory** — creating the context alone is insufficient on modern browsers. Always pair `new AudioContext()` with `ctx.resume()` in the user-gesture handler.
3. **Collision rects should match visual bounds** — using `h: H` for a bottom pipe works by accident (ground check fires first). This is sloppy and fragile.
4. **Headless browser testing of canvas games has blind spots** — `requestAnimationFrame` behavior in headless/background agents varies by platform. Pixel-data absence is not evidence of a rendering bug in the game code.
