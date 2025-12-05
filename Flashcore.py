import asyncio
import json
from playwright.async_api import async_playwright

async def expandir_todos_los_partidos(page):
    while True:
        boton = page.locator("a[data-testid='wcl-buttonLink']:has-text('Mostrar más')")
        if await boton.count() == 0:
            break
        await boton.first.scroll_into_view_if_needed()
        await boton.first.click()
        await page.wait_for_timeout(800)

async def extraer_goles(detail_page):
    sections = await detail_page.locator(".smv__verticalSections > div").all()
    current_half = None
    goles_1t_home = []
    goles_1t_away = []
    goles_2t_home = []
    goles_2t_away = []
    for sec in sections:
        if await sec.evaluate("e => e.classList.contains('wclHeaderSection--summary')"):
            half_elem = sec.locator(".wcl-overline_uwiIT:has-text('Tiempo')")
            if await half_elem.count() > 0:
                half_text = await half_elem.inner_text()
                if "1er" in half_text:
                    current_half = 1
                elif "2º" in half_text:
                    current_half = 2
            continue
        # Check if it's a participant row with a goal
        if await sec.locator("[data-testid=\"wcl-icon-soccer\"]").count() > 0:
            time_elem = sec.locator(".smv__timeBox")
            if await time_elem.count() > 0:
                time = await time_elem.inner_text()
                time = time.rstrip("'")
                class_list = await sec.evaluate("el => Array.from(el.classList)")
                team = 'home' if 'smv__homeParticipant' in class_list else 'away'
                if current_half == 1:
                    if team == 'home':
                        goles_1t_home.append(time)
                    else:
                        goles_1t_away.append(time)
                elif current_half == 2:
                    if team == 'home':
                        goles_2t_home.append(time)
                    else:
                        goles_2t_away.append(time)
    return {
        "local_1t": ", ".join(goles_1t_home),
        "visitante_1t": ", ".join(goles_1t_away),
        "local_2t": ", ".join(goles_2t_home),
        "visitante_2t": ", ".join(goles_2t_away)
    }

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        url = "https://www.flashscore.co/futbol/alemania/bundesliga-2024-2025/resultados/"
        await page.goto(url, wait_until="networkidle")
        # Expandir todos los partidos
        await expandir_todos_los_partidos(page)
        # Capturar todos los nodos del feed
        nodos = page.locator(".event__round, .event__match")
        total_nodos = await nodos.count()
        jornada_actual = "Unknown"
        resultados = []
        for i in range(total_nodos):
            item = nodos.nth(i)
            # Si es una jornada
            if await item.evaluate("e => e.classList.contains('event__round')"):
                jornada_actual = await item.inner_text()
                continue
            # Si es un partido
            if await item.evaluate("e => e.classList.contains('event__match')"):
                fecha = await item.locator(".event__time").inner_text()
                local = await item.locator(".event__homeParticipant .wcl-name_jjfMf").inner_text()
                visitante = await item.locator(".event__awayParticipant .wcl-name_jjfMf").inner_text()
                goles_local = await item.locator(".event__score--home").inner_text()
                goles_visita = await item.locator(".event__score--away").inner_text()
                # Obtener el link al detalle del partido
                link_elem = item.locator("a.eventRowLink")
                href = await link_elem.get_attribute("href") if await link_elem.count() > 0 else None
                goles_detalle = {}
                if href:
                    full_href = "https://www.flashscore.co" + href if not href.startswith("http") else href
                    detail_page = await browser.new_page()
                    await detail_page.goto(full_href, wait_until="networkidle")
                    goles_detalle = await extraer_goles(detail_page)
                    await detail_page.close()
                    await page.wait_for_timeout(1000)  # Pausa para no sobrecargar el sitio
                resultados.append({
                    "jornada": jornada_actual,
                    "fecha": fecha,
                    "local": local,
                    "visitante": visitante,
                    "goles_local": goles_local,
                    "goles_visitante": goles_visita,
                    **goles_detalle
                })
                print(jornada_actual, fecha, local, visitante, goles_local, goles_visita, goles_detalle)
        print(f"\nTotal partidos: {len(resultados)}")
        # Guardar en JSON para mejor manejo
        with open("resultados_bundesliga.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
        await browser.close()

asyncio.run(main())