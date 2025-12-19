# goals_worker.py - Versión mejorada
import asyncio
from db import update_match
from config import MAX_PARTIDOS_POR_PAGINA

class GoalsWorker:
    def __init__(self, worker_id, context, page_pool, cola_partidos):
        self.worker_id = worker_id
        self.context = context
        self.page_pool = page_pool
        self.cola_partidos = cola_partidos
        self.page = None
        self.contador_partidos = 0
        self.total_procesados = 0

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
            self.contador_partidos = 0

    async def _reiniciar_pagina_si_necesario(self):
        """Reinicia la página periódicamente"""
        if self.contador_partidos >= MAX_PARTIDOS_POR_PAGINA:
            print(f"[GoalsWorker {self.worker_id}] 🔄 Reiniciando página ({self.contador_partidos} partidos)")
            await self.release_page()
            await asyncio.sleep(0.2)  # Pequeña pausa

    async def extraer_detalles_goles(self, url):
        """Extrae los goles de la página de detalle de un partido"""
        try:
            page = await self.get_page()
            
            # Intentar navegar con timeout reducido
            for intento in range(2):
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=5000)
                    await page.wait_for_selector(".smv__verticalSections", timeout=3000)
                    break
                except:
                    if intento == 1:
                        return self._datos_vacios()
                    await asyncio.sleep(0.5)
        except:
            return self._datos_vacios()
        
        sections = await page.locator(".smv__verticalSections > div").all()
        current_half = None
        goles = [[[], []], [[], []]]  # [1t/2t][home/away]
        
        for sec in sections:
            try:
                if await sec.evaluate("e => e.classList.contains('wclHeaderSection--summary')"):
                    half_elem = sec.locator(".wcl-overline_uwiIT:has-text('Tiempo')")
                    if await half_elem.count() > 0:
                        txt = await half_elem.inner_text()
                        current_half = 1 if "1er" in txt else 2 if "2º" in txt else None
                    continue
                
                if await sec.locator("[data-testid='wcl-icon-soccer']").count() > 0:
                    time_elem = sec.locator(".smv__timeBox")
                    if await time_elem.count() > 0:
                        time = (await time_elem.inner_text()).rstrip("'")
                        is_home = 'smv__homeParticipant' in await sec.evaluate("el => Array.from(el.classList)")
                        
                        if current_half == 1:
                            goles[0][0 if is_home else 1].append(time)
                        elif current_half == 2:
                            goles[1][0 if is_home else 1].append(time)
            except:
                continue
        
        def orden(x):
            try:
                if "+" in x:
                    a, b = x.split("+")
                    return int(a) * 100 + int(b)
                return int(x) * 100
            except:
                return 0
        
        return {
            "g_local_1t": len(goles[0][0]),
            "g_visitante_1t": len(goles[0][1]),
            "g_local_2t": len(goles[1][0]),
            "g_visitante_2t": len(goles[1][1]),
            "minutos_local_1t": ", ".join(sorted(goles[0][0], key=orden)),
            "minutos_visitante_1t": ", ".join(sorted(goles[0][1], key=orden)),
            "minutos_local_2t": ", ".join(sorted(goles[1][0], key=orden)),
            "minutos_visitante_2t": ", ".join(sorted(goles[1][1], key=orden)),
        }

    def _datos_vacios(self):
        """Retorna datos vacíos para partidos sin información"""
        return {
            "g_local_1t": 0, "g_visitante_1t": 0,
            "g_local_2t": 0, "g_visitante_2t": 0,
            "minutos_local_1t": "", "minutos_visitante_1t": "",
            "minutos_local_2t": "", "minutos_visitante_2t": "",
        }

    async def procesar_partido(self, partido):
        """Procesa un partido individual"""
        await self._reiniciar_pagina_si_necesario()
        
        try:
            datos_goles = await self.extraer_detalles_goles(partido['url'])
            
            # Actualizar la base de datos
            update_match(
                partido['db_name'],
                partido['pais'],
                partido['liga'],
                partido['temporada'],
                partido['fase'],
                partido['jornada'],
                partido['fecha'],
                partido['local'],
                partido['visitante'],
                datos_goles
            )
            
            self.contador_partidos += 1
            self.total_procesados += 1
            
            if self.total_procesados % 20 == 0:
                total_local = datos_goles["g_local_1t"] + datos_goles["g_local_2t"]
                total_visitante = datos_goles["g_visitante_1t"] + datos_goles["g_visitante_2t"]
                print(f"[GoalsWorker {self.worker_id}] ✅ {partido['local']} {total_local}-{total_visitante} {partido['visitante']} (Total: {self.total_procesados})")
            
        except Exception as e:
            print(f"[GoalsWorker {self.worker_id}] ❌ Error procesando {partido['local']} vs {partido['visitante']}: {str(e)[:50]}")

    async def worker_loop(self):
        """Loop principal del worker"""
        print(f"[GoalsWorker {self.worker_id}] 🚀 Iniciando worker...")
        
        try:
            while True:
                partido = await self.cola_partidos.get()
                if partido is None:  # Señal de terminación
                    await self.release_page()
                    await self.cola_partidos.put(None)  # Pasar la señal
                    break
                
                try:
                    await self.procesar_partido(partido)
                except Exception as e:
                    print(f"[GoalsWorker {self.worker_id}] ⚠️ Error en partido: {e}")
                
                self.cola_partidos.task_done()
                
                # Pequeña pausa para no saturar
                if self.contador_partidos % 5 == 0:
                    await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"[GoalsWorker {self.worker_id}] 💥 Error fatal: {e}")
        finally:
            await self.release_page()
            print(f"[GoalsWorker {self.worker_id}] 🏁 Terminando worker. Procesados: {self.total_procesados}")