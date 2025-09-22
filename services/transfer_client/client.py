import os
from typing import Tuple, Iterator
import grpc
import transfer_pb2 as pb2
import transfer_pb2_grpc as pb2_grpc
from services.file_simple.service import get_base_directory

CHUNK_SIZE = 64 * 1024

def _ensure_base_dir() -> str:
    base = get_base_directory()
    if not base:
        raise RuntimeError("Base directory not set. Call set_base_directory() first.")
    os.makedirs(base, exist_ok=True)
    return base

def _iter_file_chunks(path: str) -> Iterator[pb2.FileChunk]:
    with open(path, "rb") as f:
        seq = 0
        while True:
            data = f.read(CHUNK_SIZE)
            if not data:
                break
            yield pb2.FileChunk(content=data, seq=seq)
            seq += 1

def download_file(grpc_address: str, filename: str) -> Tuple[bool, str]:
    """
    Descarga 'filename' desde un servidor gRPC Transfer en grpc_address y
    lo guarda en el directorio base del nodo.

    Retorna (ok, message)
    """
    base_dir = _ensure_base_dir()
    dest_path = os.path.join(base_dir, filename)
    os.makedirs(os.path.dirname(dest_path) or base_dir, exist_ok=True)

    with grpc.insecure_channel(grpc_address) as channel:
        stub = pb2_grpc.TransferStub(channel)
        try:
            stream = stub.Download(pb2.FileRequest(filename=filename))
            with open(dest_path, "wb") as out:
                for chunk in stream:
                    if chunk and chunk.content:
                        out.write(chunk.content)
            return True, f"Descargado en {dest_path}"
        except grpc.RpcError as e:
            return False, f"gRPC error: {e.code().name} {e.details()}"
        except Exception as e:
            return False, str(e)

def upload_file(grpc_address: str, filename: str) -> Tuple[bool, str]:
    """
    Sube 'filename' desde el directorio base del nodo a un servidor gRPC Transfer en grpc_address.

    Retorna (ok, message)
    """
    base_dir = _ensure_base_dir()
    src_path = os.path.join(base_dir, filename)
    if not os.path.isfile(src_path):
        return False, f"Archivo no existe: {src_path}"

    with grpc.insecure_channel(grpc_address) as channel:
        stub = pb2_grpc.TransferStub(channel)
        try:
            # Enviar stream de chunks con metadata para filename destino
            response = stub.Upload(_iter_file_chunks(src_path), metadata=(("filename", filename),))
            return bool(response.ok), response.message or ("ok" if response.ok else "error")
        except grpc.RpcError as e:
            return False, f"gRPC error: {e.code().name} {e.details()}"
        except Exception as e:
            return False, str(e)