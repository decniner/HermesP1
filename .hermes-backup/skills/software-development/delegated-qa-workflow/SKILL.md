---
name: delegated-qa-workflow
description: "Use when you've written code locally and want a subagent to run tests, report results, and verify fixes in a CI-like loop — write, delegate testing, fix, retest, deliver."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [testing, qa, delegation, subagent, development-workflow, ci-loop]
    related_skills: [test-driven-development, systematic-debugging]
---

# Delegated QA Workflow

Run independent QA testing via subagents in a write → test → fix → retest loop. Unlike TDD (where a subagent implements via test-first), this pattern has **you write the code**, then delegates **verification** to an independent subagent.

## When to Use

- You wrote code and want a subagent to run tests independently and report results
- You want a CI-like feedback loop: test → get failure report → fix → test again
- You want to keep your context focused on development while QA runs in the background
- The user wants to see a complete development cycle with quality gates

Don't use for:
- Full implementation by subagent (use `test-driven-development` instead)
- Debugging a live issue (use `systematic-debugging` instead)
- Code review of a PR (use `requesting-code-review` instead)
- Frontend web app / HTML game auditing (use `web-app-audit` instead — covers browser testing, canvas game logic, drag-and-drop, localStorage, and state-machine analysis)

## The Cycle

```
┌─ Dev ───────────────────┐
│ ✏️ Write code + tests    │
└──────────┬───────────────┘
           ▼
┌─ QA Subagent ───────────┐
│ 🧪 Run ALL tests         │
│ 📋 Report: pass/fail/err │
└──────────┬───────────────┘
           ▼
┌─ Dev ───────────────────┐
│ 🔧 Review failures       │
│ 🔨 Fix bugs              │
│ 📝 Improve test coverage │
└──────────┬───────────────┘
           ▼
┌─ QA Subagent (Round 2) ─┐
│ 🧪 Re-run ALL tests      │
│ ✅ Verify fixes           │
└──────────┬───────────────┘
           ▼
        ⚠️ Failures?
        ├── YES → back to Dev fix
        └── NO  → ✅ Deploy to user
```

## Step-by-Step

### Step 1: Write code and tests

Create your source files and a test suite using your preferred test runner (pytest, unittest, etc.). The tests should cover:
- Normal cases (happy path)
- Edge cases (boundaries, empty inputs)
- Error cases (invalid input, missing data)

### Step 2: Delegate initial QA

Use `delegate_task` with a goal focused only on testing. Keep the subagent's toolset minimal — it only needs `terminal` to run the test command:

```python
delegate_task(
    goal=f"Run ALL tests in the project and report results",
    context=f"""
    Project path: {project_path}

    Commands to run:
    cd {project_path}
    pip install pytest
    python3 -m pytest test_*.py -v --tb=long

    Report EXACTLY:
    1. Which tests PASSED
    2. Which tests FAILED
    3. Full error message for EACH failure (copy the traceback)
    4. Any warnings or notable observations
    """,
    toolsets=['terminal']
)
```

**Key details in the context:**
- Full `cd` + install + test command sequence (subagent starts from scratch)
- `--tb=long` for complete tracebacks on failures
- `toolsets=['terminal']` restricts the subagent to shell only — no file/browser distractions
- On Windows git-bash, the subagent may need `python3` or `python` — let it figure out which works

### Step 3: Review and fix

The subagent's report comes back as a new message. Review it for:
- **False positives** — test failures that reveal bugs in the code
- **Test quality** — tests that should catch edge cases but don't
- **Missing coverage** — behaviors that went untested

Fix the issues in your code, then update tests if needed to cover the missing cases.

### Step 4: Delegate retest

Send the same project back to a QA subagent for verification:

```python
delegate_task(
    goal=f"Re-run ALL tests to verify the bug fixes",
    context=f"""
    Project path: {project_path}

    The previous run showed failures in:
    {list_previous_failures}

    Commands:
    cd {project_path}
    python3 -m pytest test_*.py -v --tb=long

    Confirm:
    1. Previously failing tests now PASS
    2. Previously passing tests still PASS (no regressions)
    """,
    toolsets=['terminal']
)
```

### Step 5: Loop until green

Repeat steps 3-4 until all tests pass. Each QA round should be a fresh subagent — don't reuse the same one across rounds (fresh context, no preconceptions).

### Step 6: Deliver

Once the last retest returns all green, report the result to the user with:
- Summary of what was built
- What bugs were found and fixed
- Final test count
- Where to find the project

## Example: Full Cycle (from this session)

This session's Japanese flashcard quiz app followed the exact cycle:

