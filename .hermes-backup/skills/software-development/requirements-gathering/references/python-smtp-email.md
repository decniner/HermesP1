# Python SMTP Email Sending (No External CLI)

When the himalaya CLI is not installed, use Python's built-in `smtplib` to send emails directly. This works on any system with Python stdlib — no external dependencies.

## Gmail SMTP

| Setting | Value |
|---------|-------|
| Server | `smtp.gmail.com:587` |
| Encryption | `starttls` |
| Auth | App password (requires 2FA enabled) |

## Sending a Plain Text Email

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

msg = MIMEMultipart()
msg['From'] = 'you@gmail.com'
msg['To'] = 'recipient@gmail.com'
msg['Subject'] = 'Subject'
msg.attach(MIMEText('Body text', 'plain'))

s = smtplib.SMTP('smtp.gmail.com', 587)
s.starttls()
s.login('you@gmail.com', 'app-password-here')
s.send_message(msg)
s.quit()
```

## Sending with HTML File Attachment

```python
from email.mime.base import MIMEBase
from email import encoders

# Attach after MIMEText body
with open('file.html', 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', 'attachment; filename="name.html"')
msg.attach(part)
```

## Pitfalls

1. **`execute_code` blocks SMTP** — use `terminal` tool with `python3 -c "..."` to pass through the approval gate
2. **Gmail app passwords** are 16 chars in 4 groups of 4, generated at https://myaccount.google.com/apppasswords — spaces included
3. **Same sender + recipient** works fine (send reports to yourself)
4. **Keep volume low** — Gmail rate-limits; not for bulk sending
