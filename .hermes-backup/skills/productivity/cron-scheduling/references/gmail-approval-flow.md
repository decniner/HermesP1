# Gmail Cleanup Approval Workflow

Pattern for automated Gmail inbox cleanup with **human-in-the-loop approval**. The agent scans old unread emails, flags candidates, presents them to the user for review, and deletes them on approval.

## The Approval Flow

```
cron (daily 8am JST)
  → gmail_scan.py
    → Search: UNSEEN BEFORE {30 days ago}
    → Filter: skip protected senders (bank, gov, real people, known domains)
    → Skip: emails with attachments
    → ★ Flag (star) matching emails in Gmail
    → Output: summary report with sample senders
  → stdout delivered to Telegram as no_agent cron job
  → User reviews the report
  → User replies "approve all" (or "approve delete")
  → Agent reads message and runs gmail_delete.py
    → Search: FLAGGED (starred emails)
    → Move each to [Gmail]/Trash via `mail.store(id, '+X-GM-LABELS', '\\\\Trash')`
    → Report: count deleted
```

## Protected Senders List

The `is_protected()` function checks in order:

1. **User-specified whitelist** — stored as a list in the script:
   ```python
   protected_emails = [
       'payroll.japan@hays.co.jp',
       'miki.sawafuji@hays.co.jp',
       'denver.sanchez@nomura.com',
       'noreply@travelsure.ph',
       'decniner@gmail.com'
   ]
   if addr in protected_emails: return True
   ```

2. **Personal email providers** — gmail.com, yahoo.co.jp, icloud.com, outlook.com, hotmail.com

3. **Google system emails** — google.com with security/recovery/alert/verification keywords

4. **Important domains** — .gov, .ac.jp, .edu, mufg.jp, mitsubishiufg, .go.jp

5. **Subject keywords** — bank, school, tax, invoice, bill, receipt, statement, salary, payroll, 社保, 年金, 保険, 契約, important

The protected list grows over time as the user discovers new senders that shouldn't be touched.

## Add Protected Senders on the Fly

When the user says "don't delete emails from X", take these actions:

1. **IMAP: Restore from trash immediately** — check `[Gmail]/Trash` for emails from that sender and copy them back to INBOX
2. **Update the script** — add the address to the `protected_emails` list so future scans skip it
3. **Confirm** — report how many emails were restored

```python
# Restore from trash
mail.select('[Gmail]/Trash')
status, ids = mail.search(None, 'FROM "sender@example.com"')
for msg_id in ids[0].split():
    mail.copy(msg_id, 'INBOX')          # Move back to inbox
    mail.store(msg_id, '+FLAGS', '\\Deleted')  # Remove from trash
mail.expunge()
```

Gmail permanently deletes trashed emails after 30 days. If the user asks later than that, recovery is impossible.

## Recovery Actions

If the user says "I deleted something I needed":

1. **Check trash immediately** — Gmail keeps trashed emails for 30 days
2. **Search by sender** — `FROM "payroll@example.com"`
3. **Copy back to INBOX** — `mail.copy(msg_id, 'INBOX')`
4. **Remove from trash** — `mail.store(msg_id, '+FLAGS', '\\Deleted')`
5. **Add to protected list** — prevent future deletion

## Script Files

- `~/AppData/Local/hermes/scripts/gmail_scan.py` — Daily scan + flag script
- `~/AppData/Local/hermes/scripts/gmail_delete.py` — Delete flagged emails script

## Common Scenarios

| User says | Action |
|-----------|--------|
| "Approve all" | Run `gmail_delete.py` to trash all flagged emails |
| "Don't delete from X" | Add to protected_emails, restore any already in trash |
| "I deleted Y by accident" | Search [Gmail]/Trash for Y, copy back to INBOX, protect sender |
| "Stop the scan" | Remove the cron job via `cronjob(action='remove', job_id='...')` |
| "Show me what's flagged" | Search INBOX for `FLAGGED` via IMAP, return list |
