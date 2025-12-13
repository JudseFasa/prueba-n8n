import os
import sqlite3
import glob
from supabase import create_client
from dotenv import load_dotenv
import sys
from datetime import datetime
import json
from tqdm import tqdm  # Para barra de progreso
import time
import calendar  # Añadido para manejar días del mes

# Cargar variables de entorno
load_dotenv()

class BatchSupabaseMigrator:
    def __init__(self, supabase_url, supabase_key):
        self.supabase = create_client(supabase_url, supabase_key)
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'leagues_created': 0,
            'seasons_created': 0,
            'teams_created': 0,
            'matches_created': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        
        # Caché para evitar inserciones duplicadas
        self.league_cache = {}  # (name, country) -> id
        self.season_cache = {}  # (league_id, year_start, year_end) -> id
        self.team_cache = {}  # (league_id, team_name) -> id
    
    def normalize_league_name(self, liga):
        """Normalizar nombres de ligas"""
        mapping = {
            'jupiler-pro-league': 'Jupiler Pro League',
            'primera-a': 'Primera A',
            'serie-a': 'Serie A',
            'laliga-ea-sports': 'La Liga',
            'premier-league': 'Premier League',
            'bundesliga': 'Bundesliga',
            'ligue-1': 'Ligue 1',
            'eredivisie': 'Eredivisie',
            'primeira-liga': 'Primeira Liga',
            'mls': 'Major League Soccer'
        }
        
        liga_lower = liga.lower().strip()
        for key, value in mapping.items():
            if key in liga_lower:
                return value
        
        return ' '.join(word.capitalize() for word in liga.replace('-', ' ').split())
    
    def normalize_country_name(self, pais):
        """Normalizar nombres de países"""
        mapping = {
            'belgica': 'Bélgica',
            'colombia': 'Colombia',
            'italia': 'Italia',
            'espana': 'España',
            'england': 'Inglaterra',
            'germany': 'Alemania',
            'france': 'Francia',
            'netherlands': 'Países Bajos',
            'portugal': 'Portugal',
            'usa': 'Estados Unidos',
            'mexico': 'México',
            'argentina': 'Argentina',
            'brazil': 'Brasil'
        }
        
        pais_lower = pais.lower().strip()
        return mapping.get(pais_lower, pais.capitalize())
    
    def extract_year_from_filename(self, filename):
        """Extraer años del nombre del archivo"""
        import re
        matches = re.findall(r'\b(20\d{2})[_.-](20\d{2})\b', filename)
        if matches:
            return int(matches[0][0]), int(matches[0][1])
        
        matches = re.findall(r'\b(20\d{2})\b', filename)
        if matches:
            year = int(matches[0])
            return year, year + 1
        
        return None, None
    
    def get_or_create_league(self, pais, liga):
        """Obtener o crear liga (con caché)"""
        cache_key = (pais, liga)
        
        if cache_key in self.league_cache:
            return self.league_cache[cache_key]
        
        try:
            # Buscar si ya existe
            result = self.supabase.table('leagues')\
                .select('*')\
                .eq('name', liga)\
                .eq('country', pais)\
                .execute()
            
            if result.data:
                league_id = result.data[0]['id']
                self.league_cache[cache_key] = league_id
                return league_id
            else:
                # Crear nueva liga
                flashscore_id = f"{pais.lower().replace(' ', '-')}/{liga.lower().replace(' ', '-')}"
                new_league = {
                    'name': liga,
                    'country': pais,
                    'flashscore_id': flashscore_id,
                    'is_active': True
                }
                
                result = self.supabase.table('leagues').insert(new_league).execute()
                league_id = result.data[0]['id']
                self.league_cache[cache_key] = league_id
                self.stats['leagues_created'] += 1
                return league_id
                
        except Exception as e:
            print(f" ❌ Error creando liga {liga}: {e}")
            self.stats['errors'] += 1
            return None
    
    def get_or_create_season(self, league_id, year_start, year_end):
        """Obtener o crear temporada (con caché)"""
        cache_key = (league_id, year_start, year_end)
        
        if cache_key in self.season_cache:
            return self.season_cache[cache_key]
        
        try:
            # Buscar si ya existe
            result = self.supabase.table('seasons')\
                .select('*')\
                .eq('league_id', league_id)\
                .eq('year_start', year_start)\
                .eq('year_end', year_end)\
                .execute()
            
            if result.data:
                season_id = result.data[0]['id']
                self.season_cache[cache_key] = season_id
                return season_id
            else:
                # Crear nueva temporada
                new_season = {
                    'league_id': league_id,
                    'year_start': year_start,
                    'year_end': year_end,
                    'is_current': False
                }
                
                result = self.supabase.table('seasons').insert(new_season).execute()
                season_id = result.data[0]['id']
                self.season_cache[cache_key] = season_id
                self.stats['seasons_created'] += 1
                return season_id
                
        except Exception as e:
            print(f" ❌ Error creando temporada {year_start}-{year_end}: {e}")
            self.stats['errors'] += 1
            return None
    
    def get_or_create_team(self, league_id, team_name):
        """Obtener o crear equipo (con caché)"""
        cache_key = (league_id, team_name)
        
        if cache_key in self.team_cache:
            return self.team_cache[cache_key]
        
        try:
            # Buscar si ya existe
            result = self.supabase.table('teams')\
                .select('*')\
                .eq('league_id', league_id)\
                .eq('name', team_name)\
                .execute()
            
            if result.data:
                team_id = result.data[0]['id']
                self.team_cache[cache_key] = team_id
                return team_id
            else:
                # Crear nuevo equipo
                new_team = {
                    'league_id': league_id,
                    'name': team_name
                }
                
                result = self.supabase.table('teams').insert(new_team).execute()
                team_id = result.data[0]['id']
                self.team_cache[cache_key] = team_id
                self.stats['teams_created'] += 1
                return team_id
                
        except Exception as e:
            print(f" ❌ Error creando equipo {team_name}: {e}")
            self.stats['errors'] += 1
            return None
    
    def parse_date(self, fecha_str, year_start):
        """Parsear fecha del formato SQLite y asegurar que sea válida"""
        try:
            if not fecha_str:
                return None
            
            # Formato: "22.05. 11:30" o "08.11. 19:30"
            parts = fecha_str.split()
            if not parts:
                return None
            
            date_part = parts[0]
            if date_part.endswith('.'):
                date_part = date_part[:-1]
            
            # Separar día y mes
            day, month = map(int, date_part.split('.'))
            
            # Determinar año (temporada cruza años)
            if month >= 8:  # Agosto en adelante
                year = year_start
            else:  # Enero a Julio
                year = year_start + 1
            
            # Obtener el último día del mes
            last_day = calendar.monthrange(year, month)[1]
            
            # Ajustar día si es inválido
            if day > last_day:
                print(f" ⚠️ Ajustando fecha inválida: {year}-{month:02d}-{day:02d} a {year}-{month:02d}-{last_day:02d}")
                day = last_day
            
            return f"{year}-{month:02d}-{day:02d}"
        except:
            return None
    
    def process_sqlite_file(self, db_path):
        """Procesar un archivo SQLite completo"""
        filename = os.path.basename(db_path)
        print(f"\n📂 Procesando: {filename}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar que tiene la tabla partidos
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='partidos'")
            if not cursor.fetchone():
                print(f" ⚠️ Saltando: No tiene tabla 'partidos'")
                conn.close()
                return False
            
            # Contar partidos
            cursor.execute("SELECT COUNT(*) FROM partidos")
            total_matches = cursor.fetchone()[0]
            print(f" 📊 {total_matches:,} partidos encontrados")
            
            # Obtener todos los partidos
            cursor.execute("SELECT * FROM partidos")
            columns = [desc[0] for desc in cursor.description]
            
            # Procesar cada partido
            processed_matches = 0
            batch_matches = []
            
            for row in cursor.fetchall():
                match_data = dict(zip(columns, row))
                
                # Extraer datos básicos
                pais = match_data.get('pais', '')
                liga = match_data.get('liga', '')
                temporada = match_data.get('temporada', '')
                
                if not pais or not liga:
                    continue
                
                # Normalizar nombres
                pais_norm = self.normalize_country_name(pais)
                liga_norm = self.normalize_league_name(liga)
                
                # Extraer años de la temporada
                year_start, year_end = None, None
                if temporada and '-' in temporada:
                    try:
                        year_start, year_end = map(int, temporada.split('-'))
                    except:
                        pass
                
                # Si no se pudo de la temporada, intentar del nombre del archivo
                if not year_start:
                    year_start, year_end = self.extract_year_from_filename(filename)
                
                if not year_start:
                    year_start, year_end = 2023, 2024  # Default
                
                # Obtener o crear liga
                league_id = self.get_or_create_league(pais_norm, liga_norm)
                if not league_id:
                    continue
                
                # Obtener o crear temporada
                season_id = self.get_or_create_season(league_id, year_start, year_end)
                if not season_id:
                    continue
                
                # Obtener o crear equipos
                home_team = match_data.get('local', '')
                away_team = match_data.get('visitante', '')
                
                home_team_id = self.get_or_create_team(league_id, home_team)
                away_team_id = self.get_or_create_team(league_id, away_team)
                
                if not home_team_id or not away_team_id:
                    continue
                
                # Preparar partido para batch insert
                match_date = self.parse_date(match_data.get('fecha'), year_start)
                home_ft = (match_data.get('g_local_1t') or 0) + (match_data.get('g_local_2t') or 0)
                away_ft = (match_data.get('g_visitante_1t') or 0) + (match_data.get('g_visitante_2t') or 0)
                
                batch_matches.append({
                    'season_id': season_id,
                    'matchday': match_data.get('jornada') or 1,
                    'date': match_date or f'{year_start}-01-01',
                    'home_team': home_team_id,
                    'away_team': away_team_id,
                    'home_ht': match_data.get('g_local_1t'),
                    'away_ht': match_data.get('g_visitante_1t'),
                    'home_ft': home_ft,
                    'away_ft': away_ft,
                    'status': 'FINISHED',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
                
                processed_matches += 1
                
                # Insertar en lotes de 100
                if len(batch_matches) >= 100:
                    self.insert_batch_matches(batch_matches)
                    batch_matches = []
                    print(f" 📈 {processed_matches}/{total_matches} partidos procesados...")
            
            # Insertar los restantes
            if batch_matches:
                self.insert_batch_matches(batch_matches)
            
            conn.close()
            self.stats['processed_files'] += 1
            self.stats['matches_created'] += processed_matches
            
            print(f" ✅ {processed_matches:,} partidos migrados")
            return True
            
        except Exception as e:
            print(f" ❌ Error procesando {filename}: {e}")
            self.stats['errors'] += 1
            return False
    
    def insert_batch_matches(self, matches_batch):
        """Insertar lote de partidos"""
        try:
            self.supabase.table('matches').insert(matches_batch).execute()
        except Exception as e:
            print(f" ⚠️ Error en batch insert: {e}")
            # Intentar uno por uno si falla el batch
            for match in matches_batch:
                try:
                    self.supabase.table('matches').insert(match).execute()
                except:
                    self.stats['errors'] += 1
    
    def find_all_db_files(self, folder_path):
        """Buscar todos los archivos .db en una carpeta"""
        pattern = os.path.join(folder_path, "*.db")
        db_files = glob.glob(pattern)
        
        # También buscar en subcarpetas
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.db'):
                    full_path = os.path.join(root, file)
                    if full_path not in db_files:
                        db_files.append(full_path)
        
        return sorted(db_files)
    
    def run_migration(self, data_folder):
        """Ejecutar migración completa de toda la carpeta"""
        print("🚀 MIGRACIÓN MASIVA - TODA LA CARPETA")
        print("=" * 70)
        
        # Buscar archivos
        db_files = self.find_all_db_files(data_folder)
        self.stats['total_files'] = len(db_files)
        
        if not db_files:
            print("❌ No se encontraron archivos .db en la carpeta")
            return False
        
        print(f"📂 Encontrados {len(db_files)} archivos .db:")
        for i, db_file in enumerate(db_files[:10], 1):
            print(f" {i}. {os.path.basename(db_file)}")
        
        if len(db_files) > 10:
            print(f" ... y {len(db_files) - 10} más")
        
        print(f"\n📍 Carpeta: {data_folder}")
        print(f"🌐 Supabase: {self.supabase.supabase_url[:30]}...")
        print("=" * 70)
        
        # Confirmar
        confirm = input("\n⚠️ ¿Migrar TODOS estos archivos a Supabase? (SI/NO): ")
        if confirm.upper() != 'SI':
            print("❌ Migración cancelada")
            return False
        
        # Procesar cada archivo
        print("\n🔄 Iniciando migración...")
        start_time = datetime.now()
        
        for i, db_file in enumerate(db_files, 1):
            print(f"\n[{i}/{len(db_files)}] ", end="")
            self.process_sqlite_file(db_file)
        
        # Estadísticas finales
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("📊 ESTADÍSTICAS FINALES DE MIGRACIÓN")
        print("=" * 70)
        print(f"📂 Archivos procesados: {self.stats['processed_files']}/{self.stats['total_files']}")
        print(f"🌍 Ligas creadas: {self.stats['leagues_created']:,}")
        print(f"📅 Temporadas creadas: {self.stats['seasons_created']:,}")
        print(f"⚽ Equipos creados: {self.stats['teams_created']:,}")
        print(f"🏟️ Partidos migrados: {self.stats['matches_created']:,}")
        print(f"⚠️ Errores: {self.stats['errors']:,}")
        print(f"⏱️ Duración: {duration:.2f} segundos")
        print(f"📈 Promedio: {self.stats['matches_created']/max(duration, 1):.1f} partidos/segundo")
        print("=" * 70)
        
        # Preparar stats para JSON (convertir datetimes a strings)
        stats_json = {
            k: v.isoformat() if isinstance(v, datetime) else v
            for k, v in self.stats.items()
        }
        
        # Guardar log en Supabase
        try:
            self.supabase.table('logs').insert({
                'source': 'batch_migration',
                'message': f'Migración masiva completada: {self.stats["matches_created"]} partidos',
                'level': 'info',
                'extra': stats_json
            }).execute()
            
            # Actualizar estadísticas en tabla config
            self.supabase.table('config').upsert({
                'key': 'migration_stats',
                'value': stats_json,
                'description': 'Estadísticas de la última migración masiva',
                'updated_at': datetime.now().isoformat()
            }).execute()
            
        except Exception as e:
            print(f"⚠️ No se pudo guardar log: {e}")
        
        print("\n🎉 ¡MIGRACIÓN MASIVA COMPLETADA!")
        return True

def main():
    """Función principal"""
    # Configuración
    supabase_url = os.getenv("SUPABASE_URL", "https://mvsnymlcqutxnmnfxdgt.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    
    # Verificar credenciales
    if not supabase_url or not supabase_key:
        print("❌ Error: Configura SUPABASE_URL y SUPABASE_KEY en el archivo .env")
        print("\n💡 Crea un archivo .env con:")
        print("SUPABASE_URL=https://mvsnymlcqutxnmnfxdgt.supabase.co")
        print("SUPABASE_KEY=tu_clave_completa_aqui")
        return
    
    # Definir carpeta de datos
    if len(sys.argv) > 1:
        data_folder = sys.argv[1]
    else:
        # Rutas comunes
        possible_paths = [
            "data",
            "X:/prueba n8n/data",
            "./data",
            os.path.join(os.getcwd(), "data")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                data_folder = path
                break
        else:
            print("❌ No se encontró la carpeta 'data'")
            print("💡 Especifica la ruta: python migrate_all.py <ruta_carpeta>")
            return
    
    # Verificar que la carpeta existe
    if not os.path.exists(data_folder):
        print(f"❌ La carpeta no existe: {data_folder}")
        return
    
    print(f"📁 Carpeta de datos: {data_folder}")
    
    # Crear migrador
    migrator = BatchSupabaseMigrator(supabase_url, supabase_key)
    
    # Ejecutar migración
    migrator.run_migration(data_folder)

if __name__ == "__main__":
    main()