# 🔴 HERMES RECOVERY GUIDE — READ THIS AFTER REFORMAT

After reinstalling Windows, follow these steps to restore everything:

## Step 1: Install Basics
1. Install Python 3.11+ from python.org
2. Install Git from git-scm.com
3. Open PowerShell as Admin and run:
   ```
   pip install hermes-agent
   ```

## Step 2: Clone Your Repos
```
cd C:\Users\decni
git clone https://github.com/decniner/HermesP1.git projects
git clone https://github.com/decniner/MQLNewStrat2.git projects\mql-bots
```

## Step 3: Restore Hermes Configuration
```
xcopy /E /I projects\.hermes-backup\memories %USERPROFILE%\.hermes\memories
xcopy /E /I projects\.hermes-backup\skills %USERPROFILE%\.hermes\skills
xcopy projects\.hermes-backup\config.yaml %USERPROFILE%\.hermes\config.yaml
xcopy projects\.hermes-backup\SOUL.md %USERPROFILE%\.hermes\SOUL.md
xcopy /E /I projects\.hermes-backup\cron %USERPROFILE%\.hermes\cron
xcopy /E /I projects\.hermes-backup\gateway_state.json %USERPROFILE%\.hermes\
xcopy /E /I projects\.hermes-backup\hooks %USERPROFILE%\.hermes\hooks
```

## Step 4: Recreate .env Files (API KEYS)
Check `profiles_keys_needed.txt` in this folder for which keys are needed.
Then create these .env files:

### Main .env at %USERPROFILE%\.hermes\.env
DEEPSEEK_API_KEY=<your key>

### Profile .env files at %USERPROFILE%\.hermes\profiles\<name>\.env
Each profile needs its Telegram Bot Token from @BotFather
See profiles_keys_needed.txt for which tokens belong to which bot.

## Step 5: Verify
```
hermes
```
Should launch with all your skills, memory, and profiles restored.

## What's in this Backup
✅ memories/ — MEMORY.md + USER.md (all your personal info)
✅ skills/ — 79 skill files
✅ config.yaml — main Hermes configuration
✅ SOUL.md — personality file
✅ cron/ — all scheduled jobs
✅ gateway_state.json — Telegram/Discord connections
✅ hooks/ — automation hooks
✅ profiles_keys_needed.txt — lists which API keys to recreate

## What's NOT in this Backup (must recreate)
❌ .env files (API keys) — security. Recreate from profiles_keys_needed.txt
❌ Hermes session history — only current memory/knowledge preserved
❌ Local game state / browser cache
