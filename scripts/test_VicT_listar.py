import os, sys, subprocess, time, json, urllib.request, yaml
<<<<<<< HEAD
from utils.test_utils import load_yaml, wait_ready
from utils.http_client import post_json as http_post, get as http_get
=======
>>>>>>> 962dda4256852d765141b22a47e3c0034c051334

ROOT = os.path.dirname(os.path.dirname(__file__))
SIMPLE_MAIN = os.path.join(ROOT, "simple_main.py")

PEER1 = os.path.join(ROOT, "config", "peer_01.yaml")
PEER2 = os.path.join(ROOT, "config", "peer_02.yaml")

def main():
    cfg1 = load_yaml(PEER1)
    cfg2 = load_yaml(PEER2)
    port1 = int(cfg1.get("rest_port"))
    port2 = int(cfg2.get("rest_port"))

    # Start both nodes, letting simple_main leer su YAML (IP y puerto vienen de args/YAML)
    p1 = subprocess.Popen([sys.executable, SIMPLE_MAIN, "--config", PEER1])
    p2 = subprocess.Popen([sys.executable, SIMPLE_MAIN, "--config", PEER2])

    try:
        print("Esperando a que los nodos inicien...")
        ok1 = wait_ready(port1)
        ok2 = wait_ready(port2)
        if not (ok1 and ok2):
            print("Algún nodo no inició a tiempo.")

        # Desde el nodo 2, pedir al nodo 1 que indexe y luego listar
        idx_url = f"http://127.0.0.1:{port1}/indexar"
        lst_url = f"http://127.0.0.1:{port1}/archivos"

        print("POST", idx_url)
        try:
            st, txt = http_post(idx_url)
            print("Respuesta indexar:", st, txt)
        except Exception as e:
            print("Error indexar:", e)

        print("GET", lst_url)
        try:
            st, txt = http_get(lst_url)
            print("Respuesta archivos:", st, txt)
        except Exception as e:
            print("Error listar:", e)

        print("Nodos ejecutándose. Ctrl+C para salir.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Saliendo...")
    finally:
        for p in (p1, p2):
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                p.kill()

if __name__ == "__main__":
    main()