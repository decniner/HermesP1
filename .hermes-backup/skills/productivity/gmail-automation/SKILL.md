---
name: gmail-automation
description: "Automate Gmail inbox management — scanning old unread emails, flagging candidates for deletion, protecting important senders, and scheduling cleanup via Hermes cron jobs. Uses IMAP + Gmail App Passwords."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gmail, email, automation, cleanup, imap, inbox-management]
    related_skills: [cron-scheduling, delegated-qa-workflow]
---

# Gmail Automation (IMAP + App Passwords)

Automate Gmail inbox management when Google Workspace OAuth is not configured. Uses IMAP with a Gmail App Password, Hermes cron jobs, and a scan → flag → approve → delete workflow.

## When to Use

- User wants to clean up a full Gmail inbox
- User wants automated flagging of old/unread emails for review
- User wants daily scanning with approval-based deletion
- Google Workspace OAuth is not set up (use IMAP + App Password instead)

## Prerequisites

1. **Enable 2-Step Verification** on the Google account
2. **Generate an App Password** at https://myaccount.google.com/apppasswords (Mail → Windows Computer)
3. The 16-character password (format: `xxxx xxxx xxxx xxxx`)

## The Workflow

```
┌─ Cron Job (daily 8am) ─────────────────────┐
│ 1. Connect to Gmail via IMAP                │
│ 2. Search: (UNSEEN BEFORE "30-days-ago")    │
│ 3. Batch-fetch headers in groups of 50      │
│ 4. Filter: check is_protected()             │
│ 5. Flag matching emails with ★ (star)       │
│ 6. Report to user: count + samples          │
└─────────────────────────────────────────────┘
         ↓
┌─ User Review ───────────────────────────────┐
│ User replies "approve delete"                │
└─────────────────────────────────────────────┘
         ↓
┌─ Delete Script ─────────────────────────────┐
│ 1. Find all FLAGGED (starred) emails         │
│ 2. Move to trash: +X-GM-LABELS \Trash       │
│ 3. Mark deleted: +FLAGS \Deleted             │
│ 4. Report count deleted                      │
└─────────────────────────────────────────────┘
```

## Script Structure

### Scan Script (`gmail_scan.py`)
- Connects to Gmail IMAP
- Searches for old unread emails (30+ days)
- Batch-fetches headers (FROM, SUBJECT, DATE) in groups of 50
- Filters through `is_protected()` function
- Flags matching emails with \\Flagged (star)
- Outputs a clean report

### Delete Script (`gmail_delete.py`)
- Searches for all FLAGGED emails
- Moves them to Gmail Trash
- Reports count

## IMAP Connection

```python
import imaplib

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('user@gmail.com', 'app-password-here')
mail.select('INBOX')
```

## Search Queries

```python
# Old unread
status, ids = mail.search(None, '(UNSEEN BEFORE "30-Jun-2026")')

# By sender
status, ids = mail.search(None, 'FROM "specific@domain.com"')

# All starred
status, ids = mail.search(None, 'FLAGGED')

# Searching by subject
status, ids = mail.search(None, 'SUBJECT "newsletter"')
```

**IMPORTANT:** IMAP search does NOT support Gmail web operators like `-has:attachment`, `from:gov`, or `newer_than:`. Use IMAP-native syntax only.

## Batch Header Fetching

Do NOT fetch emails one at a time. Batch-fetch in groups of 50-100:

```python
# IDs must be comma-separated string
ids_str = ','.join(msg_ids)

# Fetch headers only (not full body — much faster)
status, data = mail.fetch(ids_str, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')

# Parse: data alternates (content_tuple, separator_bytes)
for i in range(0, len(data), 2):
    if not isinstance(data[i], tuple): continue
    header_bytes = data[i][1]
    text = header_bytes.decode('utf-8', errors='replace')
    # Parse FROM, SUBJECT, DATE from text
```

## Sender Protection (`is_protected()`)

Define protection rules in priority order:

