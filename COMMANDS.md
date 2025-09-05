# 2KCompLeague Discord Bot - Commands Reference

## 🎮 User Commands

### `/help`

**Description**: Display help information and available commands  
**Usage**: `/help`  
**Access**: All users  
**Features**: Shows all available commands with descriptions

### `/records`

**Description**: View all-time single-game records  
**Usage**: `/records`  
**Features**:
- Shows top single-game performances across all seasons
- Clickable player names linking to profiles
- Game links for each record
- Real player names and team names
- Excludes field goal percentage for cleaner display

### `/milestones`

**Description**: View top 5 players in each statistical category  
**Usage**: `/milestones`  
**Features**:
- Career totals from All Time Statistics
- Clickable player names
- Covers all major stat categories
- Fast performance using single API call

### `/leaders`

**Description**: View season or career leaders  
**Usage**: `/leaders type:<season|career> stat:<optional>`  
**Parameters**:
- `type`: "Season" or "Career"
- `stat`: Optional specific stat (Points, Assists, Rebounds, Steals, Blocks, 3-Pointers Made)
**Features**:
- Season leaders from current season
- Career leaders from All Time Statistics
- Filterable by specific statistics
- Top 3 performers per category

### `/player <player_name>`

**Description**: View individual player statistics and rankings  
**Usage**: `/player <player_name>`  
**Example**: `/player JT5_Era`  
**Features**:
- Real career statistics from All Time Statistics
- Player rankings among all players
- Clickable profile links
- Per-game averages
- Games played and career totals

### `/history`

**Description**: View league championship history and season breakdown  
**Usage**: `/history`  
**Features**:
- Championship hierarchy by title count
- Season-by-season breakdown
- Team championship history
- Upcoming season information

### `/scorers`

**Description**: View leading scorers for each season  
**Usage**: `/scorers`  
**Features**:
- Season-by-season leading scorers
- Team names and total points
- Clickable player profile links
- Links to season stat lists
- Summary statistics

## 🔧 Admin Commands

### `/admin welcome`

**Description**: Manually trigger welcome message  
**Usage**: `/admin welcome`  
**Access**: Admin role only  
**Features**:
- Sends welcome message to random channel
- Includes countdown to NBA2K26 Season 1
- Registration reminder for 2kcompleague.com/register

### `/admin announce <message> <ping>`

**Description**: Send announcement to announce channel  
**Usage**: `/admin announce message:<text> ping:<true|false>`  
**Access**: Admin role only  
**Parameters**:
- `message`: The announcement text
- `ping`: Whether to ping @everyone (default: false)

### `/admin status`

**Description**: Check bot status and configuration  
**Usage**: `/admin status`  
**Access**: Admin role only  
**Features**:
- Bot uptime and connection status
- Channel configuration status
- System health information

### `/admin sync`

**Description**: Manually sync slash commands with Discord  
**Usage**: `/admin sync`  
**Access**: Admin role only  
**Features**:
- Forces command synchronization
- Useful for troubleshooting command issues

### `/notifications <action> <message>`

**Description**: Manage notification system  
**Usage**: `/notifications action:<status|test|weekly|manual> message:<optional>`  
**Access**: Admin role only  
**Actions**:
- `status`: Show notification system status and configuration
- `test`: Send test notification to verify system
- `weekly`: Manually send weekly summary
- `manual`: Send custom alert with optional message
