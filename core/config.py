"""Configuration management for the Discord bot."""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Bot configuration settings."""

    # Discord settings
    DISCORD_TOKEN: str = Field(..., description="Discord bot token")
    GUILD_ID: int = Field(..., description="Discord guild ID")
    ANNOUNCE_CHANNEL_ID: int = Field(..., description="Channel for announcements")
    HISTORY_CHANNEL_ID: int = Field(..., description="Channel for history posts")
    ADMIN_ROLE: str = Field(default="League Admin", description="Admin role name")

    # SportsPress API settings
    SPORTSPRESS_BASE: str = Field(
        default="https://2kcompleague.com/wp-json/sportspress/v2",
        description="SportsPress API base URL",
    )
    SEASON_ENDPOINTS: str = Field(
        default="/players?league=nba2k26s1,/players?league=nba2k25s6,/players?league=nba2k25s5,/players?league=nba2k25s4,/players?league=nba2k25s3,/players?league=nba2k25s2,/players?league=nba2k25s1,/players?league=nba2k24s2,/players?league=nba2k24s1",
        description="Comma-separated season endpoints",
    )
    LEADERS_ENDPOINT: str = Field(
        default="", description="Optional custom leaders endpoint"
    )

    # Bot behavior settings
    POLL_INTERVAL_SECONDS: int = Field(
        default=180, description="Interval for background task polling"
    )
    RECORDS_POLL_INTERVAL_SECONDS: int = Field(
        default=3600, description="Interval for records recomputation"
    )

    # File paths
    STATE_PATH: str = Field(
        default="/tmp/data/state.json", description="Path to state persistence file"
    )
    RECORDS_SEED_PATH: str = Field(
        default="/tmp/data/records_seed.json", description="Path to records seed file"
    )

    # Record thresholds
    MIN_FGA_FOR_FG_PERCENT: int = Field(
        default=10, description="Minimum FGA for FG% record consideration"
    )
    MIN_3PA_FOR_3P_PERCENT: int = Field(
        default=6, description="Minimum 3PA for 3P% record consideration"
    )

    # HTTP settings
    HTTP_TIMEOUT: int = Field(default=30, description="HTTP request timeout in seconds")
    HTTP_MAX_RETRIES: int = Field(default=3, description="Maximum HTTP retry attempts")

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="/tmp/data/bot.log", description="Log file path")

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def season_endpoints_list(self) -> List[str]:
        """Get season endpoints as a list."""
        return [ep.strip() for ep in self.SEASON_ENDPOINTS.split(",") if ep.strip()]

    @property
    def leaders_endpoint(self) -> str:
        """Get the leaders endpoint, falling back to first season endpoint."""
        if self.LEADERS_ENDPOINT:
            return self.LEADERS_ENDPOINT
        return self.season_endpoints_list[0] if self.season_endpoints_list else ""


# Global settings instance
settings = Settings()
