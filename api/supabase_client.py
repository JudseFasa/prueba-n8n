from supabase import create_client
import os
from typing import Dict, List, Any

class SupabaseClient:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
        
        self.client = create_client(url, key)
    
    # Métodos helper
    def get_league_by_name(self, country: str, name: str) -> Dict:
        result = self.client.table('leagues')\
            .select('*')\
            .eq('country', country)\
            .eq('name', name)\
            .execute()
        
        return result.data[0] if result.data else None
    
    def get_or_create_season(self, league_id: int, year_range: str) -> int:
        year_start, year_end = map(int, year_range.split('-'))
        
        result = self.client.table('seasons')\
            .select('*')\
            .eq('league_id', league_id)\
            .eq('year_start', year_start)\
            .eq('year_end', year_end)\
            .execute()
        
        if result.data:
            return result.data[0]['id']
        
        # Create new
        new_season = self.client.table('seasons').insert({
            'league_id': league_id,
            'year_start': year_start,
            'year_end': year_end,
            'is_current': True
        }).execute()
        
        return new_season.data[0]['id']
    
    def upsert_matches(self, season_id: int, matches: List[Dict]):
        for match in matches:
            # Buscar equipos o crearlos
            home_id = self.get_or_create_team(season_id, match['home_team'])
            away_id = self.get_or_create_team(season_id, match['away_team'])
            
            # Insertar/actualizar partido
            self.client.table('matches').upsert({
                'season_id': season_id,
                'matchday': match['matchday'],
                'date': match['date'],
                'home_team': home_id,
                'away_team': away_id,
                'home_ht': match.get('home_ht'),
                'away_ht': match.get('away_ht'),
                'home_ft': match.get('home_ft'),
                'away_ft': match.get('away_ft'),
                'status': match.get('status', 'FINISHED'),
                'flashscore_id': match.get('flashscore_id')
            }, on_conflict='season_id,flashscore_id').execute()
    
    def get_or_create_team(self, season_id: int, team_name: str) -> int:
        # Primero buscar en la liga de esta temporada
        result = self.client.table('teams')\
            .select('*')\
            .eq('league_id', self.get_league_from_season(season_id))\
            .eq('name', team_name)\
            .execute()
        
        if result.data:
            return result.data[0]['id']
        
        # Crear nuevo
        league_id = self.get_league_from_season(season_id)
        new_team = self.client.table('teams').insert({
            'league_id': league_id,
            'name': team_name
        }).execute()
        
        return new_team.data[0]['id']
    
    def log_sync(self, data: Dict):
        self.client.table('logs').insert({
            'source': 'lite_scraper',
            'message': 'Sync completed',
            'extra': data
        }).execute()
    
    def get_active_leagues(self) -> List[Dict]:
        result = self.client.table('leagues')\
            .select('*')\
            .eq('is_active', True)\
            .execute()
        
        return result.data

# Singleton
_supabase_instance = None

def get_supabase_client():
    global _supabase_instance
    if _supabase_instance is None:
        _supabase_instance = SupabaseClient()
    return _supabase_instance