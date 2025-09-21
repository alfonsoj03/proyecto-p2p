"""
Transfer Client - Cliente gRPC para transferencia de archivos entre nodos P2P.
"""
import os
import asyncio
import logging
from typing import Optional, AsyncIterator
from pathlib import Path

import grpc
from grpc import aio

# Importaciones que se generarán desde .proto
try:
    from . import transfer_pb2
    from . import transfer_pb2_grpc
except ImportError:
    # Fallback para cuando los archivos no estén generados aún
    transfer_pb2 = None
    transfer_pb2_grpc = None

# Importar File Service para indexar tras downloads
try:
    from services.file_simple.service import indexar_archivo_descargado
except ImportError:
    indexar_archivo_descargado = None

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 64 * 1024  # 64KB por chunk

class TransferClient:
    """Cliente para comunicación gRPC con otros nodos."""
    
    def __init__(self, node_address: str, timeout: int = 30):
        self.node_address = node_address
        self.timeout = timeout
        
    async def download_file(self, target_node: str, filename: str, save_path: str = None) -> bool:
        """Descarga un archivo de un nodo remoto."""
        if not transfer_pb2:
            logger.error("gRPC code not generated. Run generate_grpc.py first.")
            return False
        
        # Extraer host y puerto gRPC del target_node
        grpc_address = self._get_grpc_address(target_node)
        
        logger.info(f"📥 Descargando '{filename}' desde {grpc_address}")
        
        try:
            # Conectar al nodo remoto
            async with aio.insecure_channel(grpc_address) as channel:
                stub = transfer_pb2_grpc.TransferServiceStub(channel)
                
                # Crear solicitud
                request = transfer_pb2.FileRequest(
                    filename=filename,
                    requesting_node=self.node_address
                )
                
                # Llamar al método Download (streaming)
                download_stream = stub.Download(request, timeout=self.timeout)
                
                # Determinar ruta de guardado
                if not save_path:
                    downloads_dir = Path("downloads")
                    downloads_dir.mkdir(exist_ok=True)
                    save_path = downloads_dir / filename
                else:
                    save_path = Path(save_path)
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Recibir y escribir chunks
                total_bytes = 0
                chunks_received = 0
                
                with open(save_path, 'wb') as f:
                    async for chunk in download_stream:
                        f.write(chunk.data)
                        total_bytes += len(chunk.data)
                        chunks_received += 1
                        
                        logger.debug(f"📥 Recibido chunk {chunk.chunk_number} ({len(chunk.data)} bytes)")
                        
                        if chunk.is_last_chunk:
                            break
                
                logger.info(f"✅ Download completado: '{filename}' → {save_path} ({chunks_received} chunks, {total_bytes} bytes)")
                
                # Indexar archivo recién descargado
                if indexar_archivo_descargado:
                    try:
                        if indexar_archivo_descargado(str(save_path)):
                            logger.info(f"📁 Archivo descargado e indexado: {filename}")
                        else:
                            logger.warning(f"⚠️  Download exitoso pero no se pudo indexar: {filename}")
                    except Exception as e:
                        logger.error(f"❌ Error indexando {filename}: {e}")
                
                return True
                
        except grpc.RpcError as e:
            logger.error(f"❌ Error gRPC descargando '{filename}': {e.code()} - {e.details()}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado descargando '{filename}': {e}")
            return False
    
    async def upload_file(self, target_node: str, file_path: str) -> bool:
        """Sube un archivo a un nodo remoto."""
        if not transfer_pb2:
            logger.error("gRPC code not generated. Run generate_grpc.py first.")
            return False
        
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"❌ Archivo no encontrado: {file_path}")
            return False
        
        # Extraer host y puerto gRPC del target_node
        grpc_address = self._get_grpc_address(target_node)
        filename = file_path.name
        
        logger.info(f"📤 Subiendo '{filename}' a {grpc_address}")
        
        try:
            # Conectar al nodo remoto
            async with aio.insecure_channel(grpc_address) as channel:
                stub = transfer_pb2_grpc.TransferServiceStub(channel)
                
                # Generar chunks del archivo
                chunks = self._generate_chunks(file_path)
                
                # Llamar al método Upload (streaming)
                response = await stub.Upload(chunks, timeout=self.timeout)
                
                if response.success:
                    logger.info(f"✅ Upload completado: '{filename}' ({response.bytes_transferred} bytes)")
                    return True
                else:
                    logger.error(f"❌ Upload falló: {response.message}")
                    return False
                    
        except grpc.RpcError as e:
            logger.error(f"❌ Error gRPC subiendo '{filename}': {e.code()} - {e.details()}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado subiendo '{filename}': {e}")
            return False
    
    async def check_file(self, target_node: str, filename: str) -> Optional[dict]:
        """Verifica si un archivo existe en un nodo remoto."""
        if not transfer_pb2:
            logger.error("gRPC code not generated. Run generate_grpc.py first.")
            return None
        
        # Extraer host y puerto gRPC del target_node
        grpc_address = self._get_grpc_address(target_node)
        
        logger.debug(f"🔍 Verificando '{filename}' en {grpc_address}")
        
        try:
            # Conectar al nodo remoto
            async with aio.insecure_channel(grpc_address) as channel:
                stub = transfer_pb2_grpc.TransferServiceStub(channel)
                
                # Crear solicitud
                request = transfer_pb2.FileRequest(
                    filename=filename,
                    requesting_node=self.node_address
                )
                
                # Llamar al método CheckFile
                response = await stub.CheckFile(request, timeout=5)
                
                result = {
                    "exists": response.exists,
                    "filename": response.filename,
                    "size": response.size if response.exists else 0,
                    "file_path": response.file_path if response.exists else "",
                    "node_address": response.node_address
                }
                
                if response.exists:
                    logger.debug(f"✓ Archivo '{filename}' existe en {grpc_address} ({response.size} bytes)")
                else:
                    logger.debug(f"❌ Archivo '{filename}' no existe en {grpc_address}")
                
                return result
                
        except grpc.RpcError as e:
            logger.error(f"❌ Error gRPC verificando '{filename}': {e.code()} - {e.details()}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado verificando '{filename}': {e}")
            return None
    
    async def _generate_chunks(self, file_path: Path) -> AsyncIterator:
        """Genera chunks de un archivo para streaming."""
        filename = file_path.name
        file_size = file_path.stat().st_size
        
        chunk_number = 0
        
        with open(file_path, 'rb') as f:
            while True:
                chunk_data = f.read(_CHUNK_SIZE)
                if not chunk_data:
                    break
                
                chunk_number += 1
                is_last = len(chunk_data) < _CHUNK_SIZE
                
                chunk = transfer_pb2.FileChunk(
                    filename=filename,
                    data=chunk_data,
                    chunk_number=chunk_number,
                    total_size=file_size,
                    is_last_chunk=is_last,
                    requesting_node=self.node_address
                )
                
                logger.debug(f"📤 Generando chunk {chunk_number} ({len(chunk_data)} bytes)")
                yield chunk
                
                if is_last:
                    break
    
    def _get_grpc_address(self, rest_address: str) -> str:
        """Convierte dirección REST a dirección gRPC."""
        # Asumiendo que el puerto gRPC es REST_PORT + 1000
        # Por ejemplo: 127.0.0.1:50001 → 127.0.0.1:51001
        
        if ":" in rest_address:
            host, port_str = rest_address.split(":", 1)
            rest_port = int(port_str)
            grpc_port = rest_port + 1000
            return f"{host}:{grpc_port}"
        else:
            # Solo host, usar puerto por defecto
            return f"{rest_address}:51001"

# Cliente global para reutilizar
_transfer_client: Optional[TransferClient] = None

def get_transfer_client(node_address: str = None) -> TransferClient:
    """Obtiene la instancia del Transfer Client."""
    global _transfer_client
    if _transfer_client is None:
        if not node_address:
            raise ValueError("node_address required for first initialization")
        _transfer_client = TransferClient(node_address)
    return _transfer_client
