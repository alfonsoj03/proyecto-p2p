#!/usr/bin/env python3
"""
Scripts de pruebas de concurrencia para la Fase 4 del sistema P2P.
Ejecuta múltiples operaciones simultáneas para probar la concurrencia de REST y gRPC.
"""
import asyncio
import aiohttp
import time
import logging
import statistics
from typing import List, Dict, Any, Tuple
from pathlib import Path
import json

# Importar cliente gRPC si está disponible
try:
    from services.transfer_grpc.client import TransferClient
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

logger = logging.getLogger(__name__)

class ConcurrencyTester:
    """Tester de concurrencia para operaciones P2P."""
    
    def __init__(self):
        self.results = {
            "searches": [],
            "downloads": [],
            "uploads": [],
            "indexing": [],
            "errors": [],
        }
        self.nodes = {
            "peer1": "127.0.0.1:50001",
            "peer2": "127.0.0.1:50002",
            "peer3": "127.0.0.1:50003"
        }
    
    async def concurrent_searches(self, num_concurrent: int = 10) -> Dict[str, Any]:
        """Ejecuta múltiples búsquedas simultáneas."""
        print(f"\n🔍 PRUEBA DE CONCURRENCIA - {num_concurrent} búsquedas simultáneas")
        
        search_queries = [
            ("video_especial.mp4", "peer1"),
            ("readme.md", "peer2"),
            ("script.py", "peer3"),
            ("video_comun.mp4", "peer1"),
            ("documento1.txt", "peer2"),
            ("imagen1.jpg", "peer3"),
            ("config.yaml", "peer1"),
            ("inexistente.txt", "peer2"),
        ]
        
        # Crear tareas concurrentes
        tasks = []
        start_time = time.time()
        
        for i in range(num_concurrent):
            query, node = search_queries[i % len(search_queries)]
            task = self._single_search(self.nodes[node], query, f"search_{i}")
            tasks.append(task)
        
        # Ejecutar todas las búsquedas en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analizar resultados
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed = len(results) - successful
        
        metrics = {
            "total_searches": num_concurrent,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / num_concurrent * 100,
            "total_time": total_time,
            "avg_time_per_search": total_time / num_concurrent,
            "searches_per_second": num_concurrent / total_time
        }
        
        print(f"✅ Búsquedas completadas: {successful}/{num_concurrent} ({metrics['success_rate']:.1f}%)")
        print(f"⏱️  Tiempo total: {total_time:.2f}s, Promedio: {metrics['avg_time_per_search']:.2f}s")
        print(f"🚀 Throughput: {metrics['searches_per_second']:.1f} búsquedas/segundo")
        
        self.results["searches"].append(metrics)
        return metrics
    
    async def concurrent_downloads(self, num_concurrent: int = 5) -> Dict[str, Any]:
        """Ejecuta múltiples descargas gRPC simultáneas."""
        if not GRPC_AVAILABLE:
            print("❌ gRPC no disponible para pruebas de descarga")
            return {}
        
        print(f"\n📥 PRUEBA DE CONCURRENCIA - {num_concurrent} descargas gRPC simultáneas")
        
        download_tasks = [
            ("video_especial.mp4", "peer1", "peer3"),
            ("readme.md", "peer2", "peer1"),
            ("script.py", "peer3", "peer2"),
            ("documento2.txt", "peer2", "peer3"),
            ("imagen3.gif", "peer3", "peer1"),
        ]
        
        # Crear directorio de descargas concurrentes
        concurrent_dir = Path("concurrent_downloads")
        concurrent_dir.mkdir(exist_ok=True)
        
        # Crear tareas concurrentes
        tasks = []
        start_time = time.time()
        
        for i in range(num_concurrent):
            filename, source_peer, target_peer = download_tasks[i % len(download_tasks)]
            source_node = self.nodes[source_peer]
            target_node = self.nodes[target_peer]
            
            save_path = concurrent_dir / f"{i}_{filename}"
            task = self._single_download(target_node, source_node, filename, str(save_path), f"download_{i}")
            tasks.append(task)
        
        # Ejecutar todas las descargas en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analizar resultados
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed = len(results) - successful
        
        metrics = {
            "total_downloads": num_concurrent,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / num_concurrent * 100,
            "total_time": total_time,
            "avg_time_per_download": total_time / num_concurrent,
            "downloads_per_second": num_concurrent / total_time if total_time > 0 else 0
        }
        
        print(f"✅ Descargas completadas: {successful}/{num_concurrent} ({metrics['success_rate']:.1f}%)")
        print(f"⏱️  Tiempo total: {total_time:.2f}s, Promedio: {metrics['avg_time_per_download']:.2f}s")
        
        self.results["downloads"].append(metrics)
        return metrics
    
    async def concurrent_indexing(self, num_concurrent: int = 15) -> Dict[str, Any]:
        """Ejecuta múltiples operaciones de indexación simultáneas."""
        print(f"\n📁 PRUEBA DE CONCURRENCIA - {num_concurrent} indexaciones simultáneas")
        
        # Crear tareas concurrentes de indexación
        tasks = []
        start_time = time.time()
        
        for i in range(num_concurrent):
            node = list(self.nodes.values())[i % len(self.nodes)]
            task = self._single_index(node, f"index_{i}")
            tasks.append(task)
        
        # Ejecutar todas las indexaciones en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analizar resultados
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed = len(results) - successful
        
        metrics = {
            "total_indexing": num_concurrent,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / num_concurrent * 100,
            "total_time": total_time,
            "avg_time_per_index": total_time / num_concurrent,
            "indexing_per_second": num_concurrent / total_time
        }
        
        print(f"✅ Indexaciones completadas: {successful}/{num_concurrent} ({metrics['success_rate']:.1f}%)")
        print(f"⏱️  Tiempo total: {total_time:.2f}s, Promedio: {metrics['avg_time_per_index']:.2f}s")
        print(f"🚀 Throughput: {metrics['indexing_per_second']:.1f} indexaciones/segundo")
        
        self.results["indexing"].append(metrics)
        return metrics
    
    async def _single_search(self, node: str, filename: str, task_id: str) -> Dict[str, Any]:
        """Ejecuta una búsqueda individual."""
        try:
            url = f"http://{node}/directory/search/simple/{filename}"
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        duration = time.time() - start_time
                        
                        return {
                            "success": True,
                            "task_id": task_id,
                            "node": node,
                            "filename": filename,
                            "duration": duration,
                            "results_count": len(result.get("results", []))
                        }
                    else:
                        return {"success": False, "task_id": task_id, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            return {"success": False, "task_id": task_id, "error": str(e)}
    
    async def _single_download(self, requesting_node: str, source_node: str, filename: str, save_path: str, task_id: str) -> Dict[str, Any]:
        """Ejecuta una descarga individual."""
        try:
            client = TransferClient(requesting_node)
            start_time = time.time()
            
            success = await client.download_file(source_node, filename, save_path)
            duration = time.time() - start_time
            
            return {
                "success": success,
                "task_id": task_id,
                "filename": filename,
                "duration": duration,
                "source_node": source_node,
                "requesting_node": requesting_node
            }
            
        except Exception as e:
            return {"success": False, "task_id": task_id, "error": str(e)}
    
    async def _single_index(self, node: str, task_id: str) -> Dict[str, Any]:
        """Ejecuta una indexación individual."""
        try:
            url = f"http://{node}/indexar"
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={}) as response:
                    if response.status == 200:
                        result = await response.json()
                        duration = time.time() - start_time
                        
                        return {
                            "success": True,
                            "task_id": task_id,
                            "node": node,
                            "duration": duration,
                            "files_indexed": result.get("total", 0)
                        }
                    else:
                        return {"success": False, "task_id": task_id, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            return {"success": False, "task_id": task_id, "error": str(e)}
    
    def save_results(self, filename: str = "concurrency_results.json"):
        """Guarda los resultados de las pruebas."""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"📊 Resultados guardados en: {filename}")

