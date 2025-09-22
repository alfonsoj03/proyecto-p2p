from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from services.file_simple.service import indexar, listar_archivos
from services.directory_simple.api import router as directory_router
from services.transfer_runtime.api import router as transfer_router

logger = logging.getLogger(__name__)

app = FastAPI(title="P2P File Simple API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(directory_router)
app.include_router(transfer_router)

@app.post("/indexar")
async def api_indexar():
    """Indexa el directorio configurado para este nodo y guarda en memoria."""
    total = indexar()
    return {"success": True, "total": total}

@app.get("/archivos")
async def api_archivos():
    """Lista archivos indexados en memoria para este nodo."""
    return {"success": True, "data": listar_archivos()}