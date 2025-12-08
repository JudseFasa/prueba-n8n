from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from typing import List, Optional

from config import settings
from supabase_client import get_supabase
from models import SyncRequest, LeagueConfig, HealthResponse

# Models Pydantic
from pydantic import BaseModel
from datetime import datetime
from typing import Optional as Opt

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: Opt[str] = None
    error: Opt[str] = None

class SyncRequest(BaseModel):
    leagues: Opt[List[str]] = None
    force_full: bool = False

class LeagueConfig(BaseModel):
    name: str
    country: str
    flashscore_id: str
    flashscore_url: str
    is_active: bool = True

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Iniciando API de Football Data...")
    settings.validate()
    print("✅ API lista para recibir peticiones")
    yield
    # Shutdown
    print("👋 Cerrando API...")

# Crear app
app = FastAPI(
    title="Football Data API",
    description="API para sincronizar datos de fútbol con Supabase",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints
@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "football-data-api",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    try:
        # Probar conexión a Supabase
        supabase = get_supabase()
        result = supabase.table("leagues").select("count", count="exact").limit(1).execute()
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            database="connected"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            error=str(e)
        )

@app.post("/sync", tags=["Sync"])
async def trigger_sync(request: SyncRequest, background_tasks: BackgroundTasks):
    """Endpoint para n8n - Inicia sincronización"""
    from scraper_lite import run_sync_task
    
    # Validar API key si existe
    # (Puedes añadir autenticación básica después)
    
    # Ejecutar en segundo plano
    background_tasks.add_task(run_sync_task, request.leagues)
    
    return {
        "message": "Sync iniciado en segundo plano",
        "leagues": request.leagues or "todas",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/leagues", tags=["Leagues"])
async def get_leagues(active_only: bool = True):
    """Obtener todas las ligas"""
    supabase = get_supabase()
    
    query = supabase.table("leagues").select("*")
    if active_only:
        query = query.eq("is_active", True)
    
    result = query.execute()
    return {
        "count": len(result.data),
        "leagues": result.data
    }

@app.post("/leagues", tags=["Leagues"])
async def create_league(league: LeagueConfig):
    """Añadir nueva liga"""
    supabase = get_supabase()
    
    # Verificar si ya existe
    existing = supabase.table("leagues")\
        .select("*")\
        .eq("name", league.name)\
        .eq("country", league.country)\
        .execute()
    
    if existing.data:
        raise HTTPException(status_code=400, detail="La liga ya existe")
    
    # Insertar
    result = supabase.table("leagues").insert(league.dict()).execute()
    
    return {
        "message": "Liga creada",
        "id": result.data[0]["id"]
    }

@app.get("/matches/recent", tags=["Matches"])
async def get_recent_matches(league_id: Opt[int] = None, limit: int = 50):
    """Obtener partidos recientes"""
    supabase = get_supabase()
    
    query = supabase.table("matches")\
        .select("*, teams!matches_home_team_fkey(name), teams!matches_away_team_fkey(name)")\
        .order("date", desc=True)\
        .limit(limit)
    
    if league_id:
        query = query.eq("league_id", league_id)
    
    result = query.execute()
    return {
        "count": len(result.data),
        "matches": result.data
    }

# Para ejecución local
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )