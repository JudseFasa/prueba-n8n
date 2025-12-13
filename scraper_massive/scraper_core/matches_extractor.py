# matches_extractor.py
# Extracción de partidos de una temporada y envío a la cola

import re
import sqlite3
from scraper_core.queue_manager import QueueManager
from scraper_core.utils_urls import parse_url
from scraper_core.utils_dom import click_mostrar_mas_partidos, expand_all

PAGE_TIMEOUT = 60000


def init_db(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS partidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pais TEXT,
            liga TEXT,
            temporada TEXT,
            jornada INTEGER,
            fecha TEXT,
            local TEXT,
            visitante TEXT,
            g_local_1t INTEGER,
            g_visitante_1t INTEGER,
            g_local_2t INTEGER,
            g_visitante_2t INTEGER,
            minutos_local_1t TEXT,
            minutos_visitante_1t TEXT,
            minutos_local_2t TEXT,
            minutos_visitante_2t TEXT,
            UNIQUE(pais, liga, temporada, jornada, fecha, local, visitante)
        )
    """)
    conn.commit()
    conn.close()


def save_empty_match(db_name, pais, liga, temporada, jornada, fecha, local, visitante):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO partidos
        (pais, liga, temporada, jornada, fecha, local, visitante,
         g_local_1t, g_visitante_1t, g_local_2t, g_visitante_2t,
         minutos_local_1t, minutos_visitante_1t, minutos_local_2t, minutos_visitante_2t)
        VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, '', '', '', '')
    """, (pais, liga, temporada, jornada, fecha, local, visitante))
    conn.commit()
    conn.close()


class Partido:
    __slots__ = (
        "jornada", "fecha", "local", "visitante", "match_url",
        "pais", "liga", "temporada", "db_name"
    )

    def __init__(self, jornada, fecha, local, visitante, match_url,
                 pais, liga, temporada, db_name):
        self.jornada = jornada
        self.fecha = fecha
        self.local = local
        self.visitante = visitante
        self.match_url = match_url
        self.pais = pais
        self.liga = liga
        self.temporada = temporada
        self.db_name = db_name


async def extract_matches_temporada(page, temporada_info, db_name, queue: QueueManager):
    pais = temporada_info['pais']
    liga = temporada_info['liga']
    temporada = temporada_info['año']

    print(f"\n====== {pais.upper()} | {liga} | {temporada} ======")
    print(f"🌐 URL: {temporada_info['url']}")

    init_db(db_name)

    await page.goto(temporada_info['url'], timeout=PAGE_TIMEOUT, wait_until="networkidle")

    try:
        await click_mostrar_mas_partidos(page)
        await page.wait_for_selector(".event__match", timeout=5000)
    except:
        print("⚠️ No se encontraron partidos")
        return

    await expand_all(page)

    jornada_actual = None
    rounds = page.locator(".event__round")
    for i in range(await rounds.count()):
        try:
            txt = await rounds.nth(i).inner_text()
            m = re.search(r"Jornada\s+(\d+)", txt, re.IGNORECASE)
            if m:
                jornada_actual = int(m.group(1))
        except:
            continue

    matches = page.locator(".event__match")
    total = await matches.count()
    print(f"📊 Encontrados {total} partidos")

    for i in range(total):
            item = matches.nth(i)
            data = await item.evaluate("""
                node => ({
                    fecha: node.querySelector('.event__time')?.textContent?.trim() || '',
                    local: node.querySelector('.event__homeParticipant')?.textContent?.trim() || '',
                    visitante: node.querySelector('.event__awayParticipant')?.textContent?.trim() || ''
                })
            """)

            link = item.locator("a.eventRowLink")
            href = await link.get_attribute("href") if await link.count() else None

            if not href:
                pid = await item.get_attribute("id")
                if pid and pid.startswith("g_"):
                    href = f"/partido/{pid.replace('g_', '')}/"

            if not href:
                continue

            full_url = f"https://www.flashscore.co{href}" if href.startswith("/") else href

            save_empty_match(
                db_name, pais, liga, temporada,
                jornada_actual, data['fecha'], data['local'], data['visitante']
            )

            partido = Partido(
                jornada_actual, data['fecha'], data['local'], data['visitante'],
                full_url, pais, liga, temporada, db_name
            )

            await queue.put(partido)

            if (i + 1) % 25 == 0:
                print(f"  ➕ {i + 1} partidos enviados a cola")

    print(f"📥 Total enviados a cola: {total}")
