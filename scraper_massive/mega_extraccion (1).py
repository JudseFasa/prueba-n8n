import asyncio
import sqlite3
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import time
import os
from datetime import datetime

# ======================================
# CONFIG
# ======================================
PARTIDOS_PARALELO = 2
PAGE_TIMEOUT = 60000
RETRIES = 2
MAX_TEMPORADAS = 5

# ======================================
# URL HELPERS SIMPLIFICADOS
# ======================================
def construir_url_resultados(url_base):
    """Añade /resultados/ a URL base"""
    return f"{url_base.rstrip('/')}/resultados/"

def construir_url_archivo(url_base):
    """Añade /archivo/ a URL base"""
    return f"{url_base.rstrip('/')}/archivo/"

# ======================================
# POOL DE PESTAÑAS CON LOCK
# ======================================
class TabWrapper:
    def __init__(self, page):
        self.page = page
        self.lock = asyncio.Lock()

async def create_tab_pool(context):
    return [TabWrapper(await context.new_page()) for _ in range(PARTIDOS_PARALELO)]

async def acquire_tab(pool):
    while True:
        for tab in pool:
            if not tab.lock.locked():
                await tab.lock.acquire()
                return tab
        await asyncio.sleep(0.05)

# ======================================
# BASE DE DATOS
# ======================================
def init_db(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS partidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pais TEXT,
            liga TEXT,
            temporada TEXT,
            jornada INTEGER,
            fecha TEXT,
            local TEXT,
            visitante TEXT,
            g_local_1t INTEGER,
            g_visitante_1t INTEGER,
            g_local_2t INTEGER,
            g_visitante_2t INTEGER,
            minutos_local_1t TEXT,
            minutos_visitante_1t TEXT,
            minutos_local_2t TEXT,
            minutos_visitante_2t TEXT,
            UNIQUE(pais, liga, temporada, jornada, fecha, local, visitante)
        )
    """)
    conn.commit()
    conn.close()

def save_empty_match(db_name, pais, liga, temporada, jornada, fecha, local, visitante):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO partidos
        (pais, liga, temporada, jornada, fecha, local, visitante,
         g_local_1t, g_visitante_1t, g_local_2t, g_visitante_2t,
         minutos_local_1t, minutos_visitante_1t, minutos_local_2t, minutos_visitante_2t)
        VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, '', '', '', '')
    """,(pais, liga, temporada, jornada, fecha, local, visitante))
    conn.commit()
    conn.close()

