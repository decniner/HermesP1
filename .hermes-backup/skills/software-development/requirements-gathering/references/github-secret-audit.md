# GitHub Repo Security Audit

After a user asks "check if my GitHub is leaking credentials," use this reference.

## Detection — Scan repo files for secrets

```bash
# API keys (DeepSeek, OpenAI, etc.)
grep -rn --include="*" "sk-[a-zA-Z0-9]\{20,\}" . | grep -v ".git/\|node_modules/"

# GitHub tokens
grep -rn --include="*" "ghp_[a-zA-Z0-9]\{35,\}\|github_pat_[a-zA-Z0-9]\{50,\}" . | grep -v ".git/"

# Telegram bot tokens
grep -rn --include="*" "[0-9]\{8,10\}:AA[a-zA-Z0-9_-]\{25,\}" . | grep -v ".git/"

# Generic password/secret
grep -rn --include="*" -iE "(api_key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]" . | grep -v ".git/\|node_modules/"
```

## Fix — Remove from git history

```bash
# Remove from tracking
git rm --cached -r .hermes-backup/

# Wipe from ALL history (rewrites git log — caution!)
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch -r <path>' --prune-empty --tag-name-filter cat -- --all

# Force push
git push --force origin main
```

## Prevent re-exposure

- `.env` in `.gitignore` — every repo
- `.hermes-tmp.*` in `.gitignore` 
- `profiles_keys_needed.txt` — show only key NAMES, never values
