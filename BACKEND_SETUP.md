# APEX Backend Setup & Configuration Guide

## ✅ Everything Installed & Ready

All required Python dependencies are installed and the backend API server is running!

---

## 📋 Quick Start - Using Without Frontend

### Start the Server
```bash
cd d:\APEX
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

Or with environment variables:
```bash
set GMAIL_EMAIL=your-email@gmail.com
set GMAIL_APP_PASSWORD=your-app-password
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### API Endpoints Available

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/send-otp` | POST | Send OTP via email |
| `/api/verify-otp` | POST | Verify OTP & login |
| `/api/process` | POST | Process messages (route to features) |
| `/api/logout` | POST | End session |

---

## ⚙️ Features & Configuration

### 1️⃣ **Email (Gmail) - ✅ ENABLED**

**Status**: Currently working with your credentials

**Configuration**:
- Create `.env` file in `d:\APEX` with:
```env
GMAIL_EMAIL=unnathikrishna9@gmail.com
GMAIL_APP_PASSWORD=emxj zcji nsmj gmkw
```

**How it works**:
- OTP verification codes sent via Gmail
- Emails are real and instant

---

### 2️⃣ **WhatsApp - 🔧 Needs Setup**

**What's Needed**:
1. WhatsApp Business Account (https://www.whatsapp.com/business/)
2. Get Business Account Phone Number
3. Get API Access Token and Phone ID

**Setup Instructions**:
1. Go to https://developers.facebook.com/
2. Create/Login to your app
3. Add WhatsApp Product
4. Get your **Phone Number ID** and **Access Token**
5. Create `secrets/whatsapp.json`:
```json
{
  "business_phone_id": "YOUR_PHONE_ID",
  "access_token": "YOUR_ACCESS_TOKEN",
  "business_account_id": "YOUR_BUSINESS_ACCOUNT_ID"
}
```

**Test it**:
```powershell
$body = @{
  message = "send hello to +919876543210"
  feature = "whatsapp"
  user = "your@email.com"
  token = $token
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/process" `
  -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
```

---

### 3️⃣ **SMS (Twilio) - 🔧 Optional**

**What's Needed**:
1. Twilio Account (https://www.twilio.com/)
2. Twilio Phone Number
3. Account SID & Auth Token

**Setup Instructions**:
```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

### 4️⃣ **AI Features (Search, Code, Summarize) - 🔧 Optional**

**Web Search**:
- Using Google Custom Search (built-in)
- Or Bing Search (built-in)

**Code Generation** (Optional - with AI):
```env
OPENAI_API_KEY=sk-your-api-key
```

**Summarization** (Optional - with AI):
```env
OPENAI_API_KEY=sk-your-api-key
```

---

## 🚀 Real Use Cases - Code Examples

### 1. Send Email Verification

```powershell
$body = @{
    phone = "+919876543210"
    email = "your@email.com"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/send-otp" `
    -Method POST -ContentType "application/json" -Body $body -UseBasicParsing

$data = $response.Content | ConvertFrom-Json
Write-Host "Verification code sent to: $($data.message)"
```

### 2. Login & Get Session Token

```powershell
$body = @{
    request_id = $data.request_id
    phone = "+919876543210"
    email = "your@email.com"
    otp = $data.demo_otp
    verification_code = $data.demo_code
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/verify-otp" `
    -Method POST -ContentType "application/json" -Body $body -UseBasicParsing

$result = $response.Content | ConvertFrom-Json
$token = $result.token
Write-Host "Session token: $token"
```

### 3. Send WhatsApp Message

```powershell
$body = @{
    message = "send 'Hello World' to +919876543210"
    feature = "whatsapp"
    user = "your@email.com"
    phone = "+919876543210"
    token = $token
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/process" `
    -Method POST -ContentType "application/json" -Body $body -UseBasicParsing

$result = $response.Content | ConvertFrom-Json
Write-Host "Message status: $($result.result.message)"
```

### 4. Search Online

```powershell
$body = @{
    message = "search for python machine learning tutorials"
    feature = "all"  # Auto-detects "search"
    user = "your@email.com"
    phone = "+919876543210"
    token = $token
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/process" `
    -Method POST -ContentType "application/json" -Body $body -UseBasicParsing

$result = $response.Content | ConvertFrom-Json
Write-Host "Found: $($result.result.data.results.Count) results"
```

### 5. Generate Code

```powershell
$body = @{
    message = "write python code to sort a list"
    feature = "code"
    user = "your@email.com"
    phone = "+919876543210"
    token = $token
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/process" `
    -Method POST -ContentType "application/json" -Body $body -UseBasicParsing

$result = $response.Content | ConvertFrom-Json
Write-Host "Generated code: $($result.result.data.code)"
```

---

## 📦 All Installed Packages

```
✓ FastAPI - REST API framework
✓ Uvicorn - ASGI server
✓ Pydantic - Data validation
✓ Requests - HTTP library
✓ Cryptography - Encryption
✓ python-dotenv - Environment variables
✓ PyYAML - Configuration files
✓ Streamlit - (Optional UI)
✓ Pandas - Data processing
✓ OpenAI - (Optional AI features)
```

---

## 🔒Security Features Enabled

✅ **OTP-Based Authentication** - No passwords needed
✅ **AES-128 Encryption** - Fernet encryption for sensitive data
✅ **PBKDF2 Hashing** - Secure password hashing
✅ **Session Management** - 24-hour JWT sessions
✅ **Rate Limiting** - Configurable throttling (currently disabled for demo)
✅ **CORS Protection** - Cross-origin request handling

---

## ✨ What's Working Right Now

- ✅ Email OTP verification (Gmail)
- ✅ Secure login with sessions
- ✅ Web search functionality
- ✅ Code generation (basic)
- ✅ Text summarization
- ✅ Error analysis
- ✅ Command execution (with restrictions)
- ⚠️ WhatsApp (needs credentials)
- ⚠️ SMS (needs Twilio setup)

---

## 🎯 Next Steps

### Option 1: Use Without WhatsApp/SMS
Email + Web features work out of the box. Start building!

### Option 2: Add WhatsApp
Follow the WhatsApp setup section above to enable real messaging.

### Option 3: Add OpenAI
Set `OPENAI_API_KEY` in `.env` to enable AI code generation and summarization.

---

## 📞 API Documentation

Full API docs available at:
```
http://localhost:8000/docs
```

---

## 🆘 Troubleshooting

**Email not sending?**
- Check `.env` file has correct Gmail credentials
- Verify Gmail app password is correct (not regular password)
- Check spam folder

**WhatsApp not working?**
- Verify `secrets/whatsapp.json` exists with correct credentials
- Test credentials on Facebook Developer dashboard

**Server not starting?**
- Check port 8000 is not in use
- Verify all dependencies installed: `python -m pip list | grep -i apex`

---

## 💡 Examples Working Now

Run PowerShell commands to test features directly without frontend!

**Status**: ✅ System Ready - All core features enabled!
