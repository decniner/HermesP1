---
name: requirements-gathering
description: "Use when the user requests a new project, feature, tool, or automation — stop, ask clarifying questions until fully understood, then proceed."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [requirements, gathering, project-intake, communication, clarification]
    related_skills: [plan, delegated-qa-workflow]
---

# Requirements Gathering

**Always ask before you build.** Jumping into code or solutions without understanding the full scope is the #1 source of rework. This skill governs how you handle ANY new request — project, script, automation, analysis, or tool.

**User feedback received:** Den explicitly corrected me for NOT asking clarifying questions before starting a Gmail automation project. This is a permanent behavioral rule, not a one-off preference.

## When to Use

- User asks you to build something (app, script, automation, tool)
- User asks you to analyze something with a deliverable
- User asks you to set up a new system or integration
- User says "I want to do X" without specifying how

## The Checklist — Ask These Before Building

Do not skip this. Even if the task seems obvious, ask at least questions 1-5 before touching any code or config.

### 0. CRITICAL — Ask One Topic at a Time

**Do NOT ask all questions at once.** Ask ONE question, wait for the answer, then ask the next. This is a hard behavioral rule — not a suggestion.

**Why:** Asking everything at once overwhelms the user and leads to skipped or brief answers. Sequential questioning builds understanding step by step and lets the user's answers shape the next question.

**Pattern:** *"Topic 1: [question]" → user answers → "Topic 2: [next question]" → user answers → ...*

**Stop condition:** Keep asking until you can describe the full project back to the user in your own words and they agree. Do not proceed to building until the user confirms the written vision.

**Session correction (2026-07-07):** User explicitly stated &quot;Before proposing any plan or code, ask me questions about the project—keep asking them, one topic at a time, until you fully understand.&quot; Failure to follow this will result in immediate user correction.

**Multiple corrections this session (2026-07-07):** The user corrected me TWICE for not asking questions before projects — once for the Gmail automation and once for the Windows 95 interface. The second time they said &quot;Remember you need to ask me questions before building any project.&quot; Then for the Hermes Book project, they laid out an explicit 3-phase process: ask questions one topic at a time → write vision document → only then build. This is the user&#39;s single most-frequent correction. Never rush past this step, even when the task seems obvious.

### 1. What's the real problem?
Ask: *"What's the pain point you're trying to solve?"* or *"Why do you want this?"*
The stated request is often a symptom, not the root need.

### 2. Who is this for?
- Personal use only?
- Shared with others?
- Public/team tool?

### 3. What are the must-haves vs nice-to-haves?
- "What's absolutely necessary for this to be useful?"
- "What can we skip for now?"

### 4. What are the constraints?
- Tech stack preferences (Python vs JS, etc.)
- Platform (Windows, web, mobile)
- Budget or resource limits
- Timeline

### 5. How should I deliver the result?
- Files on the PC?
- GitHub repo?
- Telegram message?
- Automated (cron job)?
- Where specifically should files go?

### 6. Security & safety
- "Are there any files, folders, or services I should NEVER touch?"
- "Any data that must be protected?"

### 7. Approval workflow
- "Should I show you before I execute?"
- "Do you want to review intermediate results?"
- "Full auto or step-by-step approval?"

### 8. Write the Project Vision Document

After gathering all answers and confirming understanding, write a complete project vision before building anything. Format as a structured document the user can review and approve:

- **Overview:** Brief description of what's being built
- **Features:** Bullet list with details
- **Architecture:** Components, files, data flow
- **User Interface:** What the user sees and interacts with
- **Delivery:** How delivered (file path, GitHub, Telegram, cron)

**Process:** Ask Qs one topic at a time → Write vision → Present for user confirmation ("Does this match?") → Only build after confirmation → Then create kanban task.

**Session signal (2026-07-07):** User required: "Once you have a complete picture, write down the full project vision in a clear, AI-readable format." Do not skip this step.

## Kanban Task Creation — At Project Start

Immediately after gathering requirements and before doing any work, create a kanban task:

```bash
hermes kanban create "Task title" --body "Description of what needs to be done"
```

**NOTE:** `hermes kanban create` does NOT accept `--initial-status`. Tasks are always created as `ready`. This is fine — the task appears on the kanban dashboard immediately. The `ready` status still makes it visible in the color-coded kanban view.

When the task is complete, mark it:

```bash
hermes kanban complete <task_id>
```

**Rules:**
- Create the task BEFORE starting work, not after the user asks why nothing is tracked
- The `ready` status is fine — the task is visible on the dashboard. The user can see what's being worked on
- Mark done when finished — **never archive completed tasks.** Archived tasks disappear from the default view and the user can't see what was already done
- If no task was created for a request, the user sees an empty board and will ask "why isn't anything showing"
- This applies to ALL project types: games, automation scripts, analysis, email scans, MQL bots

### Kanban Dashboard Design

When setting up the `http://<pc-ip>:8321/kanban` dashboard (create once per machine, not per project):

- **Collapsible sections** — Tasks and Cron Jobs each have clickable headers. Tap to collapse/expand. Saves mobile screen space.
- **All tasks visible** — Done/archived tasks stay on the board. **Never archive completed tasks** — if archived, they disappear from the default view and the user will ask what happened to them.
- **Cron jobs alongside tasks** — Show schedule, next run, last run, and green/red status for each cron job in the same view.
- **Color-coded by status** — Running=yellow, Done=green, Ready=cyan, Blocked=red, Archived=grey. Both border and status text are colored.
- **Auto-refresh** — Every 5 seconds. No manual refresh needed.
- **Access** — PC local IP on port 8321. Phone must be on same Wi-Fi.
- **Watchdog (optional)** — A cron job can check every 5 min if the server is alive and restart it. **If the user says "stop" or "remove" the watchdog**, remove the cron job immediately. Do not re-create it unless asked.

