# Hermes Cost Optimization — Quick Commands

## Simple Key/Value Changes

```bash
hermes config set agent.max_turns 30
hermes config set web.search_backend ddgs
hermes config set compression.threshold 0.40
hermes config set compression.target_ratio 0.15
```

## Install DuckDuckGo Search Backend

```bash
pip install ddgs
```

## Verify Current Config

```bash
hermes config | head -20
grep -n "max_turns\|search_backend\|platform_toolsets" "$(hermes config path)"
```

## Common Platform Toolset Keys to Comment Out

When the user asks to reduce tokens, these are the 5 heaviest unused platform entries:

| Platform | Toolset | Safe to remove if... |
|----------|---------|---------------------|
| discord | hermes-discord | No Discord gateway |
| whatsapp | hermes-whatsapp | No WhatsApp gateway |
| slack | hermes-slack | No Slack gateway |
| teams | hermes-teams | No Teams gateway |
| google_chat | hermes-google_chat | No Google Chat gateway |

## Workflow for Complex YAML Edits

When `hermes config set` can't handle the change (e.g. commenting out platform_toolsets entries):

```python
# The working pattern: write from execute_code, run from terminal
from hermes_tools import terminal, write_file

# Step 1: Read current config via terminal (cat works on Windows)
result = terminal('cat "C:/Users/decni/AppData/Local/hermes/config.yaml"')
content = result["output"]

# Step 2: Apply string-level transformations
lines = content.split('\n')
new_lines = []
for line in lines:
    if line.strip() == "discord:":
        new_lines.append(f"# {line}")
    else:
        new_lines.append(line)

# Step 3: Write via execute_code's native open() (writes to real filesystem for Windows paths)
path = "C:/Users/decni/AppData/Local/hermes/config.yaml"
with open(path, 'w') as f:
    f.write('\n'.join(new_lines))

# Step 4: Verify
result = terminal(f'grep -n "discord" "{path}"')
print(result["output"])
```

## Web Backend Resolution Order

Hermes checks backends in this priority:
1. `web.search_backend` (explicit per-capability override)
2. `web.backend` (shared fallback)
3. Auto-detect from env vars: tavily → searxng → brave-free → **ddgs** (free, no key)

`ddgs` is the only truly free tier with no API key requirement.
