#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import json
import urllib.request
import urllib.error
import yaml

ROOT = os.path.dirname(os.path.dirname(__file__))
SIMPLE_MAIN = os.path.join(ROOT, "simple_main.py")
CONFIG_DIR = os.path.join(ROOT, "config")

PEER1 = os.path.join(CONFIG_DIR, "peer_01.yaml")
PEER2 = os.path.join(CONFIG_DIR, "peer_02.yaml")
PEER3 = os.path.join(CONFIG_DIR, "peer_03.yaml")

def find_latest_peer_config():
    files = []
    for base in os.listdir(CONFIG_DIR):
        if base.startswith("peer_") and base.endswith(".yaml"):
            p = os.path.join(CONFIG_DIR, base)
            try:
                n = int(base[5:7])
            except ValueError:
                try:
                    n = int(base[5:-5])
                except Exception:
                    continue
            files.append((n, p))
    if not files:
        return None
    files.sort(key=lambda x: x[0])
    return files[-1][1]


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def wait_ready(port, timeout=20):
    url = f"http://127.0.0.1:{port}/archivos"
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


def http_post(url, data=None, timeout=10):
    body = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")


def http_get(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")


def main():
    cfg1 = load_yaml(PEER1)
    cfg2 = load_yaml(PEER2)
    port1 = int(cfg1.get("rest_port"))
    port2 = int(cfg2.get("rest_port"))

    print("Iniciando Nodo 1 y Nodo 2...")
    p1 = subprocess.Popen([sys.executable, SIMPLE_MAIN, "--config", PEER1])
    p2 = subprocess.Popen([sys.executable, SIMPLE_MAIN, "--config", PEER2])
    p3 = None

    try:
        print("Esperando readiness...")
        ok1 = wait_ready(port1)
        ok2 = wait_ready(port2)
        if not (ok1 and ok2):
            print("Advertencia: algún nodo no respondió a tiempo.")

        # 1) Indexar Nodo 1 y Nodo 2
        idx1 = f"http://127.0.0.1:{port1}/indexar"
        print("POST", idx1)
        st, txt = http_post(idx1)
        print("→ /indexar nodo1:", st, txt)

        idx2 = f"http://127.0.0.1:{port2}/indexar"
        print("POST", idx2)
        st, txt = http_post(idx2)
        print("→ /indexar nodo2:", st, txt)

        # 2) Node2 se une vía Node1 (adopta la DL retornada por el titular)
        try:
            st, txt = http_post(f"http://127.0.0.1:{port2}/directory/join", {"target": f"127.0.0.1:{port1}"}, timeout=10)
            print("Nodo2 join via Nodo1:", st, txt)
        except Exception as e:
            print("Fallo join Nodo2→Nodo1:", e)

        # 3) Elegir filename de Nodo 1
        st, txt = http_get(f"http://127.0.0.1:{port1}/archivos")
        print("GET /archivos nodo1:", st, txt)
        filename = None
        try:
            resp = json.loads(txt)
            data = resp.get("data") or []
            if isinstance(data, list) and data:
                filename = data[0].get("filename")
        except Exception:
            pass
        if not filename:
            filename = "document1.txt"  # fallback común del repo

        # 4) Crear peer_03.yaml y levantar nodo3
        print("Creando peer_03.yaml con scripts/create_peer.py...")
        cp = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "create_peer.py")], capture_output=True, text=True)
        if cp.returncode != 0:
            print("Error creando peer:", cp.stderr)
        else:
            print(cp.stdout.strip())
        created_path = find_latest_peer_config() or PEER3
        cfg3 = load_yaml(created_path)
        port3 = int(cfg3.get("rest_port", 50003))
        p3 = subprocess.Popen([sys.executable, SIMPLE_MAIN, "--config", created_path])
        ok3 = wait_ready(port3)
        if not ok3:
            print("Advertencia: nodo3 no respondió a tiempo.")

        # 5) Join del nodo3 con su titular (fallback a suplente)
        headline = (cfg3.get("headline_peer") or {}).get("address")
        substitute = (cfg3.get("substitute_peer") or {}).get("address")

        def do_join_local(target_addr):
            if not target_addr:
                return False, "sin direccion"
            url = f"http://127.0.0.1:{port3}/directory/join"
            payload = {"target": target_addr}
            print("POST", url, payload)
            try:
                st, txt = http_post(url, payload, timeout=8)
                print("→ Respuesta join nodo3:", st, txt)
                return st == 200, txt
            except Exception as e:
                print("Error join nodo3:", e)
                return False, str(e)

        ok_join, _ = do_join_local(headline)
        if not ok_join:
            print("Titular no respondió. Intentando con suplente...")
            ok_join, _ = do_join_local(substitute)
            if not ok_join:
                print("Suplente tampoco respondió. Seguimos con la prueba igualmente.")

        # 6) Indexar nodo3 (antes de usar transfer, mantenemos consistencia local)
        try:
            idx3 = f"http://127.0.0.1:{port3}/indexar"
            print("POST", idx3)
            st, txt = http_post(idx3)
            print("→ /indexar nodo3:", st, txt)
        except Exception as e:
            print("No se pudo indexar nodo3:", e)

        # 7) Solicitar descarga distribuida desde nodo3 vía /transfer/download
        tr_url = f"http://127.0.0.1:{port3}/transfer/download"
        payload = {"filename": filename, "ttl": 3}
        print("POST", tr_url, payload)
        st, txt = http_post(tr_url, payload, timeout=20)
        print("→ Respuesta /transfer/download (nodo3):", st, txt)

        # 8) Mostrar archivos de nodo3 para verificar que se descargó
        st, txt = http_get(f"http://127.0.0.1:{port3}/archivos")
        print("GET /archivos nodo3:", st, txt)

        print("Prueba completada. Ctrl+C para detener los nodos.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Saliendo...")
    finally:
        procs = [p1, p2]
        if 'p3' in locals() and p3:
            procs.append(p3)
        for p in procs:
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                p.kill()

if __name__ == "__main__":
    main()