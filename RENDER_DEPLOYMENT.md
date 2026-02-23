# Deployment Guide - Flask Backend to Render

## Step 1: Push Code to GitHub

First, commit these new files to your GitHub repository:

```bash
git add requirements.txt Procfile render.yaml
git commit -m "Add Render deployment configuration"
git push origin main
```

## Step 2: Create a Render Account & Connect GitHub

1. Go to https://render.com and sign up (free account)
2. Click **New +** → **Web Service**
3. Select **Build and deploy from a Git repository**
4. Click **Connect GitHub** and authorize Render to access your GitHub account
5. Select your **CannaGrudge** repository

## Step 3: Configure the Web Service

When creating the web service, Render will auto-detect your Procfile and render.yaml. Confirm:

- **Name**: `cannagrudge-api` (or your preferred name)
- **Runtime**: Python 3.11
- **Build Command**: `pip install -r requirements.txt` (auto-filled)
- **Start Command**: `gunicorn server:app` (auto-filled)
- **Plan**: Start with Free tier (5 minutes inactivity sleep) or Starter tier ($7/mo for always-on)

## Step 4: Add Environment Variables

In Render dashboard, go to **Environment** and add these variables:

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | Your PostgreSQL connection string | From Neon or your DB provider |
| `SQUARE_ACCESS_TOKEN` | Your Square API token | From Square Developer Dashboard |
| `SQUARE_LOCATION_ID` | Your Square location ID | From Square Dashboard |
| `FIREBASE_SERVICE_ACCOUNT_KEY` | Your Firebase service account JSON | See below ↓ |
| `RESEND_API_KEY` | Your Resend API key | From Resend Dashboard |
| `RESEND_FROM_EMAIL` | From email address | e.g., `CannaGrudge <noreply@cannagrudge.com>` |
| `SQUARE_APPLICATION_ID` | Your Square app ID | From Square Developer Dashboard |

### Getting Firebase Service Account Key:
1. Go to Firebase Console → Your Project → Settings (gear icon) → Service Accounts
2. Click **Generate New Private Key**
3. Copy the entire JSON content
4. Paste it as the `FIREBASE_SERVICE_ACCOUNT_KEY` value (it's a large JSON string)

## Step 5: Deploy

Render will automatically deploy when you push to your GitHub repository. Monitor the deployment logs in the Render dashboard.

Once deployed, you'll get a URL like: **`https://cannagrudge-api.onrender.com`**

## Step 6: Update Frontend API Configuration

Update `api-config.js` with your Render URL:

```javascript
window.CG_API_BASE = 'https://cannagrudge-api.onrender.com';
```

Replace `cannagrudge-api` with whatever name you gave your Render service.

Then push to GitHub:
```bash
git add api-config.js
git commit -m "Update API base URL to Render"
git push origin main
```

## Step 7: Enable CORS for cannagrudge.com

Your nginx/server configuration at cannagrudge.com needs CORS headers to allow requests to the API:

```nginx
add_header 'Access-Control-Allow-Origin' 'https://cannagrudge.com' always;
add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
```

The Flask backend already has CORS enabled for `https://cannagrudge.com`.

## Step 8: Test the Connection

1. Open your admin dashboard: `https://cannagrudge.com/admin.html`
2. Sign in with Firebase
3. The `/api/admin/verify` request should now succeed ✓

## Troubleshooting

### Free Plan Hibernation
- The free Render plan goes to sleep after 15 minutes of inactivity
- First request wakes it up (takes 30-60 seconds)
- Upgrade to Starter ($7/mo) for always-on service

### Environment Variable Issues
- Make sure all required variables are set (no blanks)
- For Firebase key, use the entire JSON as a single string value
- Render will restart the service when you save env vars

### Database Connection Errors
- Verify `DATABASE_URL` is correct
- Check if your database allows connections from Render IPs
- Some databases need firewall rules updates

### CORS Errors
- Clear browser cache and hard refresh (Ctrl+Shift+R)
- Check that `api-config.js` points to correct Render URL
- Verify CORS headers in server.py (already configured)

---

Need help? Check Render's documentation: https://render.com/docs
