#!/usr/bin/env python3
"""
Colección de métricas de rendimiento y disponibilidad para la Fase 4 del sistema P2P.
Monitorea continuamente el sistema y recopila estadísticas detalladas.
"""
import asyncio
import aiohttp
import time
import psutil
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import statistics
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class MetricSnapshot:
    """Instantánea de métricas en un momento específico."""
    timestamp: float
    active_nodes: int
    response_times: Dict[str, float]
    cpu_usage: float
    memory_usage: float
    network_requests_success: int
    network_requests_failed: int
    search_operations: int
    index_operations: int
    grpc_operations: int

class PerformanceMonitor:
    """Monitor de rendimiento para el sistema P2P."""
    
    def __init__(self, monitoring_duration: int = 300):  # 5 minutos por defecto
        self.nodes = {
            "peer1": "127.0.0.1:50001",
            "peer2": "127.0.0.1:50002",
            "peer3": "127.0.0.1:50003"
        }
        self.monitoring_duration = monitoring_duration
        self.metrics_history: List[MetricSnapshot] = []
        self.operation_stats = {
            "searches": [],
            "indexing": [],
            "grpc_ops": [],
            "health_checks": []
        }
    
    async def start_continuous_monitoring(self):
        """Inicia monitoreo continuo del sistema."""
        print(f"📊 INICIANDO MONITOREO CONTINUO - {self.monitoring_duration}s")
        print("="*60)
        
        start_time = time.time()
        snapshot_interval = 10  # Cada 10 segundos
        next_snapshot = start_time + snapshot_interval
        
        while time.time() - start_time < self.monitoring_duration:
            current_time = time.time()
            
            if current_time >= next_snapshot:
                # Tomar snapshot de métricas
                snapshot = await self._take_metrics_snapshot()
                self.metrics_history.append(snapshot)
                
                # Mostrar métricas en tiempo real
                self._display_current_metrics(snapshot)
                
                next_snapshot += snapshot_interval
            
            # Realizar operaciones de prueba
            await self._perform_background_operations()
            
            await asyncio.sleep(1)
        
        print("\n📈 MONITOREO COMPLETADO")
        await self._generate_performance_report()
    
    async def benchmark_operations(self):
        """Ejecuta benchmark de operaciones específicas."""
        print("\n🏃‍♂️ BENCHMARK DE OPERACIONES")
        print("="*40)
        
        # Benchmark búsquedas
        search_times = await self._benchmark_searches(50)
        
        # Benchmark indexaciones
        index_times = await self._benchmark_indexing(30)
        
        # Benchmark operaciones gRPC (si disponible)
        grpc_times = await self._benchmark_grpc_operations(20)
        
        benchmark_results = {
            "search_operations": {
                "total_ops": len(search_times),
                "avg_time": statistics.mean(search_times) if search_times else 0,
                "median_time": statistics.median(search_times) if search_times else 0,
                "p95_time": self._percentile(search_times, 95) if search_times else 0,
                "ops_per_second": len(search_times) / sum(search_times) if search_times else 0
            },
            "index_operations": {
                "total_ops": len(index_times),
                "avg_time": statistics.mean(index_times) if index_times else 0,
                "median_time": statistics.median(index_times) if index_times else 0,
                "p95_time": self._percentile(index_times, 95) if index_times else 0,
                "ops_per_second": len(index_times) / sum(index_times) if index_times else 0
            },
            "grpc_operations": {
                "total_ops": len(grpc_times),
                "avg_time": statistics.mean(grpc_times) if grpc_times else 0,
                "median_time": statistics.median(grpc_times) if grpc_times else 0,
                "p95_time": self._percentile(grpc_times, 95) if grpc_times else 0,
                "ops_per_second": len(grpc_times) / sum(grpc_times) if grpc_times else 0
            }
        }
        
        self._display_benchmark_results(benchmark_results)
        return benchmark_results
    
    async def measure_network_latency(self):
        """Mide latencia de red entre nodos."""
        print("\n🌐 MEDICIÓN DE LATENCIA DE RED")
        print("="*35)
        
        latency_matrix = {}
        
        for source_name, source_addr in self.nodes.items():
            latency_matrix[source_name] = {}
            
            for target_name, target_addr in self.nodes.items():
                if source_name == target_name:
                    latency_matrix[source_name][target_name] = 0.0
                    continue
                
                # Medir latencia con múltiples pings
                latencies = []
                for _ in range(10):
                    latency = await self._measure_single_latency(source_addr, target_addr)
                    if latency is not None:
                        latencies.append(latency)
                
                avg_latency = statistics.mean(latencies) if latencies else float('inf')
                latency_matrix[source_name][target_name] = avg_latency
                
                print(f"📡 {source_name} → {target_name}: {avg_latency:.3f}s")
        
        return latency_matrix
    
    async def _take_metrics_snapshot(self) -> MetricSnapshot:
        """Toma una instantánea de métricas del sistema."""
        # Health check de nodos
        active_nodes = 0
        response_times = {}
        
        for node_name, node_addr in self.nodes.items():
            start_time = time.time()
            try:
                url = f"http://{node_addr}/directory/dl/all"
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            active_nodes += 1
                            response_times[node_name] = time.time() - start_time
                        else:
                            response_times[node_name] = float('inf')
            except:
                response_times[node_name] = float('inf')
        
        # Métricas del sistema
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        
        # Contar operaciones (simulado por ahora)
        search_ops = len([op for op in self.operation_stats["searches"] 
                         if time.time() - op.get("timestamp", 0) < 60])
        index_ops = len([op for op in self.operation_stats["indexing"] 
                        if time.time() - op.get("timestamp", 0) < 60])
        grpc_ops = len([op for op in self.operation_stats["grpc_ops"] 
                       if time.time() - op.get("timestamp", 0) < 60])
        
        return MetricSnapshot(
            timestamp=time.time(),
            active_nodes=active_nodes,
            response_times=response_times,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            network_requests_success=0,  # Se actualizaría con métricas reales
            network_requests_failed=0,
            search_operations=search_ops,
            index_operations=index_ops,
            grpc_operations=grpc_ops
        )
    
    def _display_current_metrics(self, snapshot: MetricSnapshot):
        """Muestra métricas actuales en tiempo real."""
        timestamp = datetime.fromtimestamp(snapshot.timestamp).strftime("%H:%M:%S")
        
        # Calcular respuesta promedio
        valid_responses = [t for t in snapshot.response_times.values() if t != float('inf')]
        avg_response = statistics.mean(valid_responses) if valid_responses else 0
        
        print(f"[{timestamp}] 🌐 Nodos: {snapshot.active_nodes}/3, "
              f"⚡ Resp: {avg_response:.3f}s, "
              f"💻 CPU: {snapshot.cpu_usage:.1f}%, "
              f"🧠 RAM: {snapshot.memory_usage:.1f}%, "
              f"🔍 Búsq: {snapshot.search_operations}, "
              f"📁 Idx: {snapshot.index_operations}")
    
    async def _perform_background_operations(self):
        """Realiza operaciones en segundo plano para generar tráfico."""
        # Operación de búsqueda aleatoria
        if len(self.nodes) > 0:
            import random
            node_addr = random.choice(list(self.nodes.values()))
            
            try:
                search_files = ["video_especial.mp4", "readme.md", "script.py", "config.yaml"]
                filename = random.choice(search_files)
                
                url = f"http://{node_addr}/directory/search/simple/{filename}"
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                    async with session.get(url) as response:
                        self.operation_stats["searches"].append({
                            "timestamp": time.time(),
                            "success": response.status == 200,
                            "node": node_addr
                        })
            except:
                pass
    
    async def _benchmark_searches(self, num_operations: int) -> List[float]:
        """Benchmark de operaciones de búsqueda."""
        print(f"🔍 Benchmarking {num_operations} búsquedas...")
        
        search_times = []
        search_files = ["video_especial.mp4", "readme.md", "script.py", "documento1.txt"]
        
        for i in range(num_operations):
            import random
            node_addr = random.choice(list(self.nodes.values()))
            filename = random.choice(search_files)
            
            start_time = time.time()
            try:
                url = f"http://{node_addr}/directory/search/simple/{filename}"
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            duration = time.time() - start_time
                            search_times.append(duration)
            except:
                pass
            
            if i % 10 == 0:
                print(f"  Progreso: {i}/{num_operations}")
        
        return search_times
    
    async def _benchmark_indexing(self, num_operations: int) -> List[float]:
        """Benchmark de operaciones de indexación."""
        print(f"📁 Benchmarking {num_operations} indexaciones...")
        
        index_times = []
        
        for i in range(num_operations):
            import random
            node_addr = random.choice(list(self.nodes.values()))
            
            start_time = time.time()
            try:
                url = f"http://{node_addr}/indexar"
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.post(url, json={}) as response:
                        if response.status == 200:
                            duration = time.time() - start_time
                            index_times.append(duration)
            except:
                pass
            
            if i % 5 == 0:
                print(f"  Progreso: {i}/{num_operations}")
        
        return index_times
    
    async def _benchmark_grpc_operations(self, num_operations: int) -> List[float]:
        """Benchmark de operaciones gRPC."""
        print(f"📡 Benchmarking {num_operations} operaciones gRPC...")
        
        grpc_times = []
        
        try:
            from services.transfer_grpc.client import TransferClient
            
            for i in range(num_operations):
                import random
                requesting_node = random.choice(list(self.nodes.values()))
                target_node = random.choice(list(self.nodes.values()))
                
                if requesting_node == target_node:
                    continue
                
                start_time = time.time()
                try:
                    client = TransferClient(requesting_node)
                    result = await client.check_file(target_node, "test_file.txt")
                    
                    duration = time.time() - start_time
                    grpc_times.append(duration)
                except:
                    pass
                
                if i % 5 == 0:
                    print(f"  Progreso: {i}/{num_operations}")
                    
        except ImportError:
            print("  ⚠️  gRPC no disponible para benchmark")
        
        return grpc_times
    
    async def _measure_single_latency(self, source_addr: str, target_addr: str) -> Optional[float]:
        """Mide latencia individual entre dos nodos."""
        try:
            start_time = time.time()
            url = f"http://{target_addr}/directory/dl/all"
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return time.time() - start_time
        except:
            pass
        return None
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcula percentil de una lista de datos."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _display_benchmark_results(self, results: Dict[str, Any]):
        """Muestra resultados del benchmark."""
        print("\n📊 RESULTADOS DEL BENCHMARK")
        print("="*40)
        
        for operation, metrics in results.items():
            if metrics["total_ops"] > 0:
                print(f"\n{operation.upper()}:")
                print(f"  🔢 Total operaciones: {metrics['total_ops']}")
                print(f"  ⚡ Tiempo promedio: {metrics['avg_time']:.3f}s")
                print(f"  📈 Tiempo mediano: {metrics['median_time']:.3f}s")
                print(f"  🔝 P95: {metrics['p95_time']:.3f}s")
                print(f"  🚀 Ops/segundo: {metrics['ops_per_second']:.1f}")
    
    async def _generate_performance_report(self):
        """Genera reporte completo de rendimiento."""
        if not self.metrics_history:
            print("⚠️  No hay datos de métricas para generar reporte")
            return
        
        print("\n📈 REPORTE DE RENDIMIENTO")
        print("="*50)
        
        # Estadísticas de disponibilidad
        active_nodes_over_time = [m.active_nodes for m in self.metrics_history]
        avg_active_nodes = statistics.mean(active_nodes_over_time)
        uptime_percentage = (avg_active_nodes / 3) * 100
        
        # Estadísticas de respuesta
        all_response_times = []
        for snapshot in self.metrics_history:
            valid_times = [t for t in snapshot.response_times.values() if t != float('inf')]
            all_response_times.extend(valid_times)
        
        avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        p95_response_time = self._percentile(all_response_times, 95) if all_response_times else 0
        
        # Estadísticas de sistema
        cpu_values = [m.cpu_usage for m in self.metrics_history]
        memory_values = [m.memory_usage for m in self.metrics_history]
        avg_cpu = statistics.mean(cpu_values)
        avg_memory = statistics.mean(memory_values)
        max_cpu = max(cpu_values)
        max_memory = max(memory_values)
        
        print(f"🌐 DISPONIBILIDAD:")
        print(f"  - Nodos activos promedio: {avg_active_nodes:.1f}/3")
        print(f"  - Tiempo de actividad: {uptime_percentage:.1f}%")
        
        print(f"\n⚡ RENDIMIENTO:")
        print(f"  - Tiempo de respuesta promedio: {avg_response_time:.3f}s")
        print(f"  - P95 tiempo de respuesta: {p95_response_time:.3f}s")
        
        print(f"\n💻 RECURSOS DEL SISTEMA:")
        print(f"  - CPU promedio: {avg_cpu:.1f}% (máx: {max_cpu:.1f}%)")
        print(f"  - Memoria promedio: {avg_memory:.1f}% (máx: {max_memory:.1f}%)")
        
        # Guardar reporte detallado
        report = {
            "monitoring_duration": self.monitoring_duration,
            "total_snapshots": len(self.metrics_history),
            "availability": {
                "avg_active_nodes": avg_active_nodes,
                "uptime_percentage": uptime_percentage
            },
            "performance": {
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_response_time
            },
            "system_resources": {
                "avg_cpu": avg_cpu,
                "max_cpu": max_cpu,
                "avg_memory": avg_memory,
                "max_memory": max_memory
            },
            "metrics_history": [asdict(m) for m in self.metrics_history]
        }
        
        with open("performance_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Reporte detallado guardado en: performance_report.json")

async def run_performance_analysis():
    """Ejecuta análisis completo de rendimiento."""
    print("📊 INICIANDO ANÁLISIS DE RENDIMIENTO - FASE 4")
    print("="*60)
    
    monitor = PerformanceMonitor(monitoring_duration=120)  # 2 minutos
    
    # Verificar que la red esté activa
    initial_snapshot = await monitor._take_metrics_snapshot()
    if initial_snapshot.active_nodes < 2:
        print(f"⚠️  Solo {initial_snapshot.active_nodes}/3 nodos activos.")
        print("Inicia la red completa primero: python scripts/start_nodes.py")
        return
    
    print(f"✅ Red inicial: {initial_snapshot.active_nodes}/3 nodos activos")
    
    # Ejecutar monitoreo continuo
    await monitor.start_continuous_monitoring()
    
    # Ejecutar benchmarks
    await monitor.benchmark_operations()
    
    # Medir latencia de red
    await monitor.measure_network_latency()
    
    print("\n✅ ANÁLISIS DE RENDIMIENTO COMPLETADO")

if __name__ == "__main__":
    asyncio.run(run_performance_analysis())
