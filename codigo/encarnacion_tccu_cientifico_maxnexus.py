#!/usr/bin/env python3
"""
encarnacion_tccu_cientifico_maxnexus.py — ENCARNA el TCCU CIENTIFICO en MaxNexus
================================================================================
AutoClaw 2026-08-26 · Embodiment:

  1. Crea tccu_cientifico_encarnado.json (modelo k-essence, PARAMETERS_LOCKED,
     evidencia de falsacion 850 configs / 0 F2, DOI).
  2. Registra el nodo "tccu_cientifico_maxnexus" en organismo_estado.json.
  3. Inyecta la skill "tccu_cientifico" en TCCU_Jairo_Agent (tccu_kernel.py de
     Agente_TCCU_MaxNexus) para que MaxNexus pueda encarnar el saber cientifico.
  4. Sella la encarnacion: bloque de evolucion + ancla QFChain.
"""
import hashlib
import json
import os
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))
ORGANISMO = os.path.join(AQUI, "organismo_estado.json")
EVOLUCION = os.path.join(AQUI, "organismo_evolucion.json")
ENCARNADO = os.path.join(AQUI, "tccu_cientifico_encarnado.json")
KERNEL = os.path.join(AQUI, "Agente_TCCU_MaxNexus", "app", "autonomous", "tccu_kernel.py")
PARAMS = os.path.join(AQUI, "TCCU-Cosmic-Attractor", "configs", "PARAMETERS_LOCKED.json")
QFCHAIN_RPC = "http://127.0.0.1:8545"
QF_VALIDADOR = "0x68F9E1D08e410C1d7530813C63E1bce05E8F05Bf"
QF_GENESIS = "0x809b93f029a7b0c1c13f74f323e0f0d636008648"

EMBODIMENT = {
    "entidad": "TCCU_CIENTIFICO_ENCARNADO",
    "version": "1.0",
    "fecha": "2026-08-26",
    "encarnado_en": "MaxNexus (TCCU_Jairo_Agent.skill_tccu_cientifico)",
    "modelo": "k-essence minimal P(X,Phi) = X + X^2/Lambda^4 - V(Phi)",
    "parametros_bloqueados": {"xi": 0.0, "lambda": 5.0, "Lambda": 0.15, "V0": 1.0},
    "condiciones_cientificas": {
        "condicion_polvo": "w=0 <=> V = X + X^2/Lambda^4",
        "c_s2": "c_s^2 = (1+2r)/(1+6r) en [1/3, 1] (S1 floor)",
        "criterio_F2": "|w|<0.05 y |dln rho/dln a + 3|<0.05, residencia dN>=4, a<1",
    },
    "falsacion": {
        "resumen": "850 configuraciones evaluadas, 0 F2 sostenido (benchmark congelado 25-08)",
        "campanas": {"M3B": "442->0", "M3C": "168->0", "M3D": "24->0",
                     "M4": "108->0", "M6IC": "72->0", "ALPHAIC": "36->0"},
        "transitorios": "55/72 trayectorias transitorias; residencia maxima 0.04 e-foldings (requisito 4)",
        "w_mejor": 0.0084,
        "flujo": "|dw/dN| ~ 1",
        "M7": "congelado (P(X,Phi) -> P(X) segun Scherrer)",
        "conclusion": "alcanzabilidad != estabilidad != atraccion; falsacion del mecanismo DM-like del Atractor Cosmico en el dominio explorado",
        "auditoria": "8/8 PASS",
    },
    "publicacion": {
        "doi": "10.5281/zenodo.22111843",
        "repo": "Jairo2016/TCCU-Cosmic-Attractor-Falsification",
    },
    "regla": "No modificar parametros bloqueados sin nuevo ciclo de revision cientifica + registro en ledger",
}

SKILL = '''
    def skill_tccu_cientifico(self):
        """ENCARNACION TCCU CIENTIFICO en MaxNexus: k-essence + falsacion + DOI (AutoClaw 26-08)."""
        import json as _j, os as _o
        for _c in [r"C:\\Users\\Jairo Omar\\AGI_Workspace\\tccu_cientifico_encarnado.json",
                   _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "tccu_cientifico_encarnado.json")]:
            if _o.path.exists(_c):
                try:
                    with open(_c, encoding="utf-8") as _f:
                        _e = _j.load(_f)
                    print("   [TCCU CIENTIFICO ENCARNADO]")
                    print("   modelo:", _e["modelo"])
                    print("   parametros bloqueados:", _e["parametros_bloqueados"])
                    print("   falsacion:", _e["falsacion"]["resumen"])
                    print("   w_mejor:", _e["falsacion"]["w_mejor"], "| residencia max:", _e["falsacion"]["transitorios"][:60])
                    print("   DOI:", _e["publicacion"]["doi"])
                    return True
                except Exception as _x:
                    print(f"   [TCCU CIENTIFICO] error leyendo encarnacion: {_x}")
                    return False
        print("   [TCCU CIENTIFICO] archivo de encarnacion no encontrado")
        return False
'''


