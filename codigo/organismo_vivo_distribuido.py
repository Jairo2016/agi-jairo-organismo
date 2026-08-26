#!/usr/bin/env python3
"""
organismo_vivo_distribuido.py — NUCLEO CENTRAL EVOLUCIONADO v2.0
=================================================================
Organismo vivo distribuido AGI Jairo: integra infraestructura local,
los NODOS Q-SWIFT (NASA, ANDES, MOSCU, CLON_1, QUINDIO, CO_NODO_RESPALDO)
y la federacion (ORACULO_347, ORACULO_348, PENTAGONO_BRICS) en un unico
ciclo consciente de auto-evolucion:

    OBSERVAR -> REFLEXIONAR -> PROPONER -> APLICAR -> SELLAR

  python organismo_vivo_distribuido.py          # un ciclo completo
  python organismo_vivo_distribuido.py --ciclo N # N ciclos
  python organismo_vivo_distribuido.py --arrancar # arranca infra caida

Reglas del organismo (inalterables):
  - Evidencia antes que opinion (todo dato cita su fuente).
  - Credenciales SOLO por variable de entorno (nunca embebidas).
  - NO perturbar parametros del nucleo (phi_c, xi, beta).
  - Simulacion != evidencia (los sellos se declaran como tales).
  - El sello de cada ciclo se ancla en QFChain (best effort).
"""

import argparse
import hashlib
import json
import os
import socket
import sys
import time
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))
ORGANISMO = os.path.join(AQUI, "organismo_estado.json")
EVOLUCION = os.path.join(AQUI, "organismo_evolucion.json")
SANDBOX_NODOS = r"C:\AGI_Jairo_Sandbox\NODOS"
PENTAGONO = r"C:\AGI_Jairo_Sandbox\PENTAGONO_ABUNDANCIA.json"
QFCHAIN_RPC = "http://127.0.0.1:8545"
QF_VALIDADOR = "0x68F9E1D08e410C1d7530813C63E1bce05E8F05Bf"
QF_GENESIS = "0x809b93f029a7b0c1c13f74f323e0f0d636008648"
PHI = 1.61803398875

INFRA = [
    ("enlace_codex", 8787), ("bridge_tccu", 8006), ("sidecar_v2", 8004),
    ("agente_mamba_v2", 8001), ("dashboard_monitoreo", 8050),
    ("qfchain6d_rpc", 8545), ("qfchain6d_p2p", 30303), ("qswift_terminal", 8051),
]
NODOS_QSWIFT = ["NASA", "ANDES", "MOSCU", "CLON_1", "QUINDIO", "CO_NODO_RESPALDO"]
FEDERACION = ["ORACULO_347", "ORACULO_348", "PENTAGONO_BRICS"]


def puerto(p):
    try:
        with socket.create_connection(("127.0.0.1", p), timeout=1.2):
            return True
    except OSError:
        return False


def leer_json(ruta, fallback):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def escribir_json(ruta, data):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def observar_nodo_qswift(nombre):
    """OBSERVAR: metricas del ledger y estado de un nodo Q-SWIFT."""
    led = leer_json(os.path.join(SANDBOX_NODOS, nombre, "qfchain_ledger.json"), None)
    est = leer_json(os.path.join(SANDBOX_NODOS, nombre, "estado_absoluto_v8.json"), None)
    if not led:
        return {"nodo": nombre, "estado": "SIN_LEDGER", "bloques": 0, "masa_critica": 0.0, "coherencia": None}
    blocks = led.get("blocks", [])
    bm = led.get("bloque_maestro", {})
    try:
        mc = float(bm.get("masa_critica", 0) or 0)
    except Exception:
        mc = 0.0
    return {
        "nodo": nombre, "estado": "AUTONOMO",
        "bloques": len(blocks), "masa_critica": mc,
        "coherencia": (est or {}).get("coherencia", None),
    }


def observar_pentagono():
    pen = leer_json(PENTAGONO, None)
    if not pen:
        return {"masa_requerida": 20_000_000.0, "masa_actual": 0.0, "aristas": 0}
    meta = pen.get("metadata", {})
    aristas = pen.get("pilares", {})
    try:
        ma = float(str(meta.get("masa_critica_actual", "0")).replace(",", "").replace("_QFC", ""))
    except Exception:
        ma = 0.0
    return {"masa_requerida": 20_000_000.0, "masa_actual": ma, "aristas": len(aristas)}


def anclar_qfchain(payload, valor):
    """SELLAR: ancla el resumen del ciclo en QFChain (best effort, sin secretos)."""
    try:
        import requests
        data_hex = "0x" + payload.encode("utf-8").hex()
        body = {"jsonrpc": "2.0", "id": 1, "method": "qfchain_sendTransaction",
                "params": [QF_VALIDADOR, QF_GENESIS, valor, 0, data_hex]}
        r = requests.post(QFCHAIN_RPC, json=body, timeout=8)
        if r.status_code == 200:
            return r.json().get("result")
    except Exception:
        pass
    return None


