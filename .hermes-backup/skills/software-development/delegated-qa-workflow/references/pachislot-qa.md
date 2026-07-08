# Pachislot Game QA Patterns (from session)

Patterns discovered while building Juggler '86, GOGO JUGGLER, and King Pulsar clones.

## State Machine Checklist

| State | What Should Be True |
|-------|-------------------|
| `idle` | Reels stopped, PULL LEVER visible, STOP buttons hidden |
| `sp` | All 3 reels spinning, STOP_READY becomes true after ~800ms (MIN_SPIN_MS), STOP buttons appear under each reel |
| `gogo` | GOGO lamp flashing (top lamps blink), bonus type determined, timer counting down |
| `bonus` | User can pull lever again (no MED deduction), BG counter decrements, reels spin normally |

## Common Bugs From Session

### Bonus Mode Never Sets `state='sp'`
After bonus deduction in `startSpin()`, state remains `'bonus'` instead of transitioning to `'sp'`. The spin loop never processes.  
**Fix:** Extract `state='sp'` to run unconditionally after the bonus/idle branch, not inside the `else` clause.

### Re-spin Blocked After First Round
`STOP_CNT` reaches 3 after all reels stop but never resets. The PULL LEVER click handler checks `STOP_CNT===0` which fails.  
**Fix:** Add a separate PULL LEVER area check that works regardless of STOP_CNT. The lever button is usually at the bottom of the canvas.

### Computed Property Name Syntax Error
```javascript
// BROKEN — bracket + colon clash
const m = {0:'a',[5:[60,'STAR×3']]};  // SyntaxError

// FIXED — bare numeric keys
const m = {0:'a',5:[60,'STAR×3']};
```
Numeric keys don't need `[brackets]`. Only use `[expr]:` when the key is a variable.

### Patch Artifacts
After multiple rapid patches, leftover orphan lines accumulate:
```javascript
    sx=e.touches[0].clientX;sy=e.touches[0].clientY;
}
    sx=e.touches[0].clientX;  // ← orphan! Still runs but wrong scope
}
```
**Validation:** After the final patch, always run `node -e` syntax check on the extracted JS.

## GOGO Lamp Visual Design (from reference image)

The GOGO! CHANCE lamp should match the pop-art style:
- **Background:** Bright pink `#FF1493` with black border
- **Starburst:** Dark blue `#1a0050` 8-point star
- **"GOGO!" text:** Glossy light pink `#FFB6C1` with highlight offset up-left
- **"CHANCE" text:** White bold block with black drop shadow
- **Animation:** Fades in/out with `Math.sin(Date.now()*0.008)` for pulsing glow

## Reel Mechanics Validation

1. Result predetermined at spin start in `RESULT_SLOT[idx]`
2. Each STOP button snaps reel to `RS[idx][RP[idx]] = RESULT_SLOT[idx]`
3. STOP buttons appear only when `SPINNING[idx]` is true
4. STOP_READY[idx] becomes true after `Date.now() - SPIN_START > MIN_SPIN_MS`
5. All 3 reels stopped → check result → pay out or enter GOGO

## Click Target Priority Order (handleClick)

1. `if(state==='bonus'){startSpin();return;}`
2. Check each STOP button area (only drawn when SPINNING)
3. Check PULL LEVER button area (bottom of canvas)
4. `if(state==='idle'&&STOP_CNT===0){startSpin();return;}` — fallback
