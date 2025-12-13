# scraper_core/seasons_extractor.py
import re
import asyncio
from scraper_core.utils_urls import (
    construir_url_archivo,
    extraer_año_url,
    parse_url,
)

PAGE_TIMEOUT = 60000


async def get_temporadas_mixto(context, url_base, pasadas=4):
    """
    Devuelve:
    - 1 temporada actual
    - N temporadas pasadas (archivo)
    """
    temporadas = []

    page = await context.new_page()

    # --- TEMPORADA ACTUAL ---
    try:
        await page.goto(url_base, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")

        pais, liga, _ = parse_url(url_base)

        año_actual = await _detectar_temporada_actual(page)
        temporadas.append({
            "url": url_base,
            "año": año_actual,
            "pais": pais,
            "liga": liga,
            "tipo": "actual"
        })
    except Exception as e:
        print(f"⚠️ Error temporada actual: {e}")

    # --- TEMPORADAS PASADAS ---
    try:
        archivo_url = construir_url_archivo(url_base)
        await page.goto(archivo_url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")

        links = page.locator("a[href*='/resultados/']")
        total = await links.count()

        usados = set()
        for i in range(total):
            if len(temporadas) >= pasadas + 1:
                break

            href = await links.nth(i).get_attribute("href")
            if not href or href in usados:
                continue

            usados.add(href)
            año = extraer_año_url(href)
            if not año:
                continue

            temporadas.append({
                "url": f"https://www.flashscore.co{href}",
                "año": año,
                "pais": pais,
                "liga": liga,
                "tipo": "archivo"
            })

    except Exception as e:
        print(f"⚠️ Error temporadas pasadas: {e}")

    await page.close()
    return temporadas


async def _detectar_temporada_actual(page):
    """
    Intenta detectar el año actual desde la página.
    """
    try:
        header = page.locator("h1")
        if await header.count() > 0:
            txt = await header.first.inner_text()
            m = re.findall(r"(20\d{2})", txt)
            if len(m) >= 2:
                return f"{m[0]}-{m[1]}"
    except:
        pass

    return "actual"
