from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

from scraper_lite import FlashscoreLiteScraper
from supabase_client import get_supabase_client

app = FastAPI(title="Football Data Sync API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos
class SyncRequest(BaseModel):
    leagues: Optional[List[str]] = None
    force_full: bool = False

class LeagueConfig(BaseModel):
    name: str
    country: str
    flashscore_id: str
    flashscore_url: str
    is_active: bool = True

# Endpoints
@app.get("/")
async def root():
    return {"status": "online", "service": "football-data-sync"}

@app.get("/health")
async def health():
    supabase = get_supabase_client()
    try:
        # Test connection
        supabase.table('leagues').select('count', count='exact').limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/sync")
async def trigger_sync(request: SyncRequest, background_tasks: BackgroundTasks):
    """Endpoint para n8n"""
    background_tasks.add_task(run_sync_task, request.leagues)
    
    return {
        "message": "Sync started",
        "leagues": request.leagues or "all",
        "background": True
    }

@app.get("/leagues")
async def get_leagues(active_only: bool = True):
    supabase = get_supabase_client()
    
    query = supabase.table('leagues').select('*')
    if active_only:
        query = query.eq('is_active', True)
    
    result = query.execute()
    return result.data

@app.post("/leagues")
async def add_league(league: LeagueConfig):
    supabase = get_supabase_client()
    
    # Check if exists
    existing = supabase.table('leagues')\
        .select('*')\
        .eq('name', league.name)\
        .eq('country', league.country)\
        .execute()
    
    if existing.data:
        raise HTTPException(400, "League already exists")
    
    result = supabase.table('leagues').insert(league.dict()).execute()
    return {"message": "League added", "id": result.data[0]['id']}

# Tarea en segundo plano
async def run_sync_task(leagues: List[str] = None):
    supabase = get_supabase_client()
    scraper = FlashscoreLiteScraper(supabase)
    
    try:
        await scraper.run_sync(leagues)
    except Exception as e:
        # Log error
        supabase.table('logs').insert({
            'source': 'api_sync',
            'message': f'Sync failed: {str(e)}',
            'level': 'error'
        }).execute()
        raise