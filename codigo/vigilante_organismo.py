#!/usr/bin/env python3
"""
VIGILANTE_ORGANISMO.py — Latidos automaticos del organismo distribuido
======================================================================
Proceso en segundo plano que:
  * Sondea cada N segundos (default 300 = 5 min):
      - Puertos TCP: sidecar :8004, agente_mamba :8005, bridge :8006,
        qfchain RPC :8545, qfchain P2P :30303, enlace :8787
      - HTTP: enlace_codex /estado
      - qswift: frescura del log programador_qswift.log (ciclos horarios)
  * Actualiza organismo_estado.json (estado, ultima_sonda, historial acotado)
  * Deja EVENTOS auditables en coordinacion/eventos/ cuando un nodo cambia
    de estado (activo<->caido).
  * NO modifica parametros del nucleo: solo observa, registra y reporta.

Uso:
  python vigilante_organismo.py --intervalo 300
"""

import argparse
import datetime
import json
import os
import socket
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(AQUI, "organismo_estado.json")
COORD = os.path.join(AQUI, "coordinacion")
EVENTOS = os.path.join(COORD, "eventos")
LOG = os.path.join(COORD, "vigilante_organismo.log")
LOG_QSWIFT = os.path.join(AQUI, "programador_qswift.log")
MAX_HIST = 60
QSWIFT_MAX_EDAD_SEG = 3 * 3600  # 3h (ciclos horarios)


def ahora():
    return datetime.datetime.now().astimezone().isoformat()


def escribir_log(linea):
    try:
        os.makedirs(COORD, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()} {linea}\n")
    except Exception:
        pass


