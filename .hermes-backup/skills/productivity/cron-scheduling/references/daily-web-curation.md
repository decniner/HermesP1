# Daily Web Curation Cron Pattern

Reusable approach for cron jobs that search multiple web sources, curate the best content, and deliver a formatted post to a channel.

## Use Case

Any "morning digest" or "daily roundup" job that:
- Searches several community sources (Reddit, HN, GitHub, X/Twitter, blogs)
- Filters/ranks results against a criteria
- Formats the top N items with summaries + actual content
- Delivers to a specific chat channel at a set time

## Reference Example: Daily AI Prompts Curation

**Job parameters used:**
```python
cronjob(
    action='create',
    name='Daily AI Prompts Curation',
    schedule='0 7 * * *',                    # 7 AM JST
    deliver='discord:1523359256345182269',   # Specific Discord channel
    attach_to_session=True,                   # Reply-able thread
    enabled_toolsets=['web', 'terminal'],     # Minimal toolset
    prompt='''...'''                          # Full curation prompt
)
```

## Anatomy of the Curation Prompt

The prompt should have these sections:

### 1. Task Definition
Clear statement of what to curate and the quality bar.

### 2. Source List
Explicit list of ALL places to search — enforce searching every source:
- Reddit subreddits
- Hacker News
- X/Twitter queries
- GitHub repos/gists/discussions
- Any other relevant forums

### 3. Filter Criteria
What qualifies for inclusion (and what does NOT). Be specific about the scope.

### 4. Output Format Template
Give a complete example of the expected output format with markdown. Include:
- Header with emoji + date
- Per-item structure: name, summary, full content in code block, source URL
- Footer line
- **Fallback instruction**: what to do if fewer items than target are found (include real finds honestly, no fabrication)

### 5. Guardrails
- "Do NOT fabricate prompts/content — every item must be sourced from a real post you extracted"
- "Use web_search to find, then web_extract to read the actual content"

## Token Optimization

- `enabled_toolsets=['web', 'terminal']` cuts ~30K+ tokens of unused tool definitions
- `attach_to_session=True` lets the user reply in-thread without re-explaining
- No skills needed for the cron job itself — the prompt is self-contained

## Kanban Integration

Before setting up the cron, create a kanban task via CLI:
```bash
hermes kanban create "Daily AI Prompts Curation" --body "Full task description..." --priority 1
```

**Note:** The kanban web dashboard at `<ip>:8321/kanban` is **read-only** (GET-only, no POST). Always use the CLI (`hermes kanban create`) to add tasks, not the browser UI.

### After the first successful job run

**CRITICAL:** The cron job's successful execution (`last_status: ok`) does NOT automatically update the kanban task. You must explicitly mark it done after the first successful run:

```bash
# Find the task ID
hermes kanban list --json --archived

# Mark it done
hermes kanban complete t_<task_id>
```

If you forget this step, the kanban board will perpetually show the curation job as "running" even though it completed successfully — the user will notice this mismatch.

For recurring daily jobs, mark done once after the first run. Do NOT archive — keep the task visible as a record.
