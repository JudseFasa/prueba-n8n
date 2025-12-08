import asyncio
from scraper_massive.run_massive import run_massive

URLS = [
    "https://www.flashscore.co/futbol/espana/laliga-ea-sports-2021-2022/resultados/|laliga_21_22",
    ...
]

if __name__ == "__main__":
    asyncio.run(run_massive(URLS))
