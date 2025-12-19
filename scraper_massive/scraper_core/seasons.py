# seasons.py
import re
import asyncio
from helpers import construir_url_resultados, construir_url_archivo, extraer_año_url, parse_url
from config import get_temporada_actual, MAX_TEMPORADAS

async def obtener_temporadas_archivo(context, url_base, max_temporadas=4):
    """Obtiene temporadas pasadas desde la página de archivo"""
    page = await context.new_page()
    temporadas_info = []
    
    try:
        archivo_url = construir_url_archivo(url_base)
        await page.goto(archivo_url, timeout=60000, wait_until="networkidle")
        
        # Buscar elementos de temporadas
        season_elements = await page.locator("a.archiveLatte__text.archiveLatte__text--clickable").all()
        
        if not season_elements:
            season_elements = await page.locator("a:has-text('20')").all()
        
        # Procesar elementos
        for element in season_elements[:max_temporadas * 2]:
            try:
                href = await element.get_attribute("href")
                text = await element.text_content()
                
                if not href or not text:
                    continue
                
                # Filtrar solo temporadas (contienen años y no son equipos)
                if not re.search(r'\d{4}', href) or "/equipo/" in href:
                    continue
                
                # Construir URL completa
                full_url = f"https://www.flashscore.co{href}"
                if not full_url.endswith("/resultados/"):
                    full_url = full_url.rstrip('/') + "/resultados/"
                
                # Extraer año
                año = extraer_año_url(full_url)
                if not año:
                    continue
                
                # Obtener país y liga de la URL base
                pais, liga, _ = parse_url(url_base)
                
                temporadas_info.append({
                    "url": full_url,
                    "nombre": text.strip()[:50],
                    "año": año,
                    "pais": pais,
                    "liga": liga
                })
                
                if len(temporadas_info) >= max_temporadas:
                    break
                    
            except:
                continue
                
    except Exception as e:
        print(f"⚠️ Error obteniendo temporadas: {e}")
    finally:
        await page.close()
    
    # Ordenar por año y limitar
    temporadas_info.sort(key=lambda x: x['año'], reverse=True)
    return temporadas_info[:max_temporadas]

async def obtener_todas_temporadas(context, url_base, nombre_base, max_temporadas=MAX_TEMPORADAS):
    """
    Función generadora que obtiene temporadas (actual + pasadas)
    y las va entregando UNA POR UNA para poner en cola inmediatamente
    """
    # 1. Añadir temporada actual
    pais, liga, _ = parse_url(url_base)
    año_actual = get_temporada_actual()
    
    temporada_actual = {
        "url": construir_url_resultados(url_base),
        "nombre": f"{nombre_base} {año_actual}",
        "año": año_actual,
        "pais": pais,
        "liga": liga,
        "liga_nombre": nombre_base
    }
    
    print(f"  📅 Temporada actual: {año_actual}")
    yield temporada_actual
    
    # 2. Obtener temporadas pasadas
    temporadas_pasadas = await obtener_temporadas_archivo(context, url_base, max_temporadas - 1)
    
    # 3. Combinar evitando duplicados
    años_existentes = {año_actual}
    for temp in temporadas_pasadas:
        if temp['año'] not in años_existentes:
            temp['liga_nombre'] = nombre_base
            yield temp
            años_existentes.add(temp['año'])