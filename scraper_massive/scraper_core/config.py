# config.py
from datetime import datetime

# Añadir al config.py existente
MEMORY_MANAGEMENT = {
    'MAX_MEMORY_MB': 500,  # Límite absoluto de memoria
    'FORCE_CLEANUP_THRESHOLD': 400,  # MB - Cuando forzar limpieza
    'PAGE_POOL_SIZE': 3,  # Máximo de páginas simultáneas por worker
    'PAGE_MAX_AGE_MINUTES': 3,  # Minutos máximos que una página puede vivir
    'CHECK_INTERVAL_SECONDS': 15,  # Segundos entre chequeos de memoria
}

# Workers ajustados
SEASON_WORKERS = 1  # Reducir temporadas en paralelo
GOALS_WORKERS = 2   # Reducir workers de goles
MAX_PARTIDOS_POR_PAGINA = 10  # Reducir partidos por página

# VARIABLES DE CONFIGURACIÓN
PAGE_TIMEOUT = 60000          # Tiempo máximo de espera para cargar páginas (60 segundos)
RETRIES = 2                   # Número de reintentos por fallo
MAX_TEMPORADAS = 5           # Máximo de temporadas por liga a procesar
GOLES_WORKERS = 4            # Número de workers para procesar goles
QUEUE_MAXSIZE = 200          # Tamaño máximo de las colas internas
MAX_PARTIDOS_POR_PAGINA = 20 # Cada worker reinicia su página cada 20 partidos

# RUTAS
DB_FOLDER = "X:/prueba n8n/data"  # Carpeta para bases de datos SQLite
LOG_FOLDER = "logs"               # Carpeta para archivos de log

# CONFIGURACIÓN DEL NAVEGADOR
BROWSER_ARGS = [
    "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage",
    "--disable-setuid-sandbox", "--blink-settings=imagesEnabled=false",
    "--disable-software-rasterizer", "--disable-background-networking",
    "--disable-default-apps", "--disable-sync", "--disable-translate",
    "--metrics-recording-only", "--mute-audio", "--no-first-run",
    "--disable-notifications",
]

def get_temporada_actual():
    """Obtiene la temporada actual"""
    ahora = datetime.now()
    año = ahora.year
    mes = ahora.month
    return f"{año}-{año+1}" if mes >= 8 else f"{año-1}-{año}"