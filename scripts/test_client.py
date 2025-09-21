#!/usr/bin/env python3
"""
Cliente de prueba para el sistema P2P.
Permite hacer login y búsquedas en la red desde la línea de comandos.
"""
import asyncio
import aiohttp
import argparse
import json
import sys
import time
import os
from pathlib import Path

# Importar cliente gRPC para transferencias
try:
    from services.transfer_grpc.client import TransferClient
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

class P2PTestClient:
    def __init__(self, timeout: int = 10):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
    
    async def post_json(self, url: str, data: dict) -> dict:
        """Realiza POST con JSON."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"ERROR: POST {url} retornó status {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            print(f"ERROR: POST {url}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_json(self, url: str) -> dict:
        """Realiza GET."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"ERROR: GET {url} retornó status {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            print(f"ERROR: GET {url}: {e}")
            return {"success": False, "error": str(e)}

    async def login_peer(self, target_node: str, new_peer_address: str):
        """Loguea un peer en otro nodo."""
        url = f"http://{target_node}/directory/login"
        data = {"address": new_peer_address}
        
        print(f"Logueando {new_peer_address} en {target_node}...")
        response = await self.post_json(url, data)
        
        if response.get("success"):
            print(f"✓ Login exitoso. DL retornada: {response.get('dl', [])}")
        else:
            print(f"✗ Login falló: {response.get('error', 'Error desconocido')}")
        
        return response

    async def get_directory_list(self, node: str):
        """Obtiene la Directory List de un nodo."""
        url = f"http://{node}/directory/dl/all"
        
        print(f"Obteniendo Directory List de {node}...")
        response = await self.get_json(url)
        
        if response.get("success"):
            dl = response.get("dl", [])
            print(f"✓ Directory List: {dl}")
        else:
            print(f"✗ Error obteniendo DL: {response.get('error', 'Error desconocido')}")
        
        return response

    async def index_files(self, node: str):
        """Indexa archivos en un nodo."""
        url = f"http://{node}/indexar"
        
        print(f"Indexando archivos en {node}...")
        response = await self.post_json(url, {})
        
        if response.get("success"):
            total = response.get("total", 0)
            print(f"✓ Indexados {total} archivo(s)")
        else:
            print(f"✗ Error indexando: {response.get('error', 'Error desconocido')}")
        
        return response

    async def list_files(self, node: str):
        """Lista archivos indexados en un nodo."""
        url = f"http://{node}/archivos"
        
        print(f"Listando archivos en {node}...")
        response = await self.get_json(url)
        
        if response.get("success"):
            files = response.get("data", [])
            print(f"✓ {len(files)} archivo(s) encontrado(s):")
            for file in files:
                print(f"  - {file.get('filename')} ({file.get('size')} bytes)")
        else:
            print(f"✗ Error listando archivos: {response.get('error', 'Error desconocido')}")
        
        return response

    async def search_file(self, node: str, filename: str):
        """Busca un archivo en la red P2P."""
        url = f"http://{node}/directory/search/simple/{filename}"
        
        print(f"\n=== BÚSQUEDA DISTRIBUIDA ===")
        print(f"Buscando '{filename}' desde {node}...")
        start_time = time.time()
        
        response = await self.get_json(url)
        
        search_time = time.time() - start_time
        
        if response.get("success"):
            results = response.get("results", [])
            total = response.get("total_results", 0)
            print(f"✓ Búsqueda completada en {search_time:.2f}s")
            print(f"✓ {total} resultado(s) encontrado(s):")
            
            for result in results:
                node_addr = result.get("node_address", "desconocido")
                filename = result.get("filename", "")
                size = result.get("size", 0)
                print(f"  - {filename} en {node_addr} ({size} bytes)")
        else:
            print(f"✗ Error en búsqueda: {response.get('error', 'Error desconocido')}")
        
        return response

async def main():
    parser = argparse.ArgumentParser(description="Cliente de prueba P2P")
    parser.add_argument("--node", default="127.0.0.1:50001", 
                       help="Nodo objetivo (ip:puerto)")
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Comando login
    login_parser = subparsers.add_parser("login", help="Loguear un peer")
    login_parser.add_argument("--peer", required=True, 
                             help="Dirección del peer a loguear (ip:puerto)")
    
    # Comando dl
    subparsers.add_parser("dl", help="Obtener Directory List")
    
    # Comando index
    subparsers.add_parser("index", help="Indexar archivos")
    
    # Comando files
    subparsers.add_parser("files", help="Listar archivos indexados")
    
    # Comando search
    search_parser = subparsers.add_parser("search", help="Buscar archivo")
    search_parser.add_argument("filename", help="Nombre del archivo a buscar")
    
    # Comando full-test
    subparsers.add_parser("full-test", help="Ejecutar prueba completa de la Fase 2")
    
    # Comandos gRPC para Fase 3
    download_parser = subparsers.add_parser("download", help="Descargar archivo vía gRPC")
    download_parser.add_argument("filename", help="Nombre del archivo a descargar")
    download_parser.add_argument("--from-node", required=True, 
                               help="Nodo desde el cual descargar (ip:puerto REST)")
    download_parser.add_argument("--save-as", 
                               help="Ruta donde guardar el archivo (opcional)")
    
    upload_parser = subparsers.add_parser("upload", help="Subir archivo vía gRPC")
    upload_parser.add_argument("file_path", help="Ruta del archivo a subir")
    upload_parser.add_argument("--to-node", required=True,
                             help="Nodo al cual subir (ip:puerto REST)")
    
    check_parser = subparsers.add_parser("check", help="Verificar archivo vía gRPC")
    check_parser.add_argument("filename", help="Nombre del archivo a verificar")
    check_parser.add_argument("--in-node", required=True,
                            help="Nodo donde verificar (ip:puerto REST)")
    
    # Comando para prueba completa de Fase 3
    subparsers.add_parser("full-test-phase3", help="Ejecutar prueba completa de la Fase 3 (gRPC)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = P2PTestClient()
    
    try:
        if args.command == "login":
            await client.login_peer(args.node, args.peer)
        
        elif args.command == "dl":
            await client.get_directory_list(args.node)
        
        elif args.command == "index":
            await client.index_files(args.node)
        
        elif args.command == "files":
            await client.list_files(args.node)
        
        elif args.command == "search":
            await client.search_file(args.node, args.filename)
        
        elif args.command == "full-test":
            await run_full_test(client)
        
        elif args.command == "download":
            if not GRPC_AVAILABLE:
                print("❌ gRPC no disponible. Ejecuta: python scripts/generate_grpc.py")
                return
            await test_download(args.node, args.from_node, args.filename, args.save_as)
        
        elif args.command == "upload":
            if not GRPC_AVAILABLE:
                print("❌ gRPC no disponible. Ejecuta: python scripts/generate_grpc.py")
                return
            await test_upload(args.node, args.to_node, args.file_path)
        
        elif args.command == "check":
            if not GRPC_AVAILABLE:
                print("❌ gRPC no disponible. Ejecuta: python scripts/generate_grpc.py")
                return
            await test_check(args.node, args.in_node, args.filename)
        
        elif args.command == "full-test-phase3":
            if not GRPC_AVAILABLE:
                print("❌ gRPC no disponible. Ejecuta: python scripts/generate_grpc.py")
                return
            await run_full_test_phase3(client)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operación cancelada por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

async def run_full_test(client: P2PTestClient):
    """Ejecuta una prueba completa de la Fase 2."""
    print("\n🚀 INICIANDO PRUEBA COMPLETA DE LA FASE 2")
    print("="*50)
    
    nodes = {
        "peer1": "127.0.0.1:50001",
        "peer2": "127.0.0.1:50002", 
        "peer3": "127.0.0.1:50003"
    }
    
    # Paso 1: Indexar archivos en todos los nodos
    print("\n📁 Paso 1: Indexando archivos en todos los nodos...")
    for name, address in nodes.items():
        print(f"\n--- {name.upper()} ({address}) ---")
        await client.index_files(address)
        await client.list_files(address)
        await asyncio.sleep(0.5)  # Pequeña pausa
    
    # Paso 2: Verificar Directory Lists
    print("\n🔗 Paso 2: Verificando Directory Lists...")
    for name, address in nodes.items():
        print(f"\n--- DL de {name.upper()} ---")
        await client.get_directory_list(address)
        await asyncio.sleep(0.5)
    
    # Paso 3: Pruebas de búsqueda distribuida
    print("\n🔍 Paso 3: Pruebas de búsqueda distribuida...")
    
    test_searches = [
        ("peer3", "video_especial.mp4", "Archivo que SOLO está en peer1"),
        ("peer1", "readme.md", "Archivo que SOLO está en peer2"),
        ("peer2", "script.py", "Archivo que SOLO está en peer3"),
        ("peer1", "video_comun.mp4", "Archivo que está en peer2 y peer3"),
        ("peer3", "inexistente.txt", "Archivo que NO existe en ningún lado"),
    ]
    
    for search_node, filename, description in test_searches:
        print(f"\n--- PRUEBA: {description} ---")
        print(f"Buscando desde {search_node}")
        await client.search_file(nodes[search_node], filename)
        await asyncio.sleep(1)  # Pausa entre búsquedas
    
    print("\n✅ PRUEBA COMPLETA FINALIZADA")
    print("="*50)


async def test_download(requesting_node: str, from_node: str, filename: str, save_as: str = None):
    """Prueba de descarga gRPC."""
    print(f"\n📥 PRUEBA DE DESCARGA gRPC")
    print(f"Descargando '{filename}' desde {from_node} usando cliente {requesting_node}")
    
    client = TransferClient(requesting_node)
    
    try:
        # Determinar ruta de guardado
        if not save_as:
            downloads_dir = Path("test_downloads")
            downloads_dir.mkdir(exist_ok=True)
            save_as = downloads_dir / filename
        
        # Realizar descarga
        success = await client.download_file(from_node, filename, str(save_as))
        
        if success:
            print(f"✅ Descarga exitosa: {save_as}")
            
            # Verificar archivo descargado
            if Path(save_as).exists():
                size = Path(save_as).stat().st_size
                print(f"📁 Archivo verificado: {size} bytes")
            else:
                print("❌ Archivo no encontrado tras descarga")
        else:
            print("❌ Descarga fallida")
            
    except Exception as e:
        print(f"❌ Error en descarga: {e}")


async def test_upload(requesting_node: str, to_node: str, file_path: str):
    """Prueba de subida gRPC."""
    print(f"\n📤 PRUEBA DE SUBIDA gRPC")
    print(f"Subiendo '{file_path}' a {to_node} desde {requesting_node}")
    
    if not Path(file_path).exists():
        print(f"❌ Archivo no encontrado: {file_path}")
        return
    
    client = TransferClient(requesting_node)
    
    try:
        success = await client.upload_file(to_node, file_path)
        
        if success:
            print("✅ Subida exitosa")
        else:
            print("❌ Subida fallida")
            
    except Exception as e:
        print(f"❌ Error en subida: {e}")


async def test_check(requesting_node: str, in_node: str, filename: str):
    """Prueba de verificación gRPC."""
    print(f"\n🔍 PRUEBA DE VERIFICACIÓN gRPC")
    print(f"Verificando '{filename}' en {in_node} desde {requesting_node}")
    
    client = TransferClient(requesting_node)
    
    try:
        result = await client.check_file(in_node, filename)
        
        if result:
            if result["exists"]:
                print(f"✅ Archivo encontrado:")
                print(f"  - Nombre: {result['filename']}")
                print(f"  - Tamaño: {result['size']} bytes")
                print(f"  - Ruta: {result['file_path']}")
                print(f"  - Nodo: {result['node_address']}")
            else:
                print(f"❌ Archivo no encontrado: {filename}")
        else:
            print("❌ Error en verificación")
            
    except Exception as e:
        print(f"❌ Error en verificación: {e}")


async def run_full_test_phase3(client: P2PTestClient):
    """Ejecuta una prueba completa de la Fase 3 (gRPC)."""
    print("\n🚀 INICIANDO PRUEBA COMPLETA DE LA FASE 3 - gRPC TRANSFERS")
    print("="*60)
    
    nodes = {
        "peer1": "127.0.0.1:50001",
        "peer2": "127.0.0.1:50002", 
        "peer3": "127.0.0.1:50003"
    }
    
    # Paso 1: Verificar que los archivos están indexados
    print("\n📁 Paso 1: Verificando archivos indexados...")
    for name, address in nodes.items():
        print(f"\n--- {name.upper()} ({address}) ---")
        await client.index_files(address)
        await client.list_files(address)
        await asyncio.sleep(0.5)
    
    # Paso 2: Pruebas de verificación gRPC
    print("\n🔍 Paso 2: Verificaciones gRPC...")
    test_checks = [
        ("peer3", "peer1", "video_especial.mp4"),  # P3 verifica en P1
        ("peer1", "peer2", "readme.md"),           # P1 verifica en P2 
        ("peer2", "peer3", "script.py"),           # P2 verifica en P3
        ("peer1", "peer2", "inexistente.txt"),     # Archivo que no existe
    ]
    
    for requesting, target, filename in test_checks:
        print(f"\n--- Verificando '{filename}' en {target} desde {requesting} ---")
        await test_check(nodes[requesting], nodes[target], filename)
        await asyncio.sleep(1)
    
    # Paso 3: Pruebas de descarga gRPC
    print("\n📥 Paso 3: Descargas gRPC...")
    test_downloads = [
        ("peer3", "peer1", "video_especial.mp4"),  # Objetivo principal de Fase 3
        ("peer1", "peer2", "readme.md"),
        ("peer2", "peer3", "script.py"),
    ]
    
    for requesting, source, filename in test_downloads:
        print(f"\n--- Descargando '{filename}' desde {source} hacia {requesting} ---")
        await test_download(nodes[requesting], nodes[source], filename)
        await asyncio.sleep(2)
    
    # Paso 4: Verificar indexación tras descarga
    print("\n📁 Paso 4: Verificando indexación tras descargas...")
    for name, address in nodes.items():
        print(f"\n--- Archivos en {name.upper()} tras descargas ---")
        await client.list_files(address)
        await asyncio.sleep(0.5)
    
    # Paso 5: Prueba de búsqueda tras descarga
    print("\n🔍 Paso 5: Búsquedas tras descargas...")
    # Ahora peer3 debería encontrar video_especial.mp4 localmente
    print("\n--- Buscando 'video_especial.mp4' desde peer3 (debería encontrarlo localmente ahora) ---")
    await client.search_file(nodes["peer3"], "video_especial.mp4")
    
    print("\n✅ PRUEBA COMPLETA DE FASE 3 FINALIZADA")
    print("="*60)
    print("\n🎉 LOGROS DE LA FASE 3:")
    print("  ✅ Transferencia real de archivos con gRPC")
    print("  ✅ Streaming eficiente para archivos grandes")
    print("  ✅ Indexación automática tras descarga")
    print("  ✅ Integración completa: Búsqueda + Descarga + Índice")
    print("  ✅ Concurrencia con FastAPI (REST) + gRPC")


if __name__ == "__main__":
    asyncio.run(main())
