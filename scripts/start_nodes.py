#!/usr/bin/env python3
"""
Script para iniciar múltiples nodos P2P para pruebas.
Inicia los nodos en procesos separados y maneja el bootstrap.
"""
import asyncio
import subprocess
import sys
import os
import time
import aiohttp
from pathlib import Path

class NodeManager:
    def __init__(self):
        self.processes = []
        self.base_dir = Path(__file__).parent.parent
        
    async def check_node_health(self, address: str, max_retries: int = 10) -> bool:
        """Verifica si un nodo está respondiendo."""
        url = f"http://{address}/directory/dl/all"
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            print(f"✓ Nodo {address} está activo")
                            return True
            except:
                pass
            
            if attempt < max_retries - 1:
                print(f"⏳ Esperando nodo {address}... (intento {attempt + 1}/{max_retries})")
                await asyncio.sleep(1)
        
        print(f"❌ Nodo {address} no respondió después de {max_retries} intentos")
        return False

    def start_node(self, peer_config: str) -> subprocess.Popen:
        """Inicia un nodo con la configuración especificada."""
        cmd = [
            sys.executable, 
            str(self.base_dir / "simple_main.py"),
            "--config", str(self.base_dir / "config" / peer_config),
            "--ip", "127.0.0.1"
        ]
        
        print(f"🚀 Iniciando nodo con config: {peer_config}")
        print(f"Comando: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            cwd=str(self.base_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        self.processes.append(process)
        return process

    async def bootstrap_network(self):
        """Bootstrap de la red P2P según el plan de fases."""
        print("\n🌐 INICIANDO BOOTSTRAP DE LA RED P2P")
        print("="*50)
        
        # Configuraciones de nodos
        node_configs = [
            ("peer_01.yaml", "127.0.0.1:50001"),
            ("peer_02.yaml", "127.0.0.1:50002"),
            ("peer_03.yaml", "127.0.0.1:50003")
        ]
        
        # Paso 1: Iniciar nodos seed (peer1 y peer2)
        print("\n📡 Paso 1: Iniciando nodos seed...")
        
        # Iniciar peer1 (nodo seed principal)
        peer1_process = self.start_node("peer_01.yaml")
        await asyncio.sleep(2)
        
        # Verificar que peer1 esté activo
        if not await self.check_node_health("127.0.0.1:50001"):
            print("❌ Error: peer1 no se inició correctamente")
            return False
        
        # Iniciar peer2 (nodo seed secundario)
        peer2_process = self.start_node("peer_02.yaml")
        await asyncio.sleep(2)
        
        # Verificar que peer2 esté activo
        if not await self.check_node_health("127.0.0.1:50002"):
            print("❌ Error: peer2 no se inició correctamente")
            return False
        
        # Paso 2: Bootstrap de peer2 con peer1
        print("\n🔗 Paso 2: Bootstrap de peer2 con peer1...")
        await self.login_peer("127.0.0.1:50001", "127.0.0.1:50002")
        await asyncio.sleep(1)
        
        # Paso 3: Iniciar peer3 y bootstrap con peer2
        print("\n📡 Paso 3: Iniciando peer3 y bootstrap...")
        peer3_process = self.start_node("peer_03.yaml")
        await asyncio.sleep(2)
        
        # Verificar que peer3 esté activo
        if not await self.check_node_health("127.0.0.1:50003"):
            print("❌ Error: peer3 no se inició correctamente")
            return False
        
        # Bootstrap de peer3 con peer2
        await self.login_peer("127.0.0.1:50002", "127.0.0.1:50003")
        await asyncio.sleep(1)
        
        # Paso 4: Verificar estado final de la red
        print("\n📊 Paso 4: Verificando estado final de la red...")
        await self.verify_network_state()
        
        print("\n✅ BOOTSTRAP COMPLETADO")
        print("="*50)
        print("La red P2P está lista para pruebas de la Fase 2")
        print("\nPara hacer pruebas manuales:")
        print("python scripts/test_client.py full-test")
        print("\nPara parar todos los nodos, presiona Ctrl+C")
        
        return True

    async def login_peer(self, target_node: str, new_peer: str):
        """Realiza login de un peer en otro nodo."""
        url = f"http://{target_node}/directory/login"
        data = {"address": new_peer}
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            dl = result.get("dl", [])
                            print(f"✓ Login {new_peer} → {target_node} exitoso. DL: {dl}")
                        else:
                            print(f"❌ Login falló: {result.get('error')}")
                    else:
                        print(f"❌ Login HTTP error: {response.status}")
        except Exception as e:
            print(f"❌ Error en login: {e}")

    async def verify_network_state(self):
        """Verifica el estado de toda la red."""
        nodes = [
            ("peer1", "127.0.0.1:50001"),
            ("peer2", "127.0.0.1:50002"),
            ("peer3", "127.0.0.1:50003")
        ]
        
        for name, address in nodes:
            print(f"\n--- Estado de {name.upper()} ({address}) ---")
            await self.get_directory_list(address)

    async def get_directory_list(self, node: str):
        """Obtiene y muestra la Directory List de un nodo."""
        url = f"http://{node}/directory/dl/all"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            dl = result.get("dl", [])
                            print(f"Directory List: {dl}")
                        else:
                            print(f"Error obteniendo DL: {result.get('error')}")
                    else:
                        print(f"HTTP error obteniendo DL: {response.status}")
        except Exception as e:
            print(f"Error obteniendo DL: {e}")

    def cleanup(self):
        """Termina todos los procesos de nodos."""
        print("\n🧹 Terminando todos los nodos...")
        for i, process in enumerate(self.processes):
            try:
                process.terminate()
                print(f"✓ Terminado proceso {i+1}")
            except:
                try:
                    process.kill()
                    print(f"✓ Forzado termine de proceso {i+1}")
                except:
                    print(f"❌ No se pudo terminar proceso {i+1}")

async def main():
    manager = NodeManager()
    
    try:
        # Crear archivos de prueba primero
        print("📁 Creando archivos de prueba...")
        setup_script = manager.base_dir / "scripts" / "setup_test_files.py"
        if setup_script.exists():
            result = subprocess.run([sys.executable, str(setup_script)], 
                                  cwd=str(manager.base_dir), 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Archivos de prueba creados")
            else:
                print(f"⚠️  Error creando archivos: {result.stderr}")
        
        # Iniciar bootstrap
        success = await manager.bootstrap_network()
        
        if success:
            # Mantener nodos activos
            print("\n⌨️  Presiona Ctrl+C para parar todos los nodos...")
            while True:
                await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Parando nodos...")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    finally:
        manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
