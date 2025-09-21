"""
Cliente HTTP para comunicación entre nodos P2P.
Incluye retry logic y timeout apropiados para la red P2P.
"""
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

class P2PHttpClient:
    def __init__(self, timeout: int = 10, max_retries: int = 2):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        
    async def post_json(self, url: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Realiza POST con JSON data y retry logic."""
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.debug(f"POST {url} exitoso en intento {attempt + 1}")
                            return result
                        else:
                            logger.warning(f"POST {url} falló con status {response.status}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"POST {url} timeout en intento {attempt + 1}")
            except aiohttp.ClientConnectorError:
                logger.warning(f"POST {url} conexión fallida en intento {attempt + 1}")
            except Exception as e:
                logger.error(f"POST {url} error inesperado: {e}")
                
            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))  # Backoff exponencial
                
        logger.error(f"POST {url} falló después de {self.max_retries + 1} intentos")
        return None
    
    async def get_json(self, url: str) -> Optional[Dict[str, Any]]:
        """Realiza GET y retorna JSON con retry logic."""
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.debug(f"GET {url} exitoso en intento {attempt + 1}")
                            return result
                        else:
                            logger.warning(f"GET {url} falló con status {response.status}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"GET {url} timeout en intento {attempt + 1}")
            except aiohttp.ClientConnectorError:
                logger.warning(f"GET {url} conexión fallida en intento {attempt + 1}")
            except Exception as e:
                logger.error(f"GET {url} error inesperado: {e}")
                
            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))
                
        logger.error(f"GET {url} falló después de {self.max_retries + 1} intentos")
        return None

# Cliente global para reutilizar
http_client = P2PHttpClient()
