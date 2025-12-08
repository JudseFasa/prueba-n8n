import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FlashscoreLiteScraper:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.session = None
        self.base_url = "https://d.flashscore.com/x/feed/"
        self.headers = {
            'authority': 'd.flashscore.com',
            'accept': '*/*',
            'accept-language': 'es-ES,es;q=0.9',
            'origin': 'https://www.flashscore.co',
            'referer': 'https://www.flashscore.co/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def fetch_json_feed(self, league_id: str, season_id: str) -> Optional[Dict]:
        """Usa la API interna de Flashscore"""
        url = f"{self.base_url}f_1_{league_id}_3_{season_id}_es_1"
        
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.text()
                    # El feed viene en formato especial, necesita parsing
                    return self.parse_feed(data)
        except Exception as e:
            logger.error(f"Error fetching feed: {e}")
        return None
    
    def parse_feed(self, feed_data: str) -> Dict:
        """Parsea el formato especial del feed"""
        matches = []
        # Implementar lógica de parsing específica
        # (Flashscore usa un formato de diccionario plano)
        return {"matches": matches}
    
    async def update_league(self, league_config: Dict):
        """Actualiza una liga específica"""
        try:
            # 1. Verificar si existe en Supabase
            league_record = self.supabase.get_league_by_name(
                league_config['country'], 
                league_config['name']
            )
            
            if not league_record:
                league_id = self.supabase.create_league(league_config)
            else:
                league_id = league_record['id']
            
            # 2. Obtener temporada actual
            current_season = self.get_current_season()
            season_id = self.supabase.get_or_create_season(league_id, current_season)
            
            # 3. Obtener últimos partidos (últimos 7 días + próximos 3 días)
            matches = await self.fetch_recent_matches(league_config['flashscore_id'])
            
            # 4. Actualizar en lotes
            batch_size = 50
            for i in range(0, len(matches), batch_size):
                batch = matches[i:i+batch_size]
                self.supabase.upsert_matches(season_id, batch)
            
            logger.info(f"Updated {len(matches)} matches for {league_config['name']}")
            
        except Exception as e:
            logger.error(f"Error updating league: {e}")
            raise
    
    async def fetch_recent_matches(self, flashscore_id: str) -> List[Dict]:
        """Obtiene partidos recientes usando API más ligera"""
        today = datetime.now().date()
        date_from = (today - timedelta(days=7)).strftime('%Y%m%d')
        date_to = (today + timedelta(days=3)).strftime('%Y%m%d')
        
        url = f"https://www.flashscore.co/matchfeed/?s=2&i={flashscore_id}&d={date_from}-{date_to}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return self.parse_matches(data)
        
        return []
    
    def parse_matches(self, data: Dict) -> List[Dict]:
        """Parsea los datos de partidos"""
        matches = []
        
        for match in data.get('matches', []):
            matches.append({
                'matchday': match.get('round'),
                'date': match.get('date'),
                'home_team': match.get('home_team'),
                'away_team': match.get('away_team'),
                'home_ft': match.get('home_score'),
                'away_ft': match.get('away_score'),
                'home_ht': match.get('home_score_ht'),
                'away_ht': match.get('away_score_ht'),
                'status': match.get('status'),
                'flashscore_id': match.get('id')
            })
        
        return matches
    
    async def run_sync(self, leagues_to_sync: List[str] = None):
        """Ejecuta sincronización completa"""
        async with aiohttp.ClientSession() as self.session:
            # Obtener configuraciones de ligas desde Supabase
            leagues_config = self.supabase.get_active_leagues()
            
            if leagues_to_sync:
                leagues_config = [l for l in leagues_config if l['code'] in leagues_to_sync]
            
            # Procesar en paralelo (máximo 3 ligas simultáneamente)
            semaphore = asyncio.Semaphore(3)
            
            async def process_league(league):
                async with semaphore:
                    await self.update_league(league)
            
            tasks = [process_league(league) for league in leagues_config]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Registrar sync
            self.supabase.log_sync({
                'type': 'auto',
                'leagues_processed': len(leagues_config),
                'timestamp': datetime.now().isoformat()
            })