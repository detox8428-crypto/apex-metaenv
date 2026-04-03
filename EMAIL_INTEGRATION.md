# Real Email Integration Guide

## Overview

APEX now supports **real email sending** in addition to simulation mode. This allows your agents to not only take email actions but to actually send real messages to real recipients.

**Key Features:**
- 🔄 **Dual-mode operation**: Simulation + optional real email
- ✉️ **Multi-provider support**: Gmail, Outlook, custom SMTP
- 👥 **Contact mapping**: Map agent contact IDs to real email addresses
- 🔐 **Secure**: Credentials stored in environment variables
- 🎯 **Backward compatible**: Works with existing simulation-only setup

---

## Quick Start (5 minutes)

### 1. Copy Configuration Template
```bash
cp .env.example .env
```

### 2. Choose Your Email Provider

#### Option A: Gmail
1. Enable 2-Factor Authentication on your Google account
2. Go to [Google App Passwords](https://support.google.com/accounts/answer/185833)
3. Generate an app password for "Mail"
4. Add to `.env`:
   ```
   EMAIL_PROVIDER=gmail
   GMAIL_EMAIL=your-email@gmail.com
   GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
   ```

#### Option B: Outlook/Hotmail
1. Go to [Microsoft Account Security](https://account.microsoft.com/account/manage-my-microsoft-account)
2. Create an app password
3. Add to `.env`:
   ```
   EMAIL_PROVIDER=outlook
   OUTLOOK_EMAIL=your-email@outlook.com
   OUTLOOK_PASSWORD=your-app-password
   ```

#### Option C: Custom SMTP (SendGrid, AWS SES, etc.)
```
EMAIL_PROVIDER=smtp
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_EMAIL=apikey
SMTP_PASSWORD=SG.your-sendgrid-key
```

### 3. Restart the Server
```bash
python run_server.py
```

You should see in the logs:
```
✓ Email Setup: Gmail provider initialized (your-email@gmail.com)
```

---

## How It Works

### Architecture

```
┌─────────────────┐
│  Frontend UI    │
│  (index.html)   │
└────────┬────────┘
         │
    [send_real ✓]
         │
    ┌────▼──────────────────┐
    │  EmailAction           │
    │  - recipient_id        │
    │  - subject             │
    │  - body                │
    │  - send_real: bool     │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │  APEXEnv._process_    │
    │  email_action()        │
    └────┬──────────────────┘
         │
         ├─→ Create email record (always)
         │
         └─→ If send_real=true & configured:
             └─→ email_manager.send_email()
                 └─→ Provider (Gmail/Outlook/SMTP)
                     └─→ 📧 Real email sent!
```

### Simulation Mode (Default)
- Emails recorded in `state.emails_sent`
- Reward calculated based on action quality
- No external dependencies needed
- Perfect for testing without credentials

### Real Email Mode
- Same as simulation + actual email delivery
- Set `send_real=true` in the EmailAction
- Requires valid email credentials in `.env`
- Emails appear in recipient's inbox immediately

---

## Contact Mapping

Map agent contact IDs to real email addresses:

### In `.env`:
```
CONTACT_1_EMAIL=john@company.com
CONTACT_1_NAME=John Smith
CONTACT_2_EMAIL=alice@company.com
CONTACT_2_NAME=Alice Johnson
```

### Programmatically:
```python
from apex_env.email_provider import email_manager

email_manager.add_contact(1, "john@company.com", "John Smith")
email_manager.add_contact(2, "alice@company.com", "Alice Johnson")
```

### Resolution
When you send to `recipient_id=1`:
1. `email_manager.resolve_email(1)` → "john@company.com"
2. Email sent to "john@company.com"

---

## API Usage

### Example 1: Simulated Email (Default)
```bash
curl -X POST http://localhost:8000/actions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "email",
    "recipient_id": 1,
    "subject": "Status Update",
    "body": "Project is on track",
    "language": "EN",
    "send_real": false
  }'
```

Response:
```json
{
  "success": true,
  "reward": {"total_reward": 0.32},
  "details": {
    "recipient": "Contact 1",
    "subject": "Status Update",
    "mode": "simulated",
    "real_email_sent": false
  }
}
```

### Example 2: Real Email (With Valid Credentials)
```bash
curl -X POST http://localhost:8000/actions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "email",
    "recipient_id": 1,
    "subject": "Status Update",
    "body": "Project is on track",
    "language": "EN",
    "send_real": true
  }'
```

Response (if credentials configured):
```json
{
  "success": true,
  "reward": {"total_reward": 0.32},
  "details": {
    "recipient": "john@company.com",
    "subject": "Status Update",
    "mode": "real",
    "real_email_sent": true
  }
}
```

---

## Frontend UI

### Email Tab

The dashboard includes a new checkbox for real email control:

```
📧 Email Tab
├── Recipient ID: [1]
├── Subject: [Meeting Tomorrow]
├── Body: [Let's discuss...]
├── Language: [English ▼]
├── Location: [Office]
│
├── ☐ ⚡ Send Real Email (if configured)   ← NEW!
│
└── [Send Email ✉️]
```

**Usage:**
1. Check "⚡ Send Real Email" to enable real delivery
2. Fill in the form
3. Click "Send Email"
4. Success message shows `⚡ REAL Email sent!` (if configured) or `📧 SIMULATED Email sent!`

---

## Troubleshooting

### Issue: "Email simulation mode (provider not configured)"

**Cause:** No `.env` file or provider not set

**Solution:**
1. Create `.env` from `.env.example`
2. Fill in provider credentials
3. Restart server
4. Check logs for initialization message

### Issue: Gmail app password keeps failing

**Cause:** 
- Using regular password instead of app password
- App password is incorrect or expired
- 2FA not enabled

**Solution:**
1. Go to [Google App Passwords](https://support.google.com/accounts/answer/185833)
2. Ensure 2FA is enabled first
3. Generate NEW app password (16 characters)
4. Remove spaces from password
5. Restart server

### Issue: "Failed to send real email" in logs

**Cause:**
- Invalid recipient email address
- SMTP server rejected email (spam filter, invalid sender domain)
- Network connectivity issue

**Solution:**
1. Verify recipient contact mapping: `CONTACT_N_EMAIL=valid-email@domain.com`
2. Test sending manually from configured email account
3. Check SMTP logs if available
4. Verify contact_id maps to valid email

### Issue: Still sending in simulation mode when I checked the box

**Cause:** 
- Email credentials not loaded (check logs at startup)
- send_real not being passed to API

**Solution:**
1. Verify `.env` file has EMAIL_PROVIDER and credentials
2. Check server startup logs for "Email Setup:" message
3. Ensure checkbox state is being captured (browser console)
4. Verify API request includes `"send_real": true`

---

## Security Best Practices

### ✅ Do:
- Store credentials in `.env` (never in code)
- Use app-specific passwords (not your main password)
- Enable 2FA on your email account
- Use environment variables in production
- Rotate app passwords periodically
- Keep `.env` in `.gitignore`

### ❌ Don't:
- Hardcode credentials in code
- Commit `.env` to version control
- Share app passwords in logs
- Use weak/reused passwords
- Enable LESS SECURE app access
- Log full request bodies with credentials

### `.env` Template (Secure)
```bash
# Store this file securely, NOT in version control
# Add to .gitignore: .env
# Permissions: chmod 600 .env

EMAIL_PROVIDER=gmail
GMAIL_EMAIL=agent@company.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # 16-char app password, no spaces
```

---

## Production Deployment

### Docker
```dockerfile
# Dockerfile already includes email_provider.py
# Pass .env as environment variables:

docker run \
  -p 8000:8000 \
  -e EMAIL_PROVIDER=gmail \
  -e GMAIL_EMAIL=agent@company.com \
  -e GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx \
  apex:latest
```

### Docker Compose
```yaml
services:
  apex:
    image: apex:latest
    ports:
      - "8000:8000"
    environment:
      EMAIL_PROVIDER: gmail
      GMAIL_EMAIL: ${GMAIL_EMAIL}
      GMAIL_APP_PASSWORD: ${GMAIL_APP_PASSWORD}
```

### Kubernetes
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: apex-email-config
type: Opaque
data:
  EMAIL_PROVIDER: Z21haWw=  # base64: gmail
  GMAIL_EMAIL: YWdlbnRAY29tcGFueS5jb20=  # base64 encoded
  GMAIL_APP_PASSWORD: eHh4eC14eHh4LXh4eHgteeHh4=  # base64 encoded
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apex
spec:
  template:
    spec:
      containers:
      - name: apex
        envFrom:
        - secretRef:
            name: apex-email-config
```

---

## Advanced Configuration

### Multiple Contact Groups

**Use case:** Different agent tasks email different groups

```python
# Production initialization script
from apex_env.email_provider import email_manager

# Sales team
email_manager.add_contact(1, "alice@company.com", "Sales Lead")
email_manager.add_contact(2, "bob@company.com", "Sales Rep")

# Engineering team  
email_manager.add_contact(10, "dev1@company.com", "Engineer 1")
email_manager.add_contact(11, "dev2@company.com", "Engineer 2")

# Exec layer
email_manager.add_contact(100, "exec@company.com", "Executive")
```

### Fallback Multiple Providers

**Use case:** Failover if primary provider is down

```python
from apex_env.email_provider import EmailManager, GmailProvider, SMTPProvider

manager = EmailManager()

# Try Gmail first
try:
    manager.setup_gmail("agent@company.com", os.getenv("GMAIL_APP_PASSWORD"))
except Exception:
    # Fallback to custom SMTP
    manager.setup_smtp(
        "smtp.company.com", 587,
        "agent@company.com", os.getenv("SMTP_PASSWORD")
    )
```

### Batch Email Operations

```python
# Send to multiple recipients
recipients = [1, 2, 3]  # contact IDs

for recipient_id in recipients:
    action = EmailAction(
        recipient_id=recipient_id,
        subject="Batch email",
        body="Sample",
        send_real=True
    )
    # Step environment with action
    env.step(action)
```

---

## Testing

### Unit Test
```python
from apex_env.email_provider import EmailManager, GmailProvider

def test_gmail_provider():
    provider = GmailProvider("test@gmail.com", "xxxx-xxxx-xxxx-xxxx")
    success = provider.send_email(
        "recipient@example.com",
        "Test Subject",
        "Test Body"
    )
    assert success is True

# Run: pytest test_email.py
```

### Integration Test
```python
from apex_env.environment import APEXEnv
from apex_env.models import EmailAction, LanguageEnum

def test_real_email_action():
    env = APEXEnv()
    env.reset()
    
    action = EmailAction(
        recipient_id=1,
        subject="Test",
        body="Test email from APEX",
        language=LanguageEnum.EN,
        send_real=True
    )
    
    obs, reward, done, truncated, info = env.step(action)
    
    # Verify reward was calculated
    assert reward.total_reward > 0
    # Verify email record was created
    assert len(env.state.emails_sent) > 0
```

---

## API Reference

### `EmailAction` Schema
```python
{
    "action_type": "email",                # Required
    "recipient_id": 1,                     # Required: 0-10000
    "subject": "string",                   # Required: 1-200 chars
    "body": "string",                      # Required: 1-5000 chars
    "language": "EN|ES|FR|DE|ZH|JA|RU",   # Optional: default EN
    "location": "string",                  # Optional: max 100 chars
    "send_real": false,                    # Optional: default false
    "cc_ids": [1, 2],                      # Optional: additional recipients
    "bcc_ids": [3, 4],                     # Optional: hidden recipients
    "priority": "LOW|MEDIUM|HIGH"          # Optional: default MEDIUM
}
```

### Response
```json
{
  "success": true,
  "reward": {
    "total_reward": 0.32,
    "components": {
      "action_success": 0.25,
      "task_progress": 0.20,
      "...": "..."
    }
  },
  "details": {
    "recipient": "john@company.com",
    "subject": "Test",
    "mode": "real|simulated",
    "real_email_sent": true
  }
}
```

---

## Support & FAQ

**Q: Can I use this without email credentials?**
A: Yes! Simulation mode works without any credentials. Only check "Send Real Email" when you have credentials configured.

**Q: What happens to emails in simulation mode?**
A: They're recorded in `env.state.emails_sent` but never actually sent to anyone.

**Q: Can I switch between providers?**
A: Yes, update `EMAIL_PROVIDER` in `.env` and restart. Only one provider can be active at a time.

**Q: Why do I need app passwords instead of my real password?**
A: App passwords are more secure. They can only access email, not your entire account. They're also easier to revoke.

**Q: Can I send to external domains?**
A: Yes, as long as you map the contact ID to an email address in `.env` or programmatically.

**Q: Is there a rate limit?**
A: SMTP providers typically allow 1-50 emails per second. APEX has no built-in rate limiting.

**Q: What about email templates?**
A: Build them in the action's `body` field. You can include HTML/CSS markup if the provider supports it.

---

## Changelog

### v1.0.0 (Current)
- ✅ Gmail SMTP support
- ✅ Outlook SMTP support  
- ✅ Generic SMTP support
- ✅ Contact ID mapping
- ✅ Environment variable configuration
- ✅ Frontend checkbox toggle
- ✅ Backward compatible with simulation mode
- ✅ Comprehensive error handling

### Future Roadmap
- 📋 Email templates with Jinja2
- 📎 File attachments support
- 🔄 Retry logic for failed sends
- 📊 Email delivery tracking
- 🔗 Webhook integration
- 📅 Scheduled email sending

---

**Last Updated:** 2024
**Status:** Production Ready ✅
