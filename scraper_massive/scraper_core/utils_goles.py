# utils_goles.py
import sqlite3


def _empty():
    return {
        "g_local_1t": 0, "g_visitante_1t": 0,
        "g_local_2t": 0, "g_visitante_2t": 0,
        "minutos_local_1t": "", "minutos_visitante_1t": "",
        "minutos_local_2t": "", "minutos_visitante_2t": "",
    }


async def extraer_detalles(detail_page):
    try:
        await detail_page.wait_for_selector(".smv__verticalSections", timeout=8000)
    except:
        return _empty()

    sections = await detail_page.locator(".smv__verticalSections > div").all()
    current_half = None
    goles = [[[], []], [[], []]]  # [1t/2t][home/away]

    for sec in sections:
        try:
            # Detectar cambio de tiempo (1T / 2T)
            if await sec.evaluate(
                "e => e.classList.contains('wclHeaderSection--summary')"
            ):
                half_elem = sec.locator(
                    ".wcl-overline_uwiIT:has-text('Tiempo')"
                )
                if await half_elem.count() > 0:
                    txt = await half_elem.inner_text()
                    if "1er" in txt:
                        current_half = 1
                    elif "2º" in txt:
                        current_half = 2
                    else:
                        current_half = None
                continue

            # Detectar gol
            if await sec.locator("[data-testid='wcl-icon-soccer']").count() > 0:
                time_elem = sec.locator(".smv__timeBox")
                if await time_elem.count() > 0:
                    time = (await time_elem.inner_text()).rstrip("'")
                    classes = await sec.evaluate(
                        "el => Array.from(el.classList)"
                    )
                    is_home = "smv__homeParticipant" in classes

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


def update_match(
    db_name, pais, liga, temporada, jornada,
    fecha, local, visitante, goles
):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("""
        UPDATE partidos SET
            g_local_1t = ?,
            g_visitante_1t = ?,
            g_local_2t = ?,
            g_visitante_2t = ?,
            minutos_local_1t = ?,
            minutos_visitante_1t = ?,
            minutos_local_2t = ?,
            minutos_visitante_2t = ?
        WHERE pais=? AND liga=? AND temporada=? AND jornada=?
          AND fecha=? AND local=? AND visitante=?
    """, (
        goles["g_local_1t"],
        goles["g_visitante_1t"],
        goles["g_local_2t"],
        goles["g_visitante_2t"],
        goles["minutos_local_1t"],
        goles["minutos_visitante_1t"],
        goles["minutos_local_2t"],
        goles["minutos_visitante_2t"],
        pais, liga, temporada, jornada,
        fecha, local, visitante
    ))

    conn.commit()
    conn.close()
