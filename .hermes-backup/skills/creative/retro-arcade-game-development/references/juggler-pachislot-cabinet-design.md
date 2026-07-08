# Pachislot Cabinet Design Reference

## Machine: GOGO JUGGLER (KITAC, First Gen ~1996)

Replicated from reference screenshot (raw cabinet photo, not a simulator).

## Layout Proportions (H=640px design size)

| Section | Y Range | % Height | Content |
|---------|---------|:--------:|---------|
| Top KITAC bar | 0-14 | 2% | Red bar, yellow "KITAC" text |
| GOGO lamps | 14-32 | 3% | 12× red circular lamps that flash on bonus |
| BIG CHANCE panel | 34-88 | 8% | Pink panel with paytable, REPLAY, clown faces |
| Reel area | 94-312 | 34% | Blue starry BG, 3 reels, left indicators, right panel |
| Control panel | 324-390 | 10% | Lever, displays, CHANCE badge, Insert Medal |
| GO! buttons | 400-440 | 6% | 4× red circular buttons |
| GOGO JUGGLER logo | 454-562 | 17% | Large 3D text logo |
| Speakers | 568-640 | 11% | Speaker grilles |

## Machine: KING PULSAR (Yamasa)

Replicated from reference screenshot. Distinct from Juggler — green/gold cabinet, frog mascot, ornate frame.

### Layout (H=660px design size)

| Section | Y Range | % Height | Content |
|---------|---------|:--------:|---------|
| YAMASA bar | 8-26 | 3% | Black bar, white "YAMASA YAMASA-NEXT" text |
| Honeycomb lamps | 26-42 | 2.5% | Orange hexagon pattern lamps, flash on bonus |
| Main screen | 44-284 | 36% | Green BG with gold filigree, reels, frog mascot |
| Controls | 296-356 | 9% | Lever, displays, BIG/REG counters |
| GO! buttons | 360-400 | 6% | 4× red circular buttons |
| PULL button | 380-416 | 5.5% | Oval button |
| KING PULSAR logo | 410-500 | 14% | Massive 3D gold serif text |
| Speakers | 508-660 | 23% | Large speaker grille section |

### Colors

| Element | Hex Code |
|---------|----------|
| Cabinet frame | `#0a0505` with green/gold borders (`#0a5a0a` / `#c80`) |
| Screen background | `#0a3a0a` (dark green) |
| Gold filigree | `rgba(200,150,50,0.15)` |
| Frog emblem | `#080` (body), `#f00` (eyes/mouth), `#c80` (sunburst) |
| BIG BONUS text | `#f00` |
| REGULAR BONUS text | `#fa0` |
| KING text | `#f00` |
| PULSAR text | 3D gold: `#c80` base, `#ff0` highlight |
| Control panel | `#0a0505` with gold `#c80` border |
| LED displays | `#f00` on `#000` background |

### Symbol Set (King Pulsar)

| Index | Emoji | Name | Weight | Payout (triple) |
|:-----:|:-----:|:----:|:------:|:--------------:|
| 0 | 🐸 | FROG | 18 | 200 (BIG BONUS) |
| 1 | 🔔 | BELL | 16 | 100 (REG BONUS) |
| 2 | 7 | SEVEN | 14 | 300 (BIG BONUS) |
| 3 | BAR | BAR | 16 | 200 (BIG BONUS) |
| 4 | 🍒 | CHERRY | 14 | 80 |
| 5 | ⭐ | STAR | 8 | 60 |
| 6 | 🔔 | BELL2 | 7 | 100 |
| 7 | 7 | SEVEN2 | 7 | 300 |

### Reel Window Elements

- **Top left:** "BIG BONUS" in red, "REGULAR BONUS" in orange
- **Top center:** Golden sunburst emblem (24 rays) with green frog face (2 white eyes with red pupils, oval green body, red open mouth)
- **Right side:** "WIN" lamp (glows yellow on bonus), cherry icon
- **Left indicators:** 5 colored circles: 3(orange), 2(blue), 1(purple), 2(orange), 3(purple)
- **Right panel text:** "Game over", "Wait", "Replay" (vertical, red)
- **Banner:** "BAT TYPE - HAVE A GOOD TIME WITH EXCITING MACHINE"

## Common Bugs & Fixes

