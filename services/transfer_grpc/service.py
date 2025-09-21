"""
Transfer Service - Implementación del servicio gRPC para transferencia de archivos P2P.
Maneja upload, download y verificación de archivos entre nodos.
"""
import os
import logging
import asyncio
from typing import Iterator, Optional
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

# Configuración global
_BASE_DIRECTORY: Optional[str] = None
_DOWNLOAD_DIRECTORY: Optional[str] = None
_CHUNK_SIZE = 64 * 1024  # 64KB por chunk

def set_directories(base_dir: str, download_dir: str = None):
    """Configura los directorios base para archivos."""
    global _BASE_DIRECTORY, _DOWNLOAD_DIRECTORY
    _BASE_DIRECTORY = base_dir
    _DOWNLOAD_DIRECTORY = download_dir or os.path.join(base_dir, "downloads")
    
    # Crear directorio de descargas si no existe
    Path(_DOWNLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)
    logger.info(f"Configurados directorios - Base: {_BASE_DIRECTORY}, Downloads: {_DOWNLOAD_DIRECTORY}")

class TransferServiceImpl(transfer_pb2_grpc.TransferServiceServicer if transfer_pb2_grpc else object):
    """Implementación del servicio de transferencia gRPC."""
    
    def __init__(self, node_address: str):
        self.node_address = node_address
        logger.info(f"Transfer Service inicializado para nodo {node_address}")
    
    async def Download(self, request, context) -> Iterator:
        """Descarga un archivo del nodo local y lo envía por streaming."""
        if not transfer_pb2:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("gRPC code not generated. Run generate_grpc.py first.")
            return
        
        filename = request.filename
        requesting_node = request.requesting_node
        
        logger.info(f"📥 Download solicitado: '{filename}' por {requesting_node}")
        
        # Buscar archivo en el directorio base
        file_path = self._find_file(filename)
        
        if not file_path:
            logger.warning(f"❌ Archivo '{filename}' no encontrado")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"File '{filename}' not found")
            return
        
        try:
            file_size = os.path.getsize(file_path)
            logger.info(f"📂 Enviando archivo: {file_path} ({file_size} bytes)")
            
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
                        requesting_node=requesting_node
                    )
                    
                    logger.debug(f"📤 Enviando chunk {chunk_number} ({len(chunk_data)} bytes)")
                    yield chunk
                    
                    if is_last:
                        break
            
            logger.info(f"✅ Download completado: '{filename}' ({chunk_number} chunks)")
            
        except Exception as e:
            logger.error(f"❌ Error en download de '{filename}': {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error reading file: {str(e)}")
    
    async def Upload(self, request_iterator, context):
        """Recibe un archivo por streaming y lo guarda localmente."""
        if not transfer_pb2:
            return transfer_pb2.TransferResponse(
                success=False,
                message="gRPC code not generated"
            )
        
        filename = None
        file_path = None
        total_size = 0
        bytes_received = 0
        chunks_received = 0
        
        try:
            file_handle = None
            
            async for chunk in request_iterator:
                if filename is None:
                    filename = chunk.filename
                    total_size = chunk.total_size
                    file_path = os.path.join(_DOWNLOAD_DIRECTORY, filename)
                    
                    logger.info(f"📥 Upload iniciado: '{filename}' ({total_size} bytes) desde {chunk.requesting_node}")
                    
                    # Abrir archivo para escritura
                    file_handle = open(file_path, 'wb')
                
                # Escribir datos del chunk
                file_handle.write(chunk.data)
                bytes_received += len(chunk.data)
                chunks_received += 1
                
                logger.debug(f"📥 Recibido chunk {chunk.chunk_number} ({len(chunk.data)} bytes)")
                
                if chunk.is_last_chunk:
                    break
            
            if file_handle:
                file_handle.close()
            
            logger.info(f"✅ Upload completado: '{filename}' ({chunks_received} chunks, {bytes_received} bytes)")
            
            # Indexar archivo recién recibido
            if indexar_archivo_descargado:
                try:
                    if indexar_archivo_descargado(file_path):
                        logger.info(f"📁 Archivo indexado automáticamente: {filename}")
                    else:
                        logger.warning(f"⚠️  No se pudo indexar: {filename}")
                except Exception as e:
                    logger.error(f"❌ Error indexando {filename}: {e}")
            
            return transfer_pb2.TransferResponse(
                success=True,
                message=f"File '{filename}' uploaded successfully and indexed",
                bytes_transferred=bytes_received,
                file_path=file_path
            )
            
        except Exception as e:
            logger.error(f"❌ Error en upload: {e}")
            
            # Limpiar archivo parcial
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"🗑️  Archivo parcial eliminado: {file_path}")
                except:
                    pass
            
            return transfer_pb2.TransferResponse(
                success=False,
                message=f"Upload failed: {str(e)}",
                bytes_transferred=bytes_received
            )
    
    async def CheckFile(self, request, context):
        """Verifica si un archivo existe en el nodo local."""
        if not transfer_pb2:
            return transfer_pb2.FileInfo(exists=False, message="gRPC code not generated")
        
        filename = request.filename
        logger.debug(f"🔍 Verificando archivo: '{filename}'")
        
        file_path = self._find_file(filename)
        
        if file_path:
            try:
                size = os.path.getsize(file_path)
                logger.debug(f"✓ Archivo encontrado: {file_path} ({size} bytes)")
                
                return transfer_pb2.FileInfo(
                    exists=True,
                    filename=filename,
                    size=size,
                    file_path=file_path,
                    node_address=self.node_address
                )
            except Exception as e:
                logger.warning(f"⚠️  Error obteniendo info de '{filename}': {e}")
        
        logger.debug(f"❌ Archivo no encontrado: '{filename}'")
        return transfer_pb2.FileInfo(
            exists=False,
            filename=filename,
            node_address=self.node_address
        )
    
    def _find_file(self, filename: str) -> Optional[str]:
        """Busca un archivo en el directorio base."""
        if not _BASE_DIRECTORY:
            logger.error("Base directory not configured")
            return None
        
        # Buscar archivo recursivamente
        for root, dirs, files in os.walk(_BASE_DIRECTORY):
            if filename in files:
                return os.path.join(root, filename)
        
        return None

# Instancia global del servicio
_transfer_service: Optional[TransferServiceImpl] = None

def get_transfer_service(node_address: str = None) -> TransferServiceImpl:
    """Obtiene la instancia del Transfer Service."""
    global _transfer_service
    if _transfer_service is None:
        if not node_address:
            raise ValueError("node_address required for first initialization")
        _transfer_service = TransferServiceImpl(node_address)
    return _transfer_service

async def start_grpc_server(host: str, port: int, node_address: str) -> aio.Server:
    """Inicia el servidor gRPC."""
    if not transfer_pb2_grpc:
        raise RuntimeError("gRPC code not generated. Run generate_grpc.py first.")
    
    server = aio.server()
    
    # Agregar servicio
    transfer_service = get_transfer_service(node_address)
    transfer_pb2_grpc.add_TransferServiceServicer_to_server(transfer_service, server)
    
    # Configurar puerto
    listen_addr = f"{host}:{port}"
    server.add_insecure_port(listen_addr)
    
    logger.info(f"🚀 Iniciando servidor gRPC en {listen_addr}")
    await server.start()
    
    return server
