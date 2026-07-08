---
name: claude-proxy-backends
description: Route Claude Code CLI (and other Anthropic-format CLIs) through local proxy/translation layers to alternative LLM providers — OpenRouter, Ollama, vLLM, local endpoints.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Claude, Proxy, OpenRouter, Alternative-Backends, Automation]
    related_skills: [claude-code, llama-cpp]
---

# Claude Proxy Backends

Route Claude Code CLI through a local translation proxy to use alternative LLM providers instead of Anthropic's native API. The proxy converts Anthropic's message/tool format into OpenAI-compatible Chat Completions, enabling Claude Code's tool-calling workflow with any provider that supports function calling.

## When to Use

- **No Anthropic Pro/Max subscription** — use free-tier or credit-based providers (OpenRouter, Together, etc.)
- **Cost optimization** — route to cheaper model tiers for development/experimentation
- **Local/air-gapped** — point at Ollama, vLLM, or llama.cpp serving an OpenAI-compatible endpoint
- **Model testing** — evaluate how different models handle Claude Code's tool-calling pattern
- **Demo/CI** — run Claude Code workflows in CI without Anthropic billing

## Architecture

```
┌─────────────────┐     Anthropic-format      ┌──────────────────┐     OpenAI Completions     ┌─────────────────┐
│  Claude Code CLI │  ──────────────────────▶  │  Local Proxy     │  ──────────────────────▶  │  Alternative     │
│  (claude -p ...) │  (messages + tools)       │  (port 8082)     │  (function calling)       │  Provider        │
│                  │  ◀──────────────────────  │                  │  ◀──────────────────────  │  (OpenRouter,    │
│  Tool execution  │   tool_use blocks back    │  Translates      │   tool_calls back          │   Ollama, etc.)  │
│  runs locally    │                           │  format both     │                           │                  │
└─────────────────┘                            │  directions       │                           └─────────────────┘
                                               └──────────────────┘
```

Claude Code executes tools **locally** via its built-in tool chain (`ENABLE_TOOL_SEARCH=true`). The proxy translates only message/tool-call formatting — actual file edits, bash commands, and git operations run on the local machine.

## Required Client-Side Env Vars

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"   # Point to local proxy
export ANTHROPIC_API_KEY="bypassed-via-local-proxy"  # Dummy — proxy handles real auth
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"  # Spoof valid Anthropic model name to bypass client-side validation
export ENABLE_TOOL_SEARCH=true                        # Keep local tool execution
```

**`ANTHROPIC_MODEL` is critical** — Claude Code v2.1+ validates model names client-side against a hardcoded list. Without this override, Claude Code defaults to `claude-opus-4-8` which fails validation and the request never reaches the proxy. The spoofed name must match a real Anthropic model string in Claude Code's internal list. Known-valid spoofs (v2.1.203): `claude-3-5-sonnet-20241022`, `claude-opus-4-8`, `claude-haiku-4-5-20251001`.

These tell Claude Code to send all API requests to the local proxy instead of api.anthropic.com. The API key is unused by the proxy but must be non-empty to bypass Claude Code's auth check.

## Community Proxy: claude-code-proxy

[`fuergaosi233/claude-code-proxy`](https://github.com/fuergaosi233/claude-code-proxy) is the primary community-maintained translation layer. It's an async Python/FastAPI server.

### Quick Start

```bash
git clone https://github.com/fuergaosi233/claude-code-proxy.git
cd claude-code-proxy
pip install -r requirements.txt
```

Create `.env`:

```ini
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
OPENAI_API_KEY="<your-api-key>"
BIG_MODEL="qwen/qwen-2.5-coder-32b-instruct:free"
MIDDLE_MODEL="qwen/qwen-2.5-coder-32b-instruct:free"
SMALL_MODEL="meta-llama/llama-3-8b-instruct:free"
HOST="127.0.0.1"
PORT=8082
LOG_LEVEL="INFO"
```

Start the listener:

```bash
python start_proxy.py
```

### Shell Alias

```bash
free-claude() {
    export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
    export ANTHROPIC_API_KEY="bypassed-via-local-proxy"
    export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
    export ENABLE_TOOL_SEARCH=true
    claude "$@"
}
```

## Provider-Specific Configuration

### OpenRouter (Free Tier)

Free models on OpenRouter change availability frequently. `qwen/qwen-2.5-coder-32b-instruct:free` is often unavailable (returns 404). The most reliable approach is:

| Strategy | Config | Notes |
|----------|--------|-------|
| **Auto-route** | all models = `openrouter/free` | OpenRouter picks the least-congested free model. Best reliability. |
| **Specific model** | `google/gemma-4-26b-a4b-it:free` | 26B MoE, decent for code. |
| **Small/fallback** | `meta-llama/llama-3.2-3b-instruct:free` | 3B, fast but weak tool calling. |

Set `OPENAI_BASE_URL` to `https://openrouter.ai/api/v1`. Rate-limited aggressively: **429 Too Many Requests** is common on all free models. The proxy has built-in retry (backoff 0.4–30s, up to 4+ retries), but multi-turn sessions will stall. For heavy use, prefer `openrouter/free` which auto-routes to the least loaded backend.

