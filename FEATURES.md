# 2KCompLeague Discord Bot - Features Overview

## 🚀 Core Features

### 📊 Real-Time Statistics
- **All-Time Statistics Integration** - Uses the complete league database with 700+ players
- **Live Game Monitoring** - Automatically detects new games and stat events
- **Record Breaking Alerts** - Instant notifications for new single-game records
- **Milestone Tracking** - Celebrates player achievements in real-time

### 🏀 League Management
- **Season Leaders** - Current season top performers
- **Career Leaders** - All-time career statistics
- **Player Profiles** - Individual player stats and rankings
- **Team Standings** - League standings and championship history

### 🔔 Automated Notifications
- **Stat Milestones** - Automatic alerts for scoring achievements
- **Record Breakers** - Special notifications for record-breaking performances
- **Weekly Summaries** - Comprehensive league activity reports
- **Game Events** - Real-time game updates and highlights

## 🔔 Notification System

### Automatic Monitoring
- **Frequency**: Checks every 5 minutes for new games
- **Scope**: Monitors last 24 hours of games
- **Duplicate Prevention**: Tracks processed games to avoid redundant notifications
- **Error Recovery**: Robust error handling with automatic retry

### Milestone Thresholds
| Stat | Milestone Alerts | Record Alerts |
|------|------------------|---------------|
| Points | 20, 30, 40, 50, 60, 70+ | 50+ |
| Assists | 10, 15, 20, 25+ | 20+ |
| Rebounds | 10, 15, 20, 25, 30+ | 20+ |
| Steals | 5, 7, 10+ | 8+ |
| Blocks | 3, 5, 7, 10+ | 5+ |
| 3-Pointers Made | 5, 7, 10, 15+ | 10+ |

### Notification Types
1. **🎉 Milestone Alerts** - Green embeds for stat achievements
2. **🔥 Record Alerts** - Red embeds for record-breaking performances
3. **📊 Weekly Summaries** - Automatic every Sunday at 6 PM
4. **📢 Manual Alerts** - Admin-triggered custom notifications

## 🏗️ Technical Architecture

### Core Components
- **`bot.py`** - Main bot file with startup and event handling
- **`core/`** - Core functionality modules
  - `config.py` - Configuration and environment variables
  - `http.py` - HTTP client with retry logic and pagination
  - `names.py` - Player and team name resolution with caching
  - `notification_system.py` - Comprehensive notification system
  - `leaders.py` - Season and career leaders calculation
  - `sportspress.py` - SportsPress API integration
  - `types.py` - Data models and type definitions
- **`cogs/`** - Discord command modules
  - `admin.py` - Admin commands
  - `status.py` - Status and leaders commands
  - `records.py` - Records command
  - `player.py` - Player command
  - `milestones.py` - Milestones command
  - `history.py` - History and scorers commands
  - `notifications.py` - Notification management

### Data Sources
- **All Time Statistics List (ID: 2347)** - 700+ players with complete career stats
- **Events API** - Real-time game data and player performances
- **Players API** - Individual player information and profiles
- **Lists API** - Season-specific statistics and standings

### Performance Optimizations
- **Single API Calls** - Uses All Time Statistics for fast data access
- **Caching System** - Player and team name caching to reduce API calls
- **Background Tasks** - Asynchronous monitoring and processing
- **Error Handling** - Robust error recovery and logging

## 📊 Data Integration

### SportsPress API Integration
- **Base URL**: `https://2kcompleague.com/wp-json/sportspress/v2`
- **Endpoints Used**:
  - `/events` - Game events and player performances
  - `/players` - Player information and statistics
  - `/lists` - Statistical lists and standings
  - `/teams` - Team information

### Website Integration
- **Season Standings**: [NBA2k26 Season 1 Standings](https://2kcompleague.com/table/nba2k26-season-1-standings/)
- **Season Stats**: [NBA2k26 Season 1 Stats](https://2kcompleague.com/list/nba2k26-season-1-stats/)
- **All Time Records**: [All Time Statistics](https://2kcompleague.com/list/all-time-statistics/)
- **Player Profiles**: Individual player pages with career stats

## 🎯 Use Cases

### For League Administrators
- **Automated Notifications** - Keep community engaged with real-time updates
- **Record Tracking** - Monitor and celebrate league achievements
- **Player Management** - Access comprehensive player statistics
- **League Promotion** - Drive traffic to 2kcompleague.com

### For Players
- **Personal Stats** - View individual performance and rankings
- **League Leaders** - See how they compare to other players
- **Record Books** - Track all-time and season records
- **Team Information** - Access team standings and history

### For Community
- **Entertainment** - Real-time stat updates and milestone celebrations
- **Engagement** - Interactive commands and rich embeds
- **Information** - Comprehensive league data and history
- **Website Traffic** - Direct links to 2kcompleague.com
