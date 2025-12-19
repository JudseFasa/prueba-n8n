# page_pool.py
import asyncio
from collections import deque
from datetime import datetime, timedelta
import random

class PagePool:
    def __init__(self, context, max_pages=5, max_age_minutes=5, cleanup_interval=30):
        self.context = context
        self.max_pages = max_pages
        self.max_age = timedelta(minutes=max_age_minutes)
        self.cleanup_interval = cleanup_interval
        
        # Estructuras de datos
        self.available_pages = deque()  # Páginas disponibles
        self.in_use_pages = {}  # Páginas en uso {page_id: {"page": page, "created_at": datetime, "last_used": datetime}}
        self.page_counter = 0
        
        # Estadísticas
        self.created_count = 0
        self.reused_count = 0
        self.cleaned_count = 0
        
        # Tarea de limpieza en segundo plano
        self.cleanup_task = None
        
    async def start(self):
        """Inicia el pool y la tarea de limpieza"""
        self.cleanup_task = asyncio.create_task(self._cleanup_old_pages())
        return self
    
    async def stop(self):
        """Detiene el pool y cierra todas las páginas"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cerrar todas las páginas
        all_pages = list(self.available_pages) + [info["page"] for info in self.in_use_pages.values()]
        for page in all_pages:
            try:
                await page.close()
            except:
                pass
        
        self.available_pages.clear()
        self.in_use_pages.clear()
    
    async def get_page(self):
        """Obtiene una página del pool (crea nueva si es necesario)"""
        now = datetime.now()
        
        # Intentar reusar una página disponible
        while self.available_pages:
            page = self.available_pages.popleft()
            page_id = id(page)
            
            # Verificar si la página es muy vieja
            if page_id in self.in_use_pages:
                page_info = self.in_use_pages[page_id]
                if now - page_info["created_at"] > self.max_age:
                    # Página muy vieja, cerrarla y crear nueva
                    try:
                        await page.close()
                    except:
                        pass
                    del self.in_use_pages[page_id]
                    self.cleaned_count += 1
                    continue
            
            # Página válida, marcar como en uso
            if page_id in self.in_use_pages:
                self.in_use_pages[page_id]["last_used"] = now
            self.reused_count += 1
            return page
        
        # Crear nueva página si no hay disponibles y no superamos el límite
        if len(self.in_use_pages) < self.max_pages:
            page = await self.context.new_page()
            page_id = id(page)
            
            self.in_use_pages[page_id] = {
                "page": page,
                "created_at": now,
                "last_used": now
            }
            self.created_count += 1
            return page
        
        # Esperar a que haya una página disponible
        print(f"⏳ Pool lleno ({len(self.in_use_pages)}/{self.max_pages}), esperando página...")
        await asyncio.sleep(random.uniform(0.1, 0.5))
        return await self.get_page()
    
    async def release_page(self, page):
        """Devuelve una página al pool"""
        page_id = id(page)
        
        if page_id in self.in_use_pages:
            # Actualizar último uso
            self.in_use_pages[page_id]["last_used"] = datetime.now()
            
            # Limpiar cookies y cache de la página
            try:
                await page.goto("about:blank")
                await page.context.clear_cookies()
            except:
                pass
            
            # Devolver al pool de disponibles
            self.available_pages.append(page)
    
    async def force_cleanup(self):
        """Fuerza limpieza de páginas antiguas"""
        now = datetime.now()
        pages_to_close = []
        
        # Identificar páginas muy antiguas
        for page_id, info in list(self.in_use_pages.items()):
            if now - info["created_at"] > self.max_age * 2:  # El doble de la edad máxima
                pages_to_close.append(info["page"])
                del self.in_use_pages[page_id]
        
        # Cerrar páginas antiguas
        for page in pages_to_close:
            try:
                await page.close()
            except:
                pass
        
        # Limpiar páginas disponibles que sean muy antiguas
        cleaned_available = 0
        temp_available = []
        
        for page in list(self.available_pages):
            page_id = id(page)
            if page_id in self.in_use_pages:
                info = self.in_use_pages[page_id]
                if now - info["created_at"] > self.max_age * 2:
                    try:
                        await page.close()
                    except:
                        pass
                    cleaned_available += 1
                else:
                    temp_available.append(page)
        
        self.available_pages = deque(temp_available)
        self.cleaned_count += len(pages_to_close) + cleaned_available
        
        if pages_to_close or cleaned_available:
            print(f"🧹 Forzada limpieza: {len(pages_to_close)} en uso + {cleaned_available} disponibles")
    
    async def _cleanup_old_pages(self):
        """Tarea en segundo plano que limpia páginas antiguas"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.force_cleanup()
                
                # Reporte periódico
                if self.created_count % 10 == 0:
                    stats = self.get_stats()
                    print(f"📊 Pool stats: {stats['active_pages']}/{stats['max_pages']} páginas, "
                          f"Reusadas: {stats['reused_percent']:.1f}%")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error en limpieza del pool: {e}")
    
    def get_stats(self):
        """Obtiene estadísticas del pool"""
        active_pages = len(self.in_use_pages)
        total_operations = self.created_count + self.reused_count
        reused_percent = (self.reused_count / total_operations * 100) if total_operations > 0 else 0
        
        return {
            'max_pages': self.max_pages,
            'active_pages': active_pages,
            'available_pages': len(self.available_pages),
            'created_count': self.created_count,
            'reused_count': self.reused_count,
            'cleaned_count': self.cleaned_count,
            'reused_percent': reused_percent
        }