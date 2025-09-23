import os, sys, time, json, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.http_client import post_json as http_post, get as http_get
from utils.test_utils import load_yaml, wait_ready

# Se asume que está corriendo setup_three_nodes

ROOT = os.path.dirname(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(ROOT, "config")

PEER1 = os.path.join(CONFIG_DIR, "peer_01.yaml")
PEER2 = os.path.join(CONFIG_DIR, "peer_02.yaml")
PEER3 = os.path.join(CONFIG_DIR, "peer_03.yaml")

def read_ports():
    p1 = int(load_yaml(PEER1).get("rest_port"))
    p2 = int(load_yaml(PEER2).get("rest_port"))
    p3 = int(load_yaml(PEER3).get("rest_port"))
    return p1, p2, p3

def main():
    # Asume que los tres nodos ya están corriendo (por setup_three_nodes.py)
    port1, port2, port3 = read_ports()

    # Elegir filename de Nodo1
    st, txt = http_get(f"http://127.0.0.1:{port1}/archivos")
    filename = None
    try:
        data = (json.loads(txt).get("data") or [])
        if data:
            filename = data[0].get("filename")
    except Exception:
        pass
    if not filename:
        filename = "document1.txt"

    print("Ejecutando prueba de concurrencia (sin bloquear)...")

    def call_search(port, idx):
        url = f"http://127.0.0.1:{port}/directory/search"
        payload = {"filename": filename, "ttl": 3}
        t0 = time.time()
        st, txt = http_post(url, payload, timeout=15)
        dt = (time.time() - t0) * 1000
        return ("search", port, idx, st, dt, txt)

    def call_download(port, idx):
        url = f"http://127.0.0.1:{port}/transfer/download"
        payload = {"filename": filename, "ttl": 3}
        t0 = time.time()
        st, txt = http_post(url, payload, timeout=25)
        dt = (time.time() - t0) * 1000
        return ("download", port, idx, st, dt, txt)

    tasks = []
    batch_t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        # peticiones cruzadas desde nodo2 y nodo3
        for i in range(4):
            tasks.append(ex.submit(call_search, port2, i))
            tasks.append(ex.submit(call_search, port3, i))
        for i in range(2):
            tasks.append(ex.submit(call_download, port2, i))
            tasks.append(ex.submit(call_download, port3, i))

        results = []
        for fut in as_completed(tasks):
            results.append(fut.result())
    batch_ms = (time.time() - batch_t0) * 1000

    # Ordenar por tiempo de inicio no es trivial; basta con imprimir los tiempos y verificar solapamiento
    results.sort(key=lambda x: (x[0], x[2], x[1]))
    for kind, port, idx, st, dt, txt in results:
        print(f"[{kind}] port={port} idx={idx} status={st} time_ms={dt:.1f} body={txt}")

    # Señal explícita de concurrencia: si el tiempo total del batch << suma de tiempos individuales,
    # hubo paralelismo (no se ejecutaron estrictamente en serie)
    search_times = [dt for kind,_,_,_,dt,_ in results if kind == "search"]
    download_times = [dt for kind,_,_,_,dt,_ in results if kind == "download"]
    sum_times = sum(search_times) + sum(download_times)
    if search_times:
        print(f"Resumen search: count={len(search_times)} max={max(search_times):.1f}ms avg={sum(search_times)/len(search_times):.1f}ms")
    if download_times:
        print(f"Resumen download: count={len(download_times)} max={max(download_times):.1f}ms avg={sum(download_times)/len(download_times):.1f}ms")
    print(f"Tiempo total batch: {batch_ms:.1f}ms; Suma de tiempos individuales: {sum_times:.1f}ms; Factor de concurrencia (suma/total): { (sum_times / batch_ms) if batch_ms>0 else float('inf') :.2f}")

    print("Si el tiempo total del batch es muy menor a la suma de tiempos individuales, hubo concurrencia (ejecución superpuesta).")


if __name__ == "__main__":
    main()