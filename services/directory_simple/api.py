from fastapi import APIRouter
from typing import Dict

from services.directory_simple.service import login_from, get_random_addresses, get_all

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
