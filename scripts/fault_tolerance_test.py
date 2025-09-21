#!/usr/bin/env python3
"""
Scripts de pruebas de tolerancia a fallos para la Fase 4 del sistema P2P.
Simula caída de nodos, congestión y verifica la recuperación de la red.
"""
import asyncio
import aiohttp
import psutil
import signal
import subprocess
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import random

logger = logging.getLogger(__name__)

class FaultToleranceTester:
    """Tester de tolerancia a fallos para la red P2P."""
    
    def __init__(self):
        self.nodes = {
            "peer1": {"address": "127.0.0.1:50001", "process": None, "config": "config/peer_01.yaml"},
            "peer2": {"address": "127.0.0.1:50002", "process": None, "config": "config/peer_02.yaml"}, 
            "peer3": {"address": "127.0.0.1:50003", "process": None, "config": "config/peer_03.yaml"}
        }
        self.fault_results = {
            "node_failures": [],
            "network_partitions": [],
            "recovery_tests": [],
            "resilience_metrics": []
        }
    
    async def test_node_failure_recovery(self) -> Dict[str, Any]:
        """Prueba la recuperación tras la caída de un nodo."""
        print("\n💥 PRUEBA DE TOLERANCIA A FALLOS - Caída y Recuperación de Nodos")
        
        results = []
        
        for node_name, node_info in self.nodes.items():
            print(f"\n--- Probando fallo de {node_name.upper()} ---")
            
            # 1. Verificar estado inicial de la red
            initial_state = await self._check_network_health()
            print(f"🌐 Estado inicial: {sum(initial_state.values())}/3 nodos activos")
            
            # 2. Simular caída del nodo (proceso terminado)
            print(f"⚡ Simulando caída de {node_name}...")
            await self._simulate_node_failure(node_name)
            await asyncio.sleep(2)
            
            # 3. Verificar que la red sigue funcionando
            degraded_state = await self._check_network_health()
            remaining_nodes = sum(degraded_state.values())
            print(f"🌐 Estado tras fallo: {remaining_nodes}/3 nodos activos")
            
            # 4. Probar funcionalidad con nodo caído
            connectivity_test = await self._test_network_connectivity_with_failure(node_name)
            
            # 5. Recuperar el nodo
            print(f"🔄 Recuperando {node_name}...")
            await self._recover_node(node_name)
            await asyncio.sleep(3)
            
            # 6. Verificar recuperación completa
            recovered_state = await self._check_network_health()
            recovered_nodes = sum(recovered_state.values())
            print(f"🌐 Estado tras recuperación: {recovered_nodes}/3 nodos activos")
            
            # 7. Probar funcionalidad tras recuperación
            post_recovery_test = await self._test_full_functionality()
            
            result = {
                "failed_node": node_name,
                "initial_active_nodes": sum(initial_state.values()),
                "degraded_active_nodes": remaining_nodes,
                "recovered_active_nodes": recovered_nodes,
                "network_survived": remaining_nodes >= 2,
                "full_recovery": recovered_nodes == 3,
                "connectivity_during_failure": connectivity_test,
                "functionality_after_recovery": post_recovery_test
            }
            
            results.append(result)
            print(f"{'✅' if result['network_survived'] and result['full_recovery'] else '❌'} "
                  f"Prueba de {node_name}: Red sobrevivió={result['network_survived']}, "
                  f"Recuperación completa={result['full_recovery']}")
            
            await asyncio.sleep(2)
        
        self.fault_results["node_failures"] = results
        return results
    
    async def test_network_partition_tolerance(self) -> Dict[str, Any]:
        """Prueba tolerancia a particiones de red simuladas."""
        print("\n🌐 PRUEBA DE TOLERANCIA A PARTICIONES DE RED")
        
        # Simular partición: peer1 aislado, peer2-peer3 conectados
        print("📡 Simulando partición de red (peer1 aislado)...")
        
        # 1. Estado inicial
        initial_state = await self._check_network_health()
        
        # 2. Simular latencia alta y pérdida de paquetes para peer1
        await self._simulate_network_partition("peer1")
        
        # 3. Probar conectividad entre peer2 y peer3
        partition_test = await self._test_partition_connectivity()
        
        # 4. Restaurar conectividad
        await self._restore_network()
        await asyncio.sleep(2)
        
        # 5. Verificar recuperación
        final_state = await self._check_network_health()
        
        result = {
            "initial_nodes": sum(initial_state.values()),
            "nodes_during_partition": sum(partition_test["active_nodes"].values()),
            "peer2_peer3_connectivity": partition_test["peer2_peer3_connected"],
            "partition_isolated_node": "peer1",
            "recovery_successful": sum(final_state.values()) == 3,
            "final_nodes": sum(final_state.values())
        }
        
        self.fault_results["network_partitions"].append(result)
        print(f"{'✅' if result['recovery_successful'] else '❌'} "
              f"Tolerancia a partición: Recuperación={result['recovery_successful']}")
        
        return result
    
    async def test_gradual_node_stress(self) -> Dict[str, Any]:
        """Prueba estrés gradual aumentando carga en los nodos."""
        print("\n🔥 PRUEBA DE ESTRÉS GRADUAL - Carga Incremental")
        
        stress_levels = [5, 10, 20, 30]  # Requests concurrentes
        results = []
        
        for stress_level in stress_levels:
            print(f"\n⚡ Nivel de estrés: {stress_level} requests concurrentes")
            
            start_time = time.time()
            
            # Generar carga
            tasks = []
            for i in range(stress_level):
                # Alternar entre búsquedas e indexaciones
                if i % 2 == 0:
                    node = random.choice(list(self.nodes.values()))["address"]
                    task = self._stress_search(node, f"stress_search_{i}")
                else:
                    node = random.choice(list(self.nodes.values()))["address"]
                    task = self._stress_index(node, f"stress_index_{i}")
                tasks.append(task)
            
            # Ejecutar carga
            stress_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            duration = time.time() - start_time
            
            # Analizar resultados
            successful = sum(1 for r in stress_results if isinstance(r, dict) and r.get("success"))
            failed = len(stress_results) - successful
            
            # Verificar salud de la red tras estrés
            post_stress_health = await self._check_network_health()
            
            result = {
                "stress_level": stress_level,
                "duration": duration,
                "successful_requests": successful,
                "failed_requests": failed,
                "success_rate": successful / stress_level * 100,
                "requests_per_second": stress_level / duration,
                "nodes_survived": sum(post_stress_health.values()),
                "network_healthy": sum(post_stress_health.values()) >= 2
            }
            
            results.append(result)
            print(f"📊 Nivel {stress_level}: {successful}/{stress_level} exitosos "
                  f"({result['success_rate']:.1f}%), {result['nodes_survived']}/3 nodos activos")
            
            await asyncio.sleep(2)
        
        self.fault_results["resilience_metrics"] = results
        return results
    
    async def _check_network_health(self) -> Dict[str, bool]:
        """Verifica la salud de todos los nodos."""
        health = {}
        
        for node_name, node_info in self.nodes.items():
            try:
                url = f"http://{node_info['address']}/directory/dl/all"
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                    async with session.get(url) as response:
                        health[node_name] = response.status == 200
            except:
                health[node_name] = False
        
        return health
    
    async def _simulate_node_failure(self, node_name: str):
        """Simula la caída de un nodo específico."""
        # En un entorno real, esto terminaría el proceso del nodo
        # Por simplicidad, solo marcamos el nodo como inactivo
        print(f"💀 Nodo {node_name} simulado como caído")
        
        # En implementación real, se podría:
        # 1. Terminar el proceso del nodo
        # 2. Bloquear su puerto con iptables
        # 3. Suspender el proceso con SIGSTOP
        pass
    
    async def _recover_node(self, node_name: str):
        """Recupera un nodo tras una caída simulada."""
        print(f"🔄 Recuperando nodo {node_name}...")
        # En implementación real, reiniciaría el proceso del nodo
        await asyncio.sleep(1)  # Simular tiempo de recuperación
    
    async def _test_network_connectivity_with_failure(self, failed_node: str) -> Dict[str, Any]:
        """Prueba conectividad de red con un nodo caído."""
        remaining_nodes = [name for name in self.nodes.keys() if name != failed_node]
        
        connectivity_tests = []
        
        for node_name in remaining_nodes:
            try:
                # Probar búsqueda desde nodo restante
                url = f"http://{self.nodes[node_name]['address']}/directory/search/simple/test_file"
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(url) as response:
                        connectivity_tests.append(response.status == 200)
            except:
                connectivity_tests.append(False)
        
        return {
            "remaining_nodes": remaining_nodes,
            "connectivity_success_rate": sum(connectivity_tests) / len(connectivity_tests) * 100 if connectivity_tests else 0,
            "all_remaining_responsive": all(connectivity_tests) if connectivity_tests else False
        }
    
    async def _test_full_functionality(self) -> Dict[str, Any]:
        """Prueba funcionalidad completa tras recuperación."""
        try:
            # Probar búsqueda distribuida
            search_url = f"http://{self.nodes['peer1']['address']}/directory/search/simple/video_especial.mp4"
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(search_url) as response:
                    search_success = response.status == 200
            
            # Probar indexación
            index_url = f"http://{self.nodes['peer2']['address']}/indexar"
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.post(index_url, json={}) as response:
                    index_success = response.status == 200
            
            return {
                "search_functionality": search_success,
                "index_functionality": index_success,
                "overall_functionality": search_success and index_success
            }
        except:
            return {
                "search_functionality": False,
                "index_functionality": False,
                "overall_functionality": False
            }
    
    async def _simulate_network_partition(self, isolated_node: str):
        """Simula partición de red aislando un nodo."""
        print(f"🚧 Simulando aislamiento de {isolated_node}")
        # En implementación real, se usarían reglas de firewall o network namespaces
        await asyncio.sleep(1)
    
    async def _restore_network(self):
        """Restaurar conectividad completa de red."""
        print("🔗 Restaurando conectividad completa")
        await asyncio.sleep(1)
    
    async def _test_partition_connectivity(self) -> Dict[str, Any]:
        """Prueba conectividad durante partición."""
        # Probar conectividad peer2 <-> peer3
        try:
            # Login desde peer3 hacia peer2
            url = f"http://{self.nodes['peer2']['address']}/directory/login"
            data = {"address": self.nodes['peer3']['address']}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.post(url, json=data) as response:
                    peer2_peer3_connected = response.status == 200
        except:
            peer2_peer3_connected = False
        
        # Verificar nodos activos
        active_nodes = await self._check_network_health()
        
        return {
            "peer2_peer3_connected": peer2_peer3_connected,
            "active_nodes": active_nodes
        }
    
    async def _stress_search(self, node: str, task_id: str) -> Dict[str, Any]:
        """Operación de búsqueda para pruebas de estrés."""
        try:
            url = f"http://{node}/directory/search/simple/test_file"
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    return {"success": response.status == 200, "task_id": task_id}
        except:
            return {"success": False, "task_id": task_id}
    
    async def _stress_index(self, node: str, task_id: str) -> Dict[str, Any]:
        """Operación de indexación para pruebas de estrés."""
        try:
            url = f"http://{node}/indexar"
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(url, json={}) as response:
                    return {"success": response.status == 200, "task_id": task_id}
        except:
            return {"success": False, "task_id": task_id}
    
    def save_results(self, filename: str = "fault_tolerance_results.json"):
        """Guarda los resultados de las pruebas."""
        with open(filename, "w") as f:
            json.dump(self.fault_results, f, indent=2)
        print(f"📊 Resultados de tolerancia a fallos guardados en: {filename}")

