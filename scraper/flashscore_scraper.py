"""
SCRAPER FLASHSCORE PRECISO - ENFOQUE EN ESTRUCTURA ESPECÍFICA
Versión optimizada para extraer solo goles reales sin duplicados
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os
import csv
import json
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FlashscorePreciseScraper:
    def __init__(self):
        self.base_url = "https://www.flashscore.co"
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.output_dir = "data"
        self.session = None
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    async def setup_session(self):
        """Configurar sesión HTTP con headers específicos para Flashscore"""
        connector = aiohttp.TCPConnector(limit=5, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
                'Referer': 'https://www.flashscore.co/'
            }
        )
        return True
    
    def extract_match_id(self, url: str) -> str:
        """Extraer ID del partido de la URL"""
        try:
            if 'mid=' in url:
                match = re.search(r'mid=([^&]+)', url)
                if match:
                    return match.group(1)
            
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            if len(path_parts) >= 4:
                # Extraer ID de la URL
                equipo1_id = path_parts[-2].split('-')[-1]
                equipo2_id = path_parts[-1].split('-')[-1]
                return f"{equipo1_id}_{equipo2_id}"
            
            return f"match_{int(datetime.now().timestamp())}"
        except:
            return f"match_{int(datetime.now().timestamp())}"
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Obtener contenido de la página con reintentos"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return html
                    elif response.status == 429:  # Too Many Requests
                        wait_time = 2 ** (attempt + 1)  # Exponential backoff
                        logger.warning(f"⚠ Rate limited. Esperando {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"❌ Error HTTP {response.status} para {url}")
                        return None
            except Exception as e:
                logger.error(f"❌ Error obteniendo página {url} (intento {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    return None
        return None
    
    async def extract_basic_data(self, html: str, url: str) -> Optional[Dict]:
        """Extraer datos básicos del partido usando BeautifulSoup"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # INTENTO 1: Buscar por estructura específica de Flashscore
            # Buscar equipos en la estructura de Flashscore
            home_team_element = soup.select_one('.duelParticipant__home .participant__participantName, .tname-home a, [class*="home"] [class*="name"]')
            away_team_element = soup.select_one('.duelParticipant__away .participant__participantName, .tname-away a, [class*="away"] [class*="name"]')
            
            home_team = home_team_element.text.strip() if home_team_element else "Desconocido Local"
            away_team = away_team_element.text.strip() if away_team_element else "Desconocido Visitante"
            
            # Buscar resultado
            score_element = soup.select_one('.detailScore__wrapper, .score, .result')
            home_score, away_score = "0", "0"
            
            if score_element:
                score_text = score_element.text.strip()
                # Buscar patrones como "2-1", "2:1", "2 – 1"
                score_match = re.search(r'(\d+)\s*[-–:]\s*(\d+)', score_text)
                if score_match:
                    home_score, away_score = score_match.groups()
            
            # Buscar fecha
            date_element = soup.select_one('.duelParticipant__startTime, .mh__date')
            date_str = date_element.text.strip() if date_element else datetime.now().strftime('%d.%m.%Y')
            
            # Estado del partido
            status_element = soup.select_one('.fixedHeaderDuel__detailStatus, .detailScore__status')
            status = status_element.text.strip() if status_element else "FINISHED"
            
            # Convertir fecha
            fecha_obj = self.convert_date_flashscore(date_str)
            fecha_formatted = fecha_obj.strftime('%d/%m/%Y') if fecha_obj else datetime.now().strftime('%d/%m/%Y')
            
            basic_data = {
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score.strip(),
                'away_score': away_score.strip(),
                'date': fecha_formatted,
                'status': status,
                'raw_date': date_str
            }
            
            logger.info(f"✅ Datos básicos: {home_team} {home_score}-{away_score} {away_team}")
            return basic_data
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos básicos: {e}")
            return None
    
    async def extract_goals_precise(self, html: str) -> List[Dict]:
        """Extraer solo goles reales basándose en la estructura específica del HTML proporcionado"""
        logger.info("🎯 Extrayendo goles de manera precisa...")
        
        goals = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # ESTRATEGIA PRINCIPAL: Buscar la estructura específica de eventos
            # Basado en el HTML que proporcionaste, los eventos están en .smv__verticalSections
            
            events_section = soup.select_one('.smv__verticalSections')
            if not events_section:
                logger.warning("⚠ No se encontró la sección de eventos")
                return goals
            
            # Buscar todos los incidentes
            incidents = events_section.select('.smv__incident')
            
            for incident in incidents:
                # VERIFICAR SI ES UN GOL:
                # 1. Buscar icono de gol (svg con class="soccer" o data-testid="wcl-icon-soccer")
                goal_icon = incident.select_one('svg.soccer, [data-testid="wcl-icon-soccer"]')
                
                if goal_icon:
                    # Extraer información del gol
                    
                    # Minuto
                    time_box = incident.select_one('.smv__timeBox')
                    minute_text = time_box.text.strip() if time_box else ""
                    
                    # Limpiar minuto (quitar el apóstrofe y manejar 90+1')
                    minute_clean = self.clean_minute(minute_text)
                    if not minute_clean:
                        continue  # Si no hay minuto válido, saltar
                    
                    # Determinar equipo
                    participant_row = incident.find_parent(class_=lambda x: x and 'smv__participantRow' in x)
                    team = "unknown"
                    
                    if participant_row:
                        if 'smv__homeParticipant' in participant_row.get('class', []):
                            team = "local"
                        elif 'smv__awayParticipant' in participant_row.get('class', []):
                            team = "visitante"
                    
                    # Jugador que anota
                    player_element = incident.select_one('.smv__playerName')
                    player = player_element.text.strip() if player_element else "Desconocido"
                    
                    # Asistencia (si hay)
                    assist_element = incident.select_one('.smv__assist .smv__playerName, .smv__assistAway .smv__playerName')
                    assist = assist_element.text.strip() if assist_element else ""
                    
                    # Determinar tiempo (1er o 2º)
                    try:
                        minute_num = int(minute_clean.replace('+', '').split('+')[0])
                        half = 2 if minute_num > 45 else 1
                    except:
                        half = 1
                    
                    # También verificar si hay marcador en el incidente (confirmación adicional)
                    score_element = incident.select_one('.smv__incidentHomeScore, .smv__incidentAwayScore')
                    score = score_element.text.strip() if score_element else ""
                    
                    goal_data = {
                        'minute_raw': minute_text,
                        'minute': minute_clean,
                        'team': team,
                        'player': player,
                        'assist': assist,
                        'half': half,
                        'score_at_time': score
                    }
                    
                    # Verificar si no es duplicado
                    is_duplicate = any(
                        g['minute'] == goal_data['minute'] and 
                        g['player'] == goal_data['player'] and 
                        g['team'] == goal_data['team']
                        for g in goals
                    )
                    
                    if not is_duplicate:
                        goals.append(goal_data)
                        logger.debug(f"✅ Gol encontrado: {goal_data}")
            
            # FILTRAR DUPLICADOS ADICIONALES (mismo minuto y equipo)
            unique_goals = []
            seen = set()
            
            for goal in goals:
                key = (goal['minute'], goal['team'], goal['player'][:20])  # Usar primeros 20 chars del nombre
                if key not in seen:
                    seen.add(key)
                    unique_goals.append(goal)
            
            logger.info(f"🎯 Goles únicos encontrados: {len(unique_goals)}")
            return unique_goals
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo goles precisos: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def clean_minute(self, minute_text: str) -> str:
        """Limpiar y validar texto de minuto"""
        try:
            minute_text = minute_text.strip().replace("'", "")
            
            # Patrones válidos: "45", "45+2", "90+3"
            if not re.match(r'^\d+(\+\d+)?$', minute_text):
                return ""
            
            # Verificar que el minuto sea razonable (1-130)
            parts = minute_text.split('+')
            base_minute = int(parts[0])
            
            if base_minute < 1 or base_minute > 130:
                return ""
            
            return minute_text
            
        except:
            return ""
    
    def convert_date_flashscore(self, date_str: str) -> datetime:
        """Convertir fecha de Flashscore a objeto datetime"""
        try:
            if not date_str:
                return datetime.now()
            
            date_str = date_str.strip()
            
            # Patrones comunes:
            # "24.11.2025 21:00"
            # "Hoy 21:00"
            # "Ayer 18:30"
            
            # Si tiene formato día.mes.año hora:minuto
            if re.match(r'\d{1,2}\.\d{1,2}\.\d{4} \d{1,2}:\d{2}', date_str):
                return datetime.strptime(date_str, '%d.%m.%Y %H:%M')
            # Si solo tiene fecha
            elif re.match(r'\d{1,2}\.\d{1,2}\.\d{4}', date_str):
                return datetime.strptime(date_str, '%d.%m.%Y')
            
            # Si es "Hoy" o "Ayer", usar fecha actual
            return datetime.now()
            
        except Exception as e:
            logger.warning(f"⚠ No se pudo parsear fecha '{date_str}': {e}")
            return datetime.now()
    
    async def extract_all_events(self, html: str) -> Dict:
        """Extraer todos los eventos del partido (goles, tarjetas, cambios)"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            events_section = soup.select_one('.smv__verticalSections')
            if not events_section:
                return {"goals": [], "cards": [], "substitutions": []}
            
            # Buscar todas las secciones de tiempo
            time_sections = events_section.select('.wclHeaderSection--summary')
            
            events_data = {
                "goals": [],
                "yellow_cards": [],
                "red_cards": [],
                "substitutions": []
            }
            
            current_half = 1  # Por defecto 1er tiempo
            
            # Recorrer todos los elementos de la sección
            for element in events_section.children:
                if element.name:  # Solo elementos HTML
                    # Verificar si es encabezado de tiempo
                    if 'wclHeaderSection--summary' in element.get('class', []):
                        # Determinar qué tiempo es
                        text = element.get_text()
                        if '1er' in text or 'Primer' in text or '1º' in text:
                            current_half = 1
                        elif '2º' in text or 'Segundo' in text:
                            current_half = 2
                    
                    # Verificar si es fila de participante
                    elif 'smv__participantRow' in element.get('class', []):
                        incident = element.select_one('.smv__incident')
                        if incident:
                            await self.process_incident(incident, element, current_half, events_data)
            
            return events_data
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo todos los eventos: {e}")
            return {"goals": [], "cards": [], "substitutions": []}
    
    async def process_incident(self, incident, parent, half, events_data):
        """Procesar un incidente individual"""
        try:
            time_box = incident.select_one('.smv__timeBox')
            minute_text = time_box.text.strip() if time_box else ""
            minute_clean = self.clean_minute(minute_text)
            
            if not minute_clean:
                return
            
            # Determinar equipo
            team = "unknown"
            if 'smv__homeParticipant' in parent.get('class', []):
                team = "local"
            elif 'smv__awayParticipant' in parent.get('class', []):
                team = "visitante"
            
            # Jugador
            player_element = incident.select_one('.smv__playerName')
            player = player_element.text.strip() if player_element else ""
            
            # TIPO DE EVENTO:
            
            # 1. GOL
            goal_icon = incident.select_one('svg.soccer, [data-testid="wcl-icon-soccer"]')
            if goal_icon:
                assist_element = incident.select_one('.smv__assist .smv__playerName, .smv__assistAway .smv__playerName')
                assist = assist_element.text.strip() if assist_element else ""
                
                goal_data = {
                    'minute': minute_clean,
                    'team': team,
                    'player': player,
                    'assist': assist,
                    'half': half
                }
                
                # Verificar duplicado
                if not any(g['minute'] == minute_clean and g['player'] == player for g in events_data["goals"]):
                    events_data["goals"].append(goal_data)
            
            # 2. TARJETA AMARILLA
            yellow_card = incident.select_one('svg.yellowCard-ico, .card-ico.yellowCard-ico')
            if yellow_card:
                card_data = {
                    'minute': minute_clean,
                    'team': team,
                    'player': player,
                    'type': 'yellow',
                    'half': half
                }
                events_data["yellow_cards"].append(card_data)
            
            # 3. TARJETA ROJA (puede buscar específicamente)
            # 4. SUSTITUCIÓN
            substitution = incident.select_one('svg.substitution, .substitution')
            if substitution:
                # Buscar jugador que sale
                sub_out = incident.select_one('.smv__subDown.smv__playerName')
                player_out = sub_out.text.strip() if sub_out else ""
                
                sub_data = {
                    'minute': minute_clean,
                    'team': team,
                    'player_in': player,
                    'player_out': player_out,
                    'half': half
                }
                events_data["substitutions"].append(sub_data)
                
        except Exception as e:
            logger.debug(f"⚠ Error procesando incidente: {e}")
    
    async def get_match_data(self, url: str) -> Tuple[Optional[Dict], List[Dict]]:
        """Obtener datos del partido desde URL"""
        logger.info(f"📊 Procesando partido: {url}")
        
        try:
            # Extraer ID del partido
            match_id = self.extract_match_id(url)
            
            # Obtener HTML de la página
            html = await self.fetch_page(url)
            if not html:
                logger.error(f"❌ No se pudo obtener HTML de {url}")
                return None, []
            
            # Guardar HTML para depuración
            debug_dir = os.path.join(self.output_dir, "debug")
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            debug_file = os.path.join(debug_dir, f"{match_id}.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.debug(f"📄 HTML guardado para depuración: {debug_file}")
            
            # Extraer datos básicos
            basic_data = await self.extract_basic_data(html, url)
            if not basic_data:
                logger.error(f"❌ No se pudieron extraer datos básicos de {url}")
                return None, []
            
            # Extraer TODOS los eventos
            all_events = await self.extract_all_events(html)
            goals = all_events["goals"]
            
            # También extraer goles de manera precisa por si acaso
            precise_goals = await self.extract_goals_precise(html)
            
            # Combinar y eliminar duplicados
            combined_goals = goals + precise_goals
            unique_goals = []
            seen = set()
            
            for goal in combined_goals:
                key = (goal.get('minute', ''), goal.get('player', '')[:20])
                if key not in seen:
                    seen.add(key)
                    unique_goals.append(goal)
            
            logger.info(f"✅ {len(unique_goals)} goles únicos encontrados para {basic_data['home_team']} vs {basic_data['away_team']}")
            
            # Procesar para formato de salida
            encuentro_data, goles_data = await self.process_for_output(basic_data, unique_goals, match_id)
            
            return encuentro_data, goles_data
            
        except Exception as e:
            logger.error(f"❌ Error procesando partido {url}: {e}")
            import traceback
            traceback.print_exc()
            return None, []
    
    async def process_for_output(self, basic_data: Dict, goals: List[Dict], match_id: str) -> Tuple[Dict, List[Dict]]:
        """Procesar datos para formato de salida"""
        try:
            # Datos del encuentro
            encuentro_data = {
                'match_id': match_id,
                'jornada': 1,
                'fecha': basic_data['date'],
                'equipo_local': basic_data['home_team'],
                'equipo_visitante': basic_data['away_team'],
                'estado': basic_data['status'],
                'resultado_local': int(basic_data['home_score']) if basic_data['home_score'].isdigit() else 0,
                'resultado_visitante': int(basic_data['away_score']) if basic_data['away_score'].isdigit() else 0,
                'raw_date': basic_data.get('raw_date', '')
            }
            
            # Procesar goles
            goles_data = []
            for i, goal in enumerate(goals, 1):
                try:
                    minute_clean = self.parse_minute(goal.get('minute', '0'))
                    gol_data = {
                        'id': i,
                        'match_id': match_id,
                        'team': goal.get('team', 'unknown'),
                        'minute': minute_clean,
                        'half': goal.get('half', 1),
                        'player': goal.get('player', 'Desconocido'),
                        'assist': goal.get('assist', ''),
                        'minute_raw': goal.get('minute_raw', goal.get('minute', ''))
                    }
                    goles_data.append(gol_data)
                except Exception as e:
                    logger.warning(f"⚠ Error procesando gol {i}: {e}")
                    continue
            
            return encuentro_data, goles_data
            
        except Exception as e:
            logger.error(f"❌ Error procesando para salida: {e}")
            return {}, []
    
    def parse_minute(self, minute_str: str) -> int:
        """Parsear minuto a entero"""
        try:
            if not minute_str:
                return 0
            
            # Limpiar
            minute_str = str(minute_str).replace("'", "").strip()
            
            if '+' in minute_str:
                parts = minute_str.split('+')
                if len(parts) == 2:
                    return int(parts[0]) + int(parts[1])
            
            return int(minute_str) if minute_str.isdigit() else 0
        except:
            return 0
    
    async def save_data(self, encuentros: List[Dict], goles: List[Dict], filename_base: str):
        """Guardar datos en archivos CSV"""
        try:
            # Guardar encuentros
            encuentros_file = os.path.join(self.output_dir, f"{filename_base}_encuentros.csv")
            with open(encuentros_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(['match_id', 'jornada', 'fecha', 'equipo_local', 'equipo_visitante', 
                               'estado', 'resultado_local', 'resultado_visitante', 'raw_date'])
                
                for encuentro in encuentros:
                    writer.writerow([
                        encuentro['match_id'],
                        encuentro['jornada'],
                        encuentro['fecha'],
                        encuentro['equipo_local'],
                        encuentro['equipo_visitante'],
                        encuentro['estado'],
                        encuentro['resultado_local'],
                        encuentro['resultado_visitante'],
                        encuentro.get('raw_date', '')
                    ])
            
            # Guardar goles
            goles_file = os.path.join(self.output_dir, f"{filename_base}_goles.csv")
            with open(goles_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(['id', 'match_id', 'team', 'minute', 'half', 'player', 'assist', 'minute_raw'])
                
                for gol in goles:
                    writer.writerow([
                        gol['id'],
                        gol['match_id'],
                        gol['team'],
                        gol['minute'],
                        gol['half'],
                        gol['player'],
                        gol['assist'],
                        gol.get('minute_raw', '')
                    ])
            
            logger.info(f"💾 Archivos guardados:")
            logger.info(f"   📄 {encuentros_file}")
            logger.info(f"   📄 {goles_file}")
            
            return encuentros_file, goles_file
            
        except Exception as e:
            logger.error(f"❌ Error guardando datos: {e}")
            return None, None
    
    async def scrape_matches(self, urls: List[str], liga_nombre: str = "Partidos", save_files: bool = True):
        """Scrapear múltiples partidos con limitación de concurrencia"""
        
        if not await self.setup_session():
            return [], []
        
        try:
            logger.info(f"🏆 Iniciando scraping de {len(urls)} partidos")
            
            encuentros_procesados = []
            goles_procesados = []
            
            # Procesar partidos uno por uno para evitar sobrecarga
            for i, url in enumerate(urls, 1):
                logger.info(f"\n🔍 Procesando partido {i}/{len(urls)}")
                logger.info(f"   URL: {url}")
                
                encuentro, goles = await self.get_match_data(url)
                if encuentro:
                    encuentros_procesados.append(encuentro)
                    goles_procesados.extend(goles)
                    logger.info(f"   ✅ {len(goles)} goles extraídos")
                else:
                    logger.warning(f"   ⚠ No se pudieron extraer datos")
                
                # Pequeña pausa entre partidos
                if i < len(urls):
                    await asyncio.sleep(2)
            
            logger.info(f"\n📊 RESUMEN:")
            logger.info(f"   Encuentros procesados: {len(encuentros_procesados)}")
            logger.info(f"   Goles extraídos: {len(goles_procesados)}")
            
            if save_files and encuentros_procesados:
                filename_base = liga_nombre.lower().replace(' ', '_')
                await self.save_data(encuentros_procesados, goles_procesados, filename_base)
            
            # Mostrar resumen detallado
            self.print_detailed_summary(encuentros_procesados, goles_procesados)
            
            return encuentros_procesados, goles_procesados
            
        except Exception as e:
            logger.error(f"❌ Error en scraping: {e}")
            import traceback
            traceback.print_exc()
            return [], []
        finally:
            if self.session:
                await self.session.close()
    
    def print_detailed_summary(self, encuentros: List[Dict], goles: List[Dict]):
        """Imprimir resumen detallado"""
        print("\n" + "="*70)
        print("📊 RESUMEN DETALLADO:")
        print("="*70)
        
        if not encuentros:
            print("❌ No se procesaron encuentros")
            return
        
        print(f"Encuentros procesados: {len(encuentros)}")
        print(f"Goles extraídos: {len(goles)}")
        print()
        
        for encuentro in encuentros:
            print(f"⚽ {encuentro['equipo_local']} {encuentro['resultado_local']}-{encuentro['resultado_visitante']} {encuentro['equipo_visitante']}")
            print(f"   📅 {encuentro['fecha']} | 🆔 {encuentro['match_id']} | 📊 {encuentro['estado']}")
            
            # Goles de este partido
            partido_goles = [g for g in goles if g['match_id'] == encuentro['match_id']]
            if partido_goles:
                print(f"   🎯 Goles ({len(partido_goles)}):")
                for gol in sorted(partido_goles, key=lambda x: x['minute']):
                    equipo = "Local" if gol['team'] == 'local' else "Visitante" if gol['team'] == 'visitante' else "Desconocido"
                    minuto = f"{gol['minute']}'" if gol['minute'] else gol.get('minute_raw', '?')
                    print(f"      • Min {minuto} (T{gol['half']}): {equipo} - {gol['player']}", end="")
                    if gol.get('assist'):
                        print(f" (Asistencia: {gol['assist']})", end="")
                    print()
            else:
                print(f"   ⚠ No se encontraron goles")
            print()
    
    async def close(self):
        """Cerrar recursos"""
        if self.session and not self.session.closed:
            await self.session.close()

# FUNCIÓN PRINCIPAL MEJORADA
async def main():
    """Función principal de prueba mejorada"""
    
    print("=" * 70)
    print("🚀 SCRAPER FLASHSCORE PRECISO - VERSIÓN OPTIMIZADA")
    print("=" * 70)
    
    # URLs de prueba (las mismas que antes)
    urls = [
        "https://www.flashscore.co/partido/futbol/rcd-espanyol-QFfPdh1J/sevilla-h8oAv4Ts/?mid=GxOpMNhm",
        "https://www.flashscore.co/partido/futbol/elche-cf-4jl02tPF/real-madrid-W8mj7MDD/?mid=pfXERqVP",
        "https://www.flashscore.co/partido/futbol/atletico-madrid-jaarqpLQ/getafe-cf-dboeiWOt/?mid=UulKzN7t"
    ]
    
    scraper = FlashscorePreciseScraper()
    
    try:
        encuentros, goles = await scraper.scrape_matches(
            urls=urls,
            liga_nombre='LaLiga_Partidos_Precisos',
            save_files=True
        )
        
        print(f"\n✅ Proceso completado: {len(encuentros)} encuentros, {len(goles)} goles")
        
    except Exception as e:
        print(f"❌ Error en ejecución: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.close()

# Versión con Playwright usando Chrome real (si prefieres esta opción)
async def main_playwright_chrome():
    """Versión usando Playwright con Chrome real (más rápido si ya tienes Chrome)"""
    from playwright.async_api import async_playwright
    
    print("=" * 70)
    print("🚀 SCRAPER FLASHSCORE CON PLAYWRIGHT + CHROME REAL")
    print("=" * 70)
    
    urls = [
        "https://www.flashscore.co/partido/futbol/rcd-espanyol-QFfPdh1J/sevilla-h8oAv4Ts/?mid=GxOpMNhm"
    ]
    
    async with async_playwright() as p:
        # Usar Chrome real en lugar de Chromium
        browser = await p.chromium.launch(
            channel="chrome",  # Esto usa Chrome real si está instalado
            headless=False,    # Cambiar a True para producción
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        for url in urls:
            print(f"\n🔍 Procesando: {url}")
            
            await page.goto(url, wait_until='networkidle')
            
            # Esperar a que cargue la sección de eventos
            await page.wait_for_selector('.smv__verticalSections', timeout=10000)
            
            # Extraer datos directamente con JavaScript
            match_data = await page.evaluate("""
                () => {
                    // Extraer datos básicos
                    const homeTeam = document.querySelector('.duelParticipant__home .participant__participantName')?.textContent.trim() || 'Local';
                    const awayTeam = document.querySelector('.duelParticipant__away .participant__participantName')?.textContent.trim() || 'Visitante';
                    
                    // Extraer resultado
                    const scoreEl = document.querySelector('.detailScore__wrapper');
                    let homeScore = '0', awayScore = '0';
                    if (scoreEl) {
                        const scoreText = scoreEl.textContent.trim();
                        const match = scoreText.match(/(\\d+)\\s*[-–:]\\s*(\\d+)/);
                        if (match) {
                            homeScore = match[1];
                            awayScore = match[2];
                        }
                    }
                    
                    // Extraer goles específicamente
                    const goals = [];
                    const incidents = document.querySelectorAll('.smv__incident');
                    
                    incidents.forEach(incident => {
                        // Verificar si es un gol
                        const isGoal = incident.querySelector('svg.soccer, [data-testid="wcl-icon-soccer"]');
                        if (isGoal) {
                            const minuteEl = incident.querySelector('.smv__timeBox');
                            const playerEl = incident.querySelector('.smv__playerName');
                            const assistEl = incident.querySelector('.smv__assist .smv__playerName, .smv__assistAway .smv__playerName');
                            
                            const minute = minuteEl?.textContent.replace(/'/g, '').trim() || '';
                            const player = playerEl?.textContent.trim() || '';
                            const assist = assistEl?.textContent.trim() || '';
                            
                            // Determinar equipo
                            const participantRow = incident.closest('.smv__participantRow');
                            let team = 'unknown';
                            if (participantRow?.classList.contains('smv__homeParticipant')) {
                                team = 'local';
                            } else if (participantRow?.classList.contains('smv__awayParticipant')) {
                                team = 'visitante';
                            }
                            
                            if (minute) {
                                goals.push({
                                    minute: minute,
                                    player: player,
                                    assist: assist,
                                    team: team
                                });
                            }
                        }
                    });
                    
                    return {
                        homeTeam,
                        awayTeam,
                        homeScore,
                        awayScore,
                        goals: goals
                    };
                }
            """)
            
            print(f"✅ {match_data.homeTeam} {match_data.homeScore}-{match_data.awayScore} {match_data.awayTeam}")
            print(f"🎯 {len(match_data.goals)} goles encontrados:")
            
            for gol in match_data.goals:
                print(f"   • Min {gol.minute}' - {gol.player} ({gol.team})", end="")
                if (gol.assist):
                    print(f" [Asistencia: {gol.assist}]", end="")
                print()
        
        await browser.close()

# EJECUTAR
if __name__ == "__main__":
    # Opción 1: Solo HTTP requests (más rápido, menos recursos)
    # asyncio.run(main())
    
    # Opción 2: Playwright con Chrome real (más preciso, necesita Chrome instalado)
    asyncio.run(main_playwright_chrome())