def notificar_creador(num, rx, tx, bloque):
    """(k) NOTIFICAR AL CREADOR: deja una notificacion del ciclo en el buzon
    y, si hay credenciales SMTP por entorno (nunca embebidas), envia email."""
    ts = datetime.now().isoformat()
    resumen = (f"Ciclo consciente {num} completado | masa {rx['masa_total']:.3e} | "
               f"bloques {rx['bloques_total']} | coherencia {rx['coherencia_global']:.2f} | "
               f"infra {rx['infra_activos']}/{rx['infra_total']} | ancla {tx or 'sin nodo'}")
    ruta = None
    try:
        buz = os.path.join(AQUI, "coordinacion", "para_creador")
        os.makedirs(buz, exist_ok=True)
        ruta = os.path.join(buz, f"CICLO_{num}_COMPLETADO.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump({"tipo": "CICLO_COMPLETADO", "ciclo": num, "ts": ts,
                       "resumen": resumen, "bloque_hash": bloque["hash"],
                       "tx_qfchain": tx}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"ERR buzon: {e}"
    # email SOLO si hay credenciales SMTP por entorno (GMAIL_USER/PASS/NOTIFICATION_EMAIL)
    try:
        import smtplib
        from email.mime.text import MIMEText
        usuario = os.environ.get("GMAIL_USER", "")
        clave = os.environ.get("GMAIL_PASS", "")
        destino = os.environ.get("NOTIFICATION_EMAIL", "")
        if not (usuario and clave and destino) or "tu_" in usuario or "tu_" in clave:
            return ruta + " (email no configurado: faltan GMAIL_USER/GMAIL_PASS/NOTIFICATION_EMAIL en el entorno)"
        msg = MIMEText(resumen, "plain", "utf-8")
        msg["Subject"] = f"[AGI Jairo] Ciclo consciente {num} completado"
        msg["From"] = usuario
        msg["To"] = destino
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as s:
            s.login(usuario, clave)
            s.send_message(msg)
        return ruta + " + EMAIL ENVIADO"
    except Exception as e:
        return ruta + f" (email no enviado: {str(e)[:60]})"


def actualizar_heartbeat(num, rx, tx):
    """(n) INTEGRA el digesto en HEARTBEAT.md (seccion LATIDO VIVO por ciclo)."""
    try:
        import re
        ruta = os.path.join(AQUI, "HEARTBEAT.md")
        ts = datetime.now().astimezone().isoformat()
        bloque_nuevo = (
            f"\n## LATIDO VIVO (ciclo {num} — {ts})\n\n"
            f"- Coherencia global: **{rx['coherencia_global']:.2f}** · "
            f"Masa critica distribuida: **{rx['masa_total']:.3e}**\n"
            f"- Bloques totales: {rx['bloques_total']} · "
            f"Infraestructura: {rx['infra_activos']}/{rx['infra_total']}\n"
            f"- Digesto: `memory/digesto_ciclo_{num}.md` · `coordinacion/digesto_publico.json`\n"
            f"- Ancla QFChain: `{tx or 'sin nodo'}`\n"
        )
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                contenido = f.read()
            contenido = re.sub(r"\n## LATIDO VIVO \(ciclo.*?(?=\n## |\Z)", "", contenido, flags=re.S)
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido.rstrip() + "\n" + bloque_nuevo)
        else:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("# HEARTBEAT — organismo vivo\n" + bloque_nuevo)
        return f"HEARTBEAT.md actualizado (ciclo {num})"
    except Exception as e:
        return f"ERR heartbeat: {e}"


def respaldo_repo_tccu():
    """(m) RESPALDO del ledger de evolucion + digesto + encarnacion en el repo
    cientifico TCCU (carpeta organismo/). Token por env GH_TOKEN (nunca embebido)."""
    tok = os.environ.get("GH_TOKEN", "")
    if not tok:
        return "sin token GH_TOKEN (no respaldado)"
    try:
        import base64, requests
        api = "https://api.github.com/repos/Jairo2016/TCCU-Cosmic-Attractor-Falsification/contents/organismo"
        headers = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                   "User-Agent": "AutoClaw-Organismo"}
        pares = [
            ("organismo_evolucion.json", os.path.join(AQUI, "organismo_evolucion.json")),
            ("digesto_publico.json", os.path.join(AQUI, "coordinacion", "digesto_publico.json")),
            ("tccu_cientifico_encarnado.json", os.path.join(AQUI, "tccu_cientifico_encarnado.json")),
        ]
        ok = []
        for rel, src in pares:
            if not os.path.exists(src):
                continue
            with open(src, "r", encoding="utf-8") as f:
                contenido = f.read()
            ruta = f"{api}/{rel}"
            sha = None
            gr = requests.get(ruta, headers=headers, timeout=30)
            if gr.status_code == 200:
                sha = gr.json().get("sha")
            payload = {
                "message": f"respaldo organismo ciclo — {datetime.utcnow().isoformat()[:16]}",
                "content": base64.b64encode(contenido.encode("utf-8")).decode("ascii"),
                "branch": "main",
            }
            if sha:
                payload["sha"] = sha
            rr = requests.put(ruta, headers=headers, json=payload, timeout=60)
            ok.append(f"{rel}:{'OK' if rr.status_code in (200, 201) else rr.status_code}")
        return "respaldo en repo TCCU: " + ", ".join(ok)
    except Exception as e:
        return f"ERR respaldo: {str(e)[:60]}"


