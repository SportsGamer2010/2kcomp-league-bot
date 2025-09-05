# 2KCompLeague Discord Bot - Deployment Guide

## 🔧 Configuration

### Environment Variables
```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token
ADMIN_ROLE=League Admin
ANNOUNCE_CHANNEL_ID=your_announce_channel_id
HISTORY_CHANNEL_ID=your_history_channel_id

# SportsPress API Configuration
SPORTSPRESS_BASE=https://2kcompleague.com/wp-json/sportspress/v2
SEASON_ENDPOINTS=/players?league=nba2k26s1,/players?league=nba2k25s6,...
LEADERS_ENDPOINT=/players?league=nba2k26s1

# HTTP Configuration
HTTP_TIMEOUT=30
HTTP_RETRY_ATTEMPTS=3
HTTP_RETRY_DELAY=1
```

### Required Permissions

- **Discord Bot Permissions**:
  - Send Messages
  - Use Slash Commands
  - Embed Links
  - Read Message History
  - Add Reactions

## 🚀 Deployment

### Local Development

1. **Clone Repository**: `git clone <repository-url>`
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Configure Environment**: Copy `.env.example` to `.env` and fill in values
4. **Run Bot**: `python bot.py`

### Production Deployment
1. **Server Setup**: Ensure Python 3.8+ and required dependencies
2. **Environment Configuration**: Set production environment variables
3. **Process Management**: Use systemd, PM2, or similar for process management
4. **Monitoring**: Set up logging and health checks
5. **Updates**: Use deployment scripts for seamless updates

## 📞 Support

### Troubleshooting
- **Command Issues**: Use `/admin sync` to refresh commands
- **Notification Problems**: Check `/notifications status` for system health
- **Data Issues**: Verify API connectivity and configuration
- **Performance**: Monitor logs for error patterns

### Maintenance
- **Regular Updates**: Keep dependencies updated
- **Log Monitoring**: Check logs for errors and performance issues
- **API Monitoring**: Ensure SportsPress API availability
- **Backup**: Regular backup of configuration and state data

## 🔮 Future Enhancements

### Planned Features
- **Slump Detection** - Identify and notify about player performance dips
- **Team Comparisons** - Compare team statistics and matchups
- **Season Predictions** - AI-powered performance predictions
- **Custom Notifications** - User-configurable notification preferences
- **Mobile App Integration** - API endpoints for mobile applications

### Potential Integrations
- **Streaming Platforms** - Twitch/YouTube integration for live games
- **Social Media** - Automatic posting to Twitter/Instagram
- **Email Notifications** - Email alerts for important events
- **Calendar Integration** - Game schedule and reminder system