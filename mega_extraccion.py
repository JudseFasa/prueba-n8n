import asyncio
import sqlite3
import re  # Añadir este import
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# ======================================
# CONFIG
# ======================================
DB_NAME = "futbol.db"
PARTIDOS_PARALELO = 10
PAGE_TIMEOUT = 120000
RETRIES = 3

# ======================================
# BASE DE DATOS
# ======================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
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


def save_empty_match(pais, liga, temporada, jornada, fecha, local, visitante):
    conn = sqlite3.connect(DB_NAME)
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


def update_match(pais, liga, temporada, jornada, fecha,
                 local, visitante, datos):
    conn = sqlite3.connect(DB_NAME)
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
# HELPERS
# ======================================
def parse_url(url):
    parts = url.split("/")
    pais = parts[4]
    liga_block = parts[5]

    if "-" in liga_block and liga_block[-9:-1].replace("-", "").isdigit():
        parts2 = liga_block.split("-")
        liga = "-".join(parts2[:-2])
        temporada = "-".join(parts2[-2:])
    else:
        liga = liga_block
        temporada = "actual"

    return pais, liga, temporada


async def expand_all(page):
    max_clicks = 50  # Para evitar bucle infinito
    clicks = 0
    while clicks < max_clicks:
        more = page.locator("a[data-testid='wcl-buttonLink']:has-text('Mostrar más')")
        if await more.count() == 0:
            break
        try:
            await more.first.click()
            await page.wait_for_timeout(700)
            clicks += 1
        except:
            break


async def extraer_detalles(page):
    try:
        await page.wait_for_selector(".smv__verticalSections", timeout=10000)
    except:
        # Si no hay resumen, devolver datos vacíos
        return {
            "g_local_1t": 0,
            "g_visitante_1t": 0,
            "g_local_2t": 0,
            "g_visitante_2t": 0,
            "minutos_local_1t": "",
            "minutos_visitante_1t": "",
            "minutos_local_2t": "",
            "minutos_visitante_2t": "",
        }

    secciones = await page.locator(".smv__verticalSections > div").all()

    half = None
    g1_home, g1_away = [], []
    g2_home, g2_away = [], []

    for s in secciones:
        classes = await s.get_attribute("class") or ""

        # Detectar si es encabezado de mitad
        if "wclHeaderSection--summary" in classes:
            t = await s.inner_text()
            if "1er" in t:
                half = 1
            elif "2º" in t:
                half = 2
            continue

        # Eventos de gol:
        if await s.locator("[data-testid='wcl-icon-soccer']").count() > 0:
            try:
                minuto = (await s.locator(".smv__timeBox").inner_text()).replace("'", "")
                is_home = "homeParticipant" in classes

                if half == 1:
                    (g1_home if is_home else g1_away).append(minuto)
                elif half == 2:
                    (g2_home if is_home else g2_away).append(minuto)
            except:
                continue

    def orden(x):
        try:
            if "+" in x:
                a,b = x.split("+")
                return int(a) * 100 + int(b)
            return int(x) * 100
        except:
            return 0

    return {
        "g_local_1t": len(g1_home),
        "g_visitante_1t": len(g1_away),
        "g_local_2t": len(g2_home),
        "g_visitante_2t": len(g2_away),
        "minutos_local_1t": ", ".join(sorted(g1_home, key=orden)),
        "minutos_visitante_1t": ", ".join(sorted(g1_away, key=orden)),
        "minutos_local_2t": ", ".join(sorted(g2_home, key=orden)),
        "minutos_visitante_2t": ", ".join(sorted(g2_away, key=orden)),
    }


