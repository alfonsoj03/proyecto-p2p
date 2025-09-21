import argparse
import uvicorn
import yaml
import asyncio
import logging
import threading
from pathlib import Path

# Importa la app FastAPI mínima y el setter del directorio base
from services.file_simple.api import app
from services.file_simple.service import set_base_directory
from services.directory_simple.service import set_self_address

# Importaciones para gRPC Transfer Service
from services.transfer_grpc import GRPC_GENERATED, start_grpc_server, set_directories, get_transfer_client

logger = logging.getLogger(__name__)

async def start_grpc_server_async(host: str, grpc_port: int, node_address: str, files_dir: str):
    """Inicia el servidor gRPC en un hilo separado."""
    if not GRPC_GENERATED:
        logger.warning("⚠️  Código gRPC no generado. Ejecuta: python scripts/generate_grpc.py")
        return None
    
    try:
        # Configurar directorios para el Transfer Service
        downloads_dir = Path(files_dir).parent / "downloads"
        set_directories(files_dir, str(downloads_dir))
        
        # Inicializar cliente gRPC
        get_transfer_client(node_address)
        
        # Iniciar servidor gRPC
        server = await start_grpc_server(host, grpc_port, node_address)
        logger.info(f"🚀 Servidor gRPC iniciado en {host}:{grpc_port}")
        
        return server
        
    except Exception as e:
        logger.error(f"❌ Error iniciando servidor gRPC: {e}")
        return None

def run_grpc_server(host: str, grpc_port: int, node_address: str, files_dir: str):
    """Ejecuta el servidor gRPC en un hilo separado."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        server = loop.run_until_complete(
            start_grpc_server_async(host, grpc_port, node_address, files_dir)
        )
        
        if server:
            # Mantener servidor activo
            loop.run_until_complete(server.wait_for_termination())
    except Exception as e:
        logger.error(f"❌ Error en hilo gRPC: {e}")
    finally:
        loop.close()

def main():
    parser = argparse.ArgumentParser(description="Inicia nodo P2P con API REST y gRPC")
    parser.add_argument("--config", required=True, help="Ruta al YAML de configuración del peer (peer_XX.yaml)")
    parser.add_argument("--ip", default="127.0.0.1", help="IP de escucha")
    parser.add_argument("--port", type=int, required=False, help="Puerto REST para este nodo (si no se pasa, se usa rest_port del YAML)")
    parser.add_argument("--no-grpc", action="store_true", 
                       help="Deshabilitar servidor gRPC (solo REST)")
    args = parser.parse_args()

    # Cargar YAML de configuración
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    
    files_dir = cfg.get("files_directory") or cfg.get("filesDir")
    if not files_dir:
        raise SystemExit("'files_directory' no encontrado en la configuración del peer")

    # Establecer el directorio base para la indexación en memoria
    set_base_directory(files_dir)

    # Configurar puertos
    rest_port = args.port or cfg.get("rest_port")
    grpc_port = cfg.get("grpc_port")
    
    if not rest_port:
        raise SystemExit("Puerto REST no especificado: pase --port o defina rest_port en el YAML")
    
    if not grpc_port and not args.no_grpc:
        raise SystemExit("Puerto gRPC no especificado: defina grpc_port en el YAML o use --no-grpc")

    # Configurar dirección del nodo
    self_ip = cfg.get("ip", "127.0.0.1")
    node_address = f"{self_ip}:{int(rest_port)}"
    set_self_address(node_address)
    
    print(f"🚀 Iniciando nodo P2P: {node_address}")
    print(f"📁 Directorio de archivos: {files_dir}")
    print(f"🌐 Puerto REST: {rest_port}")
    
    if not args.no_grpc and grpc_port:
        print(f"📡 Puerto gRPC: {grpc_port}")
        
        # Iniciar servidor gRPC en hilo separado
        grpc_thread = threading.Thread(
            target=run_grpc_server,
            args=(args.ip, grpc_port, node_address, files_dir),
            daemon=True
        )
        grpc_thread.start()
        print("✅ Servidor gRPC iniciado en hilo separado")
    else:
        print("⚠️  Servidor gRPC deshabilitado")
    
    # Iniciar servidor REST (bloquea el hilo principal)
    print(f"🌐 Iniciando servidor REST en {args.ip}:{rest_port}")
    uvicorn.run(app, host=args.ip, port=int(rest_port), log_level="info")

if __name__ == "__main__":
    main()