### 1. Computed Property Name Syntax
```javascript
// ❌ WRONG — colon inside brackets is a syntax error
{[5:[60,'STAR×3']]}

// ✅ CORRECT — bare numeric key
{5:[60,'STAR×3']}

// ✅ ALSO VALID — computed property with brackets outside
{[5]:[60,'STAR×3']}
```

### 2. Touch Swipe Y-Axis Bug
```javascript
// ❌ WRONG — uses starting X position for Y calculation
const dy = e.touches[0].clientY - sx;

// ✅ CORRECT — track BOTH axes independently
let sx = 0, sy = 0;
touchstart: { sx = t.clientX; sy = t.clientY; }
touchmove:  { dx = t.clientX - sx; dy = t.clientY - sy; }
```

### 3. Bonus State Never Set to 'sp'
```javascript
// ❌ WRONG — bonus spin leaves state='bonus', update() returns early
if (state === 'bonus') { BG--; MED -= BET; }
// ... state is still 'bonus', reels never spin

// ✅ CORRECT — must set state='sp' for ALL spins
if (state === 'bonus') { BG--; MED -= BET; }
state = 'sp'; // ← ALWAYS set this
```

### 4. Game Not Restartable After Spin
```javascript
// ❌ WRONG — STOP_CNT=3 blocks new spins
if (state === 'idle' && STOP_CNT === 0) startSpin(); // fails after 1st spin

// ✅ CORRECT — reset STOP_CNT in startSpin(), or add lever area check
// In startSpin():
STOP_CNT = 0;

// In handleClick():
if (mx >= leverArea && my >= leverArea && state === 'idle') startSpin();
```

### 5. JavaScript Syntax Verification
Always run through Node.js before delivery to catch syntax errors:
```bash
node -e "new Function(require('fs').readFileSync('game.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1]); console.log('OK');"
```

### 6. Leftover Patch Artifacts
After using the `patch` tool, re-read the file to check for duplicate/orphan lines:
```bash
# Check brace balance
grep -o '{' file.html | wc -l  # count opens
grep -o '}' file.html | wc -l  # count closes
```

## Paytable Reference

### Juggler First-Gen
| Combination | Payout | Type |
|-------------|:------:|------|
| 777 | 300 | BIG BONUS |
| BAR×3 | 200 | BIG BONUS |
| FROG×3 | 200 | BIG BONUS |
| BELL×3 | 100 | REG BONUS |
| CHERRY×3 | 80 | - |
| CHERRY×2 | 20 | - |
| CHERRY (left) | 10 | - |
| CHERRY (center) | 5 | - |

### King Pulsar
| Combination | Payout | Type |
|-------------|:------:|------|
| 777 | 300 | BIG BONUS |
| BAR×3 | 200 | BIG BONUS |
| FROG×3 | 200 | BIG BONUS |
| BELL×3 | 100 | REG BONUS |
| CHERRY×3 | 80 | - |
| CHERRY×2 | 20 | - |
| ORANGE×3 | 100 | REG BONUS |

## Bonus Mechanics
- BIG BONUS: 30 games, triggered by 777, BAR×3, or FROG×3
- REG BONUS: 8 games, triggered by BELL×3 or ORANGE×3
- Each bonus game subtracts BET from MED (but can win additional payouts)
- GOGO lamp flashes for ~2 seconds before bonus starts
- Bonus counter displays: "BIG BONUS 25/30" or "REG BONUS 5/8"

## Required State Machine for Pachislot
```
idle → startSpin() → sp → pressStop()s → idle
                                          └→ gogo → bonus → startSpin() → sp → ...
```

Critical: The `state='sp'` transition must happen for BOTH normal spins and bonus respins.

## GOGO Lamp Mechanics (ぺかる — "peka")

- **Juggler:** Row of 12 red circular lamps at top. Flashing red with shadow blur when active. "GOGO!" text lights up beneath.
- **King Pulsar:** Orange honeycomb hexagon lamps below YAMASA bar. GOGO CHANCE overlay appears over reels (pop-art style).
- **Overlay design:** Pink `#FF1493` background with black border, blue starburst with 8 points, "GOGO!" in glossy pink salmon, "CHANCE" in white with black drop shadow. Pulsing alpha animation.
