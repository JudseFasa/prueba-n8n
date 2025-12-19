# db.py
import sqlite3
import os
from config import DB_FOLDER

def init_db(db_name):
    """Crea la tabla de partidos si no existe"""
    # Asegurar que la carpeta existe
    os.makedirs(DB_FOLDER, exist_ok=True)
    
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS partidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pais TEXT,
            liga TEXT,
            temporada TEXT,
            fase TEXT,
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
            UNIQUE(pais, liga, temporada, fase, jornada, fecha, local, visitante)
        )
    """)
    conn.commit()
    conn.close()

def save_empty_match(db_name, pais, liga, temporada, fase, jornada, fecha, local, visitante):
    """Guarda un partido sin datos de goles (para ser actualizado después)"""
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO partidos
        (pais, liga, temporada, fase, jornada, fecha, local, visitante,
         g_local_1t, g_visitante_1t, g_local_2t, g_visitante_2t,
         minutos_local_1t, minutos_visitante_1t, minutos_local_2t, minutos_visitante_2t)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, '', '', '', '')
    """, (pais, liga, temporada, fase, jornada, fecha, local, visitante))
    conn.commit()
    conn.close()

def update_match(db_name, pais, liga, temporada, fase, jornada, fecha, local, visitante, datos):
    """Actualiza los goles y minutos de un partido"""
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        UPDATE partidos SET
            g_local_1t = ?, g_visitante_1t = ?, g_local_2t = ?, g_visitante_2t = ?,
            minutos_local_1t = ?, minutos_visitante_1t = ?,
            minutos_local_2t = ?, minutos_visitante_2t = ?
        WHERE pais = ? AND liga = ? AND temporada = ? AND fase = ? AND jornada = ?
          AND fecha = ? AND local = ? AND visitante = ?
    """, (
        datos["g_local_1t"], datos["g_visitante_1t"],
        datos["g_local_2t"], datos["g_visitante_2t"],
        datos["minutos_local_1t"], datos["minutos_visitante_1t"],
        datos["minutos_local_2t"], datos["minutos_visitante_2t"],
        pais, liga, temporada, fase, jornada, fecha, local, visitante
    ))
    conn.commit()
    conn.close()