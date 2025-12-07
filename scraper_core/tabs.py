import asyncio

PARTIDOS_PARALELO = 4

class TabWrapper:
    def __init__(self, page):
        self.page = page
        self.lock = asyncio.Lock()

async def create_tab_pool(context):
    pool = []
    for _ in range(PARTIDOS_PARALELO):
        page = await context.new_page()
        pool.append(TabWrapper(page))
    return pool

async def acquire_tab(pool):
    while True:
        for tab in pool:
            if not tab.lock.locked():
                await tab.lock.acquire()
                return tab
        await asyncio.sleep(0.05)
