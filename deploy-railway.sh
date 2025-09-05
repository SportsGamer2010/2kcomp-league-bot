#!/bin/bash

# Railway Deployment Script for 2KCompLeague Discord Bot
# This script helps you deploy your bot to Railway

echo "🚀 2KCompLeague Discord Bot - Railway Deployment"
echo "================================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git not initialized. Please run:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Check if remote origin exists
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "❌ No GitHub remote found. Please add your GitHub repository:"
    echo "   git remote add origin https://github.com/yourusername/2kcomp-league-bot.git"
    echo "   git push -u origin main"
    exit 1
fi

# Check if all required files exist
echo "🔍 Checking required files..."

required_files=("Dockerfile" "requirements.txt" "railway.json" "env.example")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

echo "✅ All required files found"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from env.example..."
    cp env.example .env
    echo "📝 Please edit .env file with your Discord bot credentials"
    echo "   Required variables:"
    echo "   - DISCORD_TOKEN"
    echo "   - GUILD_ID"
    echo "   - ANNOUNCE_CHANNEL_ID"
    echo "   - HISTORY_CHANNEL_ID"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git add .
git commit -m "Deploy to Railway - $(date)"
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Code pushed to GitHub successfully"
else
    echo "❌ Failed to push to GitHub"
    exit 1
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Go to https://railway.app"
echo "2. Click 'Deploy from GitHub repo'"
echo "3. Select your repository"
echo "4. Add environment variables in Railway dashboard:"
echo "   - DISCORD_TOKEN"
echo "   - GUILD_ID"
echo "   - ANNOUNCE_CHANNEL_ID"
echo "   - HISTORY_CHANNEL_ID"
echo "5. Wait for deployment to complete"
echo "6. Check health endpoint: https://your-app.railway.app/health"
echo ""
echo "📚 For detailed instructions, see RAILWAY_DEPLOYMENT.md"
echo ""
echo "🎉 Happy deploying!"
