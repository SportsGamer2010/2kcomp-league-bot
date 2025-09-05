# Railway Environment Variables

Add these environment variables in Railway dashboard:

## Required Discord Variables:
```env
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_discord_guild_id
ANNOUNCE_CHANNEL_ID=your_announce_channel_id
HISTORY_CHANNEL_ID=your_history_channel_id
```

## Data Path Variables (to fix permission issues):
```env
STATE_PATH=/tmp/data/state.json
RECORDS_SEED_PATH=/tmp/data/records_seed.json
```

## Optional Variables:
```env
SPORTSPRESS_BASE=https://2kcompleague.com/wp-json/sportspress/v2
POLL_INTERVAL_SECONDS=180
RECORDS_POLL_INTERVAL_SECONDS=3600
LOG_LEVEL=INFO
MIN_FGA_FOR_FG_PERCENT=10
MIN_3PA_FOR_3P_PERCENT=6
HTTP_TIMEOUT=30
HTTP_MAX_RETRIES=3
```

## How to Add in Railway:
1. Go to Railway dashboard
2. Click on your service
3. Go to "Variables" tab
4. Click "New Variable"
5. Add each variable one by one
6. Save and redeploy
