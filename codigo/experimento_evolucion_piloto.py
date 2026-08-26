#!/usr/bin/env python3
"""experimento_evolucion_piloto.py — PILOTO del experimento de evolucion (EVO-PILOTO-2026-08).
Linea base -> N ciclos del organismo -> metricas en SQLite -> veredicto H0/H1 pre-registrado."""
import argparse
import contextlib
import io
import json
import os
import socket
import sqlite3
import sys
import time
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import organismo_vivo_distribuido as vivo

DB = os.path.join(AQUI, "experimento_piloto.db")
REPORTE = os.path.join(AQUI, "coordinacion", "EXPERIMENTO_PILOTO_REPORTE.md")
PUERTOS = [("qfchain", 8545), ("enlace", 8787), ("bridge", 8006), ("sidecar", 8004),
           ("mamba", 8001), ("dashboard", 8050), ("qswift", 8051)]


def puerto(p):
    try:
        with socket.create_connection(("127.0.0.1", p), timeout=2):
            return True
    except OSError:
        return False


def uptime():
    act = sum(1 for _, p in PUERTOS if puerto(p))
    vig = 0
    lg = os.path.join(AQUI, "coordinacion", "vigilante_organismo.log")
    if os.path.exists(lg) and (time.time() - os.path.getmtime(lg)) < 900:
        vig = 1
    return act + vig, len(PUERTOS) + 1


def estado():
    est = vivo.leer_json(vivo.ORGANISMO, {})
    con = est.get("conciencia", {})
    return (con.get("coherencia_global", 0.0),
            con.get("masa_critica_total", 0.0),
            con.get("bloques_total", 0))


def ultima_tx():
    evo = vivo.leer_json(vivo.EVOLUCION, {"bloques": []})
    b = evo.get("bloques", [])
    return b[-1].get("tx_qfchain") if b else None


def main():
    ap = argparse.ArgumentParser(description="Piloto del experimento de evolucion")
    ap.add_argument("--ciclos", type=int, default=3)
    ap.add_argument("--pausa", type=float, default=0.0)
    args = ap.parse_args()
    N = max(1, args.ciclos)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS ciclos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ciclo INTEGER, ts TEXT,
        duracion_s REAL, coherencia REAL, masa_total REAL, uptime INTEGER,
        uptime_total INTEGER, tx_qfchain TEXT, ok INTEGER)""")

    coh0, masa0, bloq0 = estado()
    up0, tot0 = uptime()
    informe = []
    informe.append("# EXPERIMENTO DE EVOLUCION - PILOTO (EVO-PILOTO-2026-08)")
    informe.append("")
    informe.append(f"- Inicio: {datetime.now().isoformat()}")
    informe.append(f"- LINEA BASE: coherencia={coh0:.4f} | masa={masa0:.3e} | bloques={bloq0} | uptime={up0}/{tot0}")
    informe.append("")

    filas = []
    abortado = False
    for i in range(1, N + 1):
        t0 = time.time()
        buf = io.StringIO()
        ok = True
        err = ""
        with contextlib.redirect_stdout(buf):
            try:
                vivo.ciclo(i)
            except Exception as e:
                ok = False
                err = str(e)
        dur = time.time() - t0
        coh, masa, bloq = estado()
        up, tot = uptime()
        tx = ultima_tx()
        filas.append((i, datetime.now().isoformat(), dur, coh, masa, up, tot, tx, ok))
        informe.append(f"## Ciclo {i}")
        informe.append(f"- duracion={dur:.1f}s | coherencia={coh:.4f} | masa={masa:.3e} | uptime={up}/{tot} | ancla={tx or 'SIN ANCLA'} | ok={ok} {err}")
        salida = buf.getvalue()
        informe.append("```")
        informe.append(salida[-1500:] if len(salida) > 1500 else salida)
        informe.append("```")
        if up < 4 or coh < 0.5:
            abortado = True
            informe.append(f"**ABORTO:** uptime={up} o coherencia={coh} bajo el umbral.")
            break
        if args.pausa:
            time.sleep(args.pausa)

    for f in filas:
        cur.execute("INSERT INTO ciclos (ciclo, ts, duracion_s, coherencia, masa_total, uptime, uptime_total, tx_qfchain, ok) VALUES (?,?,?,?,?,?,?,?,?)", f)
    conn.commit()

    n = len(filas)
    f_coh = sum(1 for f in filas if f[3] < 1.0)
    f_up = sum(1 for f in filas if f[5] < 6)
    f_ancla = sum(1 for f in filas if not f[7])
    pct_coh = (n - f_coh) / n if n else 0
    pct_up = (n - f_up) / n if n else 0
    pct_ancla = (n - f_ancla) / n if n else 0
    masa_delta = (filas[-1][4] - masa0) / masa0 if masa0 and filas else 0
    pasa = (pct_coh >= 0.8 and pct_up >= 0.8 and pct_ancla >= 0.9
            and masa_delta > -0.01 and not abortado)
    falsa = (pct_coh <= 0.5 or pct_up <= 0.5 or f_ancla > 2
             or masa_delta < -0.01 or abortado)
    veredicto = "INCONCLUSO" if N < 3 else ("PASA" if pasa else "FALLA")

    informe.append("## Evaluacion (criterios pre-registrados)")
    informe.append(f"- ciclos evaluados: {n} (N requerido: 3)")
    informe.append(f"- coherencia >= 1.00: {pct_coh:.0%} (requerido >= 80%)")
    informe.append(f"- uptime >= 6/8:      {pct_up:.0%} (requerido >= 80%)")
    informe.append(f"- anclas QFChain:     {pct_ancla:.0%} (requerido >= 90%)")
    informe.append(f"- delta masa vs base: {masa_delta:+.2%} (permitido > -1%)")
    informe.append(f"- aborto: {'SI' if abortado else 'no'}")
    informe.append("")
    informe.append(f"**VEREDICTO: {veredicto}**")
    informe.append("")
    informe.append(f"- fin: {datetime.now().isoformat()}")
    with open(REPORTE, "w", encoding="utf-8") as f:
        f.write("\n".join(informe) + "\n")
    conn.close()

    print("=" * 60)
    print(" EXPERIMENTO DE EVOLUCION - PILOTO")
    print(f" ciclos: {n} | coherencia>=1: {pct_coh:.0%} | uptime>=6/8: {pct_up:.0%} | anclas: {pct_ancla:.0%} | delta masa: {masa_delta:+.2%}")
    print(f" VEREDICTO: {veredicto}")
    print(f" reporte: {REPORTE}")
    print(f" base de datos: {DB}")
    print("=" * 60)


if __name__ == "__main__":
    main()
