@echo off
REM Railway Deployment Script for 2KCompLeague Discord Bot
REM This script helps you deploy your bot to Railway

echo 🚀 2KCompLeague Discord Bot - Railway Deployment
echo ================================================

REM Check if git is initialized
if not exist ".git" (
    echo ❌ Git not initialized. Please run:
    echo    git init
    echo    git add .
    echo    git commit -m "Initial commit"
    pause
    exit /b 1
)

REM Check if remote origin exists
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo ❌ No GitHub remote found. Please add your GitHub repository:
    echo    git remote add origin https://github.com/yourusername/2kcomp-league-bot.git
    echo    git push -u origin main
    pause
    exit /b 1
)

REM Check if all required files exist
echo 🔍 Checking required files...

set missing_files=0

if not exist "Dockerfile" (
    echo ❌ Missing: Dockerfile
    set missing_files=1
)

if not exist "requirements.txt" (
    echo ❌ Missing: requirements.txt
    set missing_files=1
)

if not exist "railway.json" (
    echo ❌ Missing: railway.json
    set missing_files=1
)

if not exist "env.example" (
    echo ❌ Missing: env.example
    set missing_files=1
)

if %missing_files%==1 (
    echo.
    echo Please ensure all required files are present.
    pause
    exit /b 1
)

echo ✅ All required files found

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  No .env file found. Creating from env.example...
    copy env.example .env
    echo 📝 Please edit .env file with your Discord bot credentials
    echo    Required variables:
    echo    - DISCORD_TOKEN
    echo    - GUILD_ID
    echo    - ANNOUNCE_CHANNEL_ID
    echo    - HISTORY_CHANNEL_ID
    echo.
    pause
)

REM Push to GitHub
echo 📤 Pushing to GitHub...
git add .
git commit -m "Deploy to Railway - %date% %time%"
git push origin main

if errorlevel 1 (
    echo ❌ Failed to push to GitHub
    pause
    exit /b 1
)

echo ✅ Code pushed to GitHub successfully

echo.
echo 🎯 Next Steps:
echo 1. Go to https://railway.app
echo 2. Click 'Deploy from GitHub repo'
echo 3. Select your repository
echo 4. Add environment variables in Railway dashboard:
echo    - DISCORD_TOKEN
echo    - GUILD_ID
echo    - ANNOUNCE_CHANNEL_ID
echo    - HISTORY_CHANNEL_ID
echo 5. Wait for deployment to complete
echo 6. Check health endpoint: https://your-app.railway.app/health
echo.
echo 📚 For detailed instructions, see RAILWAY_DEPLOYMENT.md
echo.
echo 🎉 Happy deploying!
pause
