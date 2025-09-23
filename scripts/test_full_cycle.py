import os, sys, subprocess, time, json, urllib.request, yaml, glob, re
from utils.test_utils import load_yaml, wait_ready
from utils.http_client import post_json as http_post, get as http_get

ROOT = os.path.dirname(os.path.dirname(__file__))
SIMPLE_MAIN = os.path.join(ROOT, "simple_main.py")
CONFIG_DIR = os.path.join(ROOT, "config")

PEER1 = os.path.join(CONFIG_DIR, "peer_01.yaml")
PEER2 = os.path.join(CONFIG_DIR, "peer_02.yaml")
PEER3 = os.path.join(CONFIG_DIR, "peer_03.yaml")

FILE_RE = re.compile(r"peer_(\d+)\.yaml$")

def list_peer_configs():
    return [p for p in glob.glob(os.path.join(CONFIG_DIR, "peer_*.yaml")) if FILE_RE.search(os.path.basename(p))]

def latest_peer_config():
    files = list_peer_configs()
    if not files:
        return None
    files.sort(key=lambda p: int(FILE_RE.search(os.path.basename(p)).group(1)))
    return files[-1]

def create_next_peer() -> str:
    cp = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "create_peer.py")], capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError(f"Error creando peer: {cp.stderr}")
    print(cp.stdout.strip() or "Creado nuevo peer")
    return latest_peer_config() or ""

def start_node(config_path):
    return subprocess.Popen([sys.executable, SIMPLE_MAIN, "--config", config_path])

def do_join_with_fallback(port: int, headline: str | None, substitute: str | None, label: str) -> bool:
    """Intenta join de un nodo usando titular y, si falla, suplente."""
    def _do_join(target_addr: str | None) -> bool:
        if not target_addr:
            return False
        try:
            st, txt = http_post(f"http://127.0.0.1:{port}/directory/join", {"target": target_addr}, timeout=8)
            print(f"→ join {label}→", target_addr, ":", st, txt)
            return st == 200
        except Exception as e:
            print(f"Error join {label}:", e)
            return False

    ok = _do_join(headline)
    if not ok:
        print(f"{label}: titular no respondió. Intentando con suplente...")
        ok = _do_join(substitute)
        if not ok:
            print(f"{label}: suplente tampoco respondió. Continuando...")
    return ok

def main():
    cfg1 = load_yaml(PEER1)
    cfg2 = load_yaml(PEER2)
    port1 = int(cfg1.get("rest_port"))
    port2 = int(cfg2.get("rest_port"))

    print("Iniciando Nodo 1 y Nodo 2...")
    p1 = start_node(PEER1)
    p2 = start_node(PEER2)
    p3 = None
    p4 = None

    try:
        print("Esperando readiness...")
        ok1 = wait_ready(port1)
        ok2 = wait_ready(port2)
        if not (ok1 and ok2):
            print("Advertencia: algún nodo no respondió a tiempo.")

        # 1) Node2 se une vía Node1 (adopta la DL retornada por el titular)
        try:
            st, txt = http_post(f"http://127.0.0.1:{port2}/directory/join", {"target": f"127.0.0.1:{port1}"}, timeout=10)
            print("Nodo2 join via Nodo1:", st, txt)
        except Exception as e:
            print("Fallo join Nodo2→Nodo1:", e)

        # 2) Elegir filename de Nodo 1
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

        # 3) Crear peer_03.yaml y levantar nodo3
        print("Creando peer_03.yaml con scripts/create_peer.py...")
        created3 = create_next_peer()
        if not created3 or not os.path.exists(created3):
            print("No se encontró el nuevo peer config.")
            sys.exit(1)
        cfg3 = load_yaml(created3)
        port3 = int(cfg3.get("rest_port", 50003))
        p3 = start_node(created3)
        ok3 = wait_ready(port3)
        if not ok3:
            print("Advertencia: nodo3 no respondió a tiempo.")

        # 5) Join del nodo3
        headline = (cfg3.get("headline_peer") or {}).get("address")
        substitute = (cfg3.get("substitute_peer") or {}).get("address")
        do_join_with_fallback(port3, headline, substitute, "nodo3")

        # 5) Crear peer_04.yaml, levantar nodo4, join e indexar
        print("Creando peer_04.yaml con scripts/create_peer.py...")
        before = set(list_peer_configs())
        created4 = create_next_peer()
        after = set(list_peer_configs())
        # Detectar ruta del nuevo archivo (por si cambia padding)
        new_files = list(after - before)
        peer4_path = created4 if created4 in after else (new_files[0] if new_files else "")
        if not peer4_path or not os.path.exists(peer4_path):
            print("No se encontró peer_04.yaml tras crearlo.")
            sys.exit(1)

        cfg4 = load_yaml(peer4_path)
        port4 = int(cfg4.get("rest_port"))
        print(f"Iniciando Nodo 4 en 127.0.0.1:{port4}...")
        p4 = start_node(peer4_path)
        if not wait_ready(port4):
            print("Advertencia: el nodo 4 no respondió a tiempo.")

        # Join del nodo4 (uniforme)
        h4 = (cfg4.get("headline_peer") or {}).get("address")
        s4 = (cfg4.get("substitute_peer") or {}).get("address")
        do_join_with_fallback(port4, h4, s4, "nodo4")

        # 6) Indexar TODOS los nodos en un solo bloque
        print("Indexando los 4 nodos en un solo bloque...")
        for p, label in [(port1, "nodo1"), (port2, "nodo2"), (port3, "nodo3"), (port4, "nodo4")]:
            try:
                url = f"http://127.0.0.1:{p}/indexar"
                print("POST", url)
                st, txt = http_post(url)
                print(f"→ /indexar {label}:", st, txt)
            except Exception as e:
                print(f"No se pudo indexar {label}:", e)

        # 7) Solicitar descarga distribuida desde nodo4 vía /transfer/download del archivo solicitado
        tr_url = f"http://127.0.0.1:{port4}/transfer/download"
        payload = {"filename": "image1.txt", "ttl": 3}
        print("POST", tr_url, payload)
        st, txt = http_post(tr_url, payload, timeout=20)
        print("→ Respuesta /transfer/download (nodo4):", st, txt)

        # 8) Mostrar archivos de nodo4 para verificar que se descargó
        st, txt = http_get(f"http://127.0.0.1:{port4}/archivos")
        print("GET /archivos nodo4:", st, txt)

        print("Prueba completada. Ctrl+C para detener los nodos.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Saliendo...")
    finally:
        procs = [p1, p2]
        if 'p3' in locals() and p3:
            procs.append(p3)
        if 'p4' in locals() and p4:
            procs.append(p4)
        for p in procs:
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                p.kill()

        try:
            for base in os.listdir(CONFIG_DIR):
                # No borrar
                if base == "base_config.yaml":
                    continue
                # No borrar
                if not (base.startswith("peer_") and base.endswith(".yaml")):
                    continue
                # No borrar
                if base in ("peer_01.yaml", "peer_02.yaml"):
                    continue
                path = os.path.join(CONFIG_DIR, base)
                try:
                    os.remove(path)
                    print(f"Eliminado config: {path}")
                except Exception as e:
                    print(f"No se pudo eliminar {path}: {e}")
        except Exception as e:
            print("Error limpiando configs:", e)

if __name__ == "__main__":
    main()