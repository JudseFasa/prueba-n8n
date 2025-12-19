# fase_extractor.py
import asyncio
import re

async def expand_all(page):
    """Expande todos los botones de expansión"""
    botones = page.locator("a[data-testid='wcl-buttonLink']")
    count = await botones.count()
    for i in range(count):
        try:
            await botones.nth(i).click()
            await asyncio.sleep(0.05)
        except:
            pass

async def click_mostrar_mas_partidos(page):
    """Hace clic en 'Mostrar más partidos' hasta agotar"""
    for i in range(15):
        boton = page.locator("a[data-testid='wcl-buttonLink']", has_text="Mostrar más partidos")
        if await boton.count() == 0:
            boton = page.locator("a[data-testid='wcl-buttonLink']:has-text('Mostrar')")
        
        if await boton.count() == 0:
            break
            
        try:
            await boton.scroll_into_view_if_needed()
            await boton.click()
            await asyncio.sleep(1)
        except:
            break

def extraer_fase_nombre(fase_texto):
    """Detecta si una fase es especial y extrae su nombre"""
    palabras_clave = [
        "cuadrangular", "play off", "play-off", "playoffs",
        "conference", "descenso", "grupo de campeonato",
        "clausura", "apertura", "final", "liguilla", "play-out"
    ]
    
    lower = fase_texto.lower()
    for palabra in palabras_clave:
        if palabra in lower:
            return "especial"
    return "regular"

async def extraer_fases_y_partidos(page):
    """
    Extrae las fases y partidos de la página actual usando la lógica de prueba.py
    Retorna lista de diccionarios con: fase, jornada, fecha, local, visitante, url
    """
    # Ejecutar script similar al de prueba.py pero adaptado
    datos = await page.evaluate("""
() => {
    const palabrasClave = [
        "cuadrangular", "play off", "play-off", "playoffs",
        "conference", "descenso", "grupo de campeonato",
        "clausura", "apertura", "final", "liguilla", "play-out"
    ];

    const partidos = [];
    let faseActual = null;
    let jornadaActual = 1;

    const elementos = document.querySelectorAll(
        'div.headerLeague__wrapper, div[class*="event__match"]'
    );

    for (const el of elementos) {
        // HEADER DE FASE
        if (el.className.includes("headerLeague__wrapper")) {
            const titulo = el.querySelector("strong.headerLeague__title-text");
            if (!titulo) continue;

            const texto = titulo.textContent.trim();
            const lower = texto.toLowerCase();

            // Determinar si es fase especial o regular
            const esEspecial = palabrasClave.some(p => lower.includes(p));
            faseActual = texto;

            // Intentar extraer número de jornada
            const match = texto.match(/Jornada\\s+(\\d+)/i);
            if (match) {
                jornadaActual = parseInt(match[1]);
            }
        }
        // PARTIDO
        else if (faseActual) {
            const fechaElem = el.querySelector('.event__time');
            const localElem = el.querySelector('.event__homeParticipant');
            const visitanteElem = el.querySelector('.event__awayParticipant');
            const linkElem = el.querySelector('a.eventRowLink');

            if (fechaElem && localElem && visitanteElem) {
                const partido = {
                    fase: faseActual,
                    jornada: jornadaActual,
                    fecha: fechaElem.textContent.trim(),
                    local: localElem.textContent.trim(),
                    visitante: visitanteElem.textContent.trim(),
                    url: linkElem ? linkElem.href : null
                };
                partidos.push(partido);
            }
        }
    }

    return partidos;
}
""")
    
    # Procesar URLs para asegurar que sean completas
    for partido in datos:
        if partido['url'] and partido['url'].startswith('/'):
            partido['url'] = f"https://www.flashscore.co{partido['url']}"
    
    return datos