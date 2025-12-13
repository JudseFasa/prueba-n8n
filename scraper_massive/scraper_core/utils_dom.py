# utils_dom.py
import asyncio

async def click_mostrar_mas_partidos(page, max_clicks=50):
    for _ in range(max_clicks):
        try:
            boton = page.locator("button:has-text('Mostrar más')")
            if await boton.count() == 0:
                break
            await boton.first.click()
            await asyncio.sleep(0.3)
        except:
            break


async def expand_all(page):
    """
    Expande bloques colapsados (si existen)
    """
    try:
        botones = page.locator(".event__expander")
        for i in range(await botones.count()):
            try:
                await botones.nth(i).click()
                await asyncio.sleep(0.05)
            except:
                continue
    except:
        pass
