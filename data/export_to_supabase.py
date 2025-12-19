# export_to_supabase_v2.py
import sqlite3
from supabase import create_client
from datetime import datetime
import os

SUPABASE_URL = "https://mvsnymlcqutxnmnfxdgt.supabase.co"  # Cambiar por tu URL
SUPABASE_KEY = "sb_secret_Wo7RzDpb1DZitr-_1Dy8PA_LDq0SoME"  # Cambiar por tu service_role key
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def one(table, **eq):
    q = supabase.table(table).select("id")
    for k, v in eq.items():
        q = q.eq(k, v)
    r = q.execute()
    return r.data[0]["id"] if r.data else None


def insert_ignore(table, data):
    return supabase.table(table).insert(data).execute()


# -------------------------------------------------
# GET OR CREATE (SIMPLES)
# -------------------------------------------------

def get_pais(nombre):
    pid = one("paises", nombre=nombre)
    if pid:
        return pid
    r = insert_ignore("paises", {"nombre": nombre})
    return r.data[0]["id"]


def get_liga(pais_id, nombre):
    lid = one("ligas", pais_id=pais_id, nombre=nombre)
    if lid:
        return lid
    r = insert_ignore("ligas", {
        "pais_id": pais_id,
        "nombre": nombre,
        "is_active": True
    })
    return r.data[0]["id"]


def get_temporada(liga_id, nombre):
    tid = one("temporadas", liga_id=liga_id, nombre=nombre)
    if tid:
        return tid
    r = insert_ignore("temporadas", {
        "liga_id": liga_id,
        "nombre": nombre,
        "is_current": False
    })
    return r.data[0]["id"]


def get_fase(liga_id, nombre):
    fid = one("fases", liga_id=liga_id, nombre=nombre)
    if fid:
        return fid
    r = insert_ignore("fases", {
        "liga_id": liga_id,
        "nombre": nombre
    })
    return r.data[0]["id"]


def get_equipo(nombre):
    eid = one("equipos", nombre=nombre)
    if eid:
        return eid
    r = insert_ignore("equipos", {"nombre": nombre})
    return r.data[0]["id"]

def is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def parse_fecha_flashscore(fecha_raw: str, temporada: str) -> str:
    if not fecha_raw:
        return None

    fecha_raw = fecha_raw.split()[0].rstrip(".")
    dia, mes = map(int, fecha_raw.split("."))

    y1, y2 = map(int, temporada.split("-"))

    # año por regla general
    year = y1 if mes >= 7 else y2

    # corrección específica para 29 de febrero
    if mes == 2 and dia == 29 and not is_leap(year):
        # usar el otro año de la temporada si es bisiesto
        alt = y1 if year == y2 else y2
        if is_leap(alt):
            year = alt
        else:
            # fallback ultra seguro (no debería pasar)
            return None

    return f"{year:04d}-{mes:02d}-{dia:02d}"



# -------------------------------------------------
# MIGRACIÓN
# -------------------------------------------------

def migrate_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM partidos")
    rows = cur.fetchall()

    if not rows:
        return

    base = dict(rows[0])

    pais_id = get_pais(base["pais"])
    liga_id = get_liga(pais_id, base["liga"])
    temporada_id = get_temporada(liga_id, base["temporada"])

    equipos = set()
    fases = set()

    for r in rows:
        equipos.add(r["local"])
        equipos.add(r["visitante"])
        fases.add(r["fase"] or "Temporada Regular")

    equipos_map = {n: get_equipo(n) for n in equipos}
    fases_map = {n: get_fase(liga_id, n) for n in fases}

    partidos_payload = []

    for r in rows:
        fecha = r["fecha"]
        if "-" not in fecha:
            fecha = parse_fecha_flashscore(r["fecha"], base["temporada"])

        partidos_payload.append({
            "temporada_id": temporada_id,
            "fase_id": fases_map[r["fase"] or "Temporada Regular"],
            "jornada": r["jornada"],
            "fecha": fecha,
            "local_id": equipos_map[r["local"]],
            "visitante_id": equipos_map[r["visitante"]],
            "g_local_1t": r["g_local_1t"],
            "g_visitante_1t": r["g_visitante_1t"],
            "g_local_2t": r["g_local_2t"],
            "g_visitante_2t": r["g_visitante_2t"],
            "minutos_local_1t": r["minutos_local_1t"],
            "minutos_visitante_1t": r["minutos_visitante_1t"],
            "minutos_local_2t": r["minutos_local_2t"],
            "minutos_visitante_2t": r["minutos_visitante_2t"],
            "status": "FINISHED"
        })

    supabase.table("partidos").upsert(
        partidos_payload,
        on_conflict="temporada_id,fase_id,jornada,fecha,local_id,visitante_id"
    ).execute()

    conn.close()


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main(folder):
    for f in os.listdir(folder):
        if f.endswith(".db"):
            print("Migrando:", f)
            migrate_db(os.path.join(folder, f))


if __name__ == "__main__":
    main("X:/prueba n8n/data")