# ======================================
# SCRAPER DE UNA TEMPORADA
# ======================================
async def scrape_temporada(browser, url):
    pais, liga, temporada = parse_url(url)

    print(f"\n====== {pais.upper()} | {liga} | {temporada} ======")

    page = await browser.new_page()
    await page.goto(url, timeout=PAGE_TIMEOUT)

    await expand_all(page)
    await page.wait_for_timeout(1500)

    # Esperar a que carguen los elementos
    try:
        await page.wait_for_selector(".event__round, .event__match", timeout=10000)
    except:
        print(f"⚠️ No se encontraron partidos para {liga} {temporada}")
        await page.close()
        return

    nodos = page.locator(".event__round, .event__match")
    total = await nodos.count()

    jornada_actual = None
    partidos_batch = []

    # Recorrer nodos en orden natural
    for i in range(total):
        nodo = nodos.nth(i)
        
        # Verificar si es jornada
        class_name = await nodo.get_attribute("class") or ""
        if "event__round" in class_name:
            text = await nodo.inner_text()
            text = text.strip()
            
            # Usar regex para extraer el número de jornada
            match = re.search(r'Jornada\s+(\d+)', text, re.IGNORECASE)
            if match:
                jornada_actual = int(match.group(1))
                print(f"📅 Jornada {jornada_actual}")
            else:
                jornada_actual = None  # bloquear fases no deseadas
            
            continue

        # Solo procesar partidos dentro de jornadas válidas
        if jornada_actual is None:
            continue

        # Extraer datos del partido
        try:
            fecha_elem = nodo.locator(".event__time")
            local_elem = nodo.locator(".event__participant--home")
            visitante_elem = nodo.locator(".event__participant--away")
            
            fecha = await fecha_elem.inner_text() if await fecha_elem.count() > 0 else ""
            local = await local_elem.inner_text() if await local_elem.count() > 0 else ""
            visitante = await visitante_elem.inner_text() if await visitante_elem.count() > 0 else ""
            
            if not local or not visitante:
                continue
                
            link = await nodo.get_attribute("id")
            if not link or not link.startswith("g_"):
                continue

            save_empty_match(pais, liga, temporada, jornada_actual, fecha, local, visitante)
            partidos_batch.append((jornada_actual, fecha, local, visitante, link))
            
            print(f"  ➕ {local} vs {visitante} - {fecha}")
            
        except Exception as e:
            print(f"  ❌ Error extrayendo partido: {e}")
            continue

    await page.close()

    # ===============================
    # Procesar partidos en paralelo
    # ===============================
    if partidos_batch:
        print(f"📊 Procesando {len(partidos_batch)} partidos...")
        
        sem = asyncio.Semaphore(PARTIDOS_PARALELO)

        async def procesar(match):
            async with sem:
                return await scrape_partido(browser, pais, liga, temporada, *match)

        await asyncio.gather(*(procesar(p) for p in partidos_batch))
    else:
        print("⚠️ No se encontraron partidos para procesar")


# ======================================
# SCRAPEAR DETALLE DE PARTIDO
# ======================================
async def scrape_partido(browser, pais, liga, temporada,
                         jornada, fecha, local, visitante, match_id):
    
    # Limpiar el ID del partido
    match_id = match_id.replace("g_1_", "")
    url = f"https://www.flashscore.co/partido/{match_id}/#/resumen-del-partido/resumen"

    for i in range(RETRIES):
        try:
            page = await browser.new_page()
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(2000)  # Esperar a que cargue
            break
        except PlaywrightTimeout:
            if i == RETRIES - 1:
                print(f"❌ Timeout cargando: {local} vs {visitante}")
                await page.close()
                return
            continue
        except Exception as e:
            if i == RETRIES - 1:
                print(f"❌ Error cargando {url}: {e}")
                return
            continue
    
    try:
        datos = await extraer_detalles(page)
        update_match(pais, liga, temporada, jornada, fecha, local, visitante, datos)
        print(f"  ✅ {local} {datos['g_local_1t']+datos['g_local_2t']}-{datos['g_visitante_1t']+datos['g_visitante_2t']} {visitante}")
    except Exception as e:
        print(f"  ❌ Error procesando {local} vs {visitante}: {e}")
    finally:
        await page.close()


# ======================================
# MAIN
# ======================================
async def main(urls):
    init_db()
    print("🚀 Iniciando scraping...")

    async with async_playwright() as p:
        # Usar headless=True para mejor rendimiento
        browser = await p.chromium.launch(headless=True)

        # Procesar temporada por temporada
        for url in urls:
            try:
                await scrape_temporada(browser, url)
            except Exception as e:
                print(f"❌ Error procesando {url}: {e}")
                continue

        await browser.close()
    
    print("\n✅ Scraping completado!")


# ======================================
# EJEMPLO DE LLAMADA
# ======================================
URLS = [
    "https://www.flashscore.co/futbol/espana/laliga-ea-sports-2024-2025/resultados/",
    "https://www.flashscore.co/futbol/espana/laliga-ea-sports-2023-2024/resultados/"
]

if __name__ == "__main__":
    asyncio.run(main(URLS))