# 2KCompLeague Discord Bot

A comprehensive Discord bot for the 2KCompLeague community, providing real-time statistics, records tracking, and league management features integrated with the SportsPress API.

## 🚀 Features

### 📊 Statistics & Records
- **Player Statistics**: Detailed player cards with rankings and career stats
- **All-Time Records**: Single-game records with clickable links to games
- **Double-Doubles & Triple-Doubles**: Achievement tracking and display
- **Season Leaders**: Current season performance leaders
- **Career Milestones**: Top performers across all categories

### 📋 League Management
- **Standings**: Current season standings with team links
- **Championship History**: Complete league championship hierarchy
- **Season Scorers**: Historical leading scorers by season
- **Game Analysis**: Recent game results and highlights

### 🗳️ Community Features
- **Polling System**: Create and manage community polls
- **Notifications**: Automated alerts for records and milestones
- **Spotlight Players**: Automatic player highlights on bot startup
- **Profile Management**: Profile picture submission system

### 🔧 Admin Tools
- **Announcements**: Send messages to designated channels
- **Command Management**: Sync and manage Discord commands
- **Health Monitoring**: Bot status and system health checks
- **Data Management**: Persistent state and record tracking

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Docker (optional)
- Discord Bot Token
- SportsPress API access

### Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/2kcomp-league-bot.git
   cd 2kcomp-league-bot
   ```

2. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your Discord and API credentials
   ```

3. **Start the bot**
   ```bash
   docker-compose up -d
   ```

4. **View logs**
   ```bash
   docker-compose logs -f
   ```

### Local Development

1. **Setup virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## 📋 Commands

### League Information
- `/league` - League overview with team links
- `/standings` - Current season standings
- `/history` - Championship history
- `/commands` - List all available commands

### Player & Statistics
- `/player <name>` - Detailed player statistics and rankings
- `/scorers` - Season-by-season leading scorers
- `/leaders` - Current season leaders
- `/milestones` - Career milestone achievements

### Records & Achievements
- `/records` - All-time single-game records
- `/doubledoubles` - Double-double achievements
- `/tripledoubles` - Triple-double achievements

### Community
- `/poll <question> <options>` - Create community polls
- `/notifications` - Notification settings and history
- `/spotlight` - Manual spotlight player trigger

### Admin (Admin Only)
- `/admin-announce <message>` - Send announcements
- `/admin-sync` - Sync Discord commands
- `/admin-status` - Bot health and status
- `/admin-clear-commands` - Clear old commands

## ⚙️ Configuration

### Required Environment Variables
```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_guild_id_here
ANNOUNCE_CHANNEL_ID=your_announce_channel_id_here
HISTORY_CHANNEL_ID=your_history_channel_id_here

# SportsPress API
SPORTSPRESS_BASE=https://2kcompleague.com/wp-json/sportspress/v2
```

### Optional Configuration
```env
# Bot Behavior
POLL_INTERVAL_SECONDS=180
RECORDS_POLL_INTERVAL_SECONDS=3600
LOG_LEVEL=INFO

# File Paths
STATE_PATH=/data/state.json
RECORDS_SEED_PATH=/data/records_seed.json
```

## 🎯 Architecture

### Core Components
- **Bot Engine**: Discord.py-based command system
- **API Integration**: SportsPress API client with caching
- **Data Management**: Persistent state and record tracking
- **Notification System**: Automated alerts and reminders
- **Health Monitoring**: System health and performance tracking

### Data Flow
1. **SportsPress API** → **Data Processing** → **Discord Commands**
2. **Game Events** → **Record Detection** → **Notifications**
3. **User Interactions** → **Command Processing** → **Response Generation**

## 📊 Monitoring

### Health Checks
- HTTP endpoint: `http://localhost:8080/health`
- Docker health check included
- Comprehensive logging system

### Metrics
- Command usage statistics
- API response times
- Error rates and patterns
- Performance optimization tracking

## 🔒 Security

- Non-root Docker user
- Environment variable configuration
- Input validation and sanitization
- Rate limiting and error handling
- Secure API communication

## 📈 Performance

- Async/await architecture
- HTTP client connection pooling
- Intelligent caching system
- Optimized database queries
- Resource usage monitoring

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov=cogs
```

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [Commands Reference](COMMANDS.md) - Detailed command documentation
- [Features Overview](FEATURES.md) - Comprehensive feature list
- [API Documentation](API.md) - SportsPress API integration details

## 🐛 Troubleshooting

### Common Issues
1. **Bot not responding**: Check Discord token and permissions
2. **API errors**: Verify SportsPress API endpoints
3. **Command not found**: Use `/admin-sync` to sync commands
4. **Timeout errors**: Check network connectivity and API status

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG docker-compose up -d
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

- **Discord.py** - Discord API wrapper
- **SportsPress** - WordPress sports management plugin
- **2KCompLeague Community** - For feedback and testing

## 📞 Support

- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Community support and discussion
- **Documentation**: Comprehensive guides and references

---

**Made with ❤️ for the 2KCompLeague community**