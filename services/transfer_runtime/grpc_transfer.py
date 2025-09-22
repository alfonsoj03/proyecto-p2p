import os
import threading
from concurrent import futures
from typing import Iterator
import grpc
import transfer_pb2 as pb2
import transfer_pb2_grpc as pb2_grpc

CHUNK_SIZE = 64 * 1024  # 64KB

## Implementaciones de los métodos del servicio gRPC.
class TransferService(pb2_grpc.TransferServicer):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def Download(self, request: pb2.FileRequest, context) -> Iterator[pb2.FileChunk]:
        filename = request.filename or ""
        if not filename:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "filename requerido")
        file_path = os.path.join(self.base_dir, filename)
        if not os.path.isfile(file_path):
            context.abort(grpc.StatusCode.NOT_FOUND, f"archivo no encontrado: {filename}")
        seq = 0
        with open(file_path, "rb") as f:
            while True:
                data = f.read(CHUNK_SIZE)
                if not data:
                    break
                yield pb2.FileChunk(content=data, seq=seq)
                seq += 1

    def Upload(self, request_iterator: Iterator[pb2.FileChunk], context) -> pb2.UploadResponse:
        # filename llega por metadata del contexto
        md = dict(context.invocation_metadata() or [])
        filename = md.get("filename", "")
        if not filename:
            return pb2.UploadResponse(ok=False, message="filename metadata requerido")
        dest_path = os.path.join(self.base_dir, filename)
        os.makedirs(os.path.dirname(dest_path) or self.base_dir, exist_ok=True)
        try:
            with open(dest_path, "wb") as f:
                for chunk in request_iterator:
                    if not isinstance(chunk, pb2.FileChunk):
                        continue
                    if chunk.content:
                        f.write(chunk.content)
            return pb2.UploadResponse(ok=True, message="ok")
        except Exception as e:
            return pb2.UploadResponse(ok=False, message=str(e))

def start_grpc_server(base_dir: str, port: int) -> threading.Thread:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    pb2_grpc.add_TransferServicer_to_server(TransferService(base_dir), server)
    server.add_insecure_port(f"[::]:{int(port)}")
    server.start()

    t = threading.Thread(target=server.wait_for_termination, daemon=True)
    t.start()
    return t