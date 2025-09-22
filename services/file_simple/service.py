import os
from typing import List, Dict, Optional

# Índice simple en memoria por proceso (un proceso = un nodo)
_INDEX: List[Dict] = []
_BASE_DIR: Optional[str] = None

def set_base_directory(path: str) -> None:
    """Configura el directorio base desde el cual se indexarán archivos."""
    global _BASE_DIR
    _BASE_DIR = path

def get_base_directory() -> Optional[str]:
    """Devuelve el directorio base configurado para este nodo."""
    return _BASE_DIR

def listar_archivos() -> List[Dict]:
    """Devuelve el índice simple en memoria."""
    return list(_INDEX)

def _scan_directory(base_dir: str) -> List[Dict]:
    entries: List[Dict] = []
    for root, _, files in os.walk(base_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                size = os.path.getsize(fpath)
            except Exception:
                size = 0
            entries.append({
                "filename": fname,
                "path": fpath,
                "size": size,
            })
    return entries

def indexar() -> int:
    """Re-indexa el directorio configurado y guarda en memoria.
    Retorna el número de archivos indexados.
    """
    global _INDEX
    if not _BASE_DIR:
        raise RuntimeError("Base directory not set. Call set_base_directory() first.")
    if not os.path.isdir(_BASE_DIR):
        # No falla: retorna 0 si no existe el directorio
        _INDEX = []
        return 0

    _INDEX = _scan_directory(_BASE_DIR)
    return len(_INDEX)