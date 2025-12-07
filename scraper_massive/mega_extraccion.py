import asyncio
import sqlite3
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import time
import os

# ======================================
# CONFIG
# ======================================
PARTIDOS_PARALELO = 4
PAGE_TIMEOUT = 120000
RETRIES = 3

# ======================================
# POOL DE PESTAÑAS CON LOCK
# ======================================
class TabWrapper:
    def __init__(self, page):
        self.page = page
        self.lock = asyncio.Lock()

async def create_tab_pool(context):
    pool = []
    for _ in range(PARTIDOS_PARALELO):
        page = await context.new_page()
        pool.append(TabWrapper(page))
    return pool

async def acquire_tab(pool):
    while True:
        for tab in pool:
            if not tab.lock.locked():
                await tab.lock.acquire()
                return tab
        await asyncio.sleep(0.05)  # esperamos hasta que una pestaña esté libre

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


def update_match(db_name, pais, liga, temporada, jornada, fecha,
                 local, visitante, datos):
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
    botones = page.locator("a[data-testid='wcl-buttonLink']")

    if await botones.count() == 0:
        return  # nada que expandir

    while True:
        count = await botones.count()
        if count == 0:
            break
        for i in range(count):
            try:
                await botones.nth(i).click()
            except:
                pass
        await page.wait_for_timeout(300)


async def extraer_detalles(detail_page):
    try:
        await detail_page.wait_for_selector(".smv__verticalSections", timeout=10000)
    except:
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
    
    sections = await detail_page.locator(".smv__verticalSections > div").all()
    current_half = None
    goles_1t_home, goles_1t_away = [], []
    goles_2t_home, goles_2t_away = [], []
    
    for sec in sections:
        try:
            if await sec.evaluate("e => e.classList.contains('wclHeaderSection--summary')"):
                half_elem = sec.locator(".wcl-overline_uwiIT:has-text('Tiempo')")
                if await half_elem.count() > 0:
                    txt = await half_elem.inner_text()
                    if "1er" in txt: current_half = 1
                    elif "2º" in txt: current_half = 2
                continue
            
            if await sec.locator("[data-testid='wcl-icon-soccer']").count() > 0:
                time_elem = sec.locator(".smv__timeBox")
                if await time_elem.count() > 0:
                    time = (await time_elem.inner_text()).rstrip("'")
                    class_list = await sec.evaluate("el => Array.from(el.classList)")
                    team = 'home' if 'smv__homeParticipant' in class_list else 'away'
                    if current_half == 1:
                        (goles_1t_home if team == 'home' else goles_1t_away).append(time)
                    elif current_half == 2:
                        (goles_2t_home if team == 'home' else goles_2t_away).append(time)
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
        "g_local_1t": len(goles_1t_home),
        "g_visitante_1t": len(goles_1t_away),
        "g_local_2t": len(goles_2t_home),
        "g_visitante_2t": len(goles_2t_away),
        "minutos_local_1t": ", ".join(sorted(goles_1t_home, key=orden)),
        "minutos_visitante_1t": ", ".join(sorted(goles_1t_away, key=orden)),
        "minutos_local_2t": ", ".join(sorted(goles_2t_home, key=orden)),
        "minutos_visitante_2t": ", ".join(sorted(goles_2t_away, key=orden)),
    }

# ======================================
# SCRAPER DE UNA TEMPORADA (CON POOL DE PESTAÑAS CON LOCK)
# ======================================
async def scrape_temporada(context, main_page, url, db_name):
    pais, liga, temporada = parse_url(url)

    print(f"\n====== {pais.upper()} | {liga} | {temporada} ======")

    await main_page.set_content("")
    await main_page.goto(url, timeout=PAGE_TIMEOUT, wait_until="networkidle")
    await main_page.wait_for_selector(".event__match", timeout=8000)

    # POOL DE PESTAÑAS CON LOCK
    tab_pool = await create_tab_pool(context)

    await expand_all(main_page)

    nodos = main_page.locator(".event__round, .event__match")
    total_nodos = await nodos.count()
    
    jornada_actual = None
    partidos_batch = []

    print(f"📊 Encontrados {total_nodos} nodos...")

    for i in range(total_nodos):
        item = nodos.nth(i)
        class_name = await item.get_attribute("class") or ""

        if "event__round" in class_name:
            txt = await item.inner_text()
            match = re.search(r'Jornada\s+(\d+)', txt, re.IGNORECASE)
            jornada_actual = int(match.group(1)) if match else None
            print(f"📅 Jornada {jornada_actual}")
            continue
        
        if "event__match" in class_name and jornada_actual is not None:
            try:
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

                save_empty_match(db_name, pais, liga, temporada, jornada_actual, fecha, local, visitante)

                partidos_batch.append((jornada_actual, fecha, local, visitante, full_href))

                print(f"  ➕ {local} vs {visitante} - {fecha}")

            except:
                continue

    if partidos_batch:
        print(f"📊 Procesando {len(partidos_batch)} partidos en paralelo...")

        async def procesar(match):
            # ADQUIRIR PESTAÑA CON LOCK
            tab = await acquire_tab(tab_pool)
            try:
                await tab.page.goto("about:blank")
                return await scrape_partido(tab.page, db_name, pais, liga,
                                            temporada, *match)
            finally:
                tab.lock.release()

        await asyncio.gather(*(procesar(p) for p in partidos_batch))
    else:
        print("⚠️ No se encontraron partidos para procesar")
    
    # Cerrar todas las pestañas del pool al final
    for tab in tab_pool:
        await tab.page.close()

