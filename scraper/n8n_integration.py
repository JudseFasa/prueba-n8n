#!/usr/bin/env python3
"""
Integración del scraper Flashscore con n8n
Versión corregida para Docker
"""
import json
import sys
import os
import logging
import traceback
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_scraping():
    """Ejecutar el scraper Flashscore desde n8n"""
    try:
        # Leer input de n8n desde stdin
        input_data = {}
        if not sys.stdin.isatty():
            try:
                stdin_content = sys.stdin.read()
                if stdin_content.strip():
                    input_data = json.loads(stdin_content)
            except json.JSONDecodeError as e:
                logger.warning(f"No se pudo parsear JSON: {e}")
        
        # Obtener parámetros o usar valores por defecto
        match_urls = input_data.get('match_urls', [
            "https://www.flashscore.co/partido/futbol/rcd-espanyol-QFfPdh1J/sevilla-h8oAv4Ts/?mid=GxOpMNhm",
            "https://www.flashscore.co/partido/futbol/elche-cf-4jl02tPF/real-madrid-W8mj7MDD/?mid=pfXERqVP"
        ])
        
        liga_nombre = input_data.get('liga_nombre', 'n8n_scraping')
        
        logger.info(f"Iniciando scraping para {len(match_urls)} URLs")
        
        # Importar el scraper
        try:
            # Añadir el directorio actual al path
            sys.path.append('/app/scraper')
            from flashscore_scraper import FlashscoreScraper
        except ImportError as e:
            logger.error(f"Error importando scraper: {e}")
            return {
                'success': False,
                'error': f'No se pudo importar el scraper: {e}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Ejecutar scraper
        scraper = FlashscoreScraper(headless=True)
        
        # Llamar al método directamente
        logger.info("Ejecutando scraper...")
        
        # Para evitar problemas, hacemos scraping de una URL a la vez
        all_encuentros = []
        all_goles = []
        
        for i, url in enumerate(match_urls):
            logger.info(f"Procesando URL {i+1}/{len(match_urls)}: {url}")
            
            try:
                # Usar el método scrape_specific_matches con una sola URL
                encuentros, goles = scraper.scrape_specific_matches(
                    match_urls=[url],
                    liga_nombre=f"{liga_nombre}_{i}",
                    save_files=False  # No guardar archivos en Docker
                )
                
                if encuentros:
                    all_encuentros.extend(encuentros)
                    all_goles.extend(goles)
                    logger.info(f"✓ Extraídos: {len(goles)} goles")
                else:
                    logger.warning(f"✗ No se pudieron extraer datos de {url}")
                    
            except Exception as e:
                logger.error(f"Error procesando {url}: {e}")
                continue
        
        # Preparar resultado
        result = {
            'success': True,
            'message': f'Scraping completado: {len(all_encuentros)} encuentros, {len(all_goles)} goles',
            'encuentros_procesados': len(all_encuentros),
            'goles_extraidos': len(all_goles),
            'encuentros': all_encuentros,
            'goles': all_goles,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log del resultado
        logger.info(f"Resultado: {len(all_encuentros)} encuentros, {len(all_goles)} goles")
        
        return result
        
    except Exception as e:
        logger.error(f"Error en execute_scraping: {e}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Función principal"""
    try:
        # Ejecutar scraping
        result = execute_scraping()
        
        # Imprimir resultado como JSON (para n8n)
        print(json.dumps(result, ensure_ascii=False))
        
        # Retornar código de salida
        sys.exit(0 if result.get('success') else 1)
        
    except Exception as e:
        error_result = {
            'success': False,
            'error': f'Error inesperado: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()