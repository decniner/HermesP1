# Real-Time Kanban + Cron Dashboard for Phone Viewing

Pattern for setting up a live kanban board **combined with cron job status** visible on the user's phone. Users can track what tasks are running, ready, or done AND see when their cron jobs next fire — all in one auto-refreshing page.

## Architecture

```
kanban_server.py (Python HTTP server, runs as background process)
  ├── GET /kanban        → serves kanban.html (combined dashboard)
  ├── GET /kanban.json   → calls `hermes kanban list --json --archived`
  └── GET /cron.json     → calls `hermes cron list` + parses text output → JSON

kanban.html (JavaScript, auto-refreshes every 5s)
  ├── 📌 Tasks section    → fetches /kanban.json → color-coded by status
  └── ⏰ Cron Jobs section → fetches /cron.json → schedule + last/next run + status

cron job (daily 9am JST): kanban_report.py → delivers text summary to Telegram
```

## Cron Parser (Text Output → JSON)

`hermes cron list` outputs plain text with no `--json` flag. Parse it with this pattern:

```python
def _parse_cron(self, raw):
    jobs = []
    lines = raw.strip().split('\\n')
    current = None
    for line in lines:
        l = line.strip()
        if not l or l.startswith('┌') or l.startswith('└') or l.startswith('│'):
            continue
        # Detect job ID line: "  290ba24346ca [active]"
        if l[0].isalnum() and '[' in l and ']' in l:
            if current: jobs.append(current)
            current = {'id': l.split()[0], 'enabled': 'active' in l}
            continue
        if current is None: continue
        if 'Name:' in l: current['name'] = l.split('Name:')[1].strip()
        elif 'Schedule:' in l: current['schedule'] = l.split('Schedule:')[1].strip()
        elif 'Next run:' in l: current['next_run_at'] = l.split('Next run:')[1].strip()
        elif 'Last run:' in l:
            parts = l.split('Last run:')[1].strip()
            if 'never' in parts.lower():
                current['last_run_at'] = None; current['last_status'] = None
            else:
                for s in ['ok', 'fail']:
                    if parts.endswith('  '+s):
                        current['last_run_at'] = parts[:-(len(s)+2)].strip()
                        current['last_status'] = s; break
    if current: jobs.append(current)
    return json.dumps(jobs, ensure_ascii=False)
```

**Parsing pitfalls:**
- `l.startswith('  ')` doesn't work on stripped lines — check `l[0].isalnum()` instead
- Initialize `current = None`, not `current = {}` — `{}` is falsy and skips the first Name line
- `if current is None: continue` not `if not current:` — `{}` is falsy too
- `if current: jobs.append(current)` at end — `None` is falsy so skipped correctly
- Trailing "ok" on last_run: check `parts.endswith('  ok')` (two spaces before status word)

## Combined Dashboard HTML

Two sections, auto-refreshing every 5 seconds:

```html
<h1>📋 Hermes Dashboard</h1>
<h2>📌 Tasks</h2>
<div id="board"></div>
<h2>⏰ Cron Jobs</h2>
<div id="cron"></div>
```

JavaScript fetches both endpoints:

```javascript
async function loadBoard() {
    // Load tasks
    const r = await fetch('/kanban.json?t=' + Date.now());
    const data = await r.json();
    const tasks = Array.isArray(data) ? data : (data.tasks || []);
    tasks.forEach(t => {
        // Render with: .task + .{status} classes for color coding
        // Show: id, title, body excerpt, status, assignee
    });

    // Load cron jobs
    const r2 = await fetch('/cron.json?t=' + Date.now());
    const jobs2 = Array.isArray(await r2.json()) ? ... : [];
    jobs2.forEach(j => {
        // Show: name, schedule, next_run_at, last_run_at, status
        // CSS class: .job + .ok/.fail/.disabled
        const cls = j.enabled ? (j.last_status === 'fail' ? 'fail' : 'ok') : 'disabled';
    });
}
```

### Task Status Colors
```css
.running { border-color: #ff0; background: #1a1a00; }  /* Yellow */
.done    { border-color: #0f0; background: #001a00; opacity: 0.7; }  /* Green */
.archived{ border-color: #555; background: #0a0a0a; opacity: 0.35; }  /* Dim */
.ready   { border-color: #0ff; background: #001a1a; }
.blocked { border-color: #f44; background: #1a0000; }
.todo    { border-color: #55f; background: #00001a; }
```

