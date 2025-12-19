# scraper_lite.py
import asyncio
import json
from playwright.async_api import async_playwright
from supabase import create_client
from datetime import datetime, timedelta
import os
import sys

# ======================================
# CONFIGURACIÓN
# ======================================
SUPABASE_URL = "https://mvsnymlcqutxnmnfxdgt.supabase.co"
SUPABASE_KEY = "TU_SUPABASE_SERVICE_KEY"  # ¡IMPORTANTE! Consíguela en Settings > API
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# LIGAS A MONITOREAR (ajusta según necesites)
LIGAS_MONITOREO = [
    {
        "pais": "españa",
        "liga": "laliga",
        "liga_id": 1  # ID que ya tienes en Supabase
    },
    {
        "pais": "inglaterra", 
        "liga": "premier-league",
        "liga_id": 2
    },
    {
        "pais": "italia",
        "liga": "serie-a",
        "liga_id": 3
    }
]

# ======================================
# FUNCIONES AUXILIARES
# ======================================
def obtener_temporada_actual():
    """Obtiene ID de temporada actual desde Supabase"""
    try:
        response = supabase.table("temporadas")\
            .select("id")\
            .eq("is_current", True)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
    except Exception as e:
        print(f"Error obteniendo temporada: {e}")
    
    return None

def partido_existe(liga_id, temporada_id, fecha, local, visitante):
    """Verifica si partido ya existe en Supabase"""
    try:
        response = supabase.table("partidos")\
            .select("id")\
            .eq("liga_id", liga_id)\
            .eq("temporada_id", temporada_id)\
            .eq("fecha", fecha)\
            .eq("local_id", local)\
            .eq("visitante_id", visitante)\
            .execute()
        
        return len(response.data) > 0
    except:
        return False

def obtener_equipo_id(nombre):
    """Obtiene o crea equipo en Supabase"""
    try:
        # Buscar equipo
        response = supabase.table("equipos")\
            .select("id")\
            .eq("nombre", nombre)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        
        # Crear equipo si no existe
        insert = supabase.table("equipos")\
            .insert({"nombre": nombre})\
            .execute()
        
        return insert.data[0]["id"]
    except Exception as e:
        print(f"Error con equipo {nombre}: {e}")
        return None

