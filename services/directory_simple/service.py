from typing import List, Optional, Dict, Any
import random
import asyncio
import uuid
import time
import logging
from services.http_client import http_client
from services.file_simple.service import listar_archivos

logger = logging.getLogger(__name__)

# Directorio en memoria por proceso (un proceso = un nodo)
_DL: List[str] = []  # direcciones como "ip:port"
_SELF: Optional[str] = None

# QuerySet para evitar redundancia en búsquedas (máximo 5 queryIDs)
_QUERY_SET: List[str] = []  # Almacena queryIDs ya procesados
_MAX_QUERY_SET_SIZE = 5


def set_self_address(address: str) -> None:
    """Configura la dirección propia del nodo y la asegura en la DL."""
    global _SELF
    _SELF = address
    _ensure_in_dl(address)


def _ensure_in_dl(address: str) -> None:
    if address not in _DL:
        _DL.append(address)
    _enforce_max_size()


def _enforce_max_size() -> None:
    # Máximo 3 direcciones, la propia debe permanecer siempre
    global _DL
    if len(_DL) <= 3:
        return
    # Mantener SELF y recortar las demás (mantener las 2 más recientes después de SELF)
    if _SELF in _DL:
        others = [a for a in _DL if a != _SELF]
        others = others[-2:]
        _DL = [_SELF] + others
    else:
        _DL = _DL[-3:]


def login_from(new_address: str) -> List[str]:
    """Agrega la dirección del nuevo nodo a la DL local y retorna la DL local.
    La DL siempre contendrá al menos la dirección propia.
    """
    _ensure_in_dl(new_address)
    if _SELF is not None:
        _ensure_in_dl(_SELF)
    return list(_DL)


def get_random_addresses(limit: int = 2) -> List[str]:
    """Devuelve hasta 'limit' direcciones random de la DL.
    Si existe la propia, puede estar incluida.
    """
    if limit <= 0:
        return []
    return random.sample(_DL, k=min(limit, len(_DL)))


def get_all() -> List[str]:
    return list(_DL)


def _add_to_query_set(query_id: str) -> None:
    """Agrega un queryID al conjunto, manteniendo máximo 5 elementos."""
    global _QUERY_SET
    if query_id not in _QUERY_SET:
        _QUERY_SET.append(query_id)
        # Mantener solo los últimos 5
        if len(_QUERY_SET) > _MAX_QUERY_SET_SIZE:
            _QUERY_SET = _QUERY_SET[-_MAX_QUERY_SET_SIZE:]
        logger.debug(f"QueryID {query_id} agregado al query set. Set actual: {_QUERY_SET}")


def _is_query_processed(query_id: str) -> bool:
    """Verifica si un queryID ya fue procesado."""
    return query_id in _QUERY_SET


def _search_local(filename: str) -> List[Dict[str, Any]]:
    """Busca un archivo en el índice local del nodo."""
    archivos = listar_archivos()
    resultados = []
    
    for archivo in archivos:
        if filename.lower() in archivo.get("filename", "").lower():
            resultados.append({
                "filename": archivo["filename"],
                "path": archivo["path"],
                "size": archivo["size"],
                "node_address": _SELF
            })
    
    logger.debug(f"Búsqueda local de '{filename}': {len(resultados)} resultado(s)")
    return resultados


async def buscar_flooding(
    filename: str, 
    query_id: str = None, 
    ttl: int = 3, 
    source_address: str = None
) -> List[Dict[str, Any]]:
    """Busca un archivo usando flooding con TTL.
    
    Args:
        filename: Nombre del archivo a buscar
        query_id: ID único de la consulta (se genera si no se proporciona)
        ttl: Time To Live para la propagación
        source_address: Dirección del nodo que originó la búsqueda
    
    Returns:
        Lista de resultados encontrados
    """
    # Generar query_id si no se proporciona (búsqueda iniciada en este nodo)
    if query_id is None:
        query_id = str(uuid.uuid4())
        source_address = _SELF
        logger.info(f"Iniciando búsqueda de '{filename}' con queryID {query_id}")
    
    # Verificar si ya procesamos esta consulta
    if _is_query_processed(query_id):
        logger.debug(f"QueryID {query_id} ya procesado, ignorando")
        return []
    
    # Marcar como procesado
    _add_to_query_set(query_id)
    
    # Buscar localmente
    resultados_locales = _search_local(filename)
    
    # Si TTL > 0, propagar a vecinos
    resultados_remotos = []
    if ttl > 0:
        logger.debug(f"Propagando búsqueda queryID {query_id} con TTL {ttl}")
        resultados_remotos = await _flood_search(filename, query_id, ttl - 1, source_address)
    
    # Combinar resultados
    todos_resultados = resultados_locales + resultados_remotos
    logger.info(f"Búsqueda queryID {query_id} completada: {len(todos_resultados)} resultado(s)")
    
    return todos_resultados


async def _flood_search(
    filename: str, 
    query_id: str, 
    ttl: int, 
    source_address: str
) -> List[Dict[str, Any]]:
    """Propaga la búsqueda a los nodos vecinos."""
    if ttl <= 0:
        return []
    
    # Obtener vecinos (excluyendo la dirección propia y la fuente)
    vecinos = [addr for addr in _DL if addr != _SELF and addr != source_address]
    
    if not vecinos:
        logger.debug("No hay vecinos para propagar la búsqueda")
        return []
    
    logger.debug(f"Propagando a {len(vecinos)} vecino(s): {vecinos}")
    
    # Crear tareas para propagar en paralelo
    tareas = []
    for vecino in vecinos:
        tarea = _send_search_to_node(vecino, filename, query_id, ttl, source_address)
        tareas.append(tarea)
    
    # Ejecutar en paralelo y recopilar resultados
    resultados = await asyncio.gather(*tareas, return_exceptions=True)
    
    # Procesar resultados
    todos_resultados = []
    for i, resultado in enumerate(resultados):
        if isinstance(resultado, Exception):
            logger.error(f"Error propagando a {vecinos[i]}: {resultado}")
        elif isinstance(resultado, list):
            todos_resultados.extend(resultado)
    
    return todos_resultados


async def _send_search_to_node(
    node_address: str, 
    filename: str, 
    query_id: str, 
    ttl: int, 
    source_address: str
) -> List[Dict[str, Any]]:
    """Envía una búsqueda a un nodo específico."""
    url = f"http://{node_address}/directory/search"
    data = {
        "filename": filename,
        "query_id": query_id,
        "ttl": ttl,
        "source_address": source_address
    }
    
    logger.debug(f"Enviando búsqueda a {node_address}: {data}")
    
    try:
        response = await http_client.post_json(url, data)
        
        if response and response.get("success"):
            resultados = response.get("results", [])
            logger.debug(f"Nodo {node_address} retornó {len(resultados)} resultado(s)")
            return resultados
        else:
            logger.warning(f"Nodo {node_address} retornó respuesta inválida: {response}")
            return []
            
    except Exception as e:
        logger.error(f"Error enviando búsqueda a {node_address}: {e}")
        return []
