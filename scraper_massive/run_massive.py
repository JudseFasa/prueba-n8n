import asyncio
from scraper_core.browser import init_browser
from scraper_core.season_scraper import scrape_temporada
from db.sqlite import init_db
import os

async def run_massive(URLS):
    p, browser, context = await init_browser()
    main_page = await context.new_page()

    for entry in URLS:
        url, name = entry.split("|")
        name = name.strip().replace("/", "_")

        DB_FOLDER = "X:/prueba n8n/data"
        db_name = os.path.join(DB_FOLDER, f"{name}.db")
        print(f"\n📄 Base de datos: {db_name}")

        init_db(db_name)

        print(f"🌐 Procesando {url}")
        await scrape_temporada(context, main_page, url, db_name)

    await main_page.close()
    await browser.close()
    await p.stop()
