from fastapi import APIRouter
from typing import Dict

from services.directory_simple.service import (
    login_from,
    start_search,
    handle_query,
    join_with,
)

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

@router.post("/search")
async def search(payload: Dict[str, object]):
    """
    Inicia una búsqueda floodeada con TTL (default 3).
    Body: { "filename": "...", "ttl": 3 }
    Retorna: { found: bool, owner_id?: str, address?: str }
    """
    filename = ""
    ttl = 3
    if isinstance(payload, dict):
        filename = str(payload.get("filename", "") or "")
        try:
            ttl = int(payload.get("ttl", 3))
        except Exception:
            ttl = 3
    if not filename:
        return {"success": False, "error": "filename requerido"}
    result = start_search(filename, ttl)
    return {"success": True, **result}

@router.post("/query")
async def relay_query(payload: Dict[str, object]):
    """
    Maneja una consulta de búsqueda recibida desde otro nodo.
    Body: { "query_id": str, "filename": str, "ttl": int, "origin": "ip:port" }
    Retorna: { found: bool, owner_id?: str, address?: str }
    """
    if not isinstance(payload, dict):
        return {"success": False, "error": "payload inválido"}
    qid = str(payload.get("query_id", "") or "")
    filename = str(payload.get("filename", "") or "")
    try:
        ttl = int(payload.get("ttl", 0))
    except Exception:
        ttl = 0
    origin = payload.get("origin")
    if not qid or not filename:
        return {"success": False, "error": "query_id y filename requeridos"}
    result = handle_query(qid, filename, ttl, origin if isinstance(origin, str) else None)
    return {"success": True, **result}

@router.post("/join")
async def join(payload: Dict[str, str]):
    """
    Hace que ESTE nodo se una a la red a través de un "target" (ip:port):
    1) Realiza un login remoto contra target (enviando nuestra dirección propia ya configurada)
    2) Recibe la DL que devuelve el target
    3) Siembra la DL local de este nodo con esa DL
    Body: { "target": "ip:port" }
    """
    target = payload.get("target", "") if isinstance(payload, dict) else ""
    if not target:
        return {"success": False, "error": "target requerido"}
    resp = join_with(target)
    return resp