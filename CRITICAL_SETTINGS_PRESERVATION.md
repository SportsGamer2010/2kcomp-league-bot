# Critical Settings Preservation Guide

## 🚨 IMPORTANT: Do Not Modify These Settings

This document preserves all critical settings and configurations that have been tested and verified to work correctly. **DO NOT CHANGE** these settings without thorough testing.

---

## 📋 **Discord.py Embed Footer Compatibility**

### ✅ **CORRECT Syntax (Use This)**
```python
# Create embed without footer parameter
embed = discord.Embed(
    title="Title",
    description="Description", 
    color=0xFFD700
)
# Set footer using method
embed.set_footer(text="Footer text")
```

### ❌ **INCORRECT Syntax (Do NOT Use)**
```python
# This will cause errors in newer Discord.py versions
embed = discord.Embed(
    title="Title",
    description="Description",
    color=0xFFD700,
    footer={"text": "Footer text"}  # ❌ DEPRECATED
)
```

### 📁 **Files That Use Correct Syntax:**
- `cogs/milestones.py` - ✅ Fixed
- `cogs/history.py` - ✅ Fixed  
- `cogs/player.py` - ✅ Uses `embed.set_footer()`
- `cogs/records.py` - ✅ Uses `embed.set_footer()`
- `cogs/status.py` - ✅ Uses `embed.set_footer()`
- `cogs/admin.py` - ✅ Uses `embed.set_footer()`
- `cogs/notifications.py` - ✅ Uses `embed.set_footer()`
- `core/leaders.py` - ✅ Fixed (removed footer from embed dict)
- `core/records.py` - ✅ Fixed (removed footer from embed dict)
- `core/milestones.py` - ✅ Fixed (removed footer from embed dict)

---

## 🔧 **HTTP Client Management**

### ✅ **CORRECT Pattern (Use This)**
```python
# In command methods, use the bot's shared HTTP client
http_client = getattr(self.bot, 'http_client', None)
if not http_client:
    await interaction.followup.send("❌ HTTP client not available. Please try again later.", ephemeral=True)
    return
```

### ❌ **INCORRECT Pattern (Do NOT Use)**
```python
# Do NOT create individual HTTP clients in commands
session = await create_http_session()
http_client = HTTPClient(session)
# This causes session management issues
```

### 📁 **Files Using Correct Pattern:**
- `cogs/player.py` - ✅ Uses shared HTTP client
- `cogs/milestones.py` - ✅ Uses shared HTTP client
- `cogs/status.py` - ✅ Uses shared HTTP client
- `cogs/records.py` - ✅ Uses shared HTTP client

---

## ⏱️ **Discord Interaction Timeout Handling**

### ✅ **CORRECT Pattern (Use This)**
```python
@app_commands.command(name="command_name")
async def command_name(self, interaction: discord.Interaction):
    try:
        await interaction.response.defer()
    except discord.NotFound:
        # Interaction already expired, can't respond
        logger.warning(f"Command interaction expired for user {interaction.user}")
        return
    except Exception as e:
        logger.error(f"Error deferring command: {e}")
        return
    
    try:
        # Command logic here
        pass
    except Exception as e:
        logger.error(f"Error in command: {e}")
        try:
            await interaction.followup.send("❌ An error occurred. Please try again later.", ephemeral=True)
        except:
            pass
```

### 📁 **Files Using Correct Pattern:**
- `cogs/player.py` - ✅ Has timeout handling
- `cogs/milestones.py` - ✅ Has timeout handling
- `cogs/status.py` - ✅ Has timeout handling
- `cogs/records.py` - ✅ Has timeout handling
- `cogs/admin.py` - ✅ Has timeout handling

---

## 📊 **All Time Statistics List Configuration**

### ✅ **CORRECT Configuration**
```python
# Use hardcoded ID for All Time Statistics list
list_url = f"{settings.SPORTSPRESS_BASE}/lists/2347"
```

### 📁 **Files Using Correct Configuration:**
- `cogs/player.py` - ✅ Uses ID 2347
- `cogs/milestones.py` - ✅ Uses ID 2347
- `core/leaders.py` - ✅ Uses ID 2347

---

## 🎯 **Player Data Processing**

