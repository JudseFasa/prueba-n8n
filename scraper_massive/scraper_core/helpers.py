# helpers.py
import re
from config import get_temporada_actual

def construir_url_resultados(url_base):
    """Añade /resultados/ a URL base"""
    return f"{url_base.rstrip('/')}/resultados/"

def construir_url_archivo(url_base):
    """Añade /archivo/ a URL base"""
    return f"{url_base.rstrip('/')}/archivo/"

def parse_url(url):
    """Extrae país y liga de URL base"""
    parts = url.rstrip('/').split('/')
    if len(parts) >= 6:  # https://www.flashscore.co/futbol/pais/liga
        pais = parts[-2]
        liga = parts[-1]
        
        # Verificar si la liga ya incluye temporada (años)
        year_matches = re.findall(r'\b(20\d{2})\b', liga)
        if len(year_matches) >= 2:
            liga_parts = liga.rsplit('-', 2)
            liga_base = liga_parts[0]
            temporada = f"{year_matches[0]}-{year_matches[1]}"
            return pais, liga_base, temporada
        
        return pais, liga, "actual"
    return "unknown", "unknown", "actual"

def extraer_año_url(url):
    """Extrae año de temporada desde la URL"""
    year_matches = re.findall(r'\b(20\d{2})\b', url)
    if len(year_matches) >= 2:
        return f"{year_matches[0]}-{year_matches[1]}"
    elif len(year_matches) == 1:
        return f"{year_matches[0]}-{int(year_matches[0])+1}"
    return None