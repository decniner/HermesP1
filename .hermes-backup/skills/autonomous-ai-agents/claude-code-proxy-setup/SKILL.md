---
name: claude-code-proxy-setup
description: "Route Claude Code CLI through OpenRouter free tier via claude-code-proxy — model spoofing, .env config, shell function, and rate-limit mitigation."
version: 1.0.0
platforms: [linux, macos, windows]
---

# Claude Code Free Tier — OpenRouter Proxy Setup

## When to use

Use when the user wants to run Claude Code without an Anthropic subscription, using OpenRouter's free models instead. The technique: a local Python proxy translates Anthropic Messages API calls to OpenAI-compatible format, and `ANTHROPIC_MODEL` spoofs client-side model validation.

## Architecture

```
Claude Code CLI → claude-code-proxy (localhost:8082) → OpenRouter API → Free LLM
```

## Quick Setup

```bash
# 1. Clone proxy
git clone https://github.com/fuergaosi233/claude-code-proxy.git
cd claude-code-proxy
pip install -r requirements.txt

# 2. Create .env
cat > .env << 'ENVEOF'
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
OPENAI_API_KEY="sk-or-v1-..."            # Your OpenRouter key
BIG_MODEL="openrouter/free"               # Auto-routes to least busy free model
MIDDLE_MODEL="openrouter/free"
SMALL_MODEL="openrouter/free"
HOST="127.0.0.1"
PORT=8082
LOG_LEVEL="INFO"
ENVEOF

# 3. Start proxy
python start_proxy.py
```

## Model Spoofing (Critical)

Claude Code v2.1+ validates model names client-side against a hardcoded list of Claude-only model IDs. Bypass with `ANTHROPIC_MODEL`:

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
export ANTHROPIC_API_KEY="bypassed-via-local-proxy"
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
export ENABLE_TOOL_SEARCH=true
claude "$@"
```

Pack as shell function (add to ~/.bashrc / ~/.zshrc):

```bash
free-claude() {
    export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
    export ANTHROPIC_API_KEY="bypassed-via-local-proxy"
    export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
    export ENABLE_TOOL_SEARCH=true
    claude "$@"
}
```

Usage: `free-claude -p "your task" --max-turns 5 --allowedTools "Read,Write"`

## Free Model Selection

OpenRouter has ~27 completely free models. Current list: `curl -s https://openrouter.ai/api/v1/models | jq '.data[] | select(.pricing.prompt == "0" and .pricing.completion == "0") | .id'`

| Strategy | Model String | Notes |
|----------|-------------|-------|
| **Auto-route** | `openrouter/free` | Most reliable — routes to least congested free model |
| **Coding** | `qwen/qwen3-coder:free` | Good for code gen, may get 429 |
| **Fast** | `google/gemma-4-26b-a4b-it:free` | Smaller, faster responses |
| **Large context** | `nousresearch/hermes-3-llama-3.1-405b:free` | 405B, slow but capable |
| **Fallback** | `meta-llama/llama-3.3-70b-instruct:free` | Stable, less congested |

## Known Limitations

| Symptom | Cause | Fix |
|---------|-------|-----|
| `429 Too Many Requests` | Free tier rate limit | Wait, retry, switch to `openrouter/free` |
| Task times out (>300s) | Free model too slow for large output | Split task into smaller pieces |
| Model not found (400/404) | Model slug changed on OpenRouter | Check `/api/v1/models` for current slugs |
| `:free` suffix fails | Model no longer free | Remove `:free` suffix, use `openrouter/free` |
| Binary hangs on startup | No ANTHROPIC_MODEL set | Must set spoofed model name |

## Verification

```bash
free-claude -p "reply just: WORKS" --max-turns 1 --allowedTools "Read"
# Expected: "WORKS"
```

Add to `~/.bashrc` (or `~/.zshrc`):

```bash
# Free Claude Code via OpenRouter proxy
free-claude() {
    export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
    export ANTHROPIC_API_KEY="bypassed-via-local-proxy"
    export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
    export ENABLE_TOOL_SEARCH=true
    claude "$@"
}
```
