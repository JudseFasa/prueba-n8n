from scraper_lite.extract_lite import extract_todays_matches
from scraper_core.extract import parse_url
from scraper_core.partido_scraper import scrape_partido
from db.sqlite import init_db, save_empty_match

async def process_lite(page, url_liga, db_path):
    """
    - Entra a la sección /partidos/
    - Toma solo los partidos del día
    - Guarda vacíos si no existen
    - Scrapea detalles solo de ellos
    """

    print("⚡ Modo Lite: buscando partidos del día...")

    pais, liga, _ = parse_url(url_liga)

    # asegurar BD
    init_db(db_path)

    # /resultados/ → /partidos/
    url_partidos = url_liga.replace("/resultados/", "/partidos/")

    partidos_hoy = await extract_todays_matches(page, url_partidos)

    print(f"📅 Partidos de HOY encontrados: {len(partidos_hoy)}")

    for fecha, local, visitante, enlace in partidos_hoy:

        print(f"➡ Procesando {local} vs {visitante}")

        # crear registro si no existe
        save_empty_match(
            db_path, pais, liga, "actual", 0, fecha, local, visitante
        )

        # scrappear detalle
        await scrape_partido(
            page,
            db_path,
            pais,
            liga,
            "actual",
            0,  # jornada no aplica en lite
            fecha,
            local,
            visitante,
            enlace
        )
