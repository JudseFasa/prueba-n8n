import asyncio
from playwright.async_api import async_playwright

URL = "https://www.flashscore.co/futbol/"

async def main():
    async with async_playwright() as p:
        # Puedes usar chromium, firefox o webkit
        browser = await p.chromium.launch(headless=False)  # True = sin ventana
        page = await browser.new_page()

        print(f"Abriendo {URL}")
        await page.goto(URL, wait_until="networkidle")

        # Cerrar banner de cookies si aparece
        try:
            await page.locator("button#onetrust-accept-btn-handler").click(timeout=5000)
            print("Cookies aceptadas.")
        except:
            print("No apareció el banner de cookies.")


        # Esperar a que aparezca el div
        await page.wait_for_selector("div.left_menu_categories_seo")

        # Seleccionar todos los <a> dentro del div
        enlaces = page.locator("div.left_menu_categories_seo a")

        cantidad = await enlaces.count()
        print(f"\nEncontrados {cantidad} enlaces:\n")

        nombres = []

        for i in range(cantidad):
            texto = await enlaces.nth(i).inner_text()
            href = await enlaces.nth(i).get_attribute("href")
            nombres.append((texto, href))
            print(f"{i+1}. {texto} -> {href}")

        # SI QUIERES, GUARDAR A TXT AUTOMÁTICAMENTE
        with open("ligas_extraidas.txt", "w", encoding="utf-8") as f:
            for nombre, link in nombres:
                f.write(f"{nombre} | {link}\n")

        print("\nGuardado en ligas_extraidas.txt")

        await browser.close()

# Ejecutar script
asyncio.run(main())
