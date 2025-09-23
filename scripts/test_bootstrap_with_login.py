import os, sys, subprocess, time, json, urllib.request, yaml
<<<<<<< HEAD
from utils.http_client import post_json as http_post
from utils.test_utils import load_yaml, wait_ready
=======
>>>>>>> 962dda4256852d765141b22a47e3c0034c051334

ROOT = os.path.dirname(os.path.dirname(__file__))
SIMPLE_MAIN = os.path.join(ROOT, "simple_main.py")
CREATE_PEER = os.path.join(ROOT, "scripts", "create_peer.py")
CONFIG_DIR = os.path.join(ROOT, "config")

PEER1 = os.path.join(CONFIG_DIR, "peer_01.yaml")
PEER2 = os.path.join(CONFIG_DIR, "peer_02.yaml")
PEER3 = os.path.join(CONFIG_DIR, "peer_03.yaml")

<<<<<<< HEAD
=======
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

>>>>>>> 962dda4256852d765141b22a47e3c0034c051334
# IMPORTANTE: Función helper que inicia el nodo en un proceso separado.
def start_node(config_path):
    return subprocess.Popen([sys.executable, SIMPLE_MAIN, "--config", config_path])

def main():
    # Start first two nodes
    cfg1 = load_yaml(PEER1)
    cfg2 = load_yaml(PEER2)
    port1 = int(cfg1.get("rest_port"))
    port2 = int(cfg2.get("rest_port"))

    print("Iniciando Nodo 1 y Nodo 2...")
    p1 = start_node(PEER1)
    p2 = start_node(PEER2)

    try:
        print("Esperando readiness...")
        ok1 = wait_ready(port1)
        ok2 = wait_ready(port2)
        if not (ok1 and ok2):
            print("Advertencia: algún nodo no respondió a tiempo.")

        # Paso A) Nodo2 se loguea en Nodo1 usando /directory/login del titular (Nodo1)
        # y adopta localmente la DL retornada por Nodo1.
        try:
            url_login = f"http://127.0.0.1:{port1}/directory/login"
            payload = {"address": f"127.0.0.1:{port2}"}
            print("POST", url_login, payload)
            st, txt = http_post(url_login, payload, timeout=6)
            print("Respuesta login Nodo1 ← Nodo2:", st, txt)
            # Adoptar DL en Nodo2: por cada addr de la DL devuelta por Nodo1,
            # ejecutar localmente /directory/login en Nodo2 para poblar su DL.
            try:
                resp = json.loads(txt or "{}")
                dl = resp.get("dl") if isinstance(resp, dict) else None
                if isinstance(dl, list):
                    for addr in dl:
                        if addr:
                            try:
                                http_post(f"http://127.0.0.1:{port2}/directory/login", {"address": addr}, timeout=6)
                            except Exception:
                                pass
                # Asegurar que Nodo2 tenga a Nodo1 (por si acaso)
                http_post(f"http://127.0.0.1:{port2}/directory/login", {"address": f"127.0.0.1:{port1}"}, timeout=6)
            except Exception as e:
                print("No se pudo adoptar DL en Nodo2:", e)
        except Exception as e:
            print("Fallo login de Nodo2 en Nodo1:", e)

        # Create new peer config (peer_03.yaml esperado) en paralelo.
        print("Creando nuevo peer con create_peer.py...")
        cp = subprocess.run([sys.executable, CREATE_PEER, "--config-dir", CONFIG_DIR, "--base-config", os.path.join(CONFIG_DIR, "base_config.yaml")], capture_output=True, text=True)
        if cp.returncode != 0:
            print("Error creando peer:", cp.stderr)
            sys.exit(1)
        else:
            print(cp.stdout.strip())

        # Verificar que la config del nuevo nodo exista.
        if not os.path.exists(PEER3):
            print("No se encontró el nuevo peer config.")
            sys.exit(1)

        new_cfg = load_yaml(PEER3)
        new_port = int(new_cfg.get("rest_port"))
        new_ip = new_cfg.get("ip", "127.0.0.1")
        new_addr = f"{new_ip}:{new_port}"

        # Start new node
        print(f"Iniciando nuevo nodo con {PEER3} en {new_addr}...")
        p_new = start_node(PEER3)

        # Wait for readiness
        if not wait_ready(new_port):
            print("El nuevo nodo no respondió a tiempo.")

        # Try login against headline, then substitute
        headline = (new_cfg.get("headline_peer") or {}).get("address")
        substitute = (new_cfg.get("substitute_peer") or {}).get("address")

        def do_login(target_addr):
            if not target_addr:
                return False, "sin direccion"
            url = f"http://{target_addr}/directory/login"
            payload = {"address": new_addr}
            print("POST", url, payload)
            try:
                st, txt = http_post(url, payload, timeout=6)
                print("Respuesta login:", st, txt)
                return st == 200, txt
            except Exception as e:
                print("Error login:", e)
                return False, str(e)

        print("Intentando login con titular...")
        ok, login_txt = do_login(headline)
        used_target = headline if ok else None
        if not ok:
            print("Titular no respondió. Intentando con suplente...")
            ok, login_txt = do_login(substitute)
            if ok:
                used_target = substitute
            else:
                print("Suplente tampoco respondió. Puedes reintentar más tarde.")

        # Si el login devolvió una DL, sembrar DL local del nuevo nodo con esas direcciones
        try:
            resp = json.loads(login_txt or "{}")
            dl = resp.get("dl") if isinstance(resp, dict) else None
            if isinstance(dl, list):
                for addr in dl:
                    if addr and f":{new_port}" not in addr:
                        try:
                            http_post(f"http://127.0.0.1:{new_port}/directory/login", {"address": addr}, timeout=6)
                            print(f"Nuevo nodo agregó a su DL: {addr}")
                        except Exception as e:
                            print("No se pudo agregar a DL local del nuevo nodo:", addr, e)
        except Exception:
            pass

        # Imprimir información sobre las operaciones hechas.
        try:
            if used_target:
                with urllib.request.urlopen(f"http://{used_target}/directory/dl", timeout=6) as r:
                    print("DL del que logueó (", used_target, "):", r.read().decode("utf-8"))
            with urllib.request.urlopen(f"http://127.0.0.1:{new_port}/directory/dl", timeout=6) as r:
                print("DL del nuevo nodo (127.0.0.1:", new_port, "):", r.read().decode("utf-8"))
        except Exception as e:
            print("No se pudieron obtener las DL para verificación:", e)

        print("Bootstrap y login completados. Ctrl+C para detener.")
        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Saliendo...")
    finally:
        # Terminate processes
        for p in (p1, p2):
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                p.kill()
        # p_new might be defined
        try:
            p_new.terminate()
            p_new.wait(timeout=5)
        except Exception:
            try:
                p_new.kill()
            except Exception:
                pass

        # Limpiar configs: borrar todos los peer_*.yaml excepto peer_01.yaml y peer_02.yaml
        try:
            for base in os.listdir(CONFIG_DIR):
                if not (base.startswith("peer_") and base.endswith(".yaml")):
                    continue
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