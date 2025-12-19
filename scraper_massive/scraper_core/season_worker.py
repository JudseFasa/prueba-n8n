# season_worker.py - Versión mejorada
import asyncio
import os
from db import init_db, save_empty_match
from matches import extraer_partidos_temporada
from config import DB_FOLDER

class SeasonWorker:
    def __init__(self, worker_id, context, page_pool, cola_temporadas, cola_partidos):
        self.worker_id = worker_id
        self.context = context
        self.page_pool = page_pool
        self.cola_temporadas = cola_temporadas
        self.cola_partidos = cola_partidos
        self.page = None

    async def get_page(self):
        """Obtiene una página del pool"""
        if self.page is None:
            self.page = await self.page_pool.get_page()
        return self.page

    async def release_page(self):
        """Devuelve la página al pool"""
        if self.page:
            await self.page_pool.release_page(self.page)
            self.page = None

    async def procesar_temporada(self, temp_info):
        """Procesa una temporada completa"""
        try:
            # Obtener página del pool
            page = await self.get_page()
            
            # Crear nombre de archivo para la base de datos
            año_limpio = temp_info['año'].replace("-", "_")
            nombre_archivo = f"{temp_info['liga_nombre']}_{año_limpio}"
            db_name = os.path.join(DB_FOLDER, f"{nombre_archivo}.db")
            
            print(f"[SeasonWorker {self.worker_id}] 📄 Creando DB: {db_name}")
            init_db(db_name)
            
            # Extraer partidos de la temporada
            partidos = await extraer_partidos_temporada(page, temp_info)
            
            if not partidos:
                print(f"[SeasonWorker {self.worker_id}] ⚠️ No se encontraron partidos")
                return
            
            # Guardar partidos vacíos en DB y poner en cola para extraer goles
            for partido in partidos:
                if self.cola_partidos.qsize() > 40:  # Si la cola está llena
                    print(f"[SeasonWorker {self.worker_id}] ⏳ Cola llena, esperando...")
                    await asyncio.sleep(1)
                
                # Guardar en DB
                save_empty_match(
                    db_name, 
                    partido['pais'], 
                    partido['liga'], 
                    partido['temporada'], 
                    partido['fase'], 
                    partido['jornada'], 
                    partido['fecha'], 
                    partido['local'], 
                    partido['visitante']
                )
                
                # Añadir db_name al partido
                partido['db_name'] = db_name
                
                # Poner en la cola de partidos
                await self.cola_partidos.put(partido)
            
            print(f"[SeasonWorker {self.worker_id}] ✅ Temporada {temp_info['año']} procesada. {len(partidos)} partidos encolados.")
            
        except Exception as e:
            print(f"[SeasonWorker {self.worker_id}] ❌ Error procesando temporada: {e}")
            # Forzar liberación de página en caso de error
            await self.release_page()

    async def worker_loop(self):
        """Loop principal del worker"""
        print(f"[SeasonWorker {self.worker_id}] 🚀 Iniciando worker...")
        
        try:
            while True:
                temp_info = await self.cola_temporadas.get()
                if temp_info is None:  # Señal de terminación
                    await self.release_page()
                    await self.cola_temporadas.put(None)  # Pasar la señal
                    break
                
                try:
                    await self.procesar_temporada(temp_info)
                finally:
                    # Liberar página después de cada temporada
                    await self.release_page()
                    await asyncio.sleep(0.5)  # Pequeña pausa
                
                self.cola_temporadas.task_done()
                
        except Exception as e:
            print(f"[SeasonWorker {self.worker_id}] 💥 Error fatal: {e}")
        finally:
            print(f"[SeasonWorker {self.worker_id}] 🏁 Terminando worker")