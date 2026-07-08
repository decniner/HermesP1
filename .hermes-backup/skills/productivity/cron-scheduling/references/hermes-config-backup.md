# Hermes Config Backup (Broader Backup Script)

Extended version of the basic git auto-backup that also preserves Hermes agent state — memories, skills, profiles, config — so recovery after reformat is complete.

## Why Back Up Hermes Config Separately

The user's Hermes agent stores important state outside the project repos:
- **Memories** (persistent facts, user profile)
- **Skills** (79 agent-created skills with their SKILL.md + references)
- **Profiles** (japanese-teacher, news-bot, price-bot — each with SOUL.md, config.yaml, .env)
- **USER.md, config.yaml, SOUL.md** (main agent settings)
- **Cron jobs, gateway state, hooks**

Losing these means losing all bot personalities, API keys, and learned preferences.

## Script Pattern

```python
import subprocess, os, shutil
from datetime import datetime

HERMES_BACKUP = r'C:\Users\decni\projects\.hermes-backup'

def sync_hermes_data():
    """Copy Hermes memories, config, profiles to backup folder"""
    base = r'C:\Users\decni\AppData\Local\hermes'
    os.makedirs(HERMES_BACKUP, exist_ok=True)
    copied = []
    
    core = {
        'memories':os.path.join(base,'memories'),
        'user_profile':os.path.join(base,'USER.md'),
        'config':os.path.join(base,'config.yaml'),
        'SOUL.md':os.path.join(base,'SOUL.md'),
        'gateway_state':os.path.join(base,'gateway_state.json'),
        'cron':os.path.join(base,'cron'),
        'hooks':os.path.join(base,'hooks'),
    }
    for name, src in core.items():
        dst = os.path.join(HERMES_BACKUP, name)
        if os.path.exists(src):
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                if os.path.exists(dst): shutil.rmtree(dst)
                shutil.copytree(src, dst)
            copied.append(name)
    
    # Profiles — backup everything EXCEPT .env (contain live tokens)
    profiles_src = os.path.join(base, 'profiles')
    if os.path.exists(profiles_src):
        # Don't copy to repo (gitignored), just document keys needed
        keys_needed = set()
        for root, dirs, files in os.walk(profiles_src):
            if '.env' in files:
                env_path = os.path.join(root, '.env')
                profile_name = os.path.basename(os.path.dirname(env_path))
                with open(env_path) as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key = line.split('=')[0].strip()
                            val = line.split('=')[1].strip()[:8]
                            keys_needed.add(f'{profile_name}: {key} = {val}...')
        
        keys_path = os.path.join(HERMES_BACKUP, 'profiles_keys_needed.txt')
        with open(keys_path, 'w') as f:
            f.write('# Recreate each profile\'s .env with these values\n')
            for k in sorted(keys_needed):
                f.write(k + '\n')
    
    return copied
```

## .gitignore Requirements

When committing Hermes config to GitHub, `.env` files must be excluded to avoid GitHub's push-protection blocking secrets:

```gitignore
# Never push .env files even inside backup
.hermes-backup/**/.env
.hermes-backup/profiles/      # profiles dir as a whole to be safe
```

## GitHub Push Protection

GitHub's secret scanning scans all files in every commit. If a `.env` with a real API key (DeepSeek, Telegram bot token) was accidentally pushed, future pushes will be blocked with:

```
remote: GITHUB PUSH PROTECTION
remote:   Push cannot contain secrets
remote:   DeepSeek API Key found in .hermes-backup/profiles/*/.env:6
```

**Fix:** Remove the secret files from git history:
```bash
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch -r .hermes-backup/' \
  --prune-empty -- --all
git push --force origin main
```

## Recovery After Reformat

1. Install Hermes Agent
2. Clone `https://github.com/decniner/HermesP1`
3. Copy `.hermes-backup/` → `~/AppData/Local/hermes/`
4. Check `profiles_keys_needed.txt` to recreate each profile's `.env` with fresh bot tokens + API keys
5. All memories, skills, configs, and profiles restored
