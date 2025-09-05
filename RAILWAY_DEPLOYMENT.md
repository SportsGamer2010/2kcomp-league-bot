# 🚀 Railway Deployment Guide

Complete guide to deploy your 2KCompLeague Discord Bot to Railway.

## 📋 Prerequisites

1. **GitHub Account** - Your code needs to be on GitHub
2. **Railway Account** - Sign up at [railway.app](https://railway.app)
3. **Discord Bot Token** - From Discord Developer Portal
4. **Discord Server IDs** - Channel IDs for your bot

## 🔧 Step 1: Prepare Your Repository

### 1.1 Push to GitHub
```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/2kcomp-league-bot.git
git push -u origin main
```

### 1.2 Verify Required Files
Make sure these files exist in your repository:
- ✅ `Dockerfile`
- ✅ `requirements.txt`
- ✅ `railway.json`
- ✅ `.railwayignore`
- ✅ `env.example`

## 🚀 Step 2: Deploy to Railway

### 2.1 Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click **"Deploy from GitHub repo"**
3. Select your repository
4. Railway will auto-detect Docker and start building

### 2.2 Configure Environment Variables
In Railway dashboard, go to **Variables** tab and add:

#### Required Variables:
```env
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_discord_guild_id
ANNOUNCE_CHANNEL_ID=your_announce_channel_id
HISTORY_CHANNEL_ID=your_history_channel_id
```

#### Optional Variables (with defaults):
```env
SPORTSPRESS_BASE=https://2kcompleague.com/wp-json/sportspress/v2
POLL_INTERVAL_SECONDS=180
RECORDS_POLL_INTERVAL_SECONDS=3600
LOG_LEVEL=INFO
STATE_PATH=/data/state.json
RECORDS_SEED_PATH=/data/records_seed.json
MIN_FGA_FOR_FG_PERCENT=10
MIN_3PA_FOR_3P_PERCENT=6
HTTP_TIMEOUT=30
HTTP_MAX_RETRIES=3
```

### 2.3 Deploy
1. Railway will automatically build and deploy
2. Check the **Deployments** tab for build progress
3. View logs in the **Logs** tab

## 🔍 Step 3: Verify Deployment

### 3.1 Check Health Endpoint
Your bot exposes a health endpoint at:
```
https://your-app-name.railway.app/health
```

### 3.2 Monitor Logs
```bash
# In Railway dashboard, go to Logs tab
# Look for these success messages:
# - "Bot logged in as YourBot#1234"
# - "Health server started at http://0.0.0.0:8080"
# - "All cogs loaded"
```

### 3.3 Test Discord Commands
1. Go to your Discord server
2. Try `/league` command
3. Check if bot responds

## 🛠️ Step 4: Troubleshooting

### Common Issues:

#### Bot Not Responding
- ✅ Check `DISCORD_TOKEN` is correct
- ✅ Verify bot has proper permissions in Discord
- ✅ Check logs for authentication errors

#### Health Check Failing
- ✅ Ensure health server is starting (check logs)
- ✅ Verify port 8080 is exposed in Dockerfile
- ✅ Check Railway health check configuration

#### Build Failures
- ✅ Verify all dependencies in `requirements.txt`
- ✅ Check Dockerfile syntax
- ✅ Ensure all files are committed to GitHub

### Debug Commands:
```bash
# Check bot status
curl https://your-app-name.railway.app/health

# Check metrics
curl https://your-app-name.railway.app/metrics

# Check performance
curl https://your-app-name.railway.app/performance
```

## 📊 Step 5: Monitoring & Maintenance

### 5.1 Railway Dashboard
- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Deployments**: Build and deployment history

### 5.2 Health Monitoring
- **Health Endpoint**: `/health` - Basic health check
- **Metrics Endpoint**: `/metrics` - Prometheus metrics
- **Performance**: `/performance` - Performance data

### 5.3 Updates
To update your bot:
1. Push changes to GitHub
2. Railway automatically redeploys
3. Monitor logs for successful deployment

## 💰 Step 6: Cost Management

### Free Tier Limits:
- **$5 credit monthly** (usually enough for small bots)
- **512MB RAM** per service
- **1GB storage**
- **Unlimited builds**

### Usage Monitoring:
- Check **Usage** tab in Railway dashboard
- Monitor credit consumption
- Upgrade to paid plan if needed

## 🔧 Step 7: Advanced Configuration

### 7.1 Custom Domain
1. Go to **Settings** → **Domains**
2. Add your custom domain
3. Configure DNS records

### 7.2 Environment-Specific Deployments
Create separate Railway projects for:
- **Development**: `dev-2kcomp-bot`
- **Staging**: `staging-2kcomp-bot`
- **Production**: `2kcomp-bot`

### 7.3 Database Integration
If you need persistent storage:
1. Add **PostgreSQL** service in Railway
2. Update environment variables
3. Modify bot code to use database

## 📚 Step 8: Useful Commands

### Railway CLI (Optional)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up

# View logs
railway logs

# Open dashboard
railway open
```

## ✅ Success Checklist

- [ ] Bot deployed to Railway
- [ ] Health endpoint responding
- [ ] Discord bot online and responding
- [ ] All environment variables configured
- [ ] Logs showing successful startup
- [ ] Commands working in Discord
- [ ] Monitoring set up

## 🆘 Support

### Railway Support:
- **Documentation**: [docs.railway.app](https://docs.railway.app)
- **Discord**: Railway Discord community
- **GitHub Issues**: Railway GitHub repository

### Bot Issues:
- Check application logs in Railway dashboard
- Verify Discord bot permissions
- Test health endpoints
- Review environment variables

---

**🎉 Congratulations! Your Discord bot is now running on Railway!**

Your bot will be available 24/7 with automatic restarts and monitoring.
