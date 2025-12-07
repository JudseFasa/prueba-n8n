from playwright.async_api import async_playwright

async def init_browser():
    p = await async_playwright().start()
    browser = await p.chromium.launch(
        headless=True,
        args=[
            "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
            "--disable-features=IsolateOrigins,site-per-process",
            "--blink-settings=imagesEnabled=false",
            "--disable-software-rasterizer",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-sync",
            "--disable-translate",
            "--metrics-recording-only",
            "--mute-audio",
            "--no-first-run",
            "--disable-notifications",
        ]
    )
    context = await browser.new_context()
    await context.route("**/*.{png,jpg,jpeg,gif,svg,webp}", lambda r: r.abort())
    await context.route("**/*.{css,woff,woff2}", lambda r: r.abort())
    return p, browser, context
