# Debugging Transcript — Claude Code + OpenRouter Proxy

## Symptoms Encountered

### Symptom 1: "There's an issue with the selected model"

**Cause:** Claude Code v2.1+ compiled binary validates model names client-side against an internal hardcoded list. The binary exits immediately without making any network call when the model name isn't recognized.

**Failed approaches:**
- Setting `ANTHROPIC_BASE_URL` alone (model not in the internal list → fails at binary level)
- Using OpenRouter model IDs directly as `--model` flag (Claude Code's internal validator doesn't know OpenRouter slugs)
- Providing `/v1/models` responses via proxy (validation happens before the network call)

**Working fix:** Set `ANTHROPIC_MODEL` env var to a known Anthropic model string (e.g. `claude-3-5-sonnet-20241022`). This env var overrides the internal model name before validation runs. The proxy never sees this validated name — it receives what the `.env` file sends.

### Symptom 2: Proxy starts but no logs / exits silently

**Cause:** On Windows git-bash, background process output is suppressed. The startup log messages (`Configuration loaded`, `🚀 Claude-to-OpenAI API Proxy`) are written to stdout which isn't captured.

**Check:** `curl -s http://127.0.0.1:8082/health` — if it returns `{"status":"healthy"}`, the proxy is running even though no startup messages appeared.

### Symptom 3: "429 Too Many Requests"

**Cause:** OpenRouter free tier has aggressive rate limits. Common when:
- Multiple Claude Code sessions start simultaneously (it opens 2+ connections)
- The proxy retries and compounds the rate limiting
- A popular free model is under heavy load

**Observed behavior:** The proxy retries with backoff (25s → 24s → 14s → 10s → 30s), but all retries fail with 429.

### Symptom 4: Model ":free" suffix not available

**Symptom:** `POST /v1/chat/completions` returns 404 with `"This model is unavailable for free. The paid version is available now - use this slug instead: qwen/qwen-2.5-coder-32b-instruct"`

**Cause:** The `:free` suffix was removed from a previously-free model. OpenRouter changes free model availability without notice.

**Fix:** Remove the `:free` suffix, or switch to a currently-available free model from the models listing.

## Verified Working Configuration

| Component | Value |
|-----------|-------|
| Claude Code version | 2.1.203 |
| Proxy repo | github.com/fuergaosi233/claude-code-proxy |
| Proxy port | 127.0.0.1:8082 |
| Spoofed model | claude-3-5-sonnet-20241022 |
| Working free models | qwen/qwen3-coder:free, meta-llama/llama-3.3-70b-instruct:free |

## Key Insight: Two-Layer Validation

Claude Code v2.1+ has TWO independent validation layers:

1. **Binary-level model validation** (client-side) — The compiled `claude.exe` has a hardcoded list of ~20-30 valid Claude model names. It checks `--model` flag or internal default against this list and exits immediately if no match. **Bypassed by `ANTHROPIC_MODEL` env var.**

2. **API-level model validation** (server-side) — The proxy receives the request and translates to OpenRouter. OpenRouter validates the model slug from `.env` against its own catalog. **Handled by choosing a valid free model slug.**
