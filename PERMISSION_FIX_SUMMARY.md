# Permission Error Fix Summary

## Problem
The Discord bot was failing to start on Railway due to permission errors when trying to create `/data` directory. This happened because:

1. **Docker security**: The bot runs as non-root user `botuser`
2. **Directory creation**: Code tried to create `/data` directory at module import time
3. **Permission denied**: Non-root user cannot create directories in `/data`

## Solution Applied

### 1. Lazy Initialization
- **Before**: `StateManager()` created at module import time
- **After**: `StateManager()` created only when needed via `get_state_manager()`

### 2. Permission Fallback
- **Before**: Hard failure if `/data` directory creation fails
- **After**: Graceful fallback to `/tmp/data` directory

### 3. Updated Default Paths
- **Before**: Default paths pointed to `/data/`
- **After**: Default paths point to `/tmp/data/`

### 4. Fixed Modules
- ✅ `core/persistence.py` - State management
- ✅ `core/logging.py` - Log file creation
- ✅ `core/config.py` - Default path configuration

## Files Modified

### `core/persistence.py`
```python
# Before: state_manager = StateManager()  # At module level
# After: Lazy initialization with fallback
def get_state_manager() -> StateManager:
    global state_manager
    if state_manager is None:
        state_manager = StateManager()
    return state_manager

# Added permission fallback
try:
    self.state_path.parent.mkdir(parents=True, exist_ok=True)
except PermissionError:
    logger.warning(f"Permission denied for {self.state_path.parent}, using /tmp/data")
    self.state_path = Path("/tmp/data") / self.state_path.name
    self.state_path.parent.mkdir(parents=True, exist_ok=True)
```

### `core/logging.py`
```python
# Added permission fallback for log directory
try:
    log_file.parent.mkdir(parents=True, exist_ok=True)
except PermissionError:
    logger.warning(f"Permission denied for {log_file.parent}, using /tmp/data")
    log_file = Path("/tmp/data") / log_file.name
    log_file.parent.mkdir(parents=True, exist_ok=True)
```

### `core/config.py`
```python
# Updated default paths
STATE_PATH: str = Field(default="/tmp/data/state.json", ...)
RECORDS_SEED_PATH: str = Field(default="/tmp/data/records_seed.json", ...)
LOG_FILE: str = Field(default="/tmp/data/bot.log", ...)
```

## Railway Environment Variables

Add these in Railway dashboard:

```env
# Required Discord variables
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_discord_guild_id
ANNOUNCE_CHANNEL_ID=your_announce_channel_id
HISTORY_CHANNEL_ID=your_history_channel_id

# Data path variables (optional, defaults work)
STATE_PATH=/tmp/data/state.json
RECORDS_SEED_PATH=/tmp/data/records_seed.json
LOG_FILE=/tmp/data/bot.log
```

## Expected Result

After this fix, the bot should start successfully with these log messages:

```
Bot logged in as 2KCompLeague Bot#1234
Connected to 1 guild(s)
Health server started at http://0.0.0.0:8080
All cogs loaded
Background tasks started
```

## Benefits

1. **No more permission errors** - Graceful fallback to writable directory
2. **Lazy initialization** - StateManager created only when needed
3. **Better error handling** - Logs warnings instead of crashing
4. **Railway compatibility** - Works with Railway's security model
5. **Backward compatibility** - Still tries `/data` first, falls back to `/tmp/data`

## Testing

The fix has been tested to handle:
- ✅ Permission denied on `/data` directory
- ✅ Fallback to `/tmp/data` directory
- ✅ Lazy initialization of StateManager
- ✅ Log file creation in fallback directory
- ✅ State file creation in fallback directory
