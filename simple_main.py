import argparse
import uvicorn
import yaml

# Importa la app FastAPI mínima y el setter del directorio base
from services.file_simple.api import app
from services.file_simple.service import set_base_directory
from services.directory_simple.service import set_self_address, set_self_info

def main():
    parser = argparse.ArgumentParser(description="Inicia una API simple de File Service por nodo")
    parser.add_argument("--config", required=True, help="Ruta al YAML de configuración del peer (peer_XX.yaml)")
    parser.add_argument("--ip", default="127.0.0.1", help="IP de escucha")
    parser.add_argument("--port", type=int, required=False, help="Puerto REST para este nodo (si no se pasa, se usa rest_port del YAML)")
    args = parser.parse_args()

    # Cargar YAML de configuración para obtener files_directory
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    files_dir = cfg.get("files_directory") or cfg.get("filesDir")
    if not files_dir:
        raise SystemExit("'files_directory' no encontrado en la configuración del peer")

    # Establecer el directorio base para la indexación en memoria
    set_base_directory(files_dir)

    port = args.port or cfg.get("rest_port")
    if not port:
        raise SystemExit("Puerto no especificado: pase --port o defina rest_port en el YAML")
    # Registrar identidad y dirección propia del nodo en el Directory List simple
    self_ip = cfg.get("ip", "127.0.0.1")
    peer_id = cfg.get("peer_id", "")
    if peer_id:
        set_self_info(peer_id, f"{self_ip}:{int(port)}")
    else:
        set_self_address(f"{self_ip}:{int(port)}")
    uvicorn.run(app, host=args.ip, port=int(port), log_level="info")

if __name__ == "__main__":
    main()