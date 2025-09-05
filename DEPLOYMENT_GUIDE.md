# 2KCompLeague Discord Bot - Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- Discord Bot Token
- Discord Guild (Server) ID
- Channel IDs for announcements

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/2kcomp-league-bot.git
cd 2kcomp-league-bot
```

### 2. Environment Setup
```bash
# Copy the example environment file
cp env.example .env

# Edit the environment file with your values
nano .env
```

### 3. Required Environment Variables
```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_guild_id_here
ANNOUNCE_CHANNEL_ID=your_announce_channel_id_here
HISTORY_CHANNEL_ID=your_history_channel_id_here

# SportsPress API
SPORTSPRESS_BASE=https://2kcompleague.com/wp-json/sportspress/v2
```

### 4. Run with Docker Compose
```bash
# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

## Production Deployment

### Using Docker Compose (Recommended)
```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Docker Build
```bash
# Build the image
docker build -t 2kcomp-league-bot .

# Run the container
docker run -d \
  --name 2kcomp-league-bot \
  --env-file .env \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  2kcomp-league-bot
```

## Environment Variables Reference

### Discord Configuration
- `DISCORD_TOKEN`: Your Discord bot token
- `GUILD_ID`: Your Discord server ID
- `ANNOUNCE_CHANNEL_ID`: Channel for announcements
- `HISTORY_CHANNEL_ID`: Channel for historical records

### SportsPress API
- `SPORTSPRESS_BASE`: Base URL for SportsPress API
- `SEASON_ENDPOINTS`: Comma-separated list of season endpoints

### Bot Behavior
- `POLL_INTERVAL_SECONDS`: How often to check for updates (default: 180)
- `RECORDS_POLL_INTERVAL_SECONDS`: How often to check records (default: 3600)

### File Paths
- `STATE_PATH`: Path to state file (default: /data/state.json)
- `RECORDS_SEED_PATH`: Path to records seed file

## Monitoring and Maintenance

### Health Checks
The bot includes health check endpoints:
- HTTP: `http://localhost:8080/health`
- Docker: Built-in health check

### Logs
```bash
# View real-time logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f discord-bot
```

### Data Persistence
- Bot state is stored in `./data/state.json`
- Records are cached in `./data/previous_records.json`
- Logs are stored in `./data/bot.log`

### Updates
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check Discord token is correct
   - Verify bot has proper permissions in Discord
   - Check logs for errors

2. **API errors**
   - Verify SportsPress API endpoints are accessible
   - Check network connectivity
   - Review API rate limits

3. **Permission errors**
   - Ensure bot has required Discord permissions
   - Check channel IDs are correct
   - Verify bot is in the correct server

### Debug Mode
```bash
# Run with debug logging
docker-compose -f docker-compose.yml up -d
docker-compose logs -f discord-bot
```

## Security Considerations

- Never commit `.env` files to version control
- Use environment variables for sensitive data
- Regularly update dependencies
- Monitor logs for suspicious activity
- Use non-root user in Docker container

## Backup and Recovery

### Backup Data
```bash
# Backup data directory
tar -czf bot-backup-$(date +%Y%m%d).tar.gz data/
```

### Restore Data
```bash
# Extract backup
tar -xzf bot-backup-YYYYMMDD.tar.gz
```

## Support

For issues and questions:
- Check the logs first
- Review this deployment guide
- Create an issue on GitHub
- Contact the development team
```

