# matches.py
import asyncio
from fase_extractor import expand_all, click_mostrar_mas_partidos, extraer_fases_y_partidos

async def extraer_partidos_temporada(page, temp_info):
    """
    Extrae todos los partidos de una temporada usando el detector de fases
    Retorna lista de diccionarios con metadatos completos
    """
    pais = temp_info['pais']
    liga = temp_info['liga']
    temporada = temp_info['año']
    liga_nombre = temp_info['liga_nombre']
    url = temp_info['url']

    await page.goto(url, timeout=60000, wait_until="networkidle")
    
    try:
        # Cargar todos los partidos
        await click_mostrar_mas_partidos(page)
        await page.wait_for_selector(".event__match", timeout=5000)
    except:
        print(f"⚠️ No se encontraron partidos en {url}")
        return []

    # Expandir todas las secciones
    await expand_all(page)

    # Extraer fases y partidos usando el detector
    partidos = await extraer_fases_y_partidos(page)
    
    # Añadir metadatos
    for partido in partidos:
        partido['pais'] = pais
        partido['liga'] = liga
        partido['temporada'] = temporada
        partido['liga_nombre'] = liga_nombre
    
    print(f"    ✅ {len(partidos)} partidos extraídos")
    return partidos