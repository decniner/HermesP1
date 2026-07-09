---
name: hermes-custom-dashboard
description: "Build and run a lightweight custom web dashboard alongside Hermes Agent — visual kanban board, cron monitor, API balance tracking with dual-currency display and cumulative usage tracking. Uses a Python HTTP server that proxies Hermes CLI commands to JSON endpoints."
version: 1.0.0
author: Agent
platforms: [windows]
metadata:
  hermes:
    tags: [hermes, dashboard, kanban, web-ui, balance, monitoring, deepseek]
    related_skills: [hermes-cost-optimization, cron-scheduling]
    created_by: agent
---

# Hermes Custom Web Dashboard

A lightweight auxiliary web dashboard that extends Hermes Agent with:

- **Kanban board** — visual task board from `hermes kanban list --json`
- **Cron job monitor** — scheduled jobs overview from `hermes cron list`
- **API balance tracker** — live DeepSeek balance in USD + JPY with cumulative usage tracking

## Architecture

```
kanban_server.py          ← Python http.server (port 8322)
  ├── /kanban             → serves kanban.html (full UI)
  ├── /kanban.json        → `hermes kanban list --json --archived`
  ├── /cron.json          → parses `hermes cron list` output to JSON
  ├── /balance.json       → DeepSeek API balance + FX rate + cumulative usage
  └── balance_state.json  ← auto-created tracking file (persists across restarts)
```

## Setup

1. Create a project directory: `~/projects/hermes-kanban/`
2. Write `kanban_server.py` — a lightweight Python HTTP server (BaseHTTPRequestHandler)
3. Write `kanban.html` — the web UI frontend
4. Configure the DeepSeek API key in `~/.hermes/.env`: `DEEPSEEK_API_KEY=sk-...`
5. Start: `python kanban_server.py`
6. Open in browser: `http://<host>:8322/kanban`

## Port Management

Port 8321 is commonly used by `hermes dashboard` (uvicorn gateway with auth). If port conflicts occur:

- **Option A:** Kill the Hermes dashboard and reassign 8321: `kill <dashboard_pid>`
- **Option B:** Run custom dashboard on a different port (e.g., 8322) — update `PORT` in kanban_server.py

## Balance Tracking (Cumulative Usage from Deltas)

DeepSeek's API only provides a `/user/balance` endpoint (current remaining balance). There is no usage history API. Cumulative usage is tracked by:

1. A `balance_state.json` file that stores `{last_topped_up, last_granted, total_used}`
2. On each balance check, compare current `topped_up_balance` and `granted_balance` against the stored values
3. Any decrease is accumulated into `total_used`

**Behavior:**
- First run: establishes baseline, shows 0 used
- Subsequent checks: detects drops in topped_up/granted and accumulates
- Survives restarts (persisted in JSON file)
- Detects top-ups correctly (increases don't count as "used")

### DeepSeek Balance API

```
GET https://api.deepseek.com/user/balance
Authorization: Bearer sk-<key>

Response:
{
  "is_available": true,
  "balance_infos": [{
    "currency": "USD",
    "total_balance": "2.34",
    "granted_balance": "0.00",
    "topped_up_balance": "2.34"
  }]
}
```

Key behavior: all balance fields (`total_balance`, `topped_up_balance`, `granted_balance`) represent **remaining** amounts, not historical totals.

## FX Rate (Live USD → JPY)

Fetch live USD/JPY rate from the free exchangerate API:

```
GET https://open.er-api.com/v6/latest/USD
```

Response includes `rates.JPY`. No API key required. Rate is polled fresh each balance check.

## HTML Frontend Patterns

- Single-file HTML with inline CSS + JS (no dependencies)
- `fetch()` every 5 seconds auto-refreshing the board
- `/kanban.json`, `/cron.json`, `/balance.json` endpoints polled concurrently
- Balance display in top-right corner as a compact badge
- Tasks colored by status (running=yellow, done=green, blocked=red, etc.)
- Cron jobs colored by last status (ok=green, fail=red, disabled=gray)
- Collapsible sections for Tasks and Cron Jobs

## Key Endpoints in kanban_server.py

```python
if path == '/kanban.json':
    # Returns JSON from `hermes kanban list --json --archived`
elif path == '/cron.json':
    # Parses `hermes cron list` table output to structured JSON
elif path == '/balance.json':
    # Fetches DeepSeek balance, FX rate, computes used amount
elif path == '/' or path == '/kanban':
    # Serves kanban.html
```

## Pitfalls

- **Port conflicts:** `hermes dashboard` often takes port 8321. Always check with `netstat -ano | grep :8321` or `ps aux | grep 8321`. The server silently fails to bind if port is taken.
- **env_path escaping on Windows:** The `.env` path in kanban_server.py uses `r'C:\Users\...'` raw string format. Triple-check backslash escaping when editing — doubled backslashes (`C:\\Users`) cause path lookup failures.
- **No usage API:** DeepSeek has `/user/balance` but **no** `/user/usage` or `/billing/usage` endpoint (returns 404). The balance-delta method is the only viable approach for tracking consumption.
- **FX API reliability:** `open.er-api.com` is free but can be slow or rate-limited. The server silently falls back to `jpy_rate=0` on failure — the UI then shows ¥0.
- **State file initial baseline:** Starting fresh (`rm balance_state.json`) resets the usage counter to 0. The first fetch establishes the baseline; actual usage tracking begins from the second fetch onward.
- **User-agent header:** Some free API endpoints (including open.er-api.com) may reject requests without a `User-Agent` header. Always set one in `urllib.request.Request()`.
- **Port change requires HTML update:** The HTML uses relative paths (`/kanban.json`) so it works on any port automatically — no hardcoded URLs in the frontend.
