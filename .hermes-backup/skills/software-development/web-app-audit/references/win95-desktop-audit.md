# Win95 HTML Simulator Audit

**Source:** Single-file HTML/CSS/JS app (383 lines). Simulates Windows 95 desktop with start menu, taskbar, window manager, screensaver, BSOD, and a Minesweeper game.

**Audit method:** Python http.server → browser testing. All features exercised interactively; internal state probed via `browser_console` expressions; zero JS console errors across all operations.

## Key Findings

### Critical
| # | Bug | Why it matters | Fix |
|---|-----|----------------|-----|
| 1 | **Maximize/restore toggle broken** — `w.dataset.maxed` never set to `true` in the else branch. Second click does nothing. | Maximize is a one-way operation | Add `w.dataset.maxed = true;` after saving original dimensions |
| 3 | **Minesweeper timer never starts** — `msTimer` display is static `000`, no `setInterval` or counter logic exists | Core gameplay element missing | Start a 1-second interval on first click |

### Medium
| # | Bug | Why it matters |
|---|-----|----------------|
| 4 | **Mine counter hardcoded** — shows `💣 10` even after flags placed; `msFlagged` tracked but never reflected | Counter gives wrong information |
| 5 | **Window focus doesn't unfocus others** — `.win-title.inactive` applied but never removed from other windows | All windows show active (blue) title bars |
| 6 | **Two-finger tap for flagging** — non-standard; long-press is the expected mobile Minesweeper pattern | Poor mobile UX |
| 7 | **No screensaver auto-activation** — pipe animation exists but no idle timer triggers it | Feature incomplete |

### Low
| # | Bug | Why it matters |
|---|-----|----------------|
| 2 | **Maximize button icon never changes** — always `□` even when maximized | Visual feedback missing |
| 8 | **Empty `<img src="">` in start menu** — 3 menu items have `src=""` | Browser logs spurious requests |
| 9 | **Windows can position off-screen** — hardcoded position math doesn't account for taskbar height | Lost window content |
| 10 | **BSOD says "Press any key"** but only `onclick` handler exists, no `keydown` listener | Instructions contradict behavior |
| 11 | **Recycle Bin is placeholder** — "This folder is empty" with no actual trash functionality | Cosmetic stub |

### Working Correctly
- Start menu open/close and click-outside dismissal
- Window create, close, minimize/restore
- Taskbar buttons track window state
- Minesweeper cell reveal, flood-fill, number display, right-click flag handler (desktop)
- BSOD styling and click-to-dismiss
- Desktop icon double-click to open
- Clock display (10s interval)
- No JS console errors at any point

## Techniques Used

1. **Local HTTP server** (Python3 http.server) — file:// protocol is blocked by browser automation
2. **Read full source first** — 383 lines means reading the entire file in 2 calls before testing
3. **Probe internal state via browser_console** — verify dataset attributes, style properties, game board arrays
4. **Snapshot + Vision in tandem** — snapshot for DOM structure, vision for visual verification (maximize, BSOD)
5. **Test through full interaction cycles** — open→minimize→close→reopen→maximize→restore, not just one-off clicks
6. **List what works alongside what's broken** — balanced reporting shows the app has real functionality too