# ======================================
# SCRAPER PRINCIPAL
# ======================================
async def scrape_liga_actualizada(liga_config):
    """Scrapea partidos RECIENTES de una liga específica"""
    pais = liga_config["pais"]
    liga = liga_config["liga"]
    liga_id = liga_config["liga_id"]
    
    print(f"🔍 Scrapeando {pais}/{liga}...")
    
    partidos_nuevos = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            # Ir a resultados de la liga
            url = f"https://www.flashscore.co/futbol/{pais}/{liga}/resultados/"
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Esperar a que carguen los partidos
            await page.wait_for_selector('.event__match', timeout=10000)
            
            # Obtener partidos de las últimas 48 horas
            partidos = await page.evaluate("""
                () => {
                    const partidos = [];
                    const hoy = new Date();
                    const ayer = new Date(hoy);
                    ayer.setDate(ayer.getDate() - 1);
                    
                    const elementos = document.querySelectorAll('.event__match');
                    
                    for (const el of elementos) {
                        try {
                            // Extraer datos básicos
                            const timeElem = el.querySelector('.event__time');
                            const homeElem = el.querySelector('.event__homeParticipant .participant__participantName');
                            const awayElem = el.querySelector('.event__awayParticipant .participant__participantName');
                            const scoreElem = el.querySelector('.event__score');
                            
                            if (!homeElem || !awayElem) continue;
                            
                            const fechaTexto = timeElem ? timeElem.textContent.trim() : '';
                            const local = homeElem.textContent.trim();
                            const visitante = awayElem.textContent.trim();
                            const resultado = scoreElem ? scoreElem.textContent.trim() : '0-0';
                            
                            // Solo partidos recientes (hoy o ayer)
                            if (fechaTexto.toLowerCase().includes('today') || 
                                fechaTexto.toLowerCase().includes('ayer') ||
                                fechaTexto.toLowerCase().includes('hoy') ||
                                fechaTexto.toLowerCase().includes('yesterday')) {
                                
                                // Convertir fecha
                                let fecha = new Date();
                                if (fechaTexto.toLowerCase().includes('ayer') || 
                                    fechaTexto.toLowerCase().includes('yesterday')) {
                                    fecha.setDate(fecha.getDate() - 1);
                                }
                                
                                const fechaISO = fecha.toISOString().split('T')[0];
                                
                                // Parsear resultado
                                let goles_local = 0;
                                let goles_visitante = 0;
                                
                                if (resultado.includes('-')) {
                                    const [golL, golV] = resultado.split('-').map(g => parseInt(g.trim()) || 0);
                                    goles_local = golL;
                                    goles_visitante = golV;
                                }
                                
                                partidos.push({
                                    fecha: fechaISO,
                                    local: local,
                                    visitante: visitante,
                                    goles_local: goles_local,
                                    goles_visitante: goles_visitante,
                                    resultado: resultado
                                });
                            }
                        } catch (e) {
                            console.error('Error parseando partido:', e);
                        }
                    }
                    
                    return partidos.slice(0, 10); // Máximo 10 partidos por ejecución
                }
            """)
            
            print(f"  📊 Encontrados {len(partidos)} partidos recientes")
            
            # Obtener temporada actual
            temporada_id = obtener_temporada_actual()
            if not temporada_id:
                print("  ⚠️  No se encontró temporada actual")
                return []
            
            # Procesar cada partido
            for partido in partidos:
                try:
                    # Verificar si ya existe
                    existe = partido_existe(
                        liga_id, 
                        temporada_id, 
                        partido["fecha"], 
                        partido["local"], 
                        partido["visitante"]
                    )
                    
                    if existe:
                        print(f"  ⏭️  Partido ya existe: {partido['local']} vs {partido['visitante']}")
                        continue
                    
                    # Obtener IDs de equipos
                    local_id = obtener_equipo_id(partido["local"])
                    visitante_id = obtener_equipo_id(partido["visitante"])
                    
                    if not local_id or not visitante_id:
                        print(f"  ⚠️  Error obteniendo IDs de equipos")
                        continue
                    
                    # Preparar datos para Supabase
                    partido_data = {
                        "liga_id": liga_id,
                        "temporada_id": temporada_id,
                        "fase_id": 1,  # ID de fase "Temporada Regular" (ajusta según tu DB)
                        "jornada": 0,  # Se actualizará manualmente si es necesario
                        "fecha": partido["fecha"],
                        "local_id": local_id,
                        "visitante_id": visitante_id,
                        "g_local_1t": partido["goles_local"],  # Asumimos goles totales (ajustable)
                        "g_visitante_1t": partido["goles_visitante"],
                        "g_local_2t": 0,
                        "g_visitante_2t": 0,
                        "minutos_local_1t": "",
                        "minutos_visitante_1t": "",
                        "minutos_local_2t": "",
                        "minutos_visitante_2t": "",
                        "status": "FINISHED"
                    }
                    
                    # Insertar en Supabase
                    response = supabase.table("partidos")\
                        .insert(partido_data)\
                        .execute()
                    
                    if response.data:
                        print(f"  ✅ Nuevo: {partido['local']} {partido['resultado']} {partido['visitante']}")
                        partidos_nuevos.append({
                            "liga": liga,
                            "partido": f"{partido['local']} vs {partido['visitante']}",
                            "resultado": partido["resultado"]
                        })
                        
                except Exception as e:
                    print(f"  ❌ Error procesando partido: {e}")
                    continue
            
        except Exception as e:
            print(f"  ❌ Error scrapeando {liga}: {e}")
        finally:
            await browser.close()
    
    return partidos_nuevos

async def main():
    """Función principal"""
    print("=" * 50)
    print(f"🔄 SCRAPER LITE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    todos_partidos = []
    
    # Scrapear cada liga
    for liga in LIGAS_MONITOREO:
        partidos = await scrape_liga_actualizada(liga)
        todos_partidos.extend(partidos)
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN:")
    print(f"Total partidos nuevos: {len(todos_partidos)}")
    
    for p in todos_partidos:
        print(f"  • {p['liga']}: {p['partido']} ({p['resultado']})")
    
    # Guardar log
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "partidos_nuevos": len(todos_partidos),
        "ligas": [l["liga"] for l in LIGAS_MONITOREO],
        "detalles": todos_partidos
    }
    
    # Puedes guardar el log donde quieras (archivo, Supabase, etc.)
    with open("scraper_lite_log.json", "a") as f:
        f.write(json.dumps(log_data) + "\n")
    
    print(f"\n✅ Scraper completado a las {datetime.now().strftime('%H:%M:%S')}")
    
    return todos_partidos

# ======================================
# EJECUCIÓN
# ======================================
if __name__ == "__main__":
    # Para ejecutar desde n8n o línea de comandos
    result = asyncio.run(main())
    
    # Devolver resultado para n8n
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(json.dumps({"partidos_nuevos": result}))