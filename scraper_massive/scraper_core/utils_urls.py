# utils_urls.py
import re

def parse_url(url):
    """
    Devuelve pais, liga, resto
    """
    partes = url.strip("/").split("/")
    try:
        pais = partes[-3]
        liga = partes[-2]
        return pais, liga, partes
    except:
        return "", "", partes


def construir_url_resultados(url_base):
    return url_base.rstrip("/") + "/resultados/"


def construir_url_archivo(url_base):
    return url_base.rstrip("/") + "/archivo/"


def extraer_año_url(url):
    m = re.search(r"(20\d{2}[-/]\d{2})", url)
    return m.group(1) if m else None