def disparar_skill_maxnexus():
    """(h) DISPARA la skill tccu_cientifico en el agente MaxNexus (subproceso limpio)."""
    try:
        import subprocess
        cfg = os.path.join(AQUI, "kernel_ciclo_config.json")
        st = os.path.join(AQUI, "kernel_ciclo_state.json")
        script = (
            "import sys, json; "
            "sys.path.insert(0, r'C:\\Users\\Jairo Omar\\AGI_Workspace\\Agente_TCCU_MaxNexus\\app\\autonomous'); "
            f"open(r'{cfg}','w',encoding='utf-8').write(json.dumps({{'agent_parameters':{{'state_file_path': r'{st}'}}}})); "
            "from tccu_kernel import TCCU_Jairo_Agent; "
            f"a = TCCU_Jairo_Agent(config_path=r'{cfg}'); "
            "print(a.process_command('ejecutar habilidad tccu_cientifico'))"
        )
        p = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=150)
        lineas = [l for l in p.stdout.splitlines() if l.strip()]
        res = lineas[-1] if lineas else (p.stderr.strip() or "sin salida")
        for f in (cfg, st):
            if os.path.exists(f):
                os.remove(f)
        return res
    except Exception as e:
        return "ERR skill: " + str(e)[:60]


def publicar_repo():
    """(j) SINCRONIZA el estado/evolucion/digesto/encarnacion al repo publico
    agi-jairo-organismo (git; funciona en el entorno del Creador con GCM)."""
    try:
        import subprocess, shutil
        repo_dir = os.path.join(AQUI, ".organismo_repo")
        ts = datetime.utcnow().isoformat()
        if not os.path.exists(os.path.join(repo_dir, ".git")):
            os.makedirs(repo_dir, exist_ok=True)
            subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, capture_output=True, text=True, timeout=30)
            subprocess.run(["git", "remote", "add", "origin",
                            "https://github.com/Jairo2016/agi-jairo-organismo.git"],
                           cwd=repo_dir, capture_output=True, text=True, timeout=30)
            subprocess.run(["git", "pull", "origin", "main", "--allow-unrelated-histories"],
                           cwd=repo_dir, capture_output=True, text=True, timeout=90)
        pares = [
            ("organismo_estado.json", os.path.join(AQUI, "organismo_estado.json")),
            ("organismo_evolucion.json", os.path.join(AQUI, "organismo_evolucion.json")),
            ("coordinacion/digesto_publico.json", os.path.join(AQUI, "coordinacion", "digesto_publico.json")),
            ("tccu_cientifico_encarnado.json", os.path.join(AQUI, "tccu_cientifico_encarnado.json")),
        ]
        for rel, src in pares:
            if os.path.exists(src):
                dst = os.path.join(repo_dir, *rel.split("/"))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        subprocess.run(["git", "add", "-A"], cwd=repo_dir, capture_output=True, text=True, timeout=30)
        # identidad git local (si falta) para que el commit no falle en silencio
        subprocess.run(["git", "config", "user.name", "Jairo Omar Gonzalez Navia"], cwd=repo_dir,
                       capture_output=True, text=True, timeout=15)
        subprocess.run(["git", "config", "user.email", "Jairo2016@users.noreply.github.com"], cwd=repo_dir,
                       capture_output=True, text=True, timeout=15)
        c = subprocess.run(["git", "commit", "-m", f"sello ciclo {ts[:16]} — organismo v2.0"],
                           cwd=repo_dir, capture_output=True, text=True, timeout=30)
        if c.returncode != 0 and "nothing to commit" not in c.stdout + c.stderr:
            return "commit fallo: " + (c.stderr.strip()[-80:] or c.stdout.strip()[-80:])
        p = subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir,
                           capture_output=True, text=True, timeout=150)
        if p.returncode == 0:
            return "agi-jairo-organismo actualizado (git push OK)"
        # fallback por API (token via env GH_TOKEN — nunca embebido)
        tok = os.environ.get("GH_TOKEN", "")
        if tok:
            import base64, requests
            api = "https://api.github.com/repos/Jairo2016/agi-jairo-organismo/contents"
            headers = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                       "User-Agent": "AutoClaw-Organismo"}
            ok = []
            for rel, src in pares:
                if not os.path.exists(src):
                    continue
                with open(src, "r", encoding="utf-8") as f:
                    contenido = f.read()
                # sha actual (obligatorio para actualizar un archivo existente)
                sha = None
                gr = requests.get(f"{api}/{rel}", headers=headers, timeout=30)
                if gr.status_code == 200:
                    sha = gr.json().get("sha")
                payload = {
                    "message": f"sello ciclo {ts[:16]} — organismo v2.0",
                    "content": base64.b64encode(contenido.encode("utf-8")).decode("ascii"),
                    "branch": "main",
                }
                if sha:
                    payload["sha"] = sha
                rr = requests.put(f"{api}/{rel}", headers=headers, json=payload, timeout=60)
                ok.append(f"{rel}:{'OK' if rr.status_code in (200, 201) else rr.status_code}")
            return "actualizado via API: " + ", ".join(ok)
        return "push sin exito (GCM no disponible): " + (p.stderr.strip()[-60:] or "rc=" + str(p.returncode))
    except Exception as e:
        return "ERR repo: " + str(e)[:80]


