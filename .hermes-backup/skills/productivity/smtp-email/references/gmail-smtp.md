# Gmail SMTP — App Password Setup & Usage

## Generating an App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select app: "Mail" and device: "Other" (name it "Hermes Agent")
3. Copy the 16-character password (format: `abcd efgh ijkl mnop`)
4. Store in a local `.env` file, NOT in the script or git

## Using in a Hermes Session

When the user asks to send email from their Gmail account:

1. The app password may already be known from previous sessions (check memory)
2. If not known, ask the user to generate one or retrieve it
3. Pass the app password via terminal() command inline (it's ephemeral — not saved in chat history)

## Code Pattern

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

msg = MIMEMultipart()
msg['From'] = 'sender@gmail.com'
msg['To'] = 'recipient@gmail.com'
msg['Subject'] = 'Subject Line'

# Attach body
msg.attach(MIMEText('Email body text here', 'plain'))

# Attach file (optional)
from email.mime.base import MIMEBase
from email import encoders
with open('/path/to/file.html', 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', 'attachment; filename="report.html"')
msg.attach(part)

# Send
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('sender@gmail.com', 'app_password_here')
server.send_message(msg)
server.quit()
print('Email sent!')
```

## Troubleshooting

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `(535, b'5.7.8 Username and Password not accepted')` | Wrong app password | Generate a new app password |
| `ConnectionRefusedError` | Wrong SMTP server/port | Verify smtp.gmail.com:587 |
| `TimeoutError` | Network blocked | Check firewall or use different network |
| `smtplib.SMTPSenderRefused` | From address mismatch | Use the same email as the login |