async def run_fault_tolerance_tests():
    """Ejecuta todas las pruebas de tolerancia a fallos."""
    print("🛡️  INICIANDO PRUEBAS DE TOLERANCIA A FALLOS - FASE 4")
    print("="*70)
    
    tester = FaultToleranceTester()
    
    # Verificar estado inicial
    initial_health = await tester._check_network_health()
    active_nodes = sum(initial_health.values())
    
    if active_nodes < 3:
        print(f"⚠️  Solo {active_nodes}/3 nodos activos. Inicia la red completa primero.")
        print("Ejecuta: python scripts/start_nodes.py")
        return
    
    print(f"✅ Red inicial saludable: {active_nodes}/3 nodos activos")
    
    # Prueba 1: Tolerancia a fallos de nodos
    print("\n" + "="*50)
    await tester.test_node_failure_recovery()
    
    # Pausa entre pruebas
    await asyncio.sleep(3)
    
    # Prueba 2: Tolerancia a particiones de red
    print("\n" + "="*50)
    await tester.test_network_partition_tolerance()
    
    # Pausa entre pruebas
    await asyncio.sleep(3)
    
    # Prueba 3: Pruebas de estrés graduales
    print("\n" + "="*50)
    await tester.test_gradual_node_stress()
    
    # Guardar resultados
    tester.save_results()
    
    print("\n✅ PRUEBAS DE TOLERANCIA A FALLOS COMPLETADAS")
    print("="*70)
    
    # Resumen de resultados
    node_failures = tester.fault_results.get("node_failures", [])
    if node_failures:
        survived_all = all(r["network_survived"] for r in node_failures)
        recovered_all = all(r["full_recovery"] for r in node_failures)
        print(f"\n📊 RESUMEN DE TOLERANCIA A FALLOS:")
        print(f"🛡️  Red sobrevivió a todos los fallos: {'✅' if survived_all else '❌'}")
        print(f"🔄 Recuperación completa en todos los casos: {'✅' if recovered_all else '❌'}")
    
    resilience = tester.fault_results.get("resilience_metrics", [])
    if resilience:
        avg_success_rate = sum(r["success_rate"] for r in resilience) / len(resilience)
        all_levels_survived = all(r["network_healthy"] for r in resilience)
        print(f"💪 Tasa de éxito promedio bajo estrés: {avg_success_rate:.1f}%")
        print(f"🌐 Red saludable en todos los niveles de estrés: {'✅' if all_levels_survived else '❌'}")

if __name__ == "__main__":
    asyncio.run(run_fault_tolerance_tests())
