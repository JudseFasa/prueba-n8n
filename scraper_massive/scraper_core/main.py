# main.py - Versión compatible con Windows
import asyncio
import sys
from playwright.async_api import async_playwright
from seasons import obtener_todas_temporadas
from season_worker import SeasonWorker
from goals_worker import GoalsWorker
from config import SEASON_WORKERS, GOALS_WORKERS, BROWSER_ARGS, MEMORY_MANAGEMENT
from memory_manager import memory_manager
from page_pool import PagePool

class ScraperManager:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page_pools = {}
        self.tasks = []
        self.shutdown_event = asyncio.Event()
        
    async def setup(self):
        """Configura el navegador y pools"""
        print("🔄 Configurando sistema con gestión de memoria...")
        
        # Iniciar navegador
        playwright = await async_playwright().__aenter__()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=BROWSER_ARGS
        )
        
        # Crear contexto
        self.context = await self.browser.new_context()
        
        # Configurar bloqueo de recursos
        await self.context.route("**/*.{png,jpg,jpeg,gif,svg,webp}", lambda r: r.abort())
        await self.context.route("**/*.{css,woff,woff2}", lambda r: r.abort())
        
        # Crear pools de páginas por tipo de worker
        self.page_pools['season'] = await PagePool(
            self.context,
            max_pages=MEMORY_MANAGEMENT['PAGE_POOL_SIZE'],
            max_age_minutes=MEMORY_MANAGEMENT['PAGE_MAX_AGE_MINUTES']
        ).start()
        
        self.page_pools['goals'] = await PagePool(
            self.context,
            max_pages=MEMORY_MANAGEMENT['PAGE_POOL_SIZE'],
            max_age_minutes=MEMORY_MANAGEMENT['PAGE_MAX_AGE_MINUTES']
        ).start()
        
        # Iniciar monitor de memoria
        self.tasks.append(asyncio.create_task(memory_manager.monitor_memory()))
        
    async def cleanup(self):
        """Limpia todos los recursos"""
        print("🧹 Limpiando recursos...")
        
        # Cancelar todas las tareas
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Cerrar pools
        for pool in self.page_pools.values():
            await pool.stop()
        
        # Cerrar contexto y navegador
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        
        # Forzar garbage collection
        import gc
        gc.collect()
        
    def handle_shutdown(self):
        """Maneja señal de apagado"""
        print("\n⚠️  Recibida señal de apagado, limpiando...")
        self.shutdown_event.set()

