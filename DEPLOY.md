# Railway Deployment Guide

## Option 1: Deploy via Railway Web Interface (Recommended)

### Step 1: Push to GitHub
1. Create a new repository on GitHub
2. Push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app) and sign in (use GitHub to connect)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will automatically detect the Dockerfile and start building

### Step 3: Add Environment Variable
1. In your Railway project, go to **Variables** tab
2. Click **"New Variable"**
3. Add:
   - **Name**: `BOT_TOKEN`
   - **Value**: `8379957805:AAGq1tLbb-8dsbwaZ5f0-Dq46ZjXZT8X-Kc`
4. Click **"Add"**

### Step 4: Deploy
- Railway will automatically deploy when you push to GitHub
- Or click **"Deploy"** in the Railway dashboard
- The bot will start running once deployment completes

## Option 2: Deploy via Railway CLI

### Install Railway CLI
```bash
npm install -g @railway/cli
# or
brew install railway
```

### Login and Deploy
```bash
# Login to Railway
railway login

# Initialize project
railway init

# Link to existing project (or create new)
railway link

# Add environment variable
railway variables set BOT_TOKEN=8379957805:AAGq1tLbb-8dsbwaZ5f0-Dq46ZjXZT8X-Kc

# Deploy
railway up
```

## Verification

Once deployed:
1. Check the Railway logs to see if the bot started successfully
2. Test your bot on Telegram by sending `/start`
3. The bot should respond immediately

## Notes

- Railway automatically detects the `Dockerfile` and `railway.json` configuration
- The database will be stored in the Railway filesystem (persists between deployments)
- Railway provides free tier with generous limits for bots
- Your bot will restart automatically if it crashes (configured in `railway.json`)