### Cron Job Status Colors
```css
.job.ok  { border-color: #0f0; }  /* Green border: last run succeeded */
.job.fail{ border-color: #f44; }  /* Red border: last run failed */
.job.disabled { border-color: #444; opacity: 0.4; }  /* Dim: disabled */
```

### Cron Job Display Format
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Daily News Digest
⏰ 0 7 * * * | Next: 2026/7/6 7:00:00
🔄 Last: 2026/7/5 7:09:40
🟢 active
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## User Workflow

1. User opens **http://PC_IP:8321/kanban** on phone (same Wi-Fi required)
2. Board shows **tasks** (color-coded by status) + **cron jobs** (schedule + next/last run + status)
Both sections auto-refresh every 5 seconds.
4. User can also ask "tasks" or "kanban" in chat — agent runs `hermes kanban list`

## Collapsible Sections

User prefers **collapsible sections** so they can focus on Tasks OR Cron Jobs without scrolling. Implement with:

```css
h2 { cursor: pointer; user-select: none; }
.section { overflow: hidden; transition: max-height 0.3s ease; }
.section.collapsed { max-height: 0 !important; }
```

```html
<h2 onclick="toggle('taskSec')" data-icon="📌"> Tasks</h2>
<div id="taskSec" class="section"><div id="board"></div></div>
<h2 onclick="toggle('cronSec')" data-icon="⏰"> Cron Jobs</h2>
<div id="cronSec" class="section"><div id="cron"></div></div>
```

```javascript
function toggle(id) {
    document.getElementById(id).classList.toggle('collapsed');
}
```

The Dashboard title is `📋 Hermes Dashboard` (not "Kanban Board") to reflect both sections.
## Task Lifecycle for the Agent

For every user request, the agent should:
1. Create: `hermes kanban create "Task title" --body "What to do"` → creates as `ready`
2. When starting work, mark as `running` (set `--initial-status running`)
3. Mark `done` when finished (`hermes kanban complete <task_id>`)
4. **Do NOT archive** done tasks — user wants to see full history on the board
5. Give tasks descriptive titles the user will recognize

### Cron Job Kanban Tasks (Critical Gap)

When you create a kanban task for a **cron job** (recurring automation like daily news, weekly backup), the task lifecycle is different:

1. Create the task → status: `ready`
2. After the cron job successfully runs (at least once) → mark done
3. **The cron job does NOT auto-update the kanban task.** A cron job can have `last_status: ok` but the kanban task still shows "running" — they are completely independent systems.
4. The user will notice if a cron job's kanban task stays "running" indefinitely. When they ask "is [job name] done?", check BOTH the cron job's last_status AND the kanban task's status. If they mismatch, offer to fix.

Finding the task ID to complete:
```bash
hermes kanban list --json --archived
# Look for the matching title, grab the id field
hermes kanban complete t_<task_id>
```

## Starting and Restarting the Server

```bash
# Start (background)
python C:\path\to\kanban_server.py &

# Kill all Python servers (to restart with new code)
taskkill /F /IM python.exe

# Verify it's running
curl http://localhost:8321/kanban.json
curl http://localhost:8321/cron.json
```

**CRITICAL:** Old server processes linger with old code. Always kill ALL python.exe before restarting, not just the one PID you think is the server.

## Pitfalls

- **Old server process lingers** — restarting requires `taskkill /F /IM python.exe` first, then start fresh
- **`--archived` flag is required** — without it, `hermes kanban list` only shows non-archived tasks. Board looks empty.
- **Same Wi-Fi required** — server binds `0.0.0.0` but phone must reach PC's LAN IP (192.168.x.x)
- **Server doesn't survive PC restart** — process dies on reboot
- **Cron list has no --json flag** — must parse text output manually with the pattern above
- **Empty cron JSON after code change** — old server is still running with old code. Kill all python.exe and restart.
- **Cron list output format may change** — the parser is format-sensitive. If `hermes cron list` output format changes, update the parser.
