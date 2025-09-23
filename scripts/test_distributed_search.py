<<<<<<< HEAD
import os, time, json, urllib.request, yaml
from utils.http_client import post_json as http_post, get as http_get
from utils.test_utils import load_yaml, wait_ready
=======
import os, sys, subprocess, time, json, urllib.request, yaml
>>>>>>> 962dda4256852d765141b22a47e3c0034c051334

ROOT = os.path.dirname(os.path.dirname(__file__))
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


def http_get(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

>>>>>>> 962dda4256852d765141b22a47e3c0034c051334
def main():
    # Leer puertos de peers ya existentes
    cfg1 = load_yaml(PEER1)
    cfg2 = load_yaml(PEER2)
    cfg3 = load_yaml(PEER3)
    port1 = int(cfg1.get("rest_port"))
    port2 = int(cfg2.get("rest_port"))
    port3 = int(cfg3.get("rest_port"))

    print("Se asume que los nodos ya están corriendo")

    # Esperar readiness de los tres nodos
    wait_ready(port1)
    wait_ready(port2)
    wait_ready(port3)

<<<<<<< HEAD
    def do_search(from_port: int, filename: str, label: str):
        url = f"http://127.0.0.1:{from_port}/directory/search"
        payload = {"filename": filename, "ttl": 3}
        print(f"\n=== Prueba {label} ===")
        print("POST", url, payload)
        try:
            st, txt = http_post(url, payload, timeout=12)
            print(f"→ Respuesta /directory/search (desde {from_port}):", st, txt)
        except Exception as e:
            print(f"Fallo /directory/search desde {from_port}:", e)

    # 1) Buscar "archivo_inexistente.mp3" iniciada por peer1
    do_search(port1, "archivo_inexistente.mp3", "1: peer1 busca archivo_inexistente.mp3")
=======
        # 1) Indexar en nodo 1
        idx_url = f"http://127.0.0.1:{port1}/indexar"
        print("POST", idx_url)
        st, txt = http_post(idx_url)
        print("→ Respuesta /indexar nodo1:", st, txt)

        # 1b) Indexar en nodo 2
        idx2_url = f"http://127.0.0.1:{port2}/indexar"
        print("POST", idx2_url)
        st, txt = http_post(idx2_url)
        print("→ Respuesta /indexar nodo2:", st, txt)

        # 2) Node2 se une a la red a través del titular Node1 (adopta la DL retornada)
        try:
            st, txt = http_post(f"http://127.0.0.1:{port2}/directory/join", {"target": f"127.0.0.1:{port1}"}, timeout=10)
            print("Nodo2 join via Nodo1:", st, txt)
        except Exception as e:
            print("Fallo join Nodo2→Nodo1:", e)

        # 3) Listar archivos en nodo 1
        lst_url = f"http://127.0.0.1:{port1}/archivos"
        print("GET", lst_url)
        st, txt = http_get(lst_url)
        print("→ Respuesta /archivos nodo1:", st, txt)
        filename = None
        try:
            resp = json.loads(txt)
            data = resp.get("data") or []
            if isinstance(data, list) and data:
                filename = data[0].get("filename")
        except Exception:
            pass

        if not filename:
            # Fallback a un nombre cualquiera si el índice está vacío
            filename = "archivo_que_no_existe.xyz"

        # 4) Crear peer_03.yaml usando el script oficial y arrancar nodo 3
        print("Creando peer_03.yaml con scripts/create_peer.py...")
        cp = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "create_peer.py")], capture_output=True, text=True)
        if cp.returncode != 0:
            print("Error creando peer:", cp.stderr)
        else:
            print(cp.stdout.strip())
        
        # Verificar que el path de 3 exista
        if not os.path.exists(PEER3):
            print("No se encontró el nuevo peer config.")
            sys.exit(1)
        
        cfg3 = load_yaml(PEER3)
        port3 = int(cfg3.get("rest_port", 50003))
        p3 = subprocess.Popen([sys.executable, SIMPLE_MAIN, "--config", PEER3])
        ok3 = wait_ready(port3)
        if not ok3:
            print("Advertencia: el nodo 3 no respondió a tiempo.")

        # 4) Login del nodo3 con su titular (fallback a suplente)
        new_ip = cfg3.get("ip", "127.0.0.1")
        # 4) Pedirle al nodo titular que lo loguee a la red.
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

        # 4b) Indexar en nodo 3 antes de buscar
        try:
            idx3_url = f"http://127.0.0.1:{port3}/indexar"
            print("POST", idx3_url)
            st, txt = http_post(idx3_url)
            print("→ Respuesta /indexar nodo3:", st, txt)
        except Exception as e:
            print("No se pudo indexar nodo3:", e)

        time.sleep(0.5)
        time.sleep(0.5)

        # 5) Buscar desde nodo 3 el filename elegido (flood TTL=3)
        srch_url = f"http://127.0.0.1:{port3}/directory/search"
        payload = {"filename": filename, "ttl": 3}
        print("POST", srch_url, payload)
        try:
            st, txt = http_post(srch_url, payload, timeout=12)
            print("→ Respuesta /directory/search (desde nodo3):", st, txt)
        except Exception as e:
            print("Fallo /directory/search:", e)

        print("Prueba completada. Saliendo y cerrando nodos...")
        return
>>>>>>> 962dda4256852d765141b22a47e3c0034c051334

    # 2) Buscar "duplicado.pdf" iniciada por peer3
    do_search(port3, "duplicado.pdf", "2: peer3 busca duplicado.pdf")

    # 3) Buscar "document1.txt" iniciada por peer2
    do_search(port2, "document1.txt", "3: peer2 busca document1.txt")

        # Dejar los configs como en un inicio solo 1 y 2
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