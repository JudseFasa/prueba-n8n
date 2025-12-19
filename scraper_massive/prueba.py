import asyncio
import re
from playwright.async_api import async_playwright

# ==================================================
# CONFIGURACIÓN DE LIGAS (AGREGA LAS QUE QUIERAS)
# ==================================================

LIGAS = {
    "COLOMBIA_PRIMERA_A": {
        "pais": "COLOMBIA",
        "url": "https://www.flashscore.co/futbol/colombia/primera-a/resultados/"
    },
    "BELGICA_JUPILER": {
        "pais": "BELGICA",
        "url": "https://www.flashscore.co/futbol/belgica/jupiler-pro-league/resultados/"
    },
    "ESPAÑA_LALIGA": {
        "pais": "ESPAÑA",
        "url": "https://www.flashscore.co/futbol/espana/laliga-ea-sports/resultados/"
    },
    "ITALIA_SERIE_A": {
        "pais": "ITALIA",
        "url": "https://www.flashscore.co/futbol/italia/serie-a/resultados/"
    },
}

PALABRAS_CLAVE_FASES = [
    "cuadrangular", "play off", "play-off", "playoffs",
    "conference", "descenso", "grupo de campeonato",
    "clausura", "apertura", "final", "liguilla", "play-out"
]

# ==================================================
# FUNCIONES AUXILIARES
# ==================================================

async def expand_all(page):
    botones = page.locator("a[data-testid='wcl-buttonLink']")
    for i in range(await botones.count()):
        try:
            await botones.nth(i).click()
            await asyncio.sleep(0.05)
        except:
            pass


async def click_mostrar_mas_partidos(page, max_clicks=15):
    for i in range(max_clicks):
        boton = page.locator(
            "a[data-testid='wcl-buttonLink']:has-text('Mostrar')"
        )
        if await boton.count() == 0:
            break
        try:
            await boton.scroll_into_view_if_needed()
            await boton.first.click()
            print(f"    🔽 Clic {i + 1} en 'Mostrar más partidos'")
            await asyncio.sleep(1)
        except:
            break
    print("    ✅ Todos los partidos cargados")


# ==================================================
# SCRAPER PRINCIPAL
# ==================================================

async def extraer_jornadas_especiales(nombre_liga, pais, url_liga):

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url_liga, timeout=60000)

        print(f"🔍 Analizando: {nombre_liga}")
        print(f"🌍 País: {pais}")

        print("📂 Expandiendo secciones...")
        await expand_all(page)
        await click_mostrar_mas_partidos(page)
        await asyncio.sleep(2)

        resumen_fases = await page.evaluate(f"""
        () => {{
            const palabrasClave = {PALABRAS_CLAVE_FASES};
            const resumen = {{}};
            let faseActual = null;

            const elementos = document.querySelectorAll(
                'div.headerLeague__wrapper, div[class*="event__match"]'
            );

            for (const el of elementos) {{
                if (el.className.includes("headerLeague__wrapper")) {{
                    const titulo = el.querySelector("strong.headerLeague__title-text");
                    if (!titulo) continue;

                    faseActual = titulo.textContent.trim();
                    if (!(faseActual in resumen)) {{
                        resumen[faseActual] = 0;
                    }}
                }} else if (faseActual) {{
                    resumen[faseActual] += 1;
                }}
            }}
            return resumen;
        }}
        """)

        await browser.close()

        return {
            "liga": nombre_liga,
            "pais": pais,
            "total_partidos": sum(resumen_fases.values()),
            "fases": resumen_fases
        }


# ==================================================
# EJECUCIÓN PARA TODAS LAS LIGAS
# ==================================================

async def ejecutar_scraping(ligas):
    resultados = []

    for nombre_liga, data in ligas.items():
        print("\n" + "=" * 60)
        resultado = await extraer_jornadas_especiales(
            nombre_liga,
            data["pais"],
            data["url"]
        )

        resultados.append(resultado)

        print("=" * 60)
        print(f"📊 RESUMEN {resultado['liga']} ({resultado['pais']})")
        print("=" * 60)

        for fase, total in resultado["fases"].items():
            print(f"   {fase}: {total} partidos")

        print(f"\n📈 TOTAL: {resultado['total_partidos']} partidos")

    return resultados


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":
    asyncio.run(ejecutar_scraping(LIGAS))
