import re

def parse_url(url):
    parts = url.split("/")
    pais = parts[4]
    liga_block = parts[5]

    if "-" in liga_block and liga_block[-9:-1].replace("-", "").isdigit():
        parts2 = liga_block.split("-")
        liga = "-".join(parts2[:-2])
        temporada = "-".join(parts2[-2:])
    else:
        liga = liga_block
        temporada = "actual"

    return pais, liga, temporada


async def expand_all(page):
    botones = page.locator("a[data-testid='wcl-buttonLink']")

    if await botones.count() == 0:
        return

    while True:
        count = await botones.count()
        if count == 0:
            break
        for i in range(count):
            try:
                await botones.nth(i).click()
            except:
                pass
        await page.wait_for_timeout(300)
