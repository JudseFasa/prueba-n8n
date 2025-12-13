# workers_goles.py
# Workers permanentes para extraer detalles de goles

import asyncio
from playwright.async_api import TimeoutError as PlaywrightTimeout

from scraper_core.queue_manager import QueueManager
from scraper_core.utils_goles import extraer_detalles, update_match

# Cada cuántos partidos se reinicia la pestaña (anti memory-leak)
RESET_CADA = 150

async def goal_worker(worker_id: int, context, queue: QueueManager):
    print(f"👷 Worker goles #{worker_id} iniciado")

    page = await context.new_page()
    procesados = 0

    while True:
        # Condición de salida limpia
        if queue.finished() and queue.qsize() == 0:
            break

        try:
            partido = await asyncio.wait_for(queue.get(), timeout=3)
        except asyncio.TimeoutError:
            continue

        try:
            await procesar_partido(page, partido, worker_id)
        except Exception as e:
            print(f"👷#{worker_id} ❌ Error: {e}")
        finally:
            queue.task_done()
            procesados += 1

        # Reinicio preventivo de pestaña
        if procesados % RESET_CADA == 0:
            try:
                await page.close()
            except:
                pass
            page = await context.new_page()
            print(f"♻️ Worker #{worker_id} reinició pestaña")

    try:
        await page.close()
    except:
        pass

    print(f"👷 Worker goles #{worker_id} finalizado")


async def procesar_partido(page, partido, worker_id):
    for intento in range(2):
        try:
            await page.goto(partido.match_url, wait_until="domcontentloaded", timeout=10000)
            await page.wait_for_selector(".smv__verticalSections", timeout=5000)
            break
        except PlaywrightTimeout:
            if intento == 1:
                return
            await asyncio.sleep(0.5)

    goles = await extraer_detalles(page)

    update_match(
        partido.db_name,
        partido.pais,
        partido.liga,
        partido.temporada,
        partido.jornada,
        partido.fecha,
        partido.local,
        partido.visitante,
        goles
    )

    total_l = goles["g_local_1t"] + goles["g_local_2t"]
    total_v = goles["g_visitante_1t"] + goles["g_visitante_2t"]

    print(f"👷#{worker_id} ✅ {partido.local} {total_l}-{total_v} {partido.visitante}")


async def start_goal_workers(context, queue: QueueManager, cantidad: int):
    tasks = []
    for i in range(cantidad):
        task = asyncio.create_task(goal_worker(i + 1, context, queue))
        tasks.append(task)
    return tasks


async def stop_goal_workers(tasks):
    await asyncio.gather(*tasks, return_exceptions=True)