```python
def is_protected(from_addr, subject):
    addr = extract_email(from_addr)
    
    # 1. Specific senders (payroll, HR, work contacts)
    if addr in ['payroll@company.com', 'boss@company.com']:
        return True
    
    # 2. Personal email providers (real people)
    if any(p in addr for p in ['gmail.com', 'yahoo.co.jp', 'icloud.com']):
        return True
    
    # 3. Google system emails (security alerts)
    if 'google.com' in addr and any(
        kw in subject for kw in ['security', 'alert', 'recovery', 'verification']
    ):
        return True
    
    # 4. Important domains
    if any(d in addr for d in ['.gov', '.ac.jp', '.edu', '.go.jp']):
        return True
    
    # 5. Important subject keywords
    if any(kw in subject for kw in [
        'bank', 'tax', 'invoice', 'bill', 'receipt', 'statement',
        'salary', 'payroll', 'important', 'contract'
    ]):
        return True
    
    return False
```

## Flags vs Labels

| Action | IMAP Command | Result |
|--------|-------------|--------|
| Star email | `mail.store(msg_id, '+FLAGS', '\\Flagged')` | ★ appears in Gmail |
| Unstar email | `mail.store(msg_id, '-FLAGS', '\\Flagged')` | Removes ★ |
| Move to trash | `mail.store(msg_id, '+X-GM-LABELS', '\\\\Trash')` | Goes to Gmail Trash folder |
| Permanently delete | `mail.store(msg_id, '+FLAGS', '\\Deleted')` + `mail.expunge()` | Removes immediately |

## MIME Subject Decoding

Gmail subjects can be MIME-encoded. Decode them properly:

```python
from email.header import decode_header

def decode_mime(s):
    if not s: return ''
    parts = decode_header(s)
    result = ''
    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc if enc else 'utf-8', errors='replace')
        else:
            result += part
    return result
```

## Cron Job Setup

```python
# Create as no_agent script (no LLM, just runs the Python)
cronjob(
    action='create',
    name='Gmail Inbox Scan',
    schedule='0 8 * * *',   # Daily at 8am
    script='gmail_scan.py',  # Place in ~/.hermes/scripts/
    no_agent=True,
)
```

## Verification

After setup, test manually:
```python
python ~/.hermes/scripts/gmail_scan.py
```

Expected output:
```
Total old unread: 3667
Protected (skipped): 29
Flagged for review: 34

✅ 34 emails have been ★ flagged in your inbox.
Reply 'approve delete' and I'll trash them.
```

## Known Constraints

- **No attachment detection via IMAP search** — Must fetch BODYSTRUCTURE to detect attachments. This is expensive (1 request per email). Better to pre-filter and accept that some attachment-bearing emails slip through, then protect them in the delete step.
- **Rate limited** — Gmail IMAP allows ~1500 commands per 10 minutes. Batch operations stay well under this.
- **App Passwords require 2FA** — The user must have 2-Step Verification enabled on their Google account.
- **Trash auto-deletes after 30 days** — Google automatically purges trash contents after 30 days. No need to manually expunge.

## Common Pitfalls

1. **App Password with spaces** — The generated password includes spaces (`xxxx xxxx xxxx xxxx`). Pass it as-is; `imaplib` accepts spaces.
2. **Trash folder name** — On non-English Gmail, the trash folder may be named `[Gmail]/Trash` or `[Google Mail]/Trash` or localized equivalent. Use `+X-GM-LABELS` to bypass folder name issues.
3. **Batch response parsing** — The fetch response alternates `(header_tuple, b')')`. Skip every other item. Always check `isinstance(item, tuple)` before accessing parts.
4. **Partial batch matches** — When using IMAP search with SUBJECT for flagging, some emails may not match due to encoding differences. The flag step is best-effort; missed emails will be caught on the next daily scan.
5. **Empty inbox = no flags** — If all flagged emails were already deleted, `search(None, 'FLAGGED')` returns empty. Check `if not ids[0]` before iterating.
