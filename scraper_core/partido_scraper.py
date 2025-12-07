from scraper_core.extract import extraer_detalles
from db.sqlite import update_match

RETRIES = 3

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
                    print(f"❌ No se pudo cargar {local} vs {visitante}")
                    return
        goles = await extraer_detalles(detail_page)
        update_match(db_name, pais, liga, temporada, jornada, fecha, local, visitante, goles)

        total_local = goles["g_local_1t"] + goles["g_local_2t"]
        total_visitante = goles["g_visitante_1t"] + goles["g_visitante_2t"]

        print(f"  ✅ {local} {total_local}-{total_visitante} {visitante}")

    except Exception as e:
        print(f"  ❌ Error procesando {local} vs {visitante}: {str(e)[:100]}")