### ✅ **CORRECT Data Structure Handling**
```python
# Process All Time Statistics data (dict format)
if isinstance(data, dict):
    for player_id_key, player_data_dict in data.items():
        if player_id_key == "0":  # Skip header
            continue
        
        if isinstance(player_data_dict, dict):
            player_stats = {
                "player_id": int(player_id_key),
                "player_name": str(player_data_dict.get("name", f"Player {player_id_key}")),
                "stats": {
                    "points": float(player_data_dict.get("pts", 0)),
                    "assists": float(player_data_dict.get("ast", 0)),
                    "rebounds": float(player_data_dict.get("rebtwo", 0)),
                    "steals": float(player_data_dict.get("stl", 0)),
                    "blocks": float(player_data_dict.get("blk", 0)),
                    "threes_made": float(player_data_dict.get("threepm", 0)),
                    "games_played": int(player_data_dict.get("g", 0)),
                    # ... other stats
                }
            }
```

---

## 🔍 **Player Lookup Logic**

### ✅ **CORRECT Player Search Pattern**
```python
# Step 1: Find player by name
search_url = f"{settings.SPORTSPRESS_BASE}/players?search={player_name}&per_page=50"
players = await http_client.get_json(search_url)

# Step 2: Find exact match first, then partial match
player_data = None
for player in players:
    title = player.get("title", {}).get("rendered", "")
    if title.lower() == player_name.lower():
        player_data = player
        break

if not player_data:
    # Find partial match
    for player in players:
        title = player.get("title", {}).get("rendered", "")
        if player_name.lower() in title.lower():
            player_data = player
            break

# Step 3: Get player ID and search in all-time stats
player_id = player_data.get("id")
```

---

## 🏆 **Milestones Data Processing**

### ✅ **CORRECT Milestones Logic**
```python
# Get all-time stats and process for milestones
all_time_stats = await self._get_all_time_stats(http_client)

# Group by stat category and get top 5
milestones = {}
for stat_key, stat_display in stat_categories:
    # Sort players by this stat (descending)
    sorted_players = sorted(
        all_time_stats, 
        key=lambda x: x.get("stats", {}).get(stat_key, 0), 
        reverse=True
    )
    
    # Get top 5
    top_5 = sorted_players[:5]
    milestones[stat_key] = top_5
```

---

## 🚫 **Common Issues to Avoid**

### 1. **Embed Footer Issues**
- ❌ Never use `footer={"text": "..."}` in Embed constructor
- ✅ Always use `embed.set_footer(text="...")`

### 2. **HTTP Client Issues**
- ❌ Never create individual HTTP clients in commands
- ✅ Always use the bot's shared `http_client`

### 3. **Interaction Timeout Issues**
- ❌ Never call `await interaction.response.defer()` without try/catch
- ✅ Always wrap in `try/except discord.NotFound`

### 4. **Data Structure Issues**
- ❌ Never assume data format without checking `isinstance()`
- ✅ Always check data type before processing

### 5. **Player Lookup Issues**
- ❌ Never search all-time stats without finding player ID first
- ✅ Always search players API first, then match by ID

---

## 🔄 **Testing Checklist**

Before making any changes, verify:

1. ✅ `/milestones` command works without errors
2. ✅ `/player` command shows correct stats (not all zeros)
3. ✅ `/records` command displays properly
4. ✅ `/leaders` command functions correctly
5. ✅ No "Embed.__init__() got an unexpected keyword argument 'footer'" errors
6. ✅ No "Unknown interaction" errors
7. ✅ No "HTTP client not available" errors

---

## 📝 **Last Verified Working State**

- **Date**: September 2, 2025
- **Status**: All commands working correctly
- **Key Fixes Applied**:
  - Fixed Discord.py embed footer compatibility
  - Fixed HTTP client management
  - Fixed interaction timeout handling
  - Fixed player data processing
  - Fixed milestones data display

---

## ⚠️ **WARNING**

**DO NOT MODIFY** the following files without thorough testing:
- `cogs/milestones.py`
- `cogs/player.py`
- `cogs/status.py`
- `cogs/records.py`
- `cogs/admin.py`
- `core/leaders.py`
- `core/records.py`
- `core/milestones.py`

These files contain critical working configurations that have been tested and verified.

---

*This document should be updated whenever critical settings are changed or new issues are discovered.*
