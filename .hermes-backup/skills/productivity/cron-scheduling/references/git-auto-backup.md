# Git Auto-Backup via Cron (no_agent Script)

Pattern for automatically backing up project repositories to GitHub on a schedule.

## Use Case

Push all changes in one or more local git repos to GitHub daily/weekly without manual intervention. The user gets a summary report in Telegram.

## The Script

Place this in `~/.hermes/scripts/backup_projects.py`:

```python
"""Auto-backup projects to GitHub"""
import subprocess, os
from datetime import datetime

REPOS = [
    {
        'path': r'C:\Users\decni\projects',
        'remote': 'https://decniner:${GITHUB_TOKEN}@github.com/decniner/HermesP1.git',
        'branch': 'main',
        'name': 'HermesP1'
    },
    # Add more repos as needed
]

def run_git(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

results = []
ts = datetime.now().strftime('%Y-%m-%d %H:%M')

for repo in REPOS:
    path = repo['path']
    name = repo['name']
    
    if not os.path.exists(os.path.join(path, '.git')):
        results.append(f'❌ {name}: No .git found')
        continue
    
    run_git(['git', 'remote', 'set-url', 'origin', repo['remote']], path)
    run_git(['git', 'add', '-A'], path)
    
    code, out, err = run_git(['git', 'status', '--porcelain'], path)
    if not out.strip():
        results.append(f'⏭️  {name}: Nothing to commit')
        continue
    
    run_git(['git', 'commit', '-m', f'Auto-backup {ts}'], path)
    code, out, err = run_git(['git', 'push', '-u', 'origin', repo['branch']], path)
    
    if code == 0:
        results.append(f'✅ {name}: Backed up')
    else:
        results.append(f'❌ {name}: Push failed - {err[:100]}')

# Print results
print(f'\n📦 BACKUP REPORT — {ts}')
print('='*40)
for r in results:
    print(f'  {r}')
```

## Cron Setup

```python
cronjob(
    action='create',
    name='Auto Backup All Projects',
    schedule='0 21 * * *',        # Daily at 9pm JST
    script='backup_projects.py',   # relative to ~/.hermes/scripts/
    no_agent=True,                 # no LLM needed, just run script
    deliver='origin'               # report goes to current chat
)
```

## Key Points

- **GitHub token in URL**: Embed the token in the remote URL (`https://user:token@github.com/user/repo.git`) — the cron job has no interactive TTY to prompt for credentials.
- **Token format**: Classic PAT (`ghp_...`) works for push access. Fine-grained PATs (`github_pat_...`) need explicit "Contents: Write" permission on the repo.
- **`git status --porcelain`**: Check for changes before committing. If empty, skip the commit+push to avoid empty commits.
- **`git add -A`**: Catches all changes (new files, modified, deleted) — no need to track each one.
- **Multiple repos**: The script iterates over a list — add more entries for each repo to back up.
- **no_agent mode**: No LLM cost, just stdout delivery.
