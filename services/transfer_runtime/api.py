from fastapi import APIRouter
from typing import Dict, List
import json
import urllib.request
from services.directory_simple.service import get_all
from services.transfer_client.client import download_file
from services.file_simple.service import indexar

router = APIRouter(prefix="/transfer", tags=["transfer"])

def _post_json(url: str, payload: Dict, timeout: int = 8):
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

@router.post("/download")
def transfer_download(payload: Dict[str, object]):
    """
    - Toma filename (y TTL opcional, default=3)
    - Pide a algún vecino de la DL que ejecute /directory/search
    - Si se encuentra, deriva la dirección gRPC y descarga el archivo
    - Luego solicita al propietario que re-indexe (best-effort)
    - Retorna el resultado simple
    Body: { "filename": str, "ttl"?: int }
    """
    if not isinstance(payload, dict):
        return {"success": False, "error": "payload inválido"}

    filename = str(payload.get("filename", "") or "")
    if not filename:
        return {"success": False, "error": "filename requerido"}
    try:
        ttl = int(payload.get("ttl", 3))
    except Exception:
        ttl = 3

    # 1) Pedir a algún vecino que ejecute la búsqueda distribuida
    dl: List[str] = get_all()
    found_resp: Dict[str, object] = {}
    for addr in dl:
        try:
            st, txt = _post_json(f"http://{addr}/directory/search", {"filename": filename, "ttl": ttl})
            if st == 200:
                resp = json.loads(txt)
                if resp.get("success") and resp.get("found"):
                    found_resp = resp
                    break
        except Exception:
            continue

    if not found_resp:
        return {"success": True, "found": False}

    owner_rest = found_resp.get("address")
    owner_id = found_resp.get("owner_id") or ""
    if not owner_rest:
        return {"success": True, "found": False}

    # 2) Encontrar el puerto gRPC que es el puerto REST + 1000 por convención
    try:
        host, port_str = owner_rest.split(":", 1)
        owner_grpc = f"{host}:{int(port_str) + 1000}"
    except Exception:
        return {"success": False, "error": "no se pudo derivar direccion gRPC"}

    # 3) Descargar vía gRPC
    ok, msg = download_file(owner_grpc, filename)

    # 4) Indexar el nodo que recibe el archivo
    try:
        total = indexar()
    except Exception:
        total = None

    return {
        "success": True,
        "found": True,
        "owner_id": owner_id,
        "owner_rest": owner_rest,
        "owner_grpc": owner_grpc,
        "download_ok": ok,
        "message": msg,
        "local_reindex_total": total,
    }