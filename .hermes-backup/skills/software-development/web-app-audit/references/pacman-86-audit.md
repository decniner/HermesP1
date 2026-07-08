# Case Study: Pac-Man '86 HTML Game Audit

**App:** Single-file HTML5 Canvas Pac-Man clone with Web Audio API sound effects, tile-based maze, 4 ghost AI, power pellets, touch/swipe controls, and scoring.

**Methods used:** Static source analysis + live browser testing via local HTTP server + runtime state probing via `browser_console(expression=...)` + interactive key-press testing + screenshot verification.

## Bugs Found

### 🔴 Critical (3)

| # | Bug | Location | Root Cause | Impact |
|---|-----|----------|------------|--------|
| 1 | **Ghosts permanently stuck — cannot move after exiting house** | `isWall()`, line 127 | Ghost house bounding box check `if (r >= 11 && r <= 14 && c >= 11 && c <= 17 && map[r][c] !== 2 && map[r][c] !== 3)` treats **every** non-2/non-3 tile in the rectangle as a wall — including dot tiles (value 0). Ghosts spawn at row 11 (y = 11×T + T/2 + 4 = 188) on a dot tile (MAP_SRC[11][13] = 0). Since `0 !== 2 && 0 !== 3` is true, their own tile is a "wall." All four directions return false from `canMove()`. | **Ghosts are permanently frozen.** Zero enemy threat. The game has no chase/hunt mechanic — it is not playable as Pac-Man. **Live proof:** `canMove(216,188,'u')=false`, `canMove(216,188,'d')=false`, `canMove(216,188,'l')=false`, `canMove(216,188,'r')=false` for the entire game duration. |
| 2 | **Pac-Man spawns inside the ghost house** | `spawnPac()`, line 98 | Searches MAP_SRC row-major for the first value-2 (empty) tile. The first value-2 tile is at **row 13, col 11** — inside the ghost house interior. Confirmed: `"First empty tile: row=13 col=11"`. | Pac-Man starts in the ghost house with zero dots to eat. Must navigate through the ghost house door (row 12, cols 13–15, value 3) just to reach the maze. Every respawn after death repeats this misplacement. |
| 3 | **Ghost house ceiling dots (row 11, cols 11–17) are unreachable** | `isWall()`, line 127 (same bounding box) | Row 11 has 7 dot tiles (value 0) above the ghost house. These should be eatable maze dots. But the ghost house bounding-box check covers rows 11–14, so `isWall` returns true for these dot tiles — Pac-Man enters the bounding box when going through the door and can't traverse them. | 7 dots are permanently uneatable. The level can never be completed with a full score. |

### 🟠 High (3)

| # | Bug | Location | Detail | Impact |
|---|------|----------|--------|--------|
| 4 | **Touch Y delta uses start-X instead of start-Y** | `touchmove` handler, line 346 | `const dy = e.touches[0].clientY - sx;` — the touch-start handler only stores `sx` (line 344). There is no `sy` variable. `clientY - sx` accidentally works when the touch starts near the left of the screen (small X), but **swiping vertically DOWN from the right side** produces `clientY - sx < 0`, registering **UP instead of DOWN**. | Touch controls are unreliable for vertical swipes from the right half of the screen — a core control path on mobile. |
| 5 | **Ghost collision doesn't skip in-house ghosts** | `updateGhosts()`, line 218 | Collision check `Math.abs(g.x-pac.x) < 10 && Math.abs(g.y-pac.y) < 10` runs for **all** ghosts, including those with `g.inHouse === true`. The drawing code (line 296) skips in-house ghosts with `exitTimer > 5`, but collision logic has no guard. | Invisible ghost kills: Pac-Man near the ghost house exterior can die from a ghost that's still inside and not visually rendered. |
| 6 | **Fright mode doesn't reverse ghost direction** | `updateGhosts()`, lines 194–200 | When `g.fright = true` (power pellet eaten), ghosts should **immediately reverse direction** per classic Pac-Man. This implementation only changes the target to a random point; `g.dir` is not reversed. | Ghosts continue toward Pac-Man instead of fleeing when a power pellet is eaten, making power pellets far less effective and breaking a core game mechanic. |

### 🟡 Medium (1)

| # | Bug | Location | Detail |
|---|------|----------|--------|
| 7 | **Fragile tunnel wrap uses exact Y equality** | `moveEntity()`, lines 146–147 | `if (ny === 14*T + 8 && nx < 0)` — strict `===` on floating-point position `ny`. If the Y coordinate drifts even 1 pixel (from entry path or FP accumulation), the wrap silently fails and the entity stops at the wall. |

### 🔵 Low (3)

