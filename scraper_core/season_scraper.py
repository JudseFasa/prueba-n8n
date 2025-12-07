import re
import asyncio
from scraper_core.extract import parse_url, expand_all
from scraper_core.tabs import acquire_tab, create_tab_pool
from scraper_core.partido_scraper import scrape_partido
from db.sqlite import save_empty_match

PAGE_TIMEOUT = 120000

async def scrape_temporada(context, main_page, url, db_name):

    pais, liga, temporada = parse_url(url)
    print(f"\n====== {pais.upper()} | {liga} | {temporada} ======")

    await main_page.set_content("")
    await main_page.goto(url, timeout=PAGE_TIMEOUT, wait_until="networkidle")
    await main_page.wait_for_selector(".event__match", timeout=8000)

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

    async def procesar(match):
        tab = await acquire_tab(tab_pool)
        try:
            await tab.page.goto("about:blank")
            return await scrape_partido(tab.page, db_name, pais, liga, temporada, *match)
        finally:
            tab.lock.release()

    await asyncio.gather(*(procesar(p) for p in partidos_batch))

    for tab in tab_pool:
        await tab.page.close()