```
Round 1 QA → 10 tests passed (but hidden bug in run_quiz())
Review → Found `return` inside `for` loop — only 1 of N questions returned
Fix → Changed to build list, return all questions
         Added test_run_quiz_honors_num_questions to prevent regression
Round 2 QA → 11 tests passed ✅
Deliver → "Ready for deployment"
```

The bug was not caught by the first round because no test verified that `num_questions=5` actually returns 5 questions. The QA subagent's report was clean, but the code review step (step 3) identified the gap.

## HTML/JS Game QA (No Test Runner)

Games built as single-file HTML (no Python, no pytest) need code review, not unit tests.

### Game QA Subagent Template

```python
delegate_task(
    context=f\"\"\"
    File: {game_path}
    This is an HTML5 Canvas game. Review the JavaScript code thoroughly.

    Check:
    1. JS syntax errors, undefined variables, missing functions
    2. Game logic: movement, collision detection, spawning, scoring
    3. Touch controls: touchstart/touchmove/touchend handlers
    4. Audio: Web Audio API initializes on user interaction
    5. Game state: menu → playing → gameover → restart transitions
    6. Edge cases: boundaries, empty states, rapid inputs
    7. Canvas scaling: viewport meta, resize handler, orientation change
    8. Braces balanced (count `{` vs `}`)
    9. No DOM/JS console errors

    Read the file with read_file, then report ALL issues found.
    \"\"\",
    goal=f\"Review the HTML/JS game at {game_path} for bugs. Be thorough - check controls, logic, audio, and edge cases.\",
    toolsets=['terminal', 'file']
)
```

### Key Checks for Games

| Area | What to Check |
|------|---------------|
| **Collision** | Bullets piercing enemies? Object index skipping after splice? |
| **Touch** | `clientY` paired with `sx`? (wrong!) vs `sy`? (correct). Swipe reset after direction change? |
| **Scaling** | `orientationchange` event handled? Uses `100dvh` not `100vh`? Container div wrapping canvas? |
| **Ghost house** | Collision system needs entity type flag — ghosts vs player need different wall rules |
| **Reels** | Symbols snap to result when spinning stops? Staggered left-to-right stop timing? |

### Critical Pitfall: Do NOT Skip QA — Ever

The user explicitly demands QA before delivery. This is not optional. Shipping untested code results in the user immediately reporting it doesn't work, which wastes more time than running QA upfront.

### Self-QA: Verify Before Forwarding

When you build or deploy a service (web app, backend, tunnel), **QA it yourself end-to-end before telling the user it's ready.** The user has explicitly corrected this pattern — do not say "try it now" without first running the exact same test they would run.

**Wrong — stops too early:**
```
"Here's the URL, try it now!"
```

**Right — proves it works before asking:**
```
1. Hit the actual endpoint with curl: ✅ 200 / 20 events
2. Verify the full pipeline returns valid data: ✅ Score 72, 16 events, verdict 3,132 chars
3. Check logs for errors: ✅ No exceptions
4. Then tell the user: "Ready. [URL]"
```

**Rules for every deployment:**
1. Before messaging the user, run the endpoint with curl or the browser tool using the EXACT same URL the user would use (tunnel URL, not localhost)
2. Verify the response is valid JSON/HTML (not empty, not an error page, not a tunnel warning page)
3. Check the backend logs for any warnings or exceptions
4. Only then deliver to the user with a concrete status summary

This applies to:
- New services you spin up (Flask, Streamlit, HTTP servers)
- Tunnel URLs you create (serveo, localtunnel, cloudflared)
- API endpoints you expose
- Any "ready to test" claim

**Historical failure without this rule:** The POGIBOT tunnel was deployed via serveo, told to the user as "ready," but the tunnel was silently dropping long POST requests. The user tried it 3+ times and kept getting failures. Each round-trip wasted trust and time. Had I curled the tunnel URL first with the actual analyze payload, I'd have caught the serveo timeout issue immediately.

### HTML-Preview QA Trap: The Local vs. Deployment Gap

HTML artifacts destined for htmlpreview.github.io (or similar third-party preview services) have a critical QA gap:

A subagent testing via http://127.0.0.1:8128/ gets a FALSE PASS — the JS runs fully, all click handlers work, audio plays, swipe gestures respond. But the same artifact through the actual htmlpreview URL may silently fail because:
- Inline JS over ~3,400 chars is truncated → click handlers never registered
- External script.js files don't load → entire JS missing
- Touch/scroll events differ inside the iframe sandbox

Fix — QA through both environments:
1. First test locally (via Python HTTP server) for development feedback
2. Then push to GitHub and test through the actual htmlpreview URL before delivering to the user
3. The subagent context must include the htmlpreview URL and instructions to test there, not just the local server

