"""Utility functions for formatting and display."""

def format_number(value: float, suffix: str = "") -> str:
    """
    Format a number with commas and optional suffix.
    
    Args:
        value: The number to format
        suffix: Optional suffix (e.g., "pts", "ast", "reb")
    
    Returns:
        Formatted string (e.g., "1,718 pts")
    """
    if value is None or value == 0:
        return f"0 {suffix}".strip()
    
    # Convert to int if it's a whole number
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    
    # Format with commas
    formatted = f"{value:,}"
    
    # Add suffix with space if provided
    if suffix:
        return f"{formatted} {suffix}"
    
    return formatted

def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a percentage value.
    
    Args:
        value: The percentage value (0-100)
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string (e.g., "45.2%")
    """
    if value is None:
        return "0.0%"
    
    return f"{value:.{decimals}f}%"

def format_rank(rank: int) -> str:
    """
    Format a rank with appropriate suffix.
    
    Args:
        rank: The rank number
    
    Returns:
        Formatted rank string (e.g., "1st", "2nd", "3rd", "4th")
    """
    if rank is None:
        return "N/A"
    
    if 10 <= rank % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(rank % 10, "th")
    
    return f"{rank}{suffix}"

def get_league_colors() -> dict:
    """
    Get the official 2KCompLeague color scheme based on the logo.
    
    Returns:
        Dictionary of color codes matching the shield logo
    """
    return {
        "primary": 0xDC143C,      # Crimson Red (main logo color)
        "secondary": 0x1E90FF,    # Dodger Blue (LEAGUE banner)
        "accent": 0xFFD700,       # Gold (logo highlights)
        "success": 0x10B981,      # Green
        "warning": 0xF59E0B,      # Orange
        "info": 0x3B82F6,         # Light Blue
        "dark": 0x000000,         # Black (logo background)
        "light": 0xF3F4F6,        # Light Gray
        "shield": 0x8B0000,       # Dark Red (shield outline)
        "basketball": 0xFF4500    # Orange Red (basketball gradient)
    }

def get_league_emojis() -> dict:
    """
    Get the official 2KCompLeague emojis.
    
    Returns:
        Dictionary of emoji mappings
    """
    return {
        "points": "🏀",
        "assists": "✨", 
        "rebounds": "📊",
        "steals": "🔪",
        "blocks": "🛡️",
        "threes": "🎯",
        "fg_percent": "🎯",
        "ft_percent": "🎯",
        "league": "🏆",
        "trophy": "🏆",
        "medal": "🥇",
        "star": "⭐",
        "fire": "🔥",
        "lightning": "⚡",
        "crown": "👑",
        "target": "🎯",
        "shield": "🛡️",  # Matches your shield logo
        "sword": "⚔️",
        "diamond": "💎",
        "gem": "💎",
        "logo": "🛡️",    # Shield emoji representing your logo
        "basketball": "🏀" # Basketball from your logo
    }

def get_league_logo_url() -> str:
    """
    Get the URL for the 2KCompLeague logo.
    
    Returns:
        Logo URL string
    """
    return "https://2kcompleague.com/wp-content/uploads/2024/12/2kcomp-league-logo.png"

def get_league_branding() -> dict:
    """
    Get comprehensive league branding information.
    
    Returns:
        Dictionary with logo, colors, and branding info
    """
    return {
        "name": "2KCompLeague",
        "website": "https://2kcompleague.com",
        "logo_url": get_league_logo_url(),
        "colors": get_league_colors(),
        "emojis": get_league_emojis(),
        "tagline": "Where Champions Are Made",
        "description": "The premier NBA2K competitive league featuring monthly seasons, comprehensive statistics, and championship glory."
    }

def create_branded_footer(text: str = "") -> str:
    """
    Create a branded footer text.
    
    Args:
        text: Additional text to include
    
    Returns:
        Branded footer string
    """
    base = "2KCompLeague | Powered by 2kcompleague.com"
    if text:
        return f"{base} | {text}"
    return base

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
