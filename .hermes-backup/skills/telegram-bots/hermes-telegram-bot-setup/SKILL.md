---
name: hermes-telegram-bot-setup
description: "Set up a new Telegram bot profile for Hermes Agent — profile creation, SOUL.md, config.yaml, .env tokens, gateway start, and gotify/token handling."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [telegram, bot, hermes, profile, gateway]
    related_skills: [hermes-agent, cron-scheduling]
---

# Hermes Telegram Bot Setup

Create a dedicated Telegram bot for a specific role (news, price search, Japanese lessons, etc.) as a separate Hermes profile with its own gateway.

## When to Use

- User wants a new Telegram bot with a distinct personality/role
- User wants to separate concerns (one bot per function)
- User provides a new bot token from @BotFather

## Prerequisites

- Bot token from @BotFather (format: `1234567890:AA...`)
- User's Telegram user ID (for `TELEGRAM_ALLOWED_USERS`)
- DeepSeek API key (inherited from default profile)

## Step-by-Step

### 1. Create Profile

```bash
hermes profile create <profile-name>
```

This creates:
```
~/.hermes/profiles/<profile-name>/
├── SOUL.md
├── config.yaml
├── .env              # (empty, needs tokens)
├── skills/
├── logs/
└── ...
```

### 2. Write SOUL.md

The SOUL.md defines the bot's personality and behavior rules. Pattern:

```markdown
# 🤖 Bot Name — Purpose

You are a dedicated [role] bot. Your ONLY job is to [core function].

## How to [do the thing]

Step-by-step instructions for the bot's primary task.

## Rules
- All responses in [language]
- Tone: [friendly / professional / direct]
- [Other behavioral constraints]

## Interaction model
- User sends X → bot responds with Y
- User sends "command" → bot does Z
```

### 3. Write config.yaml

```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek
  base_url: https://api.deepseek.com/v1

agent:
  max_turns: 30

terminal:
  backend: local
  cwd: .
  timeout: 180

display:
  streaming: true

memory:
  memory_enabled: false
  user_profile_enabled: false

gateway:
  enabled: true
  platforms:
    telegram:
      enabled: true
      bot_token_env: TELEGRAM_BOT_TOKEN

platform_toolsets:
  telegram:
    - hermes-telegram

web:
  backend: firecrawl
  use_gateway: true
```

### 4. Wire .env Tokens

```bash
# Bot token from @BotFather
echo 'TELEGRAM_BOT_TOKEN=1234567890:AA...' >> ~/.hermes/profiles/<profile-name>/.env

# User whitelist
echo 'TELEGRAM_ALLOWED_USERS=6912295778' >> ~/.hermes/profiles/<profile-name>/.env

# Inherit DeepSeek API key from default profile
grep "DEEPSEEK" ~/.hermes/.env >> ~/.hermes/profiles/<profile-name>/.env
```

**IMPORTANT:** The profile's `.env` has NO API keys by default. Always copy the DEEPSEEK_API_KEY from the main `.env`. Without this, the bot starts but returns "no credentials configured" errors.

### 5. Start Gateway

```bash
hermes --profile <profile-name> gateway start
```

First startup will prompt to:
- Install the gateway service
- Start it now
- Auto-start on login
- Create a Scheduled Task (needs admin/UAC)

**Answer:** Yes (y) to all prompts. If UAC is denied, it falls back to Startup folder (.vbs script) which works but requires the user to be logged in.

### 6. Verify

```bash
# Check gateway started
tail ~/.hermes/profiles/<profile-name>/logs/gateway.log

# Expected output:
# [Telegram] Connected to Telegram (polling mode)
# ✓ telegram connected

# Check for errors
grep -i "error\|fail" ~/.hermes/profiles/<profile-name>/logs/gateway.log
```

If the gateway fails:
- Check `.env` has TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USERS
- Check the bot token is correct (paste into @BotFather `/mybots` to verify)
- Check DEEPSEEK_API_KEY is present in the profile's `.env`
- Restart: `hermes --profile <profile-name> gateway restart`

### 7. Test

Send a message to the bot on Telegram. The user must be in `TELEGRAM_ALLOWED_USERS` or the bot silently ignores them.

## Common Pitfalls

1. **Missing API keys** — Profile `.env` is EMPTY after `profile create`. Always copy DEEPSEEK_API_KEY from the main `.env`. Bot starts fine but returns "no model configured" on any message.
2. **Wrong user ID** — `TELEGRAM_ALLOWED_USERS` must be the numeric Telegram user ID, NOT the username. Get it from @userinfobot.
3. **Gateway port conflict** — If another Hermes gateway is on the same machine, the profile gateway uses a different port automatically. No manual config needed.
4. **Multiple gateways running** — Each profile's gateway runs independently. Use `tasklist | grep node` to see all gateway processes. Kill with `taskkill /F /IM node.exe` if needed (kills ALL gateways).
5. **Token rotation** — If the bot token is revoked (from @BotFather), update only the `.env` file and restart the gateway. No profile changes needed.
6. **SOUL.md not picked up** — SOUL.md is read at gateway start. Changes require a gateway restart (`hermes --profile <name> gateway restart`).
