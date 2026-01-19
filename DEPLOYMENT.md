# Antigravity Link Backend - Deployment Guide

## 🚀 Deploy to Railway.app (Recommended - Free Tier)

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub

### Step 2: Install Railway CLI (Optional but recommended)

```powershell
npm install -g @railway/cli
```

### Step 3: Deploy via GitHub (Easiest)

#### A. Push to GitHub first:

```powershell
cd "d:\Antigravity mobile\backend"

# Initialize git if not already
git init
git add .
git commit -m "Prepare for Railway deployment"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/antigravity-link-backend.git
git push -u origin main
```

#### B. Deploy on Railway:

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Python and deploy!

### Step 4: Configure Environment Variables (on Railway dashboard)

```
SECRET_KEY=your-production-secret-key-here-very-long-and-random
PORT=8000
```

### Step 5: Get Your Public URL

Railway will give you a URL like: `https://your-app.up.railway.app`

---

## 🔧 Deploy via Railway CLI (Alternative)

```powershell
cd "d:\Antigravity mobile\backend"

# Login
railway login

# Create new project
railway init

# Deploy
railway up

# Get URL
railway domain
```

---

## 📱 Update Mobile App

After deployment, update mobile app config:

**File**: `d:\Antigravity mobile\mobile\lib\config\app_config.dart`

```dart
class AppConfig {
  // Change from local IP to production URL
  static const String apiBaseUrl = 'https://your-app.up.railway.app/api/v1';
  static const String wsUrl = 'wss://your-app.up.railway.app/api/v1/ws';

  // ... rest of config
}
```

Then rebuild and reinstall mobile app!

---

## ✅ Test Deployment

```powershell
# Test health endpoint
curl https://your-app.up.railway.app/

# Test API
curl https://your-app.up.railway.app/api/v1/health
```

---

## 🎯 Next Steps After Deployment

1. Update Desktop Agent config with new WebSocket URL
2. Rebuild mobile app with production URL
3. Test from 4G/5G network
4. You can now use it from anywhere! 🌍
