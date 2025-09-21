from fastapi import APIRouter
from typing import Dict, Any
import logging

from services.directory_simple.service import login_from, get_random_addresses, get_all, buscar_flooding

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/directory", tags=["directory_simple"])


@router.post("/login")
async def login(payload: Dict[str, str]):
    """
    Registra (loguea) un nuevo nodo en la DL local. El payload debe contener:
    { "address": "ip:port" }
    Retorna la DL local completa (máximo 3 direcciones).
    """
    address = payload.get("address", "") if isinstance(payload, dict) else ""
    if not address:
        return {"success": False, "error": "address requerido"}
    dl = login_from(address)
    return {"success": True, "dl": dl}


@router.get("/dl")
async def get_dl():
    """Devuelve hasta 2 direcciones aleatorias de la DL local."""
    return {"success": True, "dl": get_random_addresses(2)}


@router.get("/dl/all")
async def get_dl_all():
    """Devuelve la DL completa (máximo 3 direcciones)."""
    return {"success": True, "dl": get_all()}


@router.post("/search")
async def search_file(payload: Dict[str, Any]):
    """
    Busca un archivo en la red P2P usando flooding con TTL.
    Payload:
    {
        "filename": "nombre_archivo",
        "query_id": "uuid_opcional",  # Para búsquedas propagadas
        "ttl": 3,  # TTL opcional, por defecto 3
        "source_address": "ip:puerto"  # Para búsquedas propagadas
    }
    """
    filename = payload.get("filename", "")
    if not filename:
        return {"success": False, "error": "filename requerido"}
    
    query_id = payload.get("query_id")  # None para búsquedas iniciadas aquí
    ttl = payload.get("ttl", 3)
    source_address = payload.get("source_address")
    
    logger.info(f"Recibida búsqueda de '{filename}' con queryID {query_id}, TTL {ttl}")
    
    try:
        resultados = await buscar_flooding(filename, query_id, ttl, source_address)
        logger.info(f"Búsqueda de '{filename}' completada: {len(resultados)} resultado(s)")
        
        return {
            "success": True, 
            "results": resultados,
            "query_id": query_id,
            "total_results": len(resultados)
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda de '{filename}': {e}")
        return {"success": False, "error": str(e)}


@router.get("/search/simple/{filename}")
async def search_file_simple(filename: str):
    """
    Endpoint simplificado para iniciar una búsqueda desde este nodo.
    """
    logger.info(f"Búsqueda simplificada de '{filename}'")
    
    try:
        resultados = await buscar_flooding(filename)
        logger.info(f"Búsqueda simplificada de '{filename}' completada: {len(resultados)} resultado(s)")
        
        return {
            "success": True, 
            "results": resultados,
            "total_results": len(resultados)
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda simplificada de '{filename}': {e}")
        return {"success": False, "error": str(e)}
