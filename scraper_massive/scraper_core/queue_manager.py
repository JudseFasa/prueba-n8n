# queue_manager.py
# Manejo centralizado de la cola de partidos y señales de control

import asyncio

class QueueManager:
    def __init__(self, maxsize=100):
        self.queue = asyncio.Queue(maxsize=maxsize)
        self._finished = False

    async def put(self, item):
        """Agrega un item a la cola (bloquea si está llena)"""
        await self.queue.put(item)

    async def get(self):
        """Obtiene un item de la cola"""
        return await self.queue.get()

    def task_done(self):
        self.queue.task_done()

    def qsize(self):
        return self.queue.qsize()

    async def wait_until_half_empty(self):
        """Evita que la cola crezca sin control (backpressure suave)"""
        while self.queue.qsize() > self.queue.maxsize // 2:
            await asyncio.sleep(0.5)

    async def finish(self):
        """Marca el fin del productor (señal de cierre)"""
        self._finished = True

    def finished(self):
        return self._finished

    async def wait_until_done(self):
        """Espera a que todos los items hayan sido procesados"""
        await self.queue.join()
