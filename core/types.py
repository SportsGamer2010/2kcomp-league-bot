"""Pydantic models for Discord bot data structures."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PlayerStats(BaseModel):
    """Player statistics from SportsPress API."""

    id: int
    name: str
    points: float = 0.0
    assists: float = 0.0
    rebounds: float = 0.0
    steals: float = 0.0
    blocks: float = 0.0
    threes_made: float = 0.0
    fgm: float = 0.0
    fga: float = 0.0
    threepm: float = 0.0
    threepa: float = 0.0
    fg_percent: float = 0.0
    threep_percent: float = 0.0


class LeaderEntry(BaseModel):
    """Single leader entry with name and value."""

    name: str
    value: float


class LeadersData(BaseModel):
    """Complete leaders data for all stats."""

    points: List[LeaderEntry] = Field(default_factory=list)
    assists: List[LeaderEntry] = Field(default_factory=list)
    rebounds: List[LeaderEntry] = Field(default_factory=list)
    steals: List[LeaderEntry] = Field(default_factory=list)
    blocks: List[LeaderEntry] = Field(default_factory=list)
    threes_made: List[LeaderEntry] = Field(default_factory=list)


class SingleGameRecord(BaseModel):
    """Single game record entry."""

    stat: str
    value: float
    holder: str
    game: str
    date: str  # YYYY-MM-DD
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    opp_team_id: Optional[int] = None
    game_url: Optional[str] = None
    player_url: Optional[str] = None


class DoubleDouble(BaseModel):
    """Double-double achievement (10+ in 2 categories)."""
    
    player: str
    game: str
    date: str
    categories: List[str]  # e.g., ["points", "rebounds"]
    values: Dict[str, float]  # e.g., {"points": 15, "rebounds": 12}
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    opp_team_id: Optional[int] = None
    game_url: Optional[str] = None
    player_url: Optional[str] = None


class TripleDouble(BaseModel):
    """Triple-double achievement (10+ in 3 categories)."""
    
    player: str
    game: str
    date: str
    categories: List[str]  # e.g., ["points", "rebounds", "assists"]
    values: Dict[str, float]  # e.g., {"points": 15, "rebounds": 12, "assists": 11}
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    opp_team_id: Optional[int] = None
    game_url: Optional[str] = None
    player_url: Optional[str] = None


class RecordsData(BaseModel):
    """Complete records data."""

    points: Optional[SingleGameRecord] = None
    rebounds: Optional[SingleGameRecord] = None
    assists: Optional[SingleGameRecord] = None
    steals: Optional[SingleGameRecord] = None
    blocks: Optional[SingleGameRecord] = None
    threes_made: Optional[SingleGameRecord] = None
    fg_percent: Optional[SingleGameRecord] = None
    threep_percent: Optional[SingleGameRecord] = None
    double_doubles: List[DoubleDouble] = Field(default_factory=list)
    triple_doubles: List[TripleDouble] = Field(default_factory=list)


class EventPlayerRow(BaseModel):
    """Player row from event box score."""

    name: str
    team: str
    opp: str
    game: str
    date: str
    points: float = 0.0
    rebounds: float = 0.0
    assists: float = 0.0
    steals: float = 0.0
    blocks: float = 0.0
    threes_made: float = 0.0
    fgm: float = 0.0
    fga: float = 0.0
    threepm: float = 0.0
    threepa: float = 0.0
    fg_percent: float = 0.0
    threep_percent: float = 0.0
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    opp_team_id: Optional[int] = None
    game_url: Optional[str] = None


class BotState(BaseModel):
    """Persistent bot state."""

    last_leaders: LeadersData = Field(default_factory=LeadersData)
    milestones_sent: Dict[str, Dict[str, List[int]]] = Field(default_factory=dict)
    last_totals: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class MilestoneNotification(BaseModel):
    """Milestone notification message."""

    player: str
    stat: str
    value: float
    threshold: int
    message: str