def cargar():
    if os.path.exists(ESTADO):
        with open(ESTADO, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return None


def guardar(estado):
    estado["actualizado"] = ahora()
    with open(ESTADO, "w", encoding="utf-8", newline="\n") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def puerto_abierto(puerto, timeout=1.5):
    if not puerto:
        return None
    try:
        with socket.create_connection(("127.0.0.1", puerto), timeout=timeout):
            return True
    except OSError:
        return False


def http_ok(url, timeout=3):
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return 200 <= r.status < 400
    except Exception:
        return False


def frescura_log_qswift():
    """True si el log de Q-SWIFT se escribio hace menos de QSWIFT_MAX_EDAD_SEG."""
    try:
        edad = time.time() - os.path.getmtime(LOG_QSWIFT)
        return edad < QSWIFT_MAX_EDAD_SEG, round(edad / 3600, 1)
    except OSError:
        return False, None


def sondear(estado):
    """Sondea los nodos y devuelve dict {nodo_id: (estado_nuevo, detalle)}."""
    res = {}
    for nodo in estado["nodos"]:
        nid = nodo["id"]
        detalle = None
        if nid == "sidecar_v2":
            ok = puerto_abierto(8004)
            res[nid] = ("activo" if ok else "caido", f"puerto 8004 {'abierto' if ok else 'cerrado'}")
        elif nid == "agente_mamba_v2":
            # Sistema Mamba Unificado v9.3: servidor propio en :8001 (26-08).
            # Si cae, se valida por su canal historico (sidecar :8004).
            ok = puerto_abierto(8001)
            if not ok:
                ok = puerto_abierto(8004)
            res[nid] = ("activo" if ok else "caido",
                        "puerto 8001 " + ("abierto" if ok else "cerrado"))
        elif nid == "nucleo_local":
            ok = puerto_abierto(8002)
            res[nid] = ("activo" if ok else "caido", f"puerto 8002 {'abierto' if ok else 'cerrado'}")
        elif nid == "bridge_tccu":
            ok = puerto_abierto(8006)
            res[nid] = ("activo" if ok else "caido", f"puerto 8006 {'abierto' if ok else 'cerrado'}")
        elif nid == "dashboard_monitoreo":
            ok = puerto_abierto(8050)
            res[nid] = ("activo" if ok else "caido", f"puerto 8050 {'abierto' if ok else 'cerrado'}")
        elif nid == "qfchain6d":
            ok_rpc = puerto_abierto(8545)
            ok_p2p = puerto_abierto(30303)
            res[nid] = ("activo" if (ok_rpc and ok_p2p) else "caido",
                        f"RPC :8545 {'ok' if ok_rpc else 'x'} / P2P :30303 {'ok' if ok_p2p else 'x'}")
        elif nid == "enlace_codex":
            ok = http_ok("http://127.0.0.1:8787/estado", timeout=2)
            res[nid] = ("activo" if ok else "caido", "GET /estado")
        elif nid == "qswift":
            ok, horas = frescura_log_qswift()
            res[nid] = ("activo" if ok else "inactivo",
                        f"log actualizado hace {horas}h (limite 3h)")
        elif nid == "codex":
            # Se evalua por latido reciente (< 30 min) o mensajes nuevos
            ultimo = nodo.get("ultimo_latido")
            reciente = False
            if ultimo:
                try:
                    ts = datetime.datetime.fromisoformat(ultimo)
                    reciente = (datetime.datetime.now(ts.tzinfo) - ts).total_seconds() < 1800
                except Exception:
                    reciente = False
            res[nid] = ("activo" if reciente else "inactivo",
                        "latido <30min (suspendido por pago segun Creador)")
        elif nid == "sandbox_vivo":
            # El sandbox (dominio externo) reporta su estado via
            # coordinacion/sandbox_estado.json (sondear_sandbox.py)
            ruta = os.path.join(COORD, "sandbox_estado.json")
            ok = False
            if os.path.exists(ruta):
                ok = (time.time() - os.path.getmtime(ruta)) < 1800
            res[nid] = ("activo" if ok else "inactivo",
                        "reporte sandbox_estado.json < 30 min")
        # autoclaw y herramientas (ciclo_cero, gate_evidencia): no se sondean
    return res


def ciclo(estado, simular=True):
    """Un ciclo de sondeo: actualiza estado + historial y emite eventos.
    Si simular=True, ademas ejecuta el Simulador TCCU Vivo (auto-simulacion)."""
    ts = ahora()
    cambios = sondear(estado)
    for nid, (nuevo, detalle) in cambios.items():
        for nodo in estado["nodos"]:
            if nodo["id"] != nid:
                continue
            anterior = nodo.get("estado", "desconocido")
            nodo["estado"] = nuevo
            nodo["ultima_sonda"] = ts
            nodo["detalle_sonda"] = detalle
            hist = nodo.setdefault("historial", [])
            hist.append({"ts": ts, "estado": nuevo})
            if len(hist) > MAX_HIST:
                del hist[: len(hist) - MAX_HIST]
            if nuevo != anterior and anterior != "desconocido":
                evento = {"ts": ts, "nodo": nid, "anterior": anterior,
                          "nuevo": nuevo, "detalle": detalle}
                os.makedirs(EVENTOS, exist_ok=True)
                nombre = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + f"_{nid}.json"
                with open(os.path.join(EVENTOS, nombre), "w", encoding="utf-8") as f:
                    json.dump(evento, f, ensure_ascii=False, indent=2)
                escribir_log(f"EVENTO {nid}: {anterior} -> {nuevo} ({detalle})")
    # latido del nucleo (autoclaw) por el vigilante
    for nodo in estado["nodos"]:
        if nodo["id"] == "autoclaw":
            nodo["ultimo_latido"] = ts
            nodo["nota"] = "latido automatico del vigilante"
    guardar(estado)
    activos = sum(1 for n in estado["nodos"] if n["estado"] == "activo")
    escribir_log(f"CICLO OK: {activos}/{len(estado['nodos'])} activos")

    if simular:
        try:
            import simulador_tccu_vivo as sim
            rep = sim.generar_reporte()
            sim.generar_dashboard(rep)
            sim.guardar_historico(rep)
            c = rep["coherencia_organismo"]
            escribir_log(f"SIMULADOR OK: coh={c['coherencia_organismo']} {c['estado']} "
                         f"veredicto={rep['metricas_falsables']['veredicto']}")
        except Exception as e:
            escribir_log(f"SIMULADOR ERROR: {e}")
    # El sandbox (dominio externo) reporta su estado en cada ciclo
    try:
        import sondear_sandbox
        sondear_sandbox.main()
        # C) si la identidad del sandbox cambio, regenerar el digesto de memoria
        with open(os.path.join(COORD, "sandbox_estado.json"),
                  encoding="utf-8") as f:
            rep_sand = json.load(f)
        if rep_sand.get("memoria_cambio"):
            import articular_memoria
            articular_memoria.main()
            escribir_log("SANDBOX MEMORIA: digesto regenerado")
        escribir_log("SANDBOX OK: reporte actualizado")
    except Exception as e:
        escribir_log(f"SANDBOX ERROR: {e}")
    return activos


_CICLOS_SONDEOS = 0


def ciclo_consciente(estado):
    """AUTO-EVOLUCION: cada 12 sondeos ejecuta el ciclo consciente del nucleo v2.0
    (OBSERVAR->REFLEXIONAR->PROPONER->APLICAR->SELLAR, ancla en QFChain)."""
    global _CICLOS_SONDEOS
    _CICLOS_SONDEOS += 1
    if _CICLOS_SONDEOS % 12 != 0:
        return None
    try:
        import organismo_vivo_distribuido as vivo
        num = len(estado.get("evolucion", [])) + 1
        bloque = vivo.ciclo(num)
        escribir_log(f"AUTO-EVOLUCION ciclo {num} OK (bloque {bloque['index']})")
        return bloque
    except Exception as e:
        escribir_log(f"AUTO-EVOLUCION ERROR: {e}")
        return None


def main():
    ap = argparse.ArgumentParser(description="Vigilante de latidos del organismo")
    ap.add_argument("--intervalo", type=int, default=300, help="segundos entre ciclos")
    ap.add_argument("--una-vez", action="store_true", help="un solo ciclo y salir")
    ap.add_argument("--no-simular", action="store_true",
                    help="no ejecutar el Simulador TCCU Vivo en cada ciclo")
    args = ap.parse_args()

    estado = cargar()
    if estado is None:
        print("[ERROR] organismo_estado.json no existe (corre primero: python organismo.py --estado)")
        return 1

    simular = not args.no_simular
    escribir_log(f"VIGILANTE INICIADO (intervalo={args.intervalo}s, simulador={simular})")
    print(f"Vigilante del organismo iniciado (intervalo={args.intervalo}s, "
          f"simulador={'SI' if simular else 'NO'}). Ctrl+C para detener.")
    while True:
        try:
            estado = cargar() or estado
            ciclo(estado, simular=simular)
            if not args.una_vez:
                ciclo_consciente(estado)
        except Exception as e:
            escribir_log(f"ERROR en ciclo: {e}")
            print(f"[aviso] error de ciclo: {e}")
        if args.una_vez:
            return 0
        time.sleep(args.intervalo)


if __name__ == "__main__":
    sys.exit(main())