async def main_pipeline(urls_base):
    """Función principal con gestión de memoria mejorada - Windows compatible"""
    manager = ScraperManager()
    
    # SOLUCIÓN: Para Windows, no usar signal handlers
    # En su lugar, usar asyncio.create_task para manejar interrupciones
    if sys.platform != 'win32':
        # Solo configurar señales en sistemas Unix/Linux
        try:
            import signal
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, manager.handle_shutdown)
        except (ImportError, NotImplementedError):
            pass
    
    try:
        await manager.setup()
        
        # 1. CREACIÓN DE COLAS
        cola_temporadas = asyncio.Queue(maxsize=5)    # Buffer reducido
        cola_partidos = asyncio.Queue(maxsize=50)     # Buffer reducido
        
        # 2. TAREA PRODUCTORA CON CONTROL
        async def productor_temporadas():
            for idx, liga in enumerate(urls_base):
                if manager.shutdown_event.is_set():
                    break
                    
                if "|" in liga:
                    url_base, nombre_base = liga.split("|")
                    nombre_base = nombre_base.strip()
                else:
                    url_base = liga
                    nombre_base = url_base.split("/")[-1]
                
                url_base = url_base.strip().rstrip('/')
                
                print(f"\n🔍 [{idx+1}/{len(urls_base)}] Procesando liga: {nombre_base}")
                
                # Chequear memoria antes de continuar
                stats = memory_manager.get_stats()
                if stats['percent_used'] > 70:
                    print(f"⚠️  Memoria alta ({stats['percent_used']:.1f}%), esperando...")
                    await memory_manager.force_memory_cleanup()
                    await asyncio.sleep(2)
                
                # Obtener temporadas
                async for temp_info in obtener_todas_temporadas(manager.context, url_base, nombre_base, max_temporadas=5):
                    if manager.shutdown_event.is_set():
                        break
                    
                    await cola_temporadas.put(temp_info)
                    print(f"[Productor] 📥 Temporada {temp_info['año']} puesta en cola.")
            
            # Señal de terminación
            for _ in range(SEASON_WORKERS):
                await cola_temporadas.put(None)
        
        # 3. CREACIÓN DE WORKERS CON POOLS
        season_workers = []
        for i in range(SEASON_WORKERS):
            worker = SeasonWorker(
                worker_id=i,
                context=manager.context,
                page_pool=manager.page_pools['season'],
                cola_temporadas=cola_temporadas,
                cola_partidos=cola_partidos
            )
            season_workers.append(worker)
        
        goals_workers = []
        for i in range(GOALS_WORKERS):
            worker = GoalsWorker(
                worker_id=i,
                context=manager.context,
                page_pool=manager.page_pools['goals'],
                cola_partidos=cola_partidos
            )
            goals_workers.append(worker)
        
        # 4. EJECUCIÓN CON SUPERVISIÓN
        tasks = []
        
        # Productor
        tasks.append(asyncio.create_task(productor_temporadas()))
        
        # Workers de temporadas
        for worker in season_workers:
            task = asyncio.create_task(worker.worker_loop())
            task.add_done_callback(lambda t: print(f"✅ SeasonWorker terminado"))
            tasks.append(task)
        
        # Workers de goles
        for worker in goals_workers:
            task = asyncio.create_task(worker.worker_loop())
            task.add_done_callback(lambda t: print(f"✅ GoalsWorker terminado"))
            tasks.append(task)
        
        # Tarea para mostrar estadísticas periódicas
        async def show_stats():
            while not manager.shutdown_event.is_set():
                await asyncio.sleep(30)
                mem_stats = memory_manager.get_stats()
                season_stats = manager.page_pools['season'].get_stats()
                goals_stats = manager.page_pools['goals'].get_stats()
                
                print(f"\n📈 ESTADÍSTICAS:")
                print(f"   🧠 Memoria: {mem_stats['memory_mb']:.1f}MB ({mem_stats['percent_used']:.1f}%)")
                print(f"   📄 Season Pool: {season_stats['active_pages']}/{season_stats['max_pages']} páginas")
                print(f"   ⚽ Goals Pool: {goals_stats['active_pages']}/{goals_stats['max_pages']} páginas")
                print(f"   📊 Colas: T[{cola_temporadas.qsize()}] P[{cola_partidos.qsize()}]")
        
        tasks.append(asyncio.create_task(show_stats()))
        
        # 5. TAREA PARA MANEJAR INTERRUPCIONES EN WINDOWS
        if sys.platform == 'win32':
            async def windows_shutdown_handler():
                """Manejador de interrupciones para Windows"""
                try:
                    # Esperar hasta que se active el shutdown_event
                    await manager.shutdown_event.wait()
                except asyncio.CancelledError:
                    pass
            
            shutdown_task = asyncio.create_task(windows_shutdown_handler())
            tasks.append(shutdown_task)
        
        # 6. ESPERA CON CONTROL DE MEMORIA
        try:
            # Crear una tarea de espera principal
            main_task = asyncio.gather(*tasks)
            
            # Para Windows: manejar KeyboardInterrupt manualmente
            if sys.platform == 'win32':
                try:
                    await main_task
                except KeyboardInterrupt:
                    print("\n🛑 Interrupción por usuario (Ctrl+C)")
                    manager.shutdown_event.set()
                    # Cancelar todas las tareas
                    for task in tasks:
                        task.cancel()
                    # Esperar a que se cancelen
                    await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # Para Unix/Linux, las señales ya están configuradas
                await main_task
                
        except asyncio.CancelledError:
            # Tarea cancelada por timeout u otra razón
            print("\n⏰ Tarea principal cancelada")
            manager.shutdown_event.set()
            
        # 7. ESPERAR A QUE TERMINEN LAS TAREAS
        print("\n⏳ Esperando que terminen las tareas...")
        
        # Señal de terminación para workers de goles
        for _ in range(GOALS_WORKERS):
            try:
                await cola_partidos.put(None)
            except:
                pass
        
        # Esperar con timeout
        try:
            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=10)
        except asyncio.TimeoutError:
            print("⚠️  Timeout esperando a que terminen las tareas")
        
    finally:
        # 8. LIMPIEZA FINAL
        await manager.cleanup()
        
        # Mostrar estadísticas finales
        print("\n" + "="*60)
        print("📊 ESTADÍSTICAS FINALES:")
        print("="*60)
        
        if hasattr(manager, 'page_pools'):
            for name, pool in manager.page_pools.items():
                stats = pool.get_stats()
                print(f"   {name.upper()} POOL:")
                print(f"      Páginas creadas: {stats['created_count']}")
                print(f"      Páginas reusadas: {stats['reused_count']}")
                print(f"      Reuso efectivo: {stats['reused_percent']:.1f}%")
        
        mem_stats = memory_manager.get_stats()
        print(f"\n   🧠 USO DE MEMORIA:")
        print(f"      Máximo permitido: {mem_stats['max_memory_mb']}MB")
        print(f"      Limpiezas forzadas: {mem_stats['restart_count']}")
        print(f"      Última limpieza: {mem_stats['last_restart']}")
        print("="*60)