| # | Bug | Detail |
|---|------|--------|
| 8 | **Dead "bounce mouth" code** | `if (!moveEntity(pac,pac.dir,2)) { /* Bounce mouth */ }` — empty if-block with only a comment. Pac-Man's mouth doesn't react to hitting a wall. |
| 9 | **Ghost scatter targets defined but never used** | Each ghost has a `scatter` value (14 or 26) in `spawnGhosts()`, but the AI (lines 193–200) always targets Pac-Man's position. No scatter/chase mode switching exists. |
| 10 | **Win condition can re-trigger during level reset** | `update()` lines 248–253: `if (dots <= 0)` fires `win()` + `setTimeout(... ,1000)`. During that 1-second delay, `update()` still runs and `dots` is still 0, so the condition can fire again, stacking multiple `setTimeout` callbacks. |

### ✅ Verified Correct

| # | Pattern | Detail |
|---|---------|--------|
| 1 | No runtime JS errors | Console was clean across all game states (menu, playing, gameover). |
| 2 | Canvas rendering | Maze walls, dots, power pellets, and ghost house door are drawn correctly. |
| 3 | Menu → Playing transition | Overlay hides, game starts, Pac-Man and ghosts spawn. |
| 4 | Eating dots | Dot-eating logic works (score increment, dot removal, chomp sound) — confirmed via runtime teleport. |
| 5 | Power pellets | Eating a power pellet sets `fright = 300` and `g.fright = true`. |
| 6 | Score display | HUD updates correctly. |
| 7 | Ghost house door rendering | Pink door drawn at correct position (row 12, cols 13–15). |

## Runtime State Probing Results

These `browser_console(expression=...)` calls revealed each issue:

### Ghost freeze verification
```js
// After ghosts exit the house — they never move
ghosts.map((g,i)=>g.name+': ('+Math.round(g.x)+','+Math.round(g.y)+') d='+g.dir+' ih='+g.inHouse).join('; ')
// Result: "Blinky: (216,188) d=u ih=false; Pinky: (216,189) d=u ih=false; Inky: (216,190) d=u ih=false; Clyde: (216,190) d=u ih=false"

// All directions blocked for Blinky:
'Blinky canMove: u='+canMove(216,188,'u')+' d='+canMove(216,188,'d')+' l='+canMove(216,188,'l')+' r='+canMove(216,188,'r')
// Result: "Blinky canMove: u=false d=false l=false r=false"

// isWall returns true on a dot tile:
'isWall at ghost pos (216,188): r='+Math.floor(188/16)+' c='+Math.floor(216/16)+' val='+MAP_SRC[11][13]+' isWall='+isWall(216,188)
// Result: "isWall at ghost pos (216,188): r=11 c=13 val=0 isWall=true"
```

### Pac-Man spawn verification
```js
// Find first empty tile in row-major order:
(function(){for(let r=0;r<31;r++)for(let c=0;c<28;c++)if(MAP_SRC[r][c]===2)return 'First empty tile: row='+r+' col='+c;return 'none'})()
// Result: "First empty tile: row=13 col=11"

// Pac-Man position after fresh start (menu→playing):
`state=${state}, score=${score}, dots=${dots}, lives=${lives}, pac=(${Math.round(pac.x)},${Math.round(pac.y)}) dir=${pac.dir}`
// Result (frame ~143): "state=playing, score=0, dots=288, lives=3, pac=(268,216) dir=r"
// Already moved right in ghost house, stuck at col-17 wall, score still 0 — no dots reachable.
```

### In-game state teleport (door escape test)
```js
// Teleport Pac-Man to ghost house door and try to leave:
pac.x = 13*16 + 8; pac.y = 13*16 + 8; pac.dir = 'r'; pac.nextDir = 'u';
// Then check pac.position to verify canMove up returns true through door (value 3 tiles)
```

## Key Methodology Takeaways

1. **Map-based ghosts need bounding-box validation** — in tile-based games with special zones (ghost houses, spawn rooms), verify the bounding box doesn't overlap with valid playable tiles. Test by spawning an entity at every tile in the zone's row range.
2. **Spawn-finding algorithms must be region-scoped** — "first empty tile" in row-major order is wrong for any map where empty tiles exist inside restricted zones before the intended spawn area. Hardcode player/ghost spawn positions instead.
3. **Touch axis copy-paste bugs are reliably found by cross-checking the variables** — if `touchstart` stores only one coordinate but two are used in `touchmove`, the second is almost always wrong.
4. **State transitions need vector updates** — any state transition that changes movement behavior (fright mode, scatter mode, stunned, frozen) should explicitly update the movement direction, not just a flag.
5. **Exact-equality checks on floating-point positions** are universally fragile. Use epsilon or range checks for edge-wrapping, warp zones, and tile-transition triggers.
6. **Dead code patterns signal missing features** — empty if-blocks and initialized-but-never-read fields are often placeholders for mechanics that were planned but never implemented.
