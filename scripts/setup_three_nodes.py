import os, sys, subprocess, time, json, urllib.request, urllib.error, yaml

ROOT = os.path.dirname(os.path.dirname(__file__))
SIMPLE_MAIN = os.path.join(ROOT, "simple_main.py")
CONFIG_DIR = os.path.join(ROOT, "config")

PEER1 = os.path.join(CONFIG_DIR, "peer_01.yaml")
PEER2 = os.path.join(CONFIG_DIR, "peer_02.yaml")
PEER3 = os.path.join(CONFIG_DIR, "peer_03.yaml")

def http_post(url, data=None, timeout=10):
    body = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

def http_get(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

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
        time.sleep(0.3)
    return False

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
        print("Esperando readiness de 1 y 2...")
        wait_ready(port1)
        wait_ready(port2)

        # Indexar 1 y 2
        for port, label in [(port1, "nodo1"), (port2, "nodo2")]:
            st, txt = http_post(f"http://127.0.0.1:{port}/indexar")
            print(f"→ /indexar {label}:", st, txt)

        # Node2 join via Node1
        try:
            st, txt = http_post(f"http://127.0.0.1:{port2}/directory/join", {"target": f"127.0.0.1:{port1}"}, timeout=10)
            print("Nodo2 join via Nodo1:", st, txt)
        except Exception as e:
            print("Fallo join Nodo2→Nodo1:", e)

        # Asegurar peer_03 existe
        if not os.path.exists(PEER3):
            print("Creando peer_03.yaml con scripts/create_peer.py...")
            cp = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "create_peer.py")], capture_output=True, text=True)
            print(cp.stdout.strip() or cp.stderr.strip())
        if not os.path.exists(PEER3):
            print("No se encontró peer_03.yaml. Saliendo.")
            return

        cfg3 = load_yaml(PEER3)
        port3 = int(cfg3.get("rest_port", 50003))
        print(f"Iniciando Nodo 3 en 127.0.0.1:{port3}...")
        p3 = subprocess.Popen([sys.executable, SIMPLE_MAIN, "--config", PEER3])
        wait_ready(port3)

        # Node3 join con titular o suplente
        headline = (cfg3.get("headline_peer") or {}).get("address")
        substitute = (cfg3.get("substitute_peer") or {}).get("address")

        def do_join_local(target_addr):
            if not target_addr:
                return False
            try:
                st, txt = http_post(f"http://127.0.0.1:{port3}/directory/join", {"target": target_addr}, timeout=8)
                print("join nodo3→", target_addr, ":", st, txt)
                return st == 200
            except Exception as e:
                print("Error join nodo3:", e)
                return False

        if not do_join_local(headline):
            do_join_local(substitute)

        # Indexar nodo3
        try:
            st, txt = http_post(f"http://127.0.0.1:{port3}/indexar")
            print("→ /indexar nodo3:", st, txt)
        except Exception as e:
            print("No se pudo indexar nodo3:", e)

        print("Red lista con 3 nodos. Deja esta consola abierta para mantenerlos ejecutándose. Ctrl+C para detener.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Saliendo...")
    finally:
        for p in [p1, p2, p3]:
            if not p:
                continue
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

if __name__ == "__main__":
    main()