# ======================================
# SCRAPEAR DETALLE DE PARTIDO
# ======================================
async def scrape_partido(detail_page, db_name, pais, liga, temporada,
                         jornada, fecha, local, visitante, match_url):

    try:
        for intento in range(1, RETRIES + 1):
            try:
                await detail_page.goto(match_url, wait_until="domcontentloaded", timeout=15000)
                await detail_page.wait_for_selector(".smv__verticalSections", timeout=10000)
                break
            except:
                if intento == RETRIES:
                    print(f"  ❌ No se pudo cargar {local} vs {visitante}")
                    return
                await asyncio.sleep(1)

        goles = await extraer_detalles(detail_page)

        update_match(db_name, pais, liga, temporada, jornada, fecha, local, visitante, goles)

        total_local = goles["g_local_1t"] + goles["g_local_2t"]
        total_visitante = goles["g_visitante_1t"] + goles["g_visitante_2t"]

        print(f"  ✅ {local} {total_local}-{total_visitante} {visitante}")

    except Exception as e:
        print(f"  ❌ Error procesando {local} vs {visitante}: {str(e)[:100]}")

# ======================================
# MAIN
# ======================================
async def main(urls):
    print("🚀 Iniciando scraping con POOL DE PESTAÑAS CON LOCK...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--disable-features=IsolateOrigins,site-per-process",
                "--blink-settings=imagesEnabled=false",
                "--disable-software-rasterizer",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
                "--disable-translate",
                "--metrics-recording-only",
                "--mute-audio",
                "--no-first-run",
                "--disable-notifications",
            ]
        )

        context = await browser.new_context()
        await context.route("**/*.{png,jpg,jpeg,gif,svg,webp}", lambda r: r.abort())
        await context.route("**/*.{css,woff,woff2}", lambda r: r.abort())

        main_page = await context.new_page()

        for entry in urls:
            url, nombre_archivo = entry.split("|")
            nombre_archivo = nombre_archivo.strip().replace("/", "_")

            DB_FOLDER = "X:/prueba n8n/data"
            db_name = os.path.join(DB_FOLDER, f"{nombre_archivo}.db")

            print(f"\n📄 Base de datos: {db_name}")
            init_db(db_name)

            try:
                print(f"🌐 Cargando URL: {url}")
                await scrape_temporada(context, main_page, url, db_name)

            except Exception as e:
                print(f"❌ Error procesando {url}: {e}")
                continue

        await main_page.close()
        await browser.close()

    print("\n✅ Scraping completado!")

# ======================================
# EJEMPLO DE LLAMADA
# ======================================
URLS = [
    "https://www.flashscore.co/futbol/espana/laliga-ea-sports-2021-2022/resultados/|laliga_21_22",
    "https://www.flashscore.co/futbol/espana/laliga-ea-sports-2022-2023/resultados/|laliga_22_23",
    "https://www.flashscore.co/futbol/espana/laliga-ea-sports-2023-2024/resultados/|laliga_23_24",
    "https://www.flashscore.co/futbol/espana/laliga-ea-sports-2024-2025/resultados/|laliga_24_25",
    "https://www.flashscore.co/futbol/espana/laliga-ea-sports/resultados/|laliga_25_26",

    "https://www.flashscore.co/futbol/belgica/jupiler-pro-league-2021-2022/resultados/|belgica_21_22",
    "https://www.flashscore.co/futbol/belgica/jupiler-pro-league-2022-2023/resultados/|belgica_22_23",
    "https://www.flashscore.co/futbol/belgica/jupiler-pro-league-2023-2024/resultados/|belgica_23_24",
    "https://www.flashscore.co/futbol/belgica/jupiler-pro-league-2024-2025/resultados/|belgica_24_25",
    "https://www.flashscore.co/futbol/belgica/jupiler-pro-league/resultados/|belgica_25_26",

    "https://www.flashscore.co/futbol/colombia/primera-a-2021-2022/resultados/|colombia_21_22",
    "https://www.flashscore.co/futbol/colombia/primera-a-2022-2023/resultados/|colombia_22_23",
    "https://www.flashscore.co/futbol/colombia/primera-a-2023-2024/resultados/|colombia_23_24",
    "https://www.flashscore.co/futbol/colombia/primera-a-2024-2025/resultados/|colombia_24_25",
    "https://www.flashscore.co/futbol/colombia/primera-a/resultados/|colombia_25_26",
]


if __name__ == "__main__":
    inicio = time.perf_counter()
    asyncio.run(main(URLS))
    fin = time.perf_counter()
    print(f"\n⏱️ Tiempo total: {fin - inicio:.2f} segundos")