When modifying the server or rendering, preserve these preferences.

## Delivery Location Preference

Den expects files delivered to BOTH locations (when applicable):
1. **Local working directory** — MetaTrader Experts/DEN_EA (for MQL bots) or projects folder (for code)
2. **GitHub** — Push to the appropriate repo (HermesP1 or MQLNewStrat2)

For MQL5/EA files specifically: copy to `DEN_EA` MetaTrader folder AND push to GitHub. Never just one.

## QA Requirement

All code/game deliverables must go through a QA subagent (`delegated-qa-workflow`) before delivery. Shipping untested code results in immediate user reports of broken functionality. QA is not optional.

## Critical Exception — When NOT to Ask

There is EXACTLY ONE case where you do NOT ask questions: **the user hands you a complete, step-by-step, file-by-file specification.**

Signal words: the message contains exact file paths, exact file contents, exact CLI commands in sequence, a structured blueprint (JSON/YAML spec), or explicit instructions like "do not deviate," "follow this blueprint exactly," "do not improvise."

In this case:
- **Execute verbatim.** Follow every instruction to the letter.
- **Do NOT ask clarifying questions.** The spec IS the requirements.
- **Do NOT substitute dependencies or approaches.** If they say `pandas-ta`, try it first; only substitute if it fails and report why.
- **Do NOT "improve" the spec.** Build what they asked for, not what you think is better.
- Report blockers honestly, but ask permission before changing anything.

**Why this rule exists:** This user has explicitly stated both rules at different times: "always ask before building" AND "when I give exact instructions, follow them precisely without deviation." The difference is whether the spec is open-ended (ask) vs fully specified (execute).

### Nuance — Partial Specs
If the user gives some specifics but leaves gaps:
- Execute the specified parts **exactly**
- Ask about ONLY the gaps, one at a time
- Do NOT re-open already-specified decisions

## Behavioral Enforcement

- **Do NOT start coding until you have clear answers to questions 1-5**
- **Do NOT say "I'll build X for you" and then write code in the same response** — first ask, get answers, THEN act
- **Create the kanban task BEFORE writing code**
- **If the user says "just do it" or seems impatient**, ask ONE clarifying question and then proceed — but never zero
- **Session correction signal (2026-07-07):** User explicitly said "Remember that when I start this new project, you will always ask me until you fully understood what I wanted to do. You never did that." — This means any future project request must be met with questions before action, EVEN IF the task seems obvious or similar to previous work. The user WILL call you out if you skip this step.

**Multiple corrections this session (2026-07-07):** The user corrected me TWICE for not asking questions before projects — once for the Gmail automation and once for the Windows 95 interface. The second time they said "Remember you need to ask me questions before building any project." Then for the Hermes Book project, they laid out an explicit 3-phase process: ask questions one topic at a time → write vision document → only then build. This is the user's single most frequent correction. Never rush past this step, even when the task seems obvious.

- **If the user corrects you for not asking** (as happened this session), that is a first-class signal to embed this behavior permanently — do NOT let it happen again in the same project or the same session

## During Execution — Progress Reporting

Once requirements are gathered and work begins, **show percentage-based progress** for any task taking over ~1 minute:

### Multi-step tasks (during chat)
- Break work into steps using the `todo` tool
- Report progress after each step completes: `🔨 3/6 done (50%) — Building UI ✅ → Integrating API 🔄 → Testing ⏳`
- The step count acts as a natural percentage

### Background processes
- Poll periodically with `process(action="poll")` and relay progress from the output
- If the process shows build steps, download %, or other measurable progress, report it: `📦 Build: compiling (60%)... linking (85%)...`
- If no % is available from the process output, report the latest output line so Den knows it's still running

### One-shot / scheduled tasks (cron jobs)
- These have no "in progress" state — they fire once at the scheduled time
- No % to report here; just deliver the result when it fires
- For visibility, offer to create a kanban card or use `cronjob list` on demand

## Reference Files

The `references/` directory under this skill can hold session-specific requirement-gathering transcripts for complex projects.

- `references/github-secret-audit.md` — Post-hoc credential leak detection and fix
- `references/visual-clone-from-reference.md` — Building a visual clone from a reference image
- `references/security-monitoring-agent.md` — Personal PC security monitoring agent with learning phase, dashboard, and Telegram alerting
- `references/structured-project-kickoff.md` — Three-phase project kickoff (discovery → vision document → build) as used for the Hermes Book. Capture of the exact process the user defined.
- `references/python-smtp-email.md` — Sending emails via Python smtplib when Himalaya CLI is not installed (Gmail app password flow, attachment support, pitfall notes).
## Common Pitfalls

1. **Assuming you understand the request** — You don't. Confirmation bias makes you fill in gaps with wrong assumptions.
2. **"The request is simple enough"** — Simple requests hide the most assumptions. Ask anyway.
3. **Asking once and accepting "okay"** — Push until you can describe the project back to the user in your own words and they agree.
4. **Asking but then ignoring the answers** — If the user says "this needs to go in folder X," remember that when you deliver.
5. **Kanban watchdog is a convenience, not a requirement** — If you add a cron job to auto-restart the kanban server and the user says "stop reminder" or "remove it", do so immediately. Do not re-create it or argue. The user knows their own tolerance for background noise.
6. **Creating a kanban task after the user asks about status** — If they say "I don't see my task on the board", the mistake already happened. Create the task at project START, not when the board looks empty.
7. **Archiving instead of completing** — Archived tasks vanish from the default kanban view. Always use `hermes kanban complete <id>`, never `hermes kanban archive <id>`. The user wants full history visible.
