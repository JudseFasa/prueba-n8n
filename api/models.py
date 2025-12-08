from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: Optional[str] = None
    error: Optional[str] = None

class SyncRequest(BaseModel):
    leagues: Optional[List[str]] = None
    force_full: bool = False

class LeagueConfig(BaseModel):
    name: str
    country: str
    flashscore_id: str
    flashscore_url: str
    is_active: bool = True

class MatchResponse(BaseModel):
    id: int
    matchday: int
    date: datetime
    home_team: str
    away_team: str
    home_ft: Optional[int] = None
    away_ft: Optional[int] = None
    home_ht: Optional[int] = None
    away_ht: Optional[int] = None
    status: str