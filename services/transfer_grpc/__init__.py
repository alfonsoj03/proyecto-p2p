"""
Transfer gRPC module - Servicios de transferencia de archivos P2P usando gRPC.

Este módulo maneja la transferencia real de archivos entre nodos P2P usando
el protocolo gRPC con streaming para eficiencia en archivos grandes.

Componentes:
- service.py: Implementación del servidor gRPC
- client.py: Cliente gRPC para comunicación
- transfer_pb2.py: Mensajes de protobuf (generado)
- transfer_pb2_grpc.py: Servicios gRPC (generado)
"""

# Verificar si el código gRPC fue generado
try:
    from . import transfer_pb2
    from . import transfer_pb2_grpc
    GRPC_GENERATED = True
except ImportError:
    GRPC_GENERATED = False

from .service import TransferServiceImpl, get_transfer_service, start_grpc_server, set_directories
from .client import TransferClient, get_transfer_client

__all__ = [
    'TransferServiceImpl',
    'TransferClient', 
    'get_transfer_service',
    'get_transfer_client',
    'start_grpc_server',
    'set_directories',
    'GRPC_GENERATED'
]
