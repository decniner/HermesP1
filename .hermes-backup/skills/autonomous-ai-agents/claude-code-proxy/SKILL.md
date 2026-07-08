---
name: claude-code-proxy
description: "Setup Claude Code with OpenRouter free tier via local translation proxy"
version: 1.0.0
platforms: [linux, macos, windows]
---

# Claude Code → OpenRouter Proxy Setup

Run Claude Code through OpenRouter's free tier using a local Python proxy that translates Anthropic Messages API ↔ OpenAI Chat Completions format, with model name spoofing to bypass Claude Code v2.1+'s client-side model validation.

## When to use

Use when the user asks to:
- Run Claude Code without an Anthropic subscription
- Route Claude Code through OpenRouter, Ollama, or any OpenAI-compatible endpoint
- Use free/open models with Claude Code's CLI
- "Free claude" or "claude with openrouter"
- Set up a proxy for Claude Code to use alternative providers
- Model spoofing to bypass Claude Code's client-side validation

## Architecture

```
Claude Code CLI  ──ANTHROPIC_BASE_URL──>  claude-code-proxy (FastAPI :8082)
    │                                       │
    │ Anthropic Messages API                │ OpenAI Chat Completions format
    │ (POST /v1/messages)                   │ (POST /v1/chat/completions)
    │ model: claude-3-5-sonnet-20241022     │ model: qwen/qwen3-coder:free
    ▼                                       ▼
  [model validation passes]           OpenRouter API
  (client-side, spoofed)            → free tier models
```

## Setup

### 1. Clone & Install

```bash
git clone https://github.com/fuergaosi233/claude-code-proxy.git
cd claude-code-proxy
pip install -r requirements.txt
```

### 2. Configure `.env`

```ini
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
OPENAI_API_KEY="sk-or-v1-YOUR_KEY"
BIG_MODEL="qwen/qwen3-coder:free"
MIDDLE_MODEL="qwen/qwen3-coder:free"
SMALL_MODEL="meta-llama/llama-3.3-70b-instruct:free"
HOST="127.0.0.1"
PORT=8082
LOG_LEVEL="INFO"
```

### 3. Add Shell Function

Add to `~/.bashrc` or `~/.zshrc`:

```bash
free-claude() {
    export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
    export ANTHROPIC_API_KEY="bypassed-via-local-proxy"
    export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
    export ENABLE_TOOL_SEARCH=true
    claude "$@"
}
```

The `ANTHROPIC_MODEL` is the **model spoof** — it overrides the internally validated model name so Claude Code's binary passes its check before the proxy ever sees the request.

### 4. Start Proxy

```bash
cd /path/to/claude-code-proxy && python start_proxy.py &
```

### 5. Use

```bash
free-claude -p "Refactor this module" --max-turns 10
```

## Checking Free Models

OpenRouter's free tier models change. Query before setup:

```bash
curl -s "https://openrouter.ai/api/v1/models" \
  -H "Authorization: Bearer $OPENROUTER_KEY" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data.get('data', []):
    p = m.get('pricing', {})
    if float(p.get('prompt', 1) or 1) == 0 and float(p.get('completion', 1) or 1) == 0:
        print(m['id'])
"
```

Look for coding-capable models: `qwen/qwen3-coder:free`, `meta-llama/llama-3.3-70b-instruct:free`, `google/gemma-4-31b-it:free`.

## Pitfalls

1. **Client-side model validation** — Claude Code v2.1+ validates model names against a hardcoded list in its compiled binary. Without `ANTHROPIC_MODEL` set to a known Anthropic model string, the CLI exits with "There's an issue with the selected model" before any network call.
2. **OpenRouter 429 rate limits** — free tier is aggressively throttled. The proxy has exponential backoff retry logic, but sustained load will fail.
3. **`:free` suffix models change** — a free model today may be paywalled tomorrow. Always re-check with the curl listing command.
4. **Proxy must be running first** — start `python start_proxy.py` before invoking `free-claude`. If the proxy isn't up, Claude Code hangs until timeout.
5. **Windows/git-bash background caveats** — `&` backgrounding in git-bash is unreliable. Use a separate terminal window or a dedicated task.

## Verification

```bash
# Check proxy health
curl -s http://127.0.0.1:8082/health

# Test end-to-end with a simple prompt
free-claude -p "Reply with just the word: WORKING" --max-turns 1 --allowedTools "Read"

# Check proxy logs for request translation
# Look for: "Model: claude-3-5-sonnet-20241022 → qwen/qwen3-coder:free"
```