async def run_concurrency_tests():
    """Ejecuta todas las pruebas de concurrencia."""
    print("🚀 INICIANDO PRUEBAS DE CONCURRENCIA - FASE 4")
    print("="*60)
    
    tester = ConcurrencyTester()
    
    # Prueba 1: Búsquedas concurrentes
    await tester.concurrent_searches(10)
    await asyncio.sleep(2)
    
    # Prueba 2: Indexaciones concurrentes
    await tester.concurrent_indexing(15)
    await asyncio.sleep(2)
    
    # Prueba 3: Descargas concurrentes (si gRPC está disponible)
    if GRPC_AVAILABLE:
        await tester.concurrent_downloads(5)
        await asyncio.sleep(2)
    
    # Prueba 4: Búsquedas intensivas
    print("\n🔥 PRUEBA INTENSIVA")
    await tester.concurrent_searches(25)
    
    # Guardar resultados
    tester.save_results()
    
    print("\n✅ PRUEBAS DE CONCURRENCIA COMPLETADAS")
    print("="*60)
    print("\n📊 RESUMEN:")
    
    if tester.results["searches"]:
        search_success_rates = [r["success_rate"] for r in tester.results["searches"]]
        print(f"🔍 Búsquedas - Tasa de éxito promedio: {statistics.mean(search_success_rates):.1f}%")
    
    if tester.results["indexing"]:
        index_success_rates = [r["success_rate"] for r in tester.results["indexing"]]
        print(f"📁 Indexaciones - Tasa de éxito promedio: {statistics.mean(index_success_rates):.1f}%")
    
    if tester.results["downloads"]:
        download_success_rates = [r["success_rate"] for r in tester.results["downloads"]]
        print(f"📥 Descargas - Tasa de éxito promedio: {statistics.mean(download_success_rates):.1f}%")

if __name__ == "__main__":
    asyncio.run(run_concurrency_tests())
