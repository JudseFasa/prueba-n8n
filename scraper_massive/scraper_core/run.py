# run.py - Versión mejorada (Windows compatible)
import asyncio
import time
import traceback
import sys
from config import get_temporada_actual
from main import main_pipeline

URLS_BASE = [
    "https://www.flashscore.co/futbol/colombia/primera-a|Colombia_Primera_A",
    "https://www.flashscore.co/futbol/belgica/jupiler-pro-league|Bélgica_Jupiler_League",
    "https://www.flashscore.co/futbol/espana/laliga-ea-sports|España_LaLiga",
    "https://www.flashscore.co/futbol/italia/serie-a|Italia_Serie_A",
]

def print_banner():
    """Imprime el banner informativo"""
    print("=" * 70)
    print("🚀 SCRAPER FLASHSCORE - SISTEMA CON GESTIÓN DE MEMORIA")
    print(f"📊 Sistema operativo: {sys.platform}")
    print("=" * 70)
    print(f"📊 Ligas a procesar: {len(URLS_BASE)}")
    print(f"📅 Temporada actual: {get_temporada_actual()}")
    print("👷 Workers de temporadas: 1 (reducido por memoria)")
    print("⚽ Workers de goles: 2 (reducido por memoria)")
    print("📄 Pool máximo de páginas: 3 por tipo")
    print("🧠 Límite de memoria: 500MB (con limpieza automática)")
    print("🔄 Reinicio de páginas: cada 10 partidos")
    print("📁 Carpeta de datos: X:/prueba n8n/data")
    print("=" * 70)
    print()

async def safe_main():
    """Función principal con manejo de errores robusto"""
    inicio = time.perf_counter()
    
    try:
        print_banner()
        
        # Configurar límite de tiempo
        timeout_minutes = 60 * 8  # 8 horas máximo total
        timeout_seconds = timeout_minutes
        
        # Para Windows, usar un enfoque diferente para timeout
        if sys.platform == 'win32':
            # En Windows, ejecutar sin wait_for para evitar problemas
            await main_pipeline(URLS_BASE)
        else:
            # En Unix/Linux, usar wait_for normalmente
            await asyncio.wait_for(main_pipeline(URLS_BASE), timeout=timeout_seconds)
        
    except asyncio.TimeoutError:
        print("\n⏰ TIMEOUT: El proceso tomó demasiado tiempo, terminando...")
    except KeyboardInterrupt:
        print("\n🛑 Interrupción por usuario (Ctrl+C)")
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO: {e}")
        print("Traceback:")
        print(traceback.format_exc())
    finally:
        fin = time.perf_counter()
        print(f"\n⏱️  Tiempo total: {fin - inicio:.2f} segundos ({((fin - inicio)/60):.1f} minutos)")
        print("✅ Proceso finalizado")

if __name__ == "__main__":
    # Configurar límite de recursión y tamaño de pool de hilos
    import sys
    sys.setrecursionlimit(10000)
    
    # Configuración específica para Windows
    if sys.platform == 'win32':
        # Configurar el event loop para Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Ejecutar
    try:
        asyncio.run(safe_main())
    except KeyboardInterrupt:
        print("\n🛑 Programa interrumpido por el usuario")