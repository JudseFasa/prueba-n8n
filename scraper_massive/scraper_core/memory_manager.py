# memory_manager.py
import psutil
import os
import gc
import asyncio
from datetime import datetime

class MemoryManager:
    def __init__(self, max_memory_mb=500, check_interval=10):
        self.max_memory_mb = max_memory_mb
        self.check_interval = check_interval
        self.force_restart_threshold = max_memory_mb * 0.8  # 80% del máximo
        self.process = psutil.Process(os.getpid())
        self.last_restart = datetime.now()
        self.restart_count = 0
        
    async def monitor_memory(self):
        """Monitorea el uso de memoria y fuerza limpieza si es necesario"""
        while True:
            memory_usage = self.process.memory_info().rss / 1024 / 1024  # MB
            
            if memory_usage > self.force_restart_threshold:
                print(f"⚠️  MEMORIA ALTA: {memory_usage:.2f}MB > {self.force_restart_threshold:.2f}MB")
                await self.force_memory_cleanup()
            
            await asyncio.sleep(self.check_interval)
    
    async def force_memory_cleanup(self):
        """Fuerza una limpieza completa de memoria"""
        print("🧹 FORZANDO LIMPIEZA DE MEMORIA...")
        
        # 1. Recolector de basura
        gc.collect()
        
        # 2. Limpiar caches de asyncio
        loop = asyncio.get_event_loop()
        if hasattr(loop, '_ready'):
            loop._ready.clear()
        
        # 3. Reportar estadísticas
        memory_before = self.process.memory_info().rss / 1024 / 1024
        print(f"   📊 Memoria antes: {memory_before:.2f}MB")
        
        self.restart_count += 1
        self.last_restart = datetime.now()
        
    def get_stats(self):
        """Obtiene estadísticas de memoria"""
        memory_usage = self.process.memory_info().rss / 1024 / 1024
        return {
            'memory_mb': memory_usage,
            'max_memory_mb': self.max_memory_mb,
            'restart_count': self.restart_count,
            'last_restart': self.last_restart.strftime('%H:%M:%S'),
            'percent_used': (memory_usage / self.max_memory_mb) * 100
        }

# Instancia global
memory_manager = MemoryManager(max_memory_mb=500)