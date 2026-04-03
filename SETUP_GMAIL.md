# Setup Gmail for APEX Email Sending

## Step 1: Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/
2. Click "Security" on the left
3. Scroll to "How you sign in to Google"
4. Enable "2-Step Verification"

## Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Google will generate a 16-character password
4. **Copy this password** (you'll need it in next step)

## Step 3: Create Configuration File
Create a `.env` file in the `d:\APEX` folder with:

```env
# Gmail Configuration
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

Replace:
- `your-email@gmail.com` with your actual Gmail address
- `xxxx xxxx xxxx xxxx` with the 16-character password from Step 2

## Step 4: Test It Works
Run this PowerShell command:

```powershell
cd d:\APEX
$phone = "+91YOUR_PHONE"; 
$email = "your-email@gmail.com"; 
$body1 = @{phone = $phone; email = $email} | ConvertTo-Json; 
$response1 = Invoke-WebRequest -Uri "http://localhost:8000/api/send-otp" -Method POST -ContentType "application/json" -Body $body1 -UseBasicParsing; 
$data1 = $response1.Content | ConvertFrom-Json; 
Write-Host "OTP sent! Check your email at $email"
```

You should receive a verification email with the OTP!

## Troubleshooting
- **"Invalid credentials"** - Double-check the app password (not your regular password)
- **"Less secure apps blocked"** - Use app password, not regular password
- **Email not received** - Check Gmail spam folder