def update_match(db_name, pais, liga, temporada, jornada, fecha, local, visitante, datos):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        UPDATE partidos SET
            g_local_1t = ?, g_visitante_1t = ?, g_local_2t = ?, g_visitante_2t = ?,
            minutos_local_1t = ?, minutos_visitante_1t = ?,
            minutos_local_2t = ?, minutos_visitante_2t = ?
        WHERE pais = ? AND liga = ? AND temporada = ? AND jornada = ?
          AND fecha = ? AND local = ? AND visitante = ?
    """,(
        datos["g_local_1t"], datos["g_visitante_1t"],
        datos["g_local_2t"], datos["g_visitante_2t"],
        datos["minutos_local_1t"], datos["minutos_visitante_1t"],
        datos["minutos_local_2t"], datos["minutos_visitante_2t"],
        pais, liga, temporada, jornada, fecha, local, visitante
    ))
    conn.commit()
    conn.close()

# ======================================
# HELPERS SIMPLIFICADOS
# ======================================
def parse_url(url):
    """Extrae país y liga de URL base"""
    parts = url.rstrip('/').split('/')
    if len(parts) >= 6:  # https://www.flashscore.co/futbol/pais/liga
        pais = parts[-2]
        liga = parts[-1]
        
        # Verificar si la liga ya incluye temporada (años)
        year_matches = re.findall(r'\b(20\d{2})\b', liga)
        if len(year_matches) >= 2:
            liga_parts = liga.rsplit('-', 2)
            liga_base = liga_parts[0]
            temporada = f"{year_matches[0]}-{year_matches[1]}"
            return pais, liga_base, temporada
        
        return pais, liga, "actual"
    return "unknown", "unknown", "actual"

def extraer_año_url(url):
    """Extrae año de temporada desde la URL"""
    year_matches = re.findall(r'\b(20\d{2})\b', url)
    if len(year_matches) >= 2:
        return f"{year_matches[0]}-{year_matches[1]}"
    elif len(year_matches) == 1:
        return f"{year_matches[0]}-{int(year_matches[0])+1}"
    return None

def get_temporada_actual():
    """Obtiene la temporada actual"""
    ahora = datetime.now()
    año = ahora.year
    mes = ahora.month
    return f"{año}-{año+1}" if mes >= 8 else f"{año-1}-{año}"

async def expand_all(page):
    """Expande botones de expansión"""
    botones = page.locator("a[data-testid='wcl-buttonLink']")
    count = await botones.count()
    for i in range(count):
        try:
            await botones.nth(i).click()
            await asyncio.sleep(0.05)
        except:
            pass

async def click_mostrar_mas_partidos(page):
    """Hace clic en 'Mostrar más partidos' hasta agotar"""
    for i in range(15):
        boton = page.locator("a[data-testid='wcl-buttonLink']", has_text="Mostrar más partidos")
        if await boton.count() == 0:
            boton = page.locator("a[data-testid='wcl-buttonLink']:has-text('Mostrar')")
        
        if await boton.count() == 0:
            break
            
        try:
            await boton.scroll_into_view_if_needed()
            await boton.click()
            print(f"    🔽 Clic {i+1} en 'Mostrar más partidos'")
            await asyncio.sleep(1)
        except:
            break
    
    print("    ✅ Todos los partidos cargados")

async def extraer_detalles(detail_page):
    try:
        await detail_page.wait_for_selector(".smv__verticalSections", timeout=8000)
    except:
        return {
            "g_local_1t": 0, "g_visitante_1t": 0,
            "g_local_2t": 0, "g_visitante_2t": 0,
            "minutos_local_1t": "", "minutos_visitante_1t": "",
            "minutos_local_2t": "", "minutos_visitante_2t": "",
        }
    
    sections = await detail_page.locator(".smv__verticalSections > div").all()
    current_half = None
    goles = [[[], []], [[], []]]  # [1t/2t][home/away]
    
    for sec in sections:
        try:
            if await sec.evaluate("e => e.classList.contains('wclHeaderSection--summary')"):
                half_elem = sec.locator(".wcl-overline_uwiIT:has-text('Tiempo')")
                if await half_elem.count() > 0:
                    txt = await half_elem.inner_text()
                    current_half = 1 if "1er" in txt else 2 if "2º" in txt else None
                continue
            
            if await sec.locator("[data-testid='wcl-icon-soccer']").count() > 0:
                time_elem = sec.locator(".smv__timeBox")
                if await time_elem.count() > 0:
                    time = (await time_elem.inner_text()).rstrip("'")
                    is_home = 'smv__homeParticipant' in await sec.evaluate("el => Array.from(el.classList)")
                    
                    if current_half == 1:
                        goles[0][0 if is_home else 1].append(time)
                    elif current_half == 2:
                        goles[1][0 if is_home else 1].append(time)
        except:
            continue
    
    def orden(x):
        try:
            if "+" in x:
                a, b = x.split("+")
                return int(a) * 100 + int(b)
            return int(x) * 100
        except:
            return 0
    
    return {
        "g_local_1t": len(goles[0][0]),
        "g_visitante_1t": len(goles[0][1]),
        "g_local_2t": len(goles[1][0]),
        "g_visitante_2t": len(goles[1][1]),
        "minutos_local_1t": ", ".join(sorted(goles[0][0], key=orden)),
        "minutos_visitante_1t": ", ".join(sorted(goles[0][1], key=orden)),
        "minutos_local_2t": ", ".join(sorted(goles[1][0], key=orden)),
        "minutos_visitante_2t": ", ".join(sorted(goles[1][1], key=orden)),
    }

async def obtener_temporadas_archivo(context, url_base, max_temporadas=4):
    """Obtiene temporadas pasadas desde la página de archivo"""
    page = await context.new_page()
    temporadas_info = []
    
    try:
        # Construir URL de archivo
        archivo_url = construir_url_archivo(url_base)
        print(f"  📂 Accediendo a: {archivo_url}")
        
        await page.goto(archivo_url, timeout=PAGE_TIMEOUT, wait_until="networkidle")
        
        # Buscar elementos de temporadas
        season_elements = await page.locator("a.archiveLatte__text.archiveLatte__text--clickable").all()
        
        if not season_elements:
            season_elements = await page.locator("a:has-text('20')").all()
        
        print(f"  🔍 Encontrados {len(season_elements)} elementos")
        
        # Procesar elementos
        for element in season_elements[:max_temporadas * 2]:
            try:
                href = await element.get_attribute("href")
                text = await element.text_content()
                
                if not href or not text:
                    continue
                
                # Filtrar solo temporadas (contienen años y no son equipos)
                if not re.search(r'\d{4}', href) or "/equipo/" in href:
                    continue
                
                # Construir URL completa
                full_url = f"https://www.flashscore.co{href}"
                if not full_url.endswith("/resultados/"):
                    full_url = full_url.rstrip('/') + "/resultados/"
                
                # Extraer año
                año = extraer_año_url(full_url)
                if not año:
                    continue
                
                # Obtener país y liga de la URL base
                pais, liga, _ = parse_url(url_base)
                
                temporadas_info.append({
                    "url": full_url,
                    "nombre": text.strip()[:50],
                    "año": año,
                    "pais": pais,
                    "liga": liga
                })
                
                if len(temporadas_info) >= max_temporadas:
                    break
                    
            except:
                continue
                
    except Exception as e:
        print(f"⚠️ Error obteniendo temporadas: {e}")
    finally:
        await page.close()
    
    # Ordenar por año y limitar
    temporadas_info.sort(key=lambda x: x['año'], reverse=True)
    return temporadas_info[:max_temporadas]

async def obtener_todas_temporadas(context, url_base, max_temporadas=MAX_TEMPORADAS):
    """Obtiene temporadas: actual + pasadas"""
    temporadas_info = []
    
    # 1. Añadir temporada actual
    pais, liga, _ = parse_url(url_base)
    año_actual = get_temporada_actual()
    
    temporada_actual = {
        "url": construir_url_resultados(url_base),
        "nombre": f"{liga} {año_actual}",
        "año": año_actual,
        "pais": pais,
        "liga": liga
    }
    
    temporadas_info.append(temporada_actual)
    print(f"  📅 Temporada actual: {año_actual}")
    
    # 2. Obtener temporadas pasadas
    temporadas_pasadas = await obtener_temporadas_archivo(context, url_base, max_temporadas - 1)
    
    # 3. Combinar evitando duplicados
    años_existentes = {año_actual}
    for temp in temporadas_pasadas:
        if temp['año'] not in años_existentes:
            temporadas_info.append(temp)
            años_existentes.add(temp['año'])
    
    print(f"  📊 Total temporadas: {len(temporadas_info)}")
    
    # Ordenar por año
    temporadas_info.sort(key=lambda x: x['año'], reverse=True)
    return temporadas_info[:max_temporadas]

# ======================================
# SCRAPER DE TEMPORADA
# ======================================
async def scrape_temporada(context, main_page, url_resultados, db_name, liga_info):
    """Procesa una temporada completa"""
    pais, liga, temporada = liga_info
    
    print(f"\n====== {pais.upper()} | {liga} | {temporada} ======")
    print(f"🌐 URL: {url_resultados}")

    await main_page.goto(url_resultados, timeout=PAGE_TIMEOUT, wait_until="networkidle")
    
    try:
        print("    🔽 Cargando todos los partidos...")
        await click_mostrar_mas_partidos(main_page)
        await main_page.wait_for_selector(".event__match", timeout=5000)
    except:
        print(f"⚠️ No se encontraron partidos")
        return

    # Pool de pestañas
    tab_pool = await create_tab_pool(context)
    await expand_all(main_page)

    # Extraer jornadas
    jornada_actual = 1
    round_elements = main_page.locator(".event__round")
    total_rounds = await round_elements.count()
    
    for i in range(total_rounds):
        try:
            txt = await round_elements.nth(i).inner_text()
            match = re.search(r'Jornada\s+(\d+)', txt, re.IGNORECASE)
            if match:
                jornada_actual = int(match.group(1))
                print(f"📅 Jornada {jornada_actual}")
        except:
            continue

    # Extraer partidos
    partidos_data = []
    match_elements = main_page.locator(".event__match")
    total_matches = await match_elements.count()
    
    print(f"📊 Encontrados {total_matches} partidos...")
    
    for i in range(total_matches):
        try:
            item = match_elements.nth(i)
            datos = await item.evaluate("""
                (node) => ({
                    fecha: node.querySelector('.event__time')?.textContent?.trim() || '',
                    local: node.querySelector('.event__homeParticipant')?.textContent?.trim() || '',
                    visitante: node.querySelector('.event__awayParticipant')?.textContent?.trim() || ''
                })
            """)
            
            fecha = datos["fecha"]
            local = datos["local"]
            visitante = datos["visitante"]
            
            link_elem = item.locator("a.eventRowLink")
            href = await link_elem.get_attribute("href") if await link_elem.count() > 0 else None
            
            if not href:
                parent_id = await item.get_attribute("id")
                if parent_id and parent_id.startswith("g_"):
                    href = f"/partido/{parent_id.replace('g_','')}/"

            if not href:
                continue

            full_href = f"https://www.flashscore.co{href}" if href.startswith("/") else href

            # Guardar en DB
            save_empty_match(db_name, pais, liga, temporada, jornada_actual, fecha, local, visitante)
            partidos_data.append((jornada_actual, fecha, local, visitante, full_href))

            if len(partidos_data) % 20 == 0:
                print(f"  ➕ {len(partidos_data)} partidos extraídos...")

        except:
            continue

    # Procesar partidos en paralelo
    if partidos_data:
        print(f"📊 Procesando {len(partidos_data)} partidos...")

        async def procesar_partido(match):
            tab = await acquire_tab(tab_pool)
            try:
                await tab.page.goto("about:blank")
                return await scrape_partido_detalle(tab.page, db_name, pais, liga, temporada, *match)
            finally:
                tab.lock.release()

        # Procesar en lotes
        batch_size = PARTIDOS_PARALELO * 2
        for i in range(0, len(partidos_data), batch_size):
            batch = partidos_data[i:i+batch_size]
            await asyncio.gather(*(procesar_partido(p) for p in batch))
    else:
        print("⚠️ No se encontraron partidos")
    
    # Limpiar
    for tab in tab_pool:
        await tab.page.close()

async def scrape_partido_detalle(detail_page, db_name, pais, liga, temporada, jornada, fecha, local, visitante, match_url):
    """Procesa detalle de un partido"""
    try:
        for intento in range(RETRIES):
            try:
                await detail_page.goto(match_url, wait_until="domcontentloaded", timeout=10000)
                await detail_page.wait_for_selector(".smv__verticalSections", timeout=5000)
                break
            except:
                if intento == RETRIES - 1:
                    return
                await asyncio.sleep(0.5)

        goles = await extraer_detalles(detail_page)
        update_match(db_name, pais, liga, temporada, jornada, fecha, local, visitante, goles)

        total_local = goles["g_local_1t"] + goles["g_local_2t"]
        total_visitante = goles["g_visitante_1t"] + goles["g_visitante_2t"]
        print(f"  ✅ {local} {total_local}-{total_visitante} {visitante}")

    except Exception as e:
        print(f"  ❌ Error en {local} vs {visitante}: {str(e)[:50]}")

# ======================================
# MAIN
# ======================================
async def main(urls_base):
    """Función principal"""
    print("🚀 Iniciando scraping...")
    print(f"📅 Temporada actual: {get_temporada_actual()}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage",
                "--disable-setuid-sandbox", "--blink-settings=imagesEnabled=false",
                "--disable-software-rasterizer", "--disable-background-networking",
                "--disable-default-apps", "--disable-sync", "--disable-translate",
                "--metrics-recording-only", "--mute-audio", "--no-first-run",
                "--disable-notifications",
            ]
        )

        context = await browser.new_context()
        await context.route("**/*.{png,jpg,jpeg,gif,svg,webp}", lambda r: r.abort())
        await context.route("**/*.{css,woff,woff2}", lambda r: r.abort())

        main_page = await context.new_page()

        for entry in urls_base:
            # Formato: "url_base|nombre_base"
            if "|" in entry:
                url_base, nombre_base = entry.split("|")
                nombre_base = nombre_base.strip()
            else:
                url_base = entry
                nombre_base = url_base.split("/")[-1]  # Usar último segmento como nombre
            
            url_base = url_base.strip().rstrip('/')
            DB_FOLDER = "X:/prueba n8n/data"

            try:
                print(f"\n🔍 Procesando liga: {nombre_base}")
                print(f"🌐 URL base: {url_base}")

                # Obtener temporadas
                temporadas_info = await obtener_todas_temporadas(context, url_base, MAX_TEMPORADAS)
                
                if not temporadas_info:
                    print(f"⚠️ No se encontraron temporadas")
                    continue
                
                # Procesar cada temporada
                for i, temp_info in enumerate(temporadas_info, 1):
                    try:
                        print(f"\n📊 [{i}/{len(temporadas_info)}] {temp_info['nombre']}")
                        
                        # Crear nombre de archivo
                        año_limpio = temp_info['año'].replace("-", "_")
                        nombre_archivo = f"{nombre_base}_{año_limpio}"
                        db_name = os.path.join(DB_FOLDER, f"{nombre_archivo}.db")
                        
                        print(f"📄 Base de datos: {db_name}")
                        init_db(db_name)
                        
                        # Procesar temporada
                        await scrape_temporada(
                            context, main_page, temp_info['url'], db_name,
                            (temp_info['pais'], temp_info['liga'], temp_info['año'])
                        )
                        
                    except Exception as e:
                        print(f"❌ Error en temporada: {e}")
                        continue

            except Exception as e:
                print(f"❌ Error procesando {url_base}: {e}")
                continue

        await main_page.close()
        await browser.close()

    print("\n✅ Scraping completado!")

# ======================================
# EJEMPLO DE LLAMADA - SOLO URLS BASE
# ======================================
URLS_BASE = [
    # Formato: "URL_BASE|NOMBRE_ARCHIVO"
    "https://www.flashscore.co/futbol/colombia/primera-a|Colombia",
    "https://www.flashscore.co/futbol/belgica/jupiler-pro-league|Bélgica",
    "https://www.flashscore.co/futbol/espana/laliga-ea-sports|España",
    "https://www.flashscore.co/futbol/italia/serie-a|Italia",
]

if __name__ == "__main__":
    inicio = time.perf_counter()
    asyncio.run(main(URLS_BASE))
    fin = time.perf_counter()
    print(f"\n⏱️ Tiempo total: {fin - inicio:.2f} segundos")