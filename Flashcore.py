import asyncio
from playwright.async_api import async_playwright

async def expandir_todos_los_partidos(page):
    while True:
        boton = page.locator("a[data-testid='wcl-buttonLink']:has-text('Mostrar más')")
        if await boton.count() == 0:
            break
        await boton.first.scroll_into_view_if_needed()
        await boton.first.click()
        await page.wait_for_timeout(800)


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

                resultados.append({
                    "jornada": jornada_actual,
                    "fecha": fecha,
                    "local": local,
                    "visitante": visitante,
                    "goles_local": goles_local,
                    "goles_visitante": goles_visita
                })

                print(jornada_actual, fecha, local, visitante, goles_local, goles_visita)

        print(f"\nTotal partidos: {len(resultados)}")
        await browser.close()


asyncio.run(main())
