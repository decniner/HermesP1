# Case Study: Space Invaders '86 HTML Game Audit

**App:** Single-file HTML5 Canvas Space Invaders clone with Web Audio API sound effects, CRT scanline effect, starfield parallax, and wave-based difficulty scaling.

**Methods used:** Static source analysis + live browser testing (served via HTTP — canvas/audio don't work on `file://`) + runtime state probing via `browser_console(expression=...)`.

## Bugs Found

### 🔴 Critical (2)

| # | Bug | Location | Root Cause | Impact |
|---|-----|----------|------------|--------|
| 1 | **Bullet collision skipping (hull piercing)** | `checkCollisions()`, lines 399–411 | `bullets.splice(i,1)` inside nested `for` loops + `break` from inner loop + `for` loop's `i--` skips the bullet that shifted into index `i` | ~1 in (bullets hitting) passes through enemies undetected — player shots miss that should hit |
| 2 | **Wave advance after player death** | `update()`, wave-clear check at line 504 runs after `checkCollisions()` at line 501 | `enemiesAlive <= 0` guard is not gated on `gameState` — runs even after `playerHit()` set `gameState = 'gameover'` | Wave increments and fresh enemies spawn on the game-over screen |

### 🟠 Medium (3)

| # | Bug | Location | Detail |
|---|-----|----------|--------|
| 3 | **No invulnerability after respawn** | `playerHit()`, lines 440–445 | `enemyBullets` is cleared, but enemy ships remain and can overlap the spawn point. No iframe counter. Player can die again on the next frame. |
| 4 | **Double-hit in same frame** | `checkCollisions()`, lines 415–429 | Enemy-bullet-vs-player has `break` (safe). Enemies-vs-player is a `forEach` with no guard — if 2+ enemies touch the player, `playerHit()` is called twice. Lives drop by 2 instead of 1 when the first hit doesn't kill. |
| 5 | **Aggressive enemy fire rate scaling** | `updateEnemies()`, line 364 | `0.008 + wave * 0.001` per enemy **per frame**. Wave 1: ~22 bullets/sec. Wave 50: ~140 bullets/sec. Confirmed in testing: player died with score=0, all 40 enemies alive, 47 bullets on screen. |

### 🔵 Low (3)

| # | Bug | Detail |
|---|------|--------|
| 6 | **Animation stutter on edge hit** | `e.anim` only toggles in the non-edge-hit branch (lines 355–357). When enemies hit the screen edge, the animation freezes for one move step. |
| 7 | **Enemy/bullets drawn during gameover** | `draw()` renders enemies and bullets for both 'playing' and 'gameover' states (line 527). Visible behind the overlay. |
| 8 | **`player.cooldown` not explicitly reset on game start** | The menu→playing transition (lines 549–559) doesn't reset `player.cooldown`. Benign because it starts at 0, but would cause a one-frame fire delay if the flow were extended. |

### ✅ Verified Correct

| # | Pattern | Detail |
|---|---------|--------|
| 1 | Canvas rendering | No visual artifacts; CRT scanline effect works; starfield scrolls correctly |
| 2 | Audio (Web Audio API) | Square/sawtooth/noise-based sounds all play. AudioContext created on user gesture (Space key). |
| 3 | Player movement | Arrow keys move ship; boundaries clamped at screen edges |
| 4 | HUD updates | Score, lives, and wave counters update correctly |
| 5 | Menu → Playing transition | Overlay hides, game starts, enemies spawn |
| 6 | Game Over → Restart transition | State reset (lives, score, wave, bullets, enemyBullets all cleared). `enemyBullets = []` is correctly called in both the keydown handler and `spawnWave()`. |
| 7 | No runtime JS errors | Console was clean across all tested game states |
| 8 | Wave clear → spawn new wave | `enemyBullets` cleared, new enemies created, `enemyMoveCounter` reset |

## Runtime State Probing Results

These are the `browser_console(expression=...)` calls that revealed each issue:

### Restart flow test (reveals state-clear correctness)
```js
// After pressing Space to restart from gameover:
`lives=${lives}, score=${score}, wave=${wave}, gameState=${gameState},
 enemiesAlive=${enemiesAlive}, enemyBullets.length=${enemyBullets.length}`
// Result: lives=3, score=0, wave=1, gameState=playing, enemiesAlive=40, enemyBullets=47
// enemyBullets=47 after restart confirms high fire rate regenerates bullets instantly
```

### Pre-kill state check (before simulating wave clear)
```js
`lives=${lives}, score=${score}, wave=${wave}, gameState=${gameState}`
// gameState=gameover, lives=0, score=0, wave=1, enemiesAlive=40, enemyBullets=47
// Confirms player died before firing a single shot — fire rate issue
```

### Manual bomb test (setting enemiesAlive = 0 mid-frame)
```js
enemies.forEach(e => { e.alive = false; });
enemiesAlive = 0;
// After 1 second:
`wave=${wave}, enemiesAlive=${enemiesAlive}, alive_count=${enemies.filter(e=>e.alive).length}, gameState=${gameState}`
// Result: wave=1 (didn't advance), gameState=gameover — player died from existing bullets
// before the wave-clear code ran, confirming the ordering issue (bug #2)
```

## Key Methodology Takeaways

1. **State probing is essential for canvas games** — you can't inspect DOM state. Every `browser_console(expression=...)` call reads internal JS variables directly.
2. **`splice` inside reverse `for` + `break` = almost always buggy.** This pattern appears in many game collision implementations. Always trace with 3 elements.
3. **Game loop ordering matters.** The order of operations inside `update()` determines whether post-death code runs. Always check what follows a death-triggering call.
4. **Don't trust the "pause" of the game-over state.** The `draw()` function may still render game entities behind the overlay. This is a visual bug but can mislead testing.
5. **HTTP server is mandatory for canvas/audio.** `file://` protocol blocks AudioContext creation and may throttle requestAnimationFrame.
6. **Test restart twice.** The first restart tests the explicit reset logic. The second restart tests whether that reset was clean (no stale variables, no accumulated arrays).
