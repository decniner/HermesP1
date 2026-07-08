# OpenRouter Free-Tier Proxy Setup — Session Proven (July 2026)

Exact working setup on Windows 10 (Git Bash). Routes Claude Code v2.1.203 through OpenRouter free tier via `fuergaosi233/claude-code-proxy`.

## Key Finding: Model Names Change

Free model availability on OpenRouter is volatile. The `qwen/qwen-2.5-coder-32b-instruct:free` model that worked in June 2025 is now 404. **Always verify** before configuring:

```bash
curl -s "https://openrouter.ai/api/v1/models" \
  -H "Authorization: Bearer $OPENAI_API_KEY" | \
  python3 -c "
import json,sys
data=json.load(sys.stdin)
for m in data.get('data',[]):
    p=m.get('pricing',{})
    prom=float(p.get('prompt',1) or 1)
    comp=float(p.get('completion',1) or 1)
    if prom==0 and comp==0: print(m['id'])
"
```

## Working .env (July 2026)

```ini
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
OPENAI_API_KEY="sk-or-v1-..."
BIG_MODEL="openrouter/free"
MIDDLE_MODEL="openrouter/free"
SMALL_MODEL="openrouter/free"
HOST="127.0.0.1"
PORT=8082
LOG_LEVEL="INFO"
```

`openrouter/free` auto-routes to the least-congested free backend. Avoids 429 rate limits better than specific model names.

## Critical: ANTHROPIC_MODEL Spoofing

Claude Code v2.1 validates model names client-side. You MUST set this env var:

```bash
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
```

Without it, Claude Code defaults to `claude-opus-4-8`, fails internal validation, and never reaches the proxy.

## Verified Test

```bash
# Start proxy
cd ~/projects/claude-code-proxy && python start_proxy.py

# Test basic connectivity
export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
export ANTHROPIC_API_KEY="bypassed-via-local-proxy"
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
export ENABLE_TOOL_SEARCH=true

claude -p "reply just: WORKS" --max-turns 1 --allowedTools "Read"
# → "WORKS"
```

## Limit: Complex Tasks Time Out

Generating large outputs (full HTML files, long refactors) on free tier consistently times out. The proxy's 90s request timeout combined with OpenRouter's rate limiting makes multi-turn code generation unreliable. Split tasks into focused sub-tasks with generous Hermes timeouts (300s+).
