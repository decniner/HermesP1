# Gmail IMAP Inbox Cleanup via Cron

Non-trivial technique for automated Gmail inbox management using Python IMAP + Hermes cron. Covers the full lifecycle: scan, flag, review, delete.

## Architecture

```
cron (daily 8am JST)
  → gmail_scan.py (IMAP over SSL)
    → Search: UNSEEN BEFORE {30 days ago}
    → Filter: skip protected senders, attachments, known domains
    → Flag: ★ (star) candidates in Gmail
    → Report: send summary to user
  → User replies "approve all"
  → gmail_delete.py
    → Search: FLAGGED
    → Move to [Gmail]/Trash
    → Auto-expunged by Gmail after 30 days
```

## Gmail IMAP Connection

```python
import imaplib
mail = imaplib.IMAP4_SSL('imap.gmail.com', timeout=15)
mail.login('user@gmail.com', 'app_password')
mail.select('INBOX')
```

**App Passwords** — Google requires an App Password (16 chars, `xxxx xxxx xxxx xxxx`) for IMAP access. Generate at https://myaccount.google.com/apppasswords. Requires 2FA to be enabled.

## IMAP Search Caveats

| Attempt | Result | Lesson |
|---------|--------|--------|
| `(UNSEEN BEFORE "date" -has:attachment)` | ❌ `BAD Could not parse command` | Gmail web search syntax (`-has:`, `-from:`) does NOT work in IMAP |
| `(UNSEEN BEFORE "date")` ✅ | Works | IMAP's SEARCH is limited to basic flags, dates, and FROM/SUBJECT criteria |
| Batch fetch `BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)]` | ✅ Works | Use comma-separated IDs: `'1,2,3'` not `'1 2 3'` |

## IMAP Response Parsing

The `fetch` response returns tuples in pairs per email:
```python
status, data = mail.fetch('1,2,3', '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
# data[0] = (b'1 (BODY[HEADER.FIELDS...] {...}', b'header content')
# data[1] = b')'
# data[2] = (b'2 (BODY[HEADER.FIELDS...] {...}', b'header content')
# data[3] = b')'
```

Parse: iterate `range(0, len(data), 2)`, check `isinstance(item, tuple)`, read `item[1]` for header bytes.

## Protected Senders List

The `is_protected()` function should check (in order):

1. **Exact email match** — `protected_emails` list (user-specified whitelist)
2. **Personal providers** — gmail.com, yahoo.co.jp, icloud.com, outlook.com, hotmail.com (likely real people)
3. **Google system emails** — google.com with security/recovery/alert keywords
4. **Important domains** — .gov, .ac.jp, .edu, .go.jp, bank domains
5. **Subject keywords** — bank, school, tax, invoice, bill, salary, payroll, important

## Recovery from Trash

```python
mail.select('[Gmail]/Trash')
status, ids = mail.search(None, 'FROM "sender@example.com"')
for msg_id in ids[0].split():
    mail.copy(msg_id, 'INBOX')
    mail.store(msg_id, '+FLAGS', '\\Deleted')
mail.expunge()
```

Gmail keeps trashed emails for 30 days. After that they're permanently deleted.

## Batch Processing

Processing 3,600+ emails one-by-one is too slow. Workflow:
1. Search for ALL candidates via SEARCH (1 call)
2. Fetch HEADERS in batches of 50-100 (1 call per batch)
3. Filter in Python
4. Flag candidates: `mail.store(id, '+FLAGS', '\\Flagged')`

## Common Pitfalls

- **IMAP doesn't support `-has:attachment`** — Filter attachments in Python by checking FETCH BODYSTRUCTURE or accept the limitation
- **Gmail's `\\Flagged` = star** — Flagging via IMAP makes the email starred in the Gmail UI
- **`mail.store(id, '+X-GM-LABELS', '\\\\Trash')` moves to trash via Gmail's IMAP extension** — alternative to `mail.copy(id, '[Gmail]/Trash')`
- **App passwords are per-account** — each Gmail account needs its own
- **Timeout on large scans** — Gmail IMAP is slow for 3,000+ emails. Set `socket.setdefaulttimeout(15)` and limit batches to 200-500 emails