To list currently available free models:
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

### Ollama (Local)

```ini
OPENAI_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="qwen2.5-coder:32b"
MIDDLE_MODEL="qwen2.5-coder:14b"
SMALL_MODEL="llama3.2:3b"
```

Requires Ollama serving an OpenAI-compatible endpoint (Ollama 0.3.0+). Download models first: `ollama pull qwen2.5-coder:32b`.

### vLLM (Local)

```ini
OPENAI_BASE_URL="http://localhost:8000/v1"
BIG_MODEL="/path/to/model"
```

vLLM natively serves an OpenAI-compatible API. Ensure the model supports function calling.

## Pitfalls & Gotchas

1. **Client-side model validation (v2.1+)** — Claude Code's binary (compiled Node.js bundle) validates model names against a **hardcoded internal list** BEFORE making any API call. Even with a proxy returning matching models from `/v1/models`, the validation is client-side and cannot be bypassed. The community proxy (`fuergaosi233/claude-code-proxy`) works around this by doing a full Anthropic→OpenAI format translation, so Claude Code sees valid Anthropic model names while the proxy maps them to OpenRouter models. A simple model-name-rewriting proxy that forwards Anthropic-format requests will NOT work — Claude Code rejects the model before the proxy ever receives a request.
   - Model names in the hardcoded list (v2.1.203): `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`, etc.
   - `--model` flag accepts aliases (`sonnet`, `opus`, `haiku`) and expands them to versioned names
   - `--bare` mode does NOT skip this validation — it only skips OAuth, hooks, and plugins

2. **Tool-calling depends on upstream model** — Qwen-2.5-Coder 32B handles function calling well; smaller models (8B range) frequently miss tool invocations or return malformed JSON.
3. **Free-tier rate limits** — multi-turn Claude Code sessions can burn through OpenRouter free-tier limits mid-task, causing silent failures.
4. **Streaming fidelity** — Anthropic-specific streaming features (thinking chunks, interleaved tool results) may not round-trip perfectly. Some proxy versions handle this better than others.
5. **Auth is fully bypassed** — the proxy never validates `ANTHROPIC_API_KEY`. Your real API key lives only in the proxy's `.env`. There's no OAuth login available.
6. **No MCP/plugins** — the proxy only translates the core messages+tools API. MCP server integration and plugin systems are unavailable.
7. **Version drift** — the proxy repo may lag behind Claude Code CLI API contract changes. If Claude Code updates its message format, the proxy may break until updated.
8. **No session persistence** — Claude Code's session/continue features may not work correctly since the proxy has no concept of Anthropic session IDs.
9. **Print mode (`-p`) works better** than interactive mode — the proxy handles one-shot request-response translation more reliably than streaming multi-turn conversations.
10. **Free-tier timeouts on large tasks** — generating output over ~10KB (e.g. writing a full HTML page) regularly times out on free-tier models. Use `terminal(..., timeout=600)` for Claude Code print tasks and split work into small, focused sub-tasks. The proxy's 90s request timeout and OpenRouter's free-tier latency compound each other.
11. **`openrouter/free` tolerates rate limits better** than specific free models — it auto-routes to the least congested backend. But it's also slower (bigger models). Use it for reliability, accept the speed hit.
