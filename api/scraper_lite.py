import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import json

from supabase_client import get_supabase, log_sync

logger = logging.getLogger(__name__)

class FlashscoreLiteScraper:
    def __init__(self):
        self.supabase = get_supabase()
        self.session = None
        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (compatible; FootballScraper/1.0; +https://github.com)",
            "Accept": "application/json, text/html",
            "Accept-Language": "es-ES,es;q=0.9",
        }
    
    async def fetch_league_data(self, league_code: str) -> Optional[dict]:
        """Obtener datos básicos de una liga"""
        url = f"https://www.flashscore.co/futbol/{league_code}/resultados/"
        
        try:
            async with self.session.get(url, headers=self.base_headers) as response:
                if response.status == 200:
                    html = await response.text()
                    # Extraer datos básicos con regex simple
                    import re
                    
                    # Buscar temporada actual
                    season_match = re.search(r'(\d{4})[./-](\d{4})', html)
                    if season_match:
                        season = f"{season_match.group(1)}-{season_match.group(2)}"
                    else:
                        season = None
                    
                    return {
                        "league_code": league_code,
                        "season": season,
                        "last_updated": datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"Error fetching {league_code}: {e}")
        
        return None
    
    async def update_single_league(self, league_config: dict):
        """Actualizar una sola liga"""
        league_id = league_config.get("id")
        league_code = league_config.get("flashscore_id")
        
        if not league_code:
            logger.warning(f"Liga sin flashscore_id: {league_config.get('name')}")
            return
        
        logger.info(f"🔄 Actualizando: {league_config.get('name')}")
        
        # 1. Obtener datos básicos
        basic_data = await self.fetch_league_data(league_code)
        
        if not basic_data:
            logger.warning(f"No se pudieron obtener datos para {league_code}")
            return
        
        # 2. Actualizar en Supabase
        self.supabase.table("league_updates").insert({
            "league_id": league_id,
            "season": basic_data.get("season"),
            "updated_at": datetime.now().isoformat(),
            "data": basic_data
        }).execute()
        
        logger.info(f"✅ Actualizada: {league_config.get('name')}")
    
    async def run_sync(self, leagues_to_sync: List[str] = None):
        """Ejecutar sincronización completa"""
        # Obtener ligas activas
        query = self.supabase.table("leagues").select("*").eq("is_active", True)
        result = query.execute()
        
        all_leagues = result.data
        leagues = all_leagues
        
        if leagues_to_sync:
            leagues = [l for l in all_leagues if l.get("code") in leagues_to_sync]
        
        logger.info(f"🔄 Sincronizando {len(leagues)} ligas")
        
        # Configurar sesión HTTP
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as self.session:
            # Procesar ligas con límite de concurrencia
            semaphore = asyncio.Semaphore(3)
            
            async def process_with_semaphore(league):
                async with semaphore:
                    await self.update_single_league(league)
            
            tasks = [process_with_semaphore(league) for league in leagues]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Contar errores
            errors = [r for r in results if isinstance(r, Exception)]
            
            # Registrar sincronización
            log_sync({
                "total_leagues": len(leagues),
                "successful": len(leagues) - len(errors),
                "errors": len(errors),
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"✅ Sincronización completada: {len(leagues)-len(errors)}/{len(leagues)}")
            
            if errors:
                logger.error(f"Errores encontrados: {len(errors)}")

# Función para Background Tasks
async def run_sync_task(leagues: List[str] = None):
    scraper = FlashscoreLiteScraper()
    await scraper.run_sync(leagues)