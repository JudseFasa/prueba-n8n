# scraper_massive/main.py
import asyncio
import os
from playwright.async_api import async_playwright

from scraper_core.seasons_extractor import get_temporadas_mixto
from scraper_core.matches_extractor import extract_matches_temporada
from scraper_core.queue_manager import QueueManager
from scraper_core.workers_goles import goal_worker

# =========================
# CONFIG
# =========================
WORKERS_GOLES = 6
TEMPORADAS_PASADAS = 4
QUEUE_SIZE = 200

DB_FOLDER = "X:/prueba n8n/data"
os.makedirs(DB_FOLDER, exist_ok=True)

LIGAS = [
    {
        "url": "https://www.flashscore.co/futbol/colombia/primera-a/",
        "nombre": "Colombia"
    },
    {
        "url": "https://www.flashscore.co/futbol/belgica/jupiler-pro-league/",
        "nombre": "Belgica"
    },
    {
        "url": "https://www.flashscore.co/futbol/espana/laliga-ea-sports/",
        "nombre": "España"
    },
    {
        "url": "https://www.flashscore.co/futbol/italia/serie-a/",
        "nombre": "Italia"
    },
]


# =========================
# MAIN
# =========================
async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        queue = QueueManager(maxsize=QUEUE_SIZE)

        # Workers de goles
        workers = [
            asyncio.create_task(goal_worker(i + 1, context, queue))
            for i in range(WORKERS_GOLES)
        ]

        for liga in LIGAS:
            liga_url = liga["url"].rstrip("/")
            nombre_liga = liga["nombre"].strip()

            print(f"\n🌍 Procesando liga: {nombre_liga}")

            temporadas = await get_temporadas_mixto(
                context,
                liga_url,
                pasadas=TEMPORADAS_PASADAS
            )

            if not temporadas:
                print("⚠️ No se encontraron temporadas")
                continue

            for temp in temporadas:
                año_limpio = temp["año"].replace("-", "_")
                db_name = os.path.join(
                    DB_FOLDER,
                    f"{nombre_liga}_{año_limpio}.db"
                )

                print(f"\n📊 Temporada {temp['año']}")
                print(f"📄 DB: {db_name}")

                await extract_matches_temporada(
                    context=context,
                    temporada_url=temp["url"],
                    db_name=db_name,
                    pais=temp["pais"],
                    liga=nombre_liga,
                    temporada=temp["año"],
                    queue=queue
                )

                # Esperar a que la cola se vacíe un poco
                await queue.wait_until_half_empty()

        # Finalizar 
        await queue.finish()  # Nueva línea: Señala que no hay más items por producir
        await queue.wait_until_done()  # Reemplaza join() por esto

        for w in workers:
            w.cancel()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())