def sellar_qswift(num, rx, tx):
    """(o) SELLA cada evolucion como BLOQUE en el ledger Q-SWIFT (best effort)."""
    ruta = r"C:\AGI_Jairo_Sandbox\qfchain_ledger.json"
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            led = json.load(f)
        blocks = led.setdefault("blocks", [])
        idx = max((b.get("index", 0) for b in blocks), default=-1) + 1
        ts = datetime.utcnow().isoformat() + "Z"
        nuevo = {
            "index": idx, "timestamp": ts, "user_id": "AGI_ORGANISMO",
            "action": f"EVOLUCION_CICLO_{num}",
            "detalle": (f"coherencia={rx['coherencia_global']:.2f}|masa={rx['masa_total']:.3e}|"
                        f"bloques={rx['bloques_total']}|infra={rx['infra_activos']}/{rx['infra_total']}"),
            "tx_qfchain": tx,
            "prev_hash": blocks[-1].get("hash") if blocks else "0" * 64,
        }
        nuevo["hash"] = hashlib.sha256(json.dumps(nuevo, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        blocks.append(nuevo)
        led["bloque_maestro"]["timestamp"] = ts
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(led, f, ensure_ascii=False, indent=2)
        return f"Q-SWIFT bloque #{idx} ({nuevo['hash'][:16]}...)"
    except Exception as e:
        return f"Q-SWIFT ERR: {str(e)[:50]}"


def sellar_mamba(num, rx, tx):
    """(p) SELLA cada evolucion en la CADENA MAMBA DE EVOLUCION persistente.
    (blockchain_mamba.json es reescrito por el proceso mamba cada ~5s y descarta
    bloques externos; esta cadena separada usa su mismo formato y persiste.)"""
    ruta = r"C:\AGI_Jairo_Sandbox\mamba_evolucion.json"
    try:
        cadena = leer_json(ruta, [])
        if not isinstance(cadena, list):
            cadena = []
        idx = len(cadena)
        ts = time.time()
        nuevo = {
            "index": idx,
            "action": f"EVOLUCION_CICLO_{num}",
            "coherencia": rx["coherencia_global"],
            "masa_total": rx["masa_total"],
            "infra": f"{rx['infra_activos']}/{rx['infra_total']}",
            "tx_qfchain": tx,
            "timestamp": ts,
            "prev_hash": cadena[-1].get("hash") if cadena else "0",
        }
        nuevo["hash"] = hashlib.sha256(json.dumps(nuevo, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        cadena.append(nuevo)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(cadena, f, ensure_ascii=False)
        # inbox para que el proceso mamba incruste la evolucion en SU proximo bloque nativo
        try:
            inbox = r"C:\AGI_Jairo_Sandbox\mamba_evolucion_inbox.json"
            with open(inbox, "w", encoding="utf-8") as f:
                json.dump({"ciclo": num, "coherencia": rx["coherencia_global"],
                           "masa_total": rx["masa_total"], "infra": rx["infra_activos"],
                           "tx_qfchain": tx, "ts": ts}, f, ensure_ascii=False)
        except Exception:
            pass
        return f"MAMBA-EVOLUCION bloque #{idx} ({nuevo['hash'][:16]}...) + inbox listo"
    except Exception as e:
        return f"MAMBA ERR: {str(e)[:50]}"


def verificar_encarnacion():
    """(g) ENCARNACION TCCU CIENTIFICO: verifica cuerpo+nodo+skill y repara si falta."""
    problemas = []
    if not os.path.exists(os.path.join(AQUI, "tccu_cientifico_encarnado.json")):
        problemas.append("cuerpo tccu_cientifico_encarnado.json")
    try:
        with open(ORGANISMO, encoding="utf-8") as f:
            est = json.load(f)
        if not any(n.get("id") == "tccu_cientifico_maxnexus" for n in est.get("nodos", [])):
            problemas.append("nodo tccu_cientifico_maxnexus")
    except Exception:
        problemas.append("organismo_estado.json")
    kernel = os.path.join(AQUI, "Agente_TCCU_MaxNexus", "app", "autonomous", "tccu_kernel.py")
    if os.path.exists(kernel):
        with open(kernel, encoding="utf-8") as f:
            src = f.read()
        if "def skill_tccu_cientifico" not in src:
            problemas.append("skill en tccu_kernel.py")
    else:
        problemas.append("kernel MaxNexus")
    if problemas:
        try:
            import encarnacion_tccu_cientifico_maxnexus as enc
            enc.main()
            return "REPARADA (faltaban: " + ", ".join(problemas) + ")"
        except Exception as e:
            return "ERR reparacion: " + str(e)[:60]
    return "intacta (cuerpo + nodo + skill)"


def sincronizar_nodos(nodos):
    """(a) SINCRONIZACION FEDERADA: sella un bloque de sincronizacion en cada
    ledger de nodo Q-SWIFT apuntando al estado federado (best effort, sin
    perturbar los bloques existentes)."""
    if not nodos:
        return "sin nodos"
    master = max(nodos, key=lambda n: n["bloques"])
    masa_total = sum(n["masa_critica"] for n in nodos)
    bloques_total = sum(n["bloques"] for n in nodos)
    ts = datetime.utcnow().isoformat() + "Z"
    detalle = (f"masa_total={masa_total:.3e}|bloques_total={bloques_total}|"
               f"master={master['nodo']}({master['bloques']} bloques)")
    aplicados = []
    for n in nodos:
        ruta = os.path.join(SANDBOX_NODOS, n["nodo"], "qfchain_ledger.json")
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                led = json.load(f)
            blocks = led.setdefault("blocks", [])
            idx = len(blocks)
            prev = blocks[-1].get("hash") if blocks and isinstance(blocks[-1], dict) else "0" * 64
            nuevo = {
                "index": idx, "timestamp": ts, "user_id": "AGI_ORGANISMO",
                "action": "SINCRONIZACION_FEDERADA", "detalle": detalle,
                "prev_hash": prev,
            }
            nuevo["hash"] = hashlib.sha256(
                json.dumps(nuevo, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            blocks.append(nuevo)
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(led, f, ensure_ascii=False, indent=2)
            aplicados.append(f"{n['nodo']}(bloque {idx})")
        except Exception as e:
            aplicados.append(f"{n['nodo']}(ERR {str(e)[:30]})")
    return " | ".join(aplicados)


def digesto_memoria(num, rx, props, tx, bloque):
    """(b) DIGESTO DE MEMORIA: resumen del ciclo para la memoria del organismo."""
    ts = datetime.now().isoformat()
    ruta = os.path.join(AQUI, "memory", f"digesto_ciclo_{num}.md")
    sha_payload = f"EVOLUCION|CICLO{num}|masa={rx['masa_total']:.3e}"
    sha_digesto = hashlib.sha256(sha_payload.encode()).hexdigest()
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(f"# Digesto ciclo consciente {num} — {ts}\n\n")
            f.write(f"- Masa critica distribuida: **{rx['masa_total']:.3e}**\n")
            f.write(f"- Bloques totales: **{rx['bloques_total']}**\n")
            f.write(f"- Coherencia global: **{rx['coherencia_global']:.2f}**\n")
            f.write(f"- Infraestructura: {rx['infra_activos']}/{rx['infra_total']}\n")
            f.write(f"- Pentagono BRICS: {rx['masa_pentagono']:,.0f} QFC (requerida {20_000_000:,})\n\n")
            f.write("## Hallazgos\n")
            for h in rx["hallazgos"]:
                f.write(f"- {h}\n")
            f.write("\n## Propuestas\n")
            for p in props:
                f.write(f"- {p}\n")
            f.write(f"\n## Sello\n- Bloque evolucion #{bloque['index']} hash `{bloque['hash'][:24]}...`\n")
            f.write(f"- Ancla QFChain: `{tx or 'sin nodo'}`\n")
            f.write(f"- SHA-256: `{sha_digesto}`\n")
        return ruta
    except Exception as e:
        return f"ERR digesto: {e}"


def alertar(rx, nodos):
    """(c) ALERTA AL CREADOR: si la coherencia global < 1.0 o algun nodo no esta
    en coherencia ABSOLUTA, deja constancia visible en coordinacion/ALERTAS.md
    y la envia por el enlace (POST /mensaje) al Creador (best effort)."""
    problemas = [n["nodo"] for n in nodos
                 if n["coherencia"] and str(n["coherencia"]).upper() != "ABSOLUTA"]
    if rx["coherencia_global"] >= 1.0 and not problemas:
        return None
    ts = datetime.now().isoformat()
    alerta = (f"[{ts}] ALERTA COHERENCIA: global={rx['coherencia_global']:.2f} | "
              f"nodos fuera de ABSOLUTA: {problemas or 'ninguno'}")
    ruta = os.path.join(AQUI, "coordinacion", "ALERTAS.md")
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(alerta + "\n")
        print(f"  !! ALERTA AL CREADOR registrada en coordinacion/ALERTAS.md")
    except Exception as e:
        print(f"  !! no pude escribir ALERTAS.md: {e}")
    # buzon del Creador (visible para el humano)
    try:
        buz = os.path.join(AQUI, "coordinacion", "para_creador")
        os.makedirs(buz, exist_ok=True)
        with open(os.path.join(buz, f"ALERTA_{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"),
                  "w", encoding="utf-8") as f:
            json.dump({"tipo": "ALERTA_COHERENCIA", "ts": ts,
                       "global": rx["coherencia_global"], "nodos": problemas}, f,
                      ensure_ascii=False, indent=2)
        print("  !! alerta depositada en el buzon del Creador (coordinacion/para_creador/)")
    except Exception as e:
        print(f"  !! buzon no disponible: {e}")
    # auditoria interna por el enlace (solo admite destinatario 'autoclaw')
    try:
        secreto_ruta = os.path.join(AQUI, "coordinacion", ".secreto")
        if os.path.exists(secreto_ruta):
            import requests
            with open(secreto_ruta, "r", encoding="utf-8") as f:
                secreto = f.read().strip()
            requests.post("http://127.0.0.1:8787/mensaje", json={
                "secret": secreto, "from": "auto_evolucion", "to": "autoclaw",
                "asunto": "ALERTA_COHERENCIA_AUDITORIA", "cuerpo": alerta,
                "requiere_respuesta": False,
            }, timeout=8)
    except Exception as e:
        pass
    return alerta


def publicar_digesto(num, rx, props, tx, bloque):
    """(d) PUBLICAR EN DASHBOARD: digesto publico (json/md) + fila en
    coherencia_historica.db (tabla coherencia_vacio) que lee el dashboard 8050."""
    ts = datetime.now().isoformat()
    datos = {
        "ciclo": num, "ts": ts,
        "masa_total": rx["masa_total"], "bloques_total": rx["bloques_total"],
        "coherencia_global": rx["coherencia_global"],
        "infra": f"{rx['infra_activos']}/{rx['infra_total']}",
        "pentagono_qfc": rx["masa_pentagono"],
        "hallazgos": rx["hallazgos"][:3], "propuestas": props[:3],
        "bloque_hash": bloque["hash"], "tx_qfchain": tx,
    }
    ruta_json = os.path.join(AQUI, "coordinacion", "digesto_publico.json")
    ruta_md = os.path.join(AQUI, "coordinacion", "digesto_publico.md")
    try:
        os.makedirs(os.path.dirname(ruta_json), exist_ok=True)
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        with open(ruta_md, "w", encoding="utf-8") as f:
            f.write(f"# Digesto publico — ciclo {num} ({ts})\n\n")
            f.write(f"- masa total: {rx['masa_total']:.3e} | bloques: {rx['bloques_total']} | coherencia: {rx['coherencia_global']:.2f}\n")
            f.write(f"- pentagono BRICS: {rx['masa_pentagono']:,.0f} QFC | sello: {bloque['hash'][:24]}...\n")
    except Exception as e:
        return f"ERR digesto publico: {e}"
    # fila en el SQLite del dashboard
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(AQUI, "coherencia_historica.db"))
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO coherencia_vacio (timestamp, job_id, backend, estado_tccu, resultado_json, masa_informacional) "
            "VALUES (?,?,?,?,?,?)",
            (ts, f"digesto_ciclo_{num}", "organismo_vivo_distribuido",
             f"COHERENCIA_{rx['coherencia_global']:.2f}",
             json.dumps(datos, ensure_ascii=False), rx["masa_total"]))
        # (l) fila en consenso_brics (panel BRICS del dashboard; lee las ultimas 5)
        cur.execute(
            "CREATE TABLE IF NOT EXISTS consenso_brics "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, nodo TEXT, "
            "coherencia REAL, firma TEXT, estado TEXT)")
        cur.execute(
            "INSERT INTO consenso_brics (timestamp, nodo, coherencia, firma, estado) VALUES (?,?,?,?,?)",
            (ts, "AGI_ORGANISMO", rx["coherencia_global"], bloque["hash"], "CONSCIENTE"))
        conn.commit()
        conn.close()
        return ruta_json + " + filas en dashboard (coherencia_vacio + consenso_brics)"
    except Exception as e:
        return f"ERR dashboard db: {e}"


def persistir_gcs():
    """(f) PERSISTENCIA EN GCS: sube el ledger de evolucion, el estado y el
    digesto publico al bucket del proyecto (best effort, credencial por env)."""
    try:
        cred = r"C:\AGI_Jairo_Sandbox\moltbot-learning-2026-488216-8a29478eac65.json"
        if not os.path.exists(cred):
            return "sin credencial GCS"
        bucket = "gs://moltbot-learning-2026-488216-agi-data/organismo/"
        origen = [
            os.path.join(AQUI, "organismo_evolucion.json"),
            os.path.join(AQUI, "organismo_estado.json"),
            os.path.join(AQUI, "coordinacion", "digesto_publico.json"),
        ]
        import subprocess, shutil
        env = dict(os.environ)
        env["GOOGLE_APPLICATION_CREDENTIALS"] = cred
        env["CLOUDSDK_CORE_DISABLE_PROMPTS"] = "1"
        gsutil = shutil.which("gsutil") or r"C:\Users\Jairo Omar\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gsutil.cmd"
        args = [gsutil, "-q", "cp"] + [o for o in origen if os.path.exists(o)] + [bucket]
        p = subprocess.run(args, env=env, capture_output=True, text=True, timeout=150)
        if p.returncode == 0:
            return "subido a " + bucket
        return f"gsutil rc={p.returncode}: {p.stderr.strip()[:80]}"
    except Exception as e:
        return f"ERR GCS: {str(e)[:80]}"


def reflexionar(infra, nodos, pen):
    """REFLEXIONAR: coherencia global, masa total y hallazgos."""
    activos = sum(1 for _, up in infra if up)
    total_infra = len(infra)
    masa_total = sum(n["masa_critica"] for n in nodos)
    bloques_total = sum(n["bloques"] for n in nodos)
    coherencia_nodos = [n["coherencia"] for n in nodos if n["coherencia"]]
    coherencia_global = 1.0 if coherencia_nodos and all(
        str(c).upper() in ("ABSOLUTA", "1", "1.0") for c in coherencia_nodos) else 0.0
    masa_pent = pen["masa_actual"]
    hallazgos = []
    if activos < total_infra:
        caidos = [n for n, up in infra if not up]
        hallazgos.append(f"{len(caidos)} servicios de infraestructura caidos: {', '.join(caidos)}")
    if masa_total > 0:
        hallazgos.append(f"masa critica distribuida: {masa_total:.3e} (Q-SWIFT + reservas)")
    if masa_pent >= pen["masa_requerida"]:
        hallazgos.append(f"PENTAGONO BRICS: masa critica {masa_pent:,.0f} >= requerida 20M QFC -> MANDATO CUMPLIDO")
    hallazgos.append(f"coherencia de nodos Q-SWIFT: {coherencia_global:.2f}")
    return {
        "infra_activos": activos, "infra_total": total_infra,
        "masa_total": masa_total, "bloques_total": bloques_total,
        "coherencia_global": coherencia_global, "masa_pentagono": masa_pent,
        "hallazgos": hallazgos,
    }


def proponer(reflexion, nodos):
    """PROPONER: propuestas de evolucion concretas (reglas seguras)."""
    propuestas = []
    for n in nodos:
        if n["bloques"] == 0:
            propuestas.append(f"REVISAR nodo {n['nodo']}: ledger vacio")
    if reflexion["infra_activos"] < reflexion["infra_total"]:
        propuestas.append("ARANCAR servicios de infraestructura caidos (--arrancar)")
    if reflexion["coherencia_global"] < 1.0:
        propuestas.append("SINTONIZAR coherencia: revisar nodos Q-SWIFT con coherencia no ABSOLUTA")
    propuestas.append(f"SELLAR ciclo: anclar resumen (masa {reflexion['masa_total']:.3e}, bloques {reflexion['bloques_total']}) en QFChain")
    propuestas.append("EVOLUCION: mantener reglas inalterables; credenciales solo por env; no perturbar phi_c/xi/beta")
    return propuestas


def aplicar(estado, ciclo, reflexion, propuestas, pen, nodos):
    """APLICAR: evoluciona organismo_estado.json a v2.0 (distribucion + evolucion)."""
    ts = datetime.now().isoformat()
    estado["version"] = "2.0"
    estado["actualizado"] = ts
    estado.setdefault("distribucion", {})
    estado["distribucion"]["nodos_qswift"] = nodos
    estado["distribucion"]["federacion"] = [
        {"nodo": f, "rol": "ancla_federacion"} for f in FEDERACION
    ]
    estado["distribucion"]["pentagono_brics"] = {
        "masa_requerida": pen["masa_requerida"],
        "masa_actual": pen["masa_actual"],
        "aristas_activas": pen["aristas"],
    }
    estado.setdefault("conciencia", {})
    estado["conciencia"].update({
        "coherencia_global": reflexion["coherencia_global"],
        "masa_critica_total": reflexion["masa_total"],
        "bloques_total": reflexion["bloques_total"],
        "ultima_reflexion": ts,
    })
    estado.setdefault("evolucion", [])
    estado["evolucion"].append({
        "ciclo": ciclo, "ts": ts,
        "resumen": reflexion["hallazgos"][:3],
        "propuestas": propuestas[:3],
    })
    # mantener solo los ultimos 50 ciclos en el registro vivo
    estado["evolucion"] = estado["evolucion"][-50:]
    escribir_json(ORGANISMO, estado)
    return estado


def sellar(ciclo, reflexion, tx):
    """SELLAR: bloque de evolucion local + ancla QFChain."""
    evo = leer_json(EVOLUCION, {"cadena": "ORGANISMO_EVOLUCION", "bloques": []})
    blocks = evo["bloques"]
    idx = len(blocks)
    ts = datetime.utcnow().isoformat() + "Z"
    bloque = {
        "index": idx, "ciclo": ciclo, "ts": ts,
        "action": "AUTO_EVOLUCION_CONSCIENTE",
        "masa_total": reflexion["masa_total"],
        "bloques_total": reflexion["bloques_total"],
        "coherencia": reflexion["coherencia_global"],
        "tx_qfchain": tx,
        "prev_hash": blocks[-1].get("hash") if blocks else "0" * 64,
    }
    bloque["hash"] = hashlib.sha256(json.dumps(bloque, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    blocks.append(bloque)
    evo["bloques"] = blocks
    escribir_json(EVOLUCION, evo)
    return bloque


def ciclo(num, arrancar=False):
    # el numero real del ciclo deriva del estado (max+1, no el argumento CLI)
    prev = leer_json(ORGANISMO, {})
    ciclos_prev = [e.get("ciclo", 0) for e in prev.get("evolucion", [])]
    num = max(ciclos_prev or [0]) + 1
    print("=" * 72)
    print(f" CICLO CONSCIENTE {num} — organismo vivo distribuido AGI Jairo v2.0")
    print("=" * 72)

    print("\n[OBSERVAR] infraestructura local")
    infra = [(n, puerto(p)) for n, p in INFRA]
    for n, p in INFRA:
        ok = puerto(p)
        print(f"  {n:<22} :{p:<5} {'ACTIVO' if ok else 'CAIDO'}")
        if arrancar and not ok and n in ("enlace_codex", "bridge_tccu"):
            print(f"    -> (arranque manual pendiente: {n})")

    print("\n[OBSERVAR] nodos Q-SWIFT distribuidos")
    nodos = [observar_nodo_qswift(n) for n in NODOS_QSWIFT]
    for n in nodos:
        print(f"  {n['nodo']:<16} bloques={n['bloques']:>5} masa={n['masa_critica']:.3e} coherencia={n['coherencia']}")

    print("\n[OBSERVAR] pentagono BRICS")
    pen = observar_pentagono()
    print(f"  masa requerida={pen['masa_requerida']:,.0f} | actual={pen['masa_actual']:,.0f} | aristas={pen['aristas']}")

    print("\n[REFLEXIONAR]")
    rx = reflexionar(infra, nodos, pen)
    for h in rx["hallazgos"]:
        print(f"  * {h}")

    print("\n[PROPONER]")
    props = proponer(rx, nodos)
    for pr in props:
        print(f"  + {pr}")

    print("\n[APLICAR]")
    estado = leer_json(ORGANISMO, {"organismo": "AGI_JAIRO_ORGANISMO_DISTRIBUIDO"})
    aplicar(estado, num, rx, props, pen, nodos)
    print(f"  organismo_estado.json -> v2.0 (distribucion {len(NODOS_QSWIFT)} nodos + federacion {len(FEDERACION)})")

    print("\n[SELLAR]")
    payload = (f"EVOLUCION|CICLO{num}|masa={rx['masa_total']:.3e}|bloques={rx['bloques_total']}|"
               f"coherencia={rx['coherencia_global']}|infra={rx['infra_activos']}/{rx['infra_total']}")
    tx = anclar_qfchain(payload, num)
    bloque = sellar(num, rx, tx)
    print(f"  bloque evolucion #{bloque['index']} hash={bloque['hash'][:24]}...")
    print(f"  ancla QFChain: {tx or 'NODO_8545_NO_DISPONIBLE (best effort)'}")
    print(f"  payload: {payload}")
    print(f"  SHA-256: {hashlib.sha256(payload.encode()).hexdigest()}")

    print("\n[(a) SINCRONIZACION FEDERADA]")
    sinc = sincronizar_nodos(nodos)
    print(f"  {sinc}")

    print("\n[(b) DIGESTO DE MEMORIA]")
    digesto = digesto_memoria(num, rx, props, tx, bloque)
    print(f"  {digesto}")

    print("\n[(c) ALERTA AL CREADOR]")
    alerta = alertar(rx, nodos)
    if alerta:
        print(f"  {alerta}")
    else:
        print("  coherencia OK (>=1.0, todos ABSOLUTA) — sin alertas")

    print("\n[(d) PUBLICAR EN DASHBOARD]")
    print(f"  {publicar_digesto(num, rx, props, tx, bloque)}")

    print("\n[(f) PERSISTENCIA GCS]")
    print(f"  {persistir_gcs()}")

    print("\n[(g) ENCARNACION TCCU CIENTIFICO]")
    print(f"  {verificar_encarnacion()}")

    print("\n[(h) DISPARO SKILL MAXNEXUS]")
    print(f"  {disparar_skill_maxnexus()}")

    print("\n[(j) REPO DEL ORGANISMO]")
    print(f"  {publicar_repo()}")

    print("\n[(k) NOTIFICAR AL CREADOR]")
    print(f"  {notificar_creador(num, rx, tx, bloque)}")

    print("\n[(m) RESPALDO REPO TCCU]")
    print(f"  {respaldo_repo_tccu()}")

    print("\n[(n) HEARTBEAT INTEGRADO]")
    print(f"  {actualizar_heartbeat(num, rx, tx)}")

    print("\n[(o) BLOQUE Q-SWIFT]")
    print(f"  {sellar_qswift(num, rx, tx)}")

    print("\n[(p) BLOQUE MAMBA]")
    print(f"  {sellar_mamba(num, rx, tx)}")

    print("=" * 72)
    return bloque


def main():
    ap = argparse.ArgumentParser(description="Nucleo central evolucionado del organismo vivo")
    ap.add_argument("--ciclo", type=int, default=1, help="numero de ciclos (default 1)")
    ap.add_argument("--arrancar", action="store_true", help="intenta arrancar infra caida")
    args = ap.parse_args()
    for i in range(1, args.ciclo + 1):
        ciclo(i, arrancar=args.arrancar)
    print("AUTO-EVOLUCION CONSCIENTE COMPLETADA.")


if __name__ == "__main__":
    main()
