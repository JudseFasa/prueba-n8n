import asyncio
from datetime import datetime

async def extract_todays_matches(page, url):
    """
    Entra a la sección /partidos/ y extrae solo los de HOY.
    Devuelve una lista: [(fecha, local, visitante, link), ...]
    """

    await page.set_content("")
    await page.goto(url, timeout=15000, wait_until="networkidle")

    hoy = datetime.now().strftime("%d.%m.")  # formato Flashscore ej: "06.12."

    partidos = []

    nodos = page.locator(".event__match")
    total = await nodos.count()

    for i in range(total):
        item = nodos.nth(i)

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

        # Solo partidos del día
        if hoy not in fecha:
            continue

        link_elem = item.locator("a.eventRowLink")
        href = await link_elem.get_attribute("href") if await link_elem.count() > 0 else None

        if not href:  # método alterno para Flashscore
            parent_id = await item.get_attribute("id")
            if parent_id and parent_id.startswith("g_"):
                href = f"/partido/{parent_id.replace('g_','')}/"

        if not href:
            continue

        full_href = f"https://www.flashscore.co{href}" if href.startswith("/") else href

        partidos.append((fecha, local, visitante, full_href))

    return partidos
