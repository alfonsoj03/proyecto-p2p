from typing import List, Optional
import random

# Directorio en memoria por proceso (un proceso = un nodo)
_DL: List[str] = []  # direcciones como "ip:port"
_SELF: Optional[str] = None


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
