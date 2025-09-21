import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Índice simple en memoria por proceso (un proceso = un nodo)
_INDEX: List[Dict] = []
_BASE_DIR: Optional[str] = None
_DOWNLOADS_DIR: Optional[str] = None


def set_base_directory(path: str) -> None:
    """Configura el directorio base desde el cual se indexarán archivos."""
    global _BASE_DIR, _DOWNLOADS_DIR
    _BASE_DIR = path
    
    # Configurar directorio de descargas
    _DOWNLOADS_DIR = str(Path(path).parent / "downloads")
    Path(_DOWNLOADS_DIR).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Configurados directorios - Base: {_BASE_DIR}, Downloads: {_DOWNLOADS_DIR}")


def listar_archivos() -> List[Dict]:
    """Devuelve el índice simple en memoria."""
    return list(_INDEX)

def indexar_archivo_descargado(file_path: str) -> bool:
    """Indexa un archivo recién descargado.
    
    Args:
        file_path: Ruta completa del archivo descargado
        
    Returns:
        True si se indexó exitosamente, False en caso contrario
    """
    global _INDEX
    
    if not os.path.exists(file_path):
        logger.error(f"Archivo no encontrado para indexar: {file_path}")
        return False
    
    try:
        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        
        # Verificar si ya está indexado (evitar duplicados)
        for existing in _INDEX:
            if existing["path"] == file_path:
                logger.debug(f"Archivo ya indexado: {filename}")
                return True
        
        # Agregar al índice
        _INDEX.append({
            "filename": filename,
            "path": file_path,
            "size": size,
        })
        
        logger.info(f"✅ Archivo indexado: {filename} ({size} bytes)")
        return True
        
    except Exception as e:
        logger.error(f"Error indexando archivo {file_path}: {e}")
        return False


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

    # Escanear directorio base
    _INDEX = _scan_directory(_BASE_DIR)
    
    # También escanear directorio de descargas si existe
    if _DOWNLOADS_DIR and os.path.isdir(_DOWNLOADS_DIR):
        downloads_files = _scan_directory(_DOWNLOADS_DIR)
        _INDEX.extend(downloads_files)
        logger.debug(f"Indexados {len(downloads_files)} archivos desde downloads")
    
    return len(_INDEX)
