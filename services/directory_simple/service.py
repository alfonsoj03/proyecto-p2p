from typing import List, Optional, Tuple, Deque, Dict
from collections import deque
import random
import json
import urllib.request
from services.file_simple.service import listar_archivos
import uuid

# Directorio en memoria por proceso (un proceso = un nodo)
_DL: List[str] = []  # direcciones como "ip:port"
_SELF_ADDR: Optional[str] = None
_SELF_ID: Optional[str] = None

# Historial simple de queries para deduplicar (guardar últimos 5)
_QUERY_HISTORY: Deque[str] = deque(maxlen=5)

def set_self_address(address: str) -> None:
    """Configura la dirección propia del nodo y la asegura en la DL."""
    global _SELF_ADDR
    _SELF_ADDR = address
    _ensure_in_dl(address)

def set_self_info(peer_id: str, address: str) -> None:
    """Configura id y dirección propia."""
    global _SELF_ID
    _SELF_ID = peer_id
    set_self_address(address)

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
    if _SELF_ADDR in _DL:
        others = [a for a in _DL if a != _SELF_ADDR]
        others = others[-2:]
        _DL = [_SELF_ADDR] + others
    else:
        _DL = _DL[-3:]

def login_from(new_address: str) -> List[str]:
    """Agrega la dirección del nuevo nodo a la DL local y retorna la DL local.
    La DL siempre contendrá al menos la dirección propia.
    """
    _ensure_in_dl(new_address)
    if _SELF_ADDR is not None:
        _ensure_in_dl(_SELF_ADDR)
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

def _has_file(filename: str) -> bool:
    try:
        for entry in listar_archivos():
            if entry.get("filename") == filename:
                return True
    except Exception:
        pass
    return False

def _post_json(url: str, payload: Dict, timeout: int = 6) -> Tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

def start_search(filename: str, ttl: int = 3) -> Dict:
    """Inicia una búsqueda floodeada con TTL entre vecinos de la DL.
    Retorna dict con found(bool), owner_id(str), address(str) si se encuentra.
    """
    qid = str(uuid.uuid4())
    # Tratar local primero
    if _has_file(filename):
        return {"found": True, "owner_id": _SELF_ID or "", "address": _SELF_ADDR or ""}

    # Propagar a vecinos
    for addr in list(_DL):
        try:
            url = f"http://{addr}/directory/query"
            st, txt = _post_json(url, {"query_id": qid, "filename": filename, "ttl": ttl - 1, "origin": _SELF_ADDR})
            if st == 200:
                resp = json.loads(txt)
                if resp.get("found"):
                    return resp
        except Exception:
            continue
    return {"found": False}

def handle_query(query_id: str, filename: str, ttl: int, origin: Optional[str]) -> Dict:
    """Maneja una consulta recibida. Deduplica por query_id, verifica local, propaga si ttl>0."""
    if query_id in _QUERY_HISTORY:
        return {"found": False}
    _QUERY_HISTORY.append(query_id)

    # Verificar local
    if _has_file(filename):
        return {"found": True, "owner_id": _SELF_ID or "", "address": _SELF_ADDR or ""}

    # Propagar si TTL > 0
    if ttl and ttl > 0:
        for addr in list(_DL):
            # Evitar enviar de vuelta directo al origin si está en la DL (opcional)
            if origin and addr == origin:
                continue
            try:
                url = f"http://{addr}/directory/query"
                st, txt = _post_json(url, {"query_id": query_id, "filename": filename, "ttl": ttl - 1, "origin": origin or _SELF_ADDR})
                if st == 200:
                    resp = json.loads(txt)
                    if resp.get("found"):
                        return resp
            except Exception:
                continue
    return {"found": False}