---
name: cron-scheduling
description: "Create and manage cron jobs — one-shot, recurring, delivery targets, timezone handling."
version: 1.0.0
author: Hermes Agent (learned from Den's correction)
metadata:
  triggers:
    - user asks to schedule, remind, alert, or notify
    - user asks for recurring delivery (daily briefing, hourly check, etc.)
    - user wants a delayed one-shot message
    - user asks to hear, listen to, or voice-deliver a cron job's output
    - user mentions sending cron job results as audio or voice
---

# Cron Scheduling

Skill for creating reliable cron jobs. Covers one-shot and recurring patterns, timezone handling, delivery targets, and common pitfalls.

## Trigger Conditions

Load this skill when the user asks you to:
- Set up a reminder, alert, or notification
- Schedule a recurring task (daily briefing, hourly check, etc.)
- Send a message after a delay
- Create, edit, or manage cron jobs

## Workflow

### 1. Determine the user's timezone

**Critical first step.** Cron timestamps default to UTC if you don't use the user's timezone. Check:

1. **User profile in memory** — look for timezone or location entries
2. **`prompt_prefix` in config** — may contain location hints (city/country)
3. **Ask** — if uncertain, ask the user

For Den (Kawagoe, Saitama, Japan): **JST (UTC+9)**.

### 2. Get the current time in the user's timezone

Use `terminal` to get current JST time for ISO timestamps:

```bash
# On Linux/Mac
TZ='Asia/Tokyo' date '+%Y-%m-%dT%H:%M:%S'

# On Windows (git-bash) — TZ env var may not work; use Python instead
python -c "from datetime import datetime, timezone, timedelta; jst = datetime.now(timezone.utc) + timedelta(hours=9); print(jst.strftime('%Y-%m-%dT%H:%M:%S'))"
```

For other timezones, replace `hours=9` with the UTC offset (e.g. `-5` for EST, `+1` for CET, `+8` for CST/SGT).

### 3. Calculate the fire time

Add the delay to the current JST time to produce the ISO timestamp.

### 4. Create the cron job

Via the `cronjob` tool (agent-side) or `hermes cron create` (CLI).

**One-shot (ISO timestamp):**
```python
# ISO timestamp MUST include timezone offset (e.g., +09:00)
cronjob(action='create', schedule='2026-07-03T22:06:55+09:00', prompt='...', name='My Job')
```

**Recurring (duration/expression):**
```python
cronjob(action='create', schedule='30m', prompt='...')     # every 30 min
cronjob(action='create', schedule='every monday 9am', ...) # weekly
cronjob(action='create', schedule='0 9 * * *', ...)        # daily at 9am
```

### 5. Set delivery target and verify the platform is reachable

- Omit `deliver` → auto-delivers to the current chat (Telegram DM, etc.)
- `deliver='origin'` → same as omit
- **Verify the platform is actually configured** before scheduling delivery. Use `hermes send --list <platform>` (e.g. `hermes send --list telegram`) to check reachable users/chats.
- **Telegram username pitfall**: sending to `telegram:@someuser` fails with "Chat not found" if that user has never messaged the bot. They must send at least `/start` to the bot first.
- **Discord channel delivery**: use `deliver="discord:<channel_id>"` where `<channel_id>` is the numeric Discord channel ID (from the channel mention like `<#1523359256345182269>`). Channel names like `discord:#ai-prompts` also work. Works for any channel the bot has access to.
- If the user asks for a platform that isn't configured or a user that's unreachable, tell them clearly and offer alternatives.

### 6. Optimize with `enabled_toolsets`

For cron jobs that only need a subset of tools, use `enabled_toolsets` to restrict which tools the job loads. This significantly reduces input token overhead:

```python
cronjob(
    action='create',
    name='Daily Web Curation',
    schedule='0 7 * * *',
    prompt='Search the web for X and report...',
    enabled_toolsets=['web', 'terminal']  # only loads web_search + terminal tools
)
```

Available toolset names: `web`, `terminal`, `file`, `delegation`, `code_exec`. Inspect your prompt to determine the minimal set needed. When omitted, all default tools are loaded.

### 7. Make cron jobs reply-able with `attach_to_session`

Set `attach_to_session=True` so the user can reply to the cron job's delivery in a thread, and the agent will have the original brief in context:

```python
cronjob(
    action='create',
    name='Daily Briefing',
    schedule='0 7 * * *',
    prompt='...',
    attach_to_session=True  # opens a dedicated thread on thread-capable platforms
)
```

Use this for conversational recurring jobs — daily briefings, reminders that kick off follow-up work. Omit for fire-and-forget alerts and watchdogs.

### 8. Clean up old test jobs

Remove one-shot test jobs after they fire so the job list stays clean:

```python
cronjob(action='remove', job_id='...')
```

## Schedule Formats

| Format | Example | Notes |
|--------|---------|-------|
| Duration | `"30m"`, `"2h"` | Minimum granularity: 1 minute |
| "Every" phrase | `"every monday 9am"` | Natural language |
| Cron expression | `"0 9 * * *"` | Standard 5-field cron |
| ISO timestamp | `"2026-07-04T09:00:00+09:00"` | One-shot, MUST include timezone offset |

## Reference Files

- `references/gmail-imap-cleanup.md` — Automated Gmail inbox management via IMAP: scan old unread emails, flag for review, protect important senders, delete after approval. Full script patterns included.
- `references/git-auto-backup.md` — Git auto-backup script pattern: commit all changes and push to GitHub on a daily schedule via no_agent cron job.
- `references/hermes-config-backup.md` — Extended backup that also preserves Hermes memories, skills, profiles, configs, and .env key documentation for full recovery after reformat.
- `references/kanban-phone-view.md` — Real-time kanban + cron dashboard accessible from the user's phone: combined web server, cron text-parse pattern, task lifecycle workflow.
- `references/daily-web-curation.md` — Reusable pattern for cron jobs that search multiple web sources, curate the best content, and deliver a formatted post to a channel (includes prompt anatomy, token optimization, and kanban integration).
- `references/htmlpreview-limitations.md` — htmlpreview constraints: inline script truncation (3,400 char limit), external JS MIME type issues, touch events in iframes, caching.
- `references/gmail-approval-flow.md` — Gmail inbox cleanup with human-in-the-loop approval: scan, flag, protect, restore, and the full approval workflow.
- `references/security-monitoring-pattern.md` — Two-phase security monitoring (learning → monitoring): behavioral baseline, SQLite database, private IP filtering, web dashboard with collapsible About section, Telegram alerting.

## Script-Based Jobs (no_agent mode)

For jobs that just run a script and deliver its output verbatim (no LLM reasoning needed), use no_agent=True with a script:

```python
cronjob(
    action='create',
    name='Gmail Inbox Scan',
    schedule='0 8 * * *',
    script='gmail_scan.py',       # relative to ~/.hermes/scripts/
    no_agent=True                  # skips LLM, delivers stdout verbatim
)
```

**Rules for script jobs:**
- Script path is **relative** to ~/.hermes/scripts/ — use just the filename, not an absolute path
- .sh / .bash → runs via bash; everything else → runs via Python
- **Non-empty stdout** → delivered verbatim to the user
- **Empty stdout** → silent (no notification). Good for watchdog scripts that only report problems
- **Non-zero exit / timeout** → sends an error alert
- prompt and skills are IGNORED when no_agent=True — all logic goes in the script
- No LLM tokens consumed, no agent loop

## Kanban Task Synchronization

**Rule: Every new project or user request gets a kanban task from the start.** Do not wait for the user to ask — create it when the project begins. The user expects to see everything reflected on the board at `http://<ip>:8321/kanban`.

### Workflow for ALL Projects (not just cron jobs)

1. **At project start:** `hermes kanban create "Descriptive Title" --body "Brief description of what's being built"`
   - Creates the task as `ready` — there is no `--initial-status` flag on `create`
   - After `create`, immediately promote or complete if already done: `hermes kanban complete <task_id>`
2. **When delivering results:** `hermes kanban complete <task_id>` — marks it `done`
   - There is no `start` or `running` subcommand; only `create`, `complete`, `edit`, `block`, `unblock`, `promote`, `archive`
3. **Do NOT archive** done tasks — the user wants full history visible on the board
4. **Give tasks descriptive titles** the user will recognize (e.g. "Animated Birthday Card for Angel" not "BD card")

### For Cron Jobs specifically

When a cron job has an associated kanban task, the task's status is **NOT** automatically updated when the cron job fires. Even if the job completes successfully (`last_status: ok`), the kanban task will remain "running" until explicitly marked done.

1. Create the kanban task before the cron job (via `hermes kanban create ...`)
2. After the cron job's **first successful run**, mark the kanban task done:
   ```bash
   hermes kanban complete <task_id>
   ```
3. For recurring cron jobs (daily, weekly), keep the kanban task visible — don't archive it. It serves as a record that the job exists and has run at least once.

### Finding the task ID
The task ID is visible in `/kanban.json` at `http://<ip>:8321/kanban.json`. Look for the `id` field matching the task title. Alternatively, list tasks via:
```bash
hermes kanban list --json --archived
```
Find the matching title and grab its `id`.

### Interactive reminder
When the user asks "is [cron job name] done?" and the cron job's last_status is "ok" but the kanban task still shows "running", proactively offer to fix it with `hermes kanban complete <task_id>`. This is a recurring point of confusion.

## Voice/TTS Delivery in Cron Jobs

Cron jobs can deliver voice messages via text-to-speech, but this requires explicit instructions in the prompt:

```python
cronjob(
    action='create',
    name='Voice Reminder',
    schedule='2026-07-07T01:00:00+09:00',
    prompt="Use text_to_speech to generate a voice message saying 'Time to sleep!' and include the MEDIA: path in your response."
)
```

**Limitations:**
- The cron agent must use the `text_to_speech` tool during its run — the prompt must tell it to do so
- Audio files are delivered as attachments (user taps play) — no autoplay on Discord/Telegram
- Keep TTS text under 200 characters for quick delivery
- Cron jobs with voice delivery still need the default toolset (not `enabled_toolsets`)
- Cannot combine with `no_agent=True` (no_agent skips the LLM entirely)

## On-Demand Voice Delivery of Cron Job Outputs

When a user asks you to send an existing cron job's output as voice (TTS), follow this pattern.

### Finding cron job output files

Cron job outputs are stored under `~/.hermes/cron/output/`:

- **no_agent script jobs**: output saved as `~/.hermes/cron/output/<job_id>/<date>.md` (a directory with dated files)
- **LLM-driven agent jobs**: output saved as `~/.hermes/cron/output/<job_id>_<timestamp>.txt` (a flat file)

### Step-by-step workflow

1. **List cron jobs** — `cronjob(action='list')` to see names, job IDs, and `last_run_at` timestamps
2. **Identify the job** — match the user's description against the `name` field
3. **Locate the output**:
   - For script jobs: `ls -lt ~/.hermes/cron/output/<job_id>/` → read the most recent `.md` file
   - For LLM jobs: `ls -lt ~/.hermes/cron/output/<job_id>*.txt` → read the most recent one
4. **Extract key facts for voice**:
   - Strip all URLs (user explicitly says "no need to mention urls")
   - Keep only the main data points, status summaries, and conclusions
   - Omit redundant headers, job metadata, and formatting
   - For rich content (e.g. curated prompts): condense to 1-2 sentences per item, keep names and summaries

### Voice conversion rules

```python
# Typical pattern:
text_to_speech(text="Concise summary of facts here")
```

- **Script-type jobs** (no_agent): usually brief output — extract the few numbers/statuses and convert
- **LLM-driven jobs** (AI Prompts, News Digest): richer content — condense each section to 1-2 sentences, strip source URLs, keep item titles and summaries
- **Keep TTS text under 3000 characters** to stay within provider limits (OpenAI 4096, others vary)
- **Do NOT mention URLs in the audio** — user's stated preference
- **Do include the cron job name and its recent run time** so the user knows which delivery they're hearing

### Common pitfalls

- **No output file found** — recent cron output may have been cleaned up. Re-run the job manually with `cronjob(action='run', job_id='...')` and wait for its result, then convert that to voice.
- **Trivial outputs** — some jobs produce "all clear, 0 new" status. If the output is essentially empty of substance, note it briefly rather than padding the audio.
- **Cancellation** — if the user says "Cancel that" after a voice delivery, don't dwell; move on to their next request.
- **Directory vs flat file** — no_agent script jobs use directories (`<job_id>/`), LLM agent jobs use flat files (`<job_id>_<timestamp>.txt`). Check both patterns.

## Pitfalls

- **UTC default traps you.** The cronjob tool accepts ISO timestamps with or without offset. If you pass a bare `2026-07-03T22:06:55` without `+09:00`, it's interpreted as UTC. Always include the timezone offset.
- **Duration formats (`30m`, `2h`) do NOT support seconds.** Minimum is 1 minute. For sub-minute delays, use an ISO timestamp.
- **Don't assume a platform is configured.** SMS, Signal, etc. need explicit setup. Use `hermes send --list <platform>` to verify reachable targets before scheduling delivery to a platform.
- **Telegram usernames require prior interaction.** You can't send to `telegram:@username` unless that user has messaged the bot at least once. The error is `Chat not found`. The only reliable way is the numeric chat_id (or the user messaging the bot first).
- **`hermes send --list telegram` shows the bot's known users** — only those who've interacted with it appear there.
- **Test jobs accumulate.** Remove them after they fire so the list doesn't fill with stale entries.
- **The `hermes-agent` skill is bundled/protected.** Do not attempt to edit it. Cron-related docs live in this skill instead.
- **One-shots with ISO timestamps in the past** — if the timestamp has already passed by the time the scheduler processes it, the job may be silently skipped. Add a 5-10 second buffer.
- **Windows git-bash: `TZ='Asia/Tokyo' date` may not work** — the TZ env var isn't always honoured by git-bash's date. Always prefer the Python one-liner on Windows.
