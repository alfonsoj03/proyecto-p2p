#!/usr/bin/env python3
"""
Script de preparación completa para la Fase 3 - Transfer Service con gRPC.
"""
import os
import sys
import subprocess
from pathlib import Path

def generate_grpc_code():
    """Genera código Python desde archivos .proto."""
    print("🔨 Generando código gRPC...")
    
    base_dir = Path(__file__).parent.parent
    script_path = base_dir / "scripts" / "generate_grpc.py"
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              cwd=str(base_dir), 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Código gRPC generado exitosamente")
            return True
        else:
            print(f"❌ Error generando código gRPC:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando generate_grpc.py: {e}")
        return False

def create_test_files():
    """Crea archivos de prueba para la Fase 3."""
    print("📁 Creando archivos de prueba...")
    
    base_dir = Path(__file__).parent.parent
    script_path = base_dir / "scripts" / "setup_test_files.py"
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              cwd=str(base_dir), 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Archivos de prueba creados")
            return True
        else:
            print(f"⚠️  Error creando archivos de prueba:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando setup_test_files.py: {e}")
        return False

def verify_structure():
    """Verifica que la estructura del proyecto esté completa."""
    print("🔍 Verificando estructura del proyecto...")
    
    base_dir = Path(__file__).parent.parent
    
    required_files = [
        "protos/transfer.proto",
        "services/transfer_grpc/__init__.py",
        "services/transfer_grpc/service.py", 
        "services/transfer_grpc/client.py",
        "config/peer_01.yaml",
        "config/peer_02.yaml",
        "config/peer_03.yaml",
        "simple_main.py",
        "scripts/test_client.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Archivos faltantes:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print("✅ Estructura del proyecto verificada")
    return True

def check_grpc_generated():
    """Verifica que el código gRPC esté generado."""
    print("🔍 Verificando código gRPC generado...")
    
    base_dir = Path(__file__).parent.parent
    grpc_files = [
        "services/transfer_grpc/transfer_pb2.py",
        "services/transfer_grpc/transfer_pb2_grpc.py"
    ]
    
    for file_path in grpc_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            print(f"❌ Archivo gRPC no encontrado: {file_path}")
            return False
    
    print("✅ Código gRPC verificado")
    return True

def show_usage_instructions():
    """Muestra instrucciones de uso para la Fase 3."""
    print("\n" + "="*70)
    print("🎉 FASE 3 PREPARADA - TRANSFER SERVICE CON gRPC")
    print("="*70)
    
    print("\n📋 CARACTERÍSTICAS DE LA FASE 3:")
    print("  ✅ Transferencia real de archivos con gRPC")
    print("  ✅ Streaming eficiente para archivos grandes (chunks de 64KB)")
    print("  ✅ Métodos Download, Upload y CheckFile")
    print("  ✅ Indexación automática tras descarga exitosa")
    print("  ✅ Integración completa con búsqueda distribuida")
    print("  ✅ Concurrencia: REST (FastAPI) + gRPC en paralelo")
    
    print("\n🚀 CÓMO EJECUTAR LA FASE 3:")
    
    print("\n1️⃣  Iniciar red completa con gRPC:")
    print("   python scripts/start_nodes.py")
    
    print("\n2️⃣  Prueba completa de Fase 3:")
    print("   python scripts/test_client.py full-test-phase3")
    
    print("\n3️⃣  Comandos individuales gRPC:")
    print("   # Verificar archivo")
    print("   python scripts/test_client.py check video_especial.mp4 --in-node 127.0.0.1:50001")
    print("   ")
    print("   # Descargar archivo")
    print("   python scripts/test_client.py download video_especial.mp4 --from-node 127.0.0.1:50001")
    print("   ")
    print("   # Subir archivo")
    print("   python scripts/test_client.py upload mi_archivo.txt --to-node 127.0.0.1:50002")
    
    print("\n4️⃣  Iniciar nodos individuales con gRPC:")
    print("   python simple_main.py --config config/peer_01.yaml")
    print("   python simple_main.py --config config/peer_02.yaml") 
    print("   python simple_main.py --config config/peer_03.yaml")
    
    print("\n5️⃣  Solo REST (sin gRPC):")
    print("   python simple_main.py --config config/peer_01.yaml --no-grpc")
    
    print("\n📊 FLUJO COMPLETO FASE 3:")
    print("   1. Nodo A busca archivo X (Fase 2)")
    print("   2. Encuentra que Nodo B tiene archivo X")
    print("   3. Nodo A descarga archivo X desde Nodo B vía gRPC")
    print("   4. Archivo X se indexa automáticamente en Nodo A")
    print("   5. Nodo A ahora tiene archivo X disponible localmente")
    
    print("\n🎯 OBJETIVO PRINCIPAL CUMPLIDO:")
    print("   ✅ PCliente en Nodo A descarga archivo de Nodo B")
    print("   ✅ Transferencia real de datos (no solo índices)")
    print("   ✅ Integración completa: Búsqueda → Descarga → Índice")

def main():
    print("🚀 PREPARANDO FASE 3 - TRANSFER SERVICE CON gRPC")
    print("="*60)
    
    success = True
    
    # Paso 1: Verificar estructura
    if not verify_structure():
        print("❌ Estructura del proyecto incompleta")
        success = False
    
    # Paso 2: Crear archivos de prueba
    if not create_test_files():
        print("⚠️  Continuando sin archivos de prueba...")
    
    # Paso 3: Generar código gRPC
    if not generate_grpc_code():
        print("❌ No se pudo generar código gRPC")
        success = False
    
    # Paso 4: Verificar que el código gRPC se generó correctamente
    if success and not check_grpc_generated():
        print("❌ Código gRPC no está disponible")
        success = False
    
    if success:
        show_usage_instructions()
    else:
        print("\n❌ PREPARACIÓN FALLIDA")
        print("Verifica que tengas instalado grpcio-tools:")
        print("  pip install grpcio-tools")
        print("\nRevisa los errores arriba para más detalles.")

if __name__ == "__main__":
    main()
