# Records Command Configuration - PRESERVE THIS STATE

## ⚠️ CRITICAL: Do Not Modify Without Preserving These Features

The `/records` command is currently working correctly and must be preserved exactly as-is. Any future modifications must maintain ALL of these features:

### ✅ Current Working Features (DO NOT BREAK):

1. **Clickable Player Names**: All player names are clickable hyperlinks to their SportsPress player profiles
   - Format: `[Player Name](https://2kcompleague.com/player/player-slug/)`
   - Example: `[CaitlinClark-](https://2kcompleague.com/player/caitlinclark/)`

2. **Clickable Game Links**: All records have "View Game" links to the actual game events
   - Format: `[View Game](https://2kcompleague.com/event/game-slug/)`
   - Links drive traffic to 2kcompleague.com

3. **Real Player Names**: Records show actual player names, not IDs
   - ✅ Shows: "CaitlinClark-", "DasalezTVYT", "Spamuel"
   - ❌ Never shows: "Player 4222", "Player None"

4. **Real Team Names**: Records show actual team names, not IDs
   - ✅ Shows: "Dream Chasers vs 2kLife", "Semi Automatic vs The Collective"
   - ❌ Never shows: "Team 4217 vs Team 4306", "Team None vs Team None"

5. **Complete Stat Coverage**: All stat types are included and working
   - 🏀 Points
   - 📊 Rebounds  
   - 🎯 Assists
   - 🦹 Steals
   - 🛡️ Blocks
   - 🎯 3-Pointers Made
   - 🎯 3P%

6. **FG% Exclusion**: Field Goal Percentage is excluded from records list
   - This was specifically requested by the user

7. **Incomplete Data Handling**: Records with missing data are still shown
   - Marked with "⚠️ *Data incomplete*" warning
   - Still displays the record value and game information

8. **Historical Data Search**: Fetches from ALL historical events
   - Searches up to 50 pages of historical data
   - Ensures all-time records are found, not just recent ones

9. **Smart Name Resolution**: Handles various data formats
   - Extracts IDs from "Player XXXX" strings when needed
   - Resolves team IDs from "Team XXXX vs Team YYYY" strings
   - Falls back gracefully when data is incomplete

10. **Proper URL Construction**: Game URLs are correctly built and displayed
    - Uses the actual game event URLs from SportsPress
    - All records have clickable game links

### 🔧 Key Files That Must Be Preserved:

- `core/records.py` - Main records logic
- `core/names.py` - Name resolution with player URL support
- `core/types.py` - Data structures with player_url field
- `cogs/records.py` - Records command implementation

### 📊 Current Working Output Example:

```
🏆 Single-Game Records
All-time single-game records in 2KCompLeague

🏀 Points
63.0pts by [CaitlinClark-](https://2kcompleague.com/player/caitlinclark/)
Game: Dream Chasers vs 2kLife
Date: 2024-12-05
[View Game](https://2kcompleague.com/event/game-slug/)

📊 Rebounds
33.0reb by [Cnashty23](https://2kcompleague.com/player/cnashty23/)
Game: Semi Automatic vs The Collective
Date: 2025-04-10
[View Game](https://2kcompleague.com/event/game-slug/)

🎯 Assists
38.0ast by [CaitlinClark-](https://2kcompleague.com/player/caitlinclark/)
Game: Bad Boyz Elite vs Dream Chasers
Date: 2025-03-10
[View Game](https://2kcompleague.com/event/game-slug/)

🦹 Steals
13.0stl by [Spamuel](https://2kcompleague.com/player/spamuel/)
Game: Bankruptcy vs Forever Legendary
Date: 2025-03-21
[View Game](https://2kcompleague.com/event/game-slug/)

🛡️ Blocks
7.0blk by [DasalezTVYT](https://2kcompleague.com/player/dasaleztvyt/)
Game: Death Valley Darksyde vs Trench University
Date: 2023-11-17
[View Game](https://2kcompleague.com/event/game-slug/)

🎯 3-Pointers Made
17.03PM by [CaitlinClark-](https://2kcompleague.com/player/caitlinclark/)
Game: Dream Chasers vs 2kLife
Date: 2024-12-05
[View Game](https://2kcompleague.com/event/game-slug/)
```

### ⚠️ WARNING:

**DO NOT MODIFY** the records functionality without:
1. Testing that ALL player names remain clickable
2. Verifying ALL game links still work
3. Confirming real names are still displayed (not IDs)
4. Ensuring all stat types are still included
5. Checking that FG% remains excluded
6. Validating that incomplete data is still handled properly

### 🎯 Business Impact:

This configuration drives maximum traffic to 2kcompleague.com through:
- Clickable player names → Player profile pages
- Clickable game links → Game event pages
- Professional presentation → User engagement
- Complete data coverage → User trust

**PRESERVE THIS EXACT CONFIGURATION AT ALL COSTS**
