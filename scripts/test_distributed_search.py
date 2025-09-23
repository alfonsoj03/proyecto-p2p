import os, time, json, urllib.request, yaml
from utils.http_client import post_json as http_post, get as http_get
from utils.test_utils import load_yaml, wait_ready

ROOT = os.path.dirname(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(ROOT, "config")

PEER1 = os.path.join(CONFIG_DIR, "peer_01.yaml")
PEER2 = os.path.join(CONFIG_DIR, "peer_02.yaml")
PEER3 = os.path.join(CONFIG_DIR, "peer_03.yaml")

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

    # 2) Buscar "duplicado.pdf" iniciada por peer3
    do_search(port3, "duplicado.pdf", "2: peer3 busca duplicado.pdf")

    # 3) Buscar "document1.txt" iniciada por peer2
    do_search(port2, "document1.txt", "3: peer2 busca document1.txt")

if __name__ == "__main__":
    main()