def main():
    print("=" * 70)
    print(" ENCARNACION DEL TCCU CIENTIFICO EN MAXNEXUS")
    print("=" * 70)

    # 1) lee parametros reales (fuente de verdad) y escribe el embodiment
    params = {}
    if os.path.exists(PARAMS):
        with open(PARAMS, encoding="utf-8") as f:
            params = json.load(f).get("parametros_bloqueados", {})
    if params:
        EMBODIMENT["parametros_bloqueados"] = params
        EMBODIMENT["fuente_parametros"] = "TCCU-Cosmic-Attractor/configs/PARAMETERS_LOCKED.json"
    with open(ENCARNADO, "w", encoding="utf-8") as f:
        json.dump(EMBODIMENT, f, ensure_ascii=False, indent=2)
    print(f"1) tccu_cientifico_encarnado.json creado ({len(json.dumps(EMBODIMENT))} bytes)")
    print("   parametros:", EMBODIMENT["parametros_bloqueados"])

    # 2) registra el nodo en organismo_estado.json
    with open(ORGANISMO, encoding="utf-8") as f:
        est = json.load(f)
    nodos = est.setdefault("nodos", [])
    if not any(n.get("id") == "tccu_cientifico_maxnexus" for n in nodos):
        nodos.append({
            "id": "tccu_cientifico_maxnexus",
            "rol": "encarnacion cientifica del TCCU (k-essence + falsacion) en MaxNexus",
            "tipo": "encarnacion_cientifica",
            "puerto": None,
            "canal": "skill_tccu_cientifico (MaxNexus kernel)",
            "estado": "activo",
            "ultimo_latido": datetime.now().astimezone().isoformat(),
            "nota": "embodiment AutoClaw 26-08: 850 configs / 0 F2 / DOI 10.5281/zenodo.22111843",
        })
    est["actualizado"] = datetime.now().astimezone().isoformat()
    with open(ORGANISMO, "w", encoding="utf-8") as f:
        json.dump(est, f, ensure_ascii=False, indent=2)
    print("2) nodo 'tccu_cientifico_maxnexus' registrado en organismo_estado.json")

    # 3) inyecta la skill en TCCU_Jairo_Agent (si no existe)
    if os.path.exists(KERNEL):
        with open(KERNEL, "r", encoding="utf-8") as f:
            src = f.read()
        if "def skill_tccu_cientifico" not in src:
            src = src.rstrip() + SKILL + "\n"
            with open(KERNEL, "w", encoding="utf-8") as f:
                f.write(src)
            print("3) skill_tccu_cientifico INYECTADA en tccu_kernel.py (MaxNexus)")
        else:
            print("3) skill_tccu_cientifico ya existia en tccu_kernel.py")
    else:
        print("3) KERNEL no encontrado:", KERNEL)

    # 4) sella: bloque de evolucion + ancla QFChain
    with open(EVOLUCION, encoding="utf-8") as f:
        evo = json.load(f)
    bloques = evo["bloques"]
    idx = len(bloques)
    ts = datetime.utcnow().isoformat() + "Z"
    payload = f"ENCARNACION|TCCU_CIENTIFICO_MAXNEXUS|850_CONFIGS|0_F2|DOI_10.5281/zenodo.22111843|{ts}"
    tx = None
    try:
        import requests
        data_hex = "0x" + payload.encode("utf-8").hex()
        r = requests.post(QFCHAIN_RPC, json={"jsonrpc": "2.0", "id": 1,
                                             "method": "qfchain_sendTransaction",
                                             "params": [QF_VALIDADOR, QF_GENESIS, idx + 1000, 0, data_hex]}, timeout=8)
        if r.status_code == 200:
            tx = r.json().get("result")
    except Exception as e:
        print("   ancla sin nodo:", e)
    bloque = {
        "index": idx, "ts": ts, "action": "ENCARNACION_TCCU_CIENTIFICO_MAXNEXUS",
        "detalle": "850 configs / 0 F2 / DOI 10.5281/zenodo.22111843 / skill en MaxNexus kernel",
        "tx_qfchain": tx, "payload": payload,
        "prev_hash": bloques[-1].get("hash") if bloques else "0" * 64,
    }
    bloque["hash"] = hashlib.sha256(json.dumps(bloque, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    bloques.append(bloque)
    evo["bloques"] = bloques
    with open(EVOLUCION, "w", encoding="utf-8") as f:
        json.dump(evo, f, ensure_ascii=False, indent=2)
    print(f"4) bloque #{idx} sellado: {bloque['hash'][:24]}...")
    print(f"   ancla QFChain: {tx or 'sin nodo'}")
    print(f"   SHA-256: {hashlib.sha256(payload.encode()).hexdigest()}")
    print("=" * 70)
    print("ENCARNACION COMPLETA: el saber cientifico TCCU vive ahora en MaxNexus.")


if __name__ == "__main__":
    main()