Historical example: This session's birthday card had a carousel that worked perfectly via localhost. The subagent reported no issues found. But through htmlpreview, the inline JS was truncated at 3,442 chars (42 over the limit), so the carousel swipe handlers never registered and the go(0) init never ran. The card appeared to open but didn't respond to swipes.

**This was a correction — encode it as a hard rule:**
1. After writing any game, script, or tool → **dispatch QA subagent immediately**
2. Wait for QA results before delivering to user
3. Fix all bugs found, then re-QA
4. Only deliver when QA passes

Consequences of shipping untested game code:
- Broken touch controls (Y-axis using X coordinate)
- Frozen enemies (wrong collision rules)
- Game that doesn't fit mobile screen
- Disjointed/syntax-broken code after patching

**Always run QA subagent before delivering game files to the user.**

See `references/game-qa-checklist.md` for the full game-specific QA template to use with subagents.

## Comparison with TDD

| Aspect | TDD Subagent | Delegated QA |
|--------|-------------|--------------|
| Who writes code | Subagent | You |
| Who writes tests | Subagent (first) | You (before or with code) |
| Subagent's role | Implement via test-first | Verify independently |
| Test timing | Before implementation | After implementation |
| Primary value | Correct-by-construction | Independent verification |

## Post-Patch Verification (HTML/JS Games)

After using `patch` on HTML/JS game files, always verify the file is still syntactically correct before delivering.

**Why:** The `patch` tool's fuzzy matching can leave orphaned lines when `old_string` doesn't exactly match the file content. This creates silent syntax errors — the game loads as a blank page with no visible error.

**Real example:** Patching the Pac-Man touch swipe code left orphaned lines `sx=e.touches[0].clientX;` between two closing braces, creating a syntax error that would only surface after the user tried to open the file.

**Fix — always run after patching a game:**

```bash
# 1. Check braces are balanced
python -c "
import re
with open('game.html') as f:
    c = f.read()
m = re.search(r'<script>(.*?)</script>', c, re.DOTALL)
js = m.group(1) if m else ''
opens = js.count('{'); closes = js.count('}')
print(f'Braces: {opens}/{closes} balanced={opens==closes}')
"

# 2. Run Node.js syntax check (catches ALL syntax errors)
node -e "
const fs = require('fs');
let html = fs.readFileSync('game.html', 'utf8');
const m = html.match(/<script>([\\s\\S]*?)<\\/script>/);
let js = m[1];
try { new Function(js); console.log('Syntax OK'); }
catch(e) { console.log('Syntax ERROR:', e.message); }
"
```

Add this as a step after every game-code patch before proceeding to the next task.

## Common Pitfalls

1. **Missing install step** — The subagent's terminal starts fresh. Always include `pip install pytest` (or whatever test runner) in the context.
2. **Overly broad subagent tools** — `toolsets=['terminal']` is usually sufficient. Adding `file` or `browser` tools adds token cost without value.
3. **One-shot retest without failure context** — When retesting, list which tests failed previously so the subagent knows what to confirm.
4. **Not cleaning up** — Delete temp analysis scripts after use (`rm path/to/script.py`).
5. **Assuming subagent result is final** — A subagent that says "uploaded successfully" may be wrong. For operations with side effects, verify independently.
7. **`execute_code` can be blocked** — Security guardrails may reject `execute_code`. Fall back to `write_file` → `terminal(command="python3 path/to/script.py")`.
8. **Windows path quirks** — In git-bash, use forward slashes or double backslashes. `taskkill //PID //F` (double // avoids path conversion).  
9. **Binary files need a python script, not read_file** — MQL5 (.mq5) files use UTF-16 encoding. `read_file` will report them as binary. Write a decoding script with `write_file`, then run via `terminal()`.
10. **Subagent `toolsets` restriction** — For test-only QA, pass `toolsets=['terminal']` to save tokens. Don't add unused toolsets.

## Verification Checklist

- [ ] Code and tests written and saved to disk
- [ ] QA subagent dispatched with minimal toolset
- [ ] Failure report reviewed and bugs fixed
- [ ] Test coverage improved where gaps were found
- [ ] Retest subagent dispatched
- [ ] All tests passing
- [ ] Temp scripts cleaned up
- [ ] User notified with project summary

## Reference Files

- `references/game-qa-checklist.md` — Full game-specific QA template: syntax check, touch controls, collision, state machines, pre-delivery validation script, and quick-check table.
- `references/session-qa-run.md` — Reference transcripts and patterns from real QA delegation runs.
- `references/pachislot-qa.md` — Pachislot/Juggler/King Pulsar QA patterns: state machine bugs, computed property syntax, reel mechanics, click target priority.
- `references/solitaire-qa.md` — Solitaire (DOM drag-and-drop) QA: suit color parity, foundation validation, stack-to-foundation rejection, event listener leaks, revert logic.
