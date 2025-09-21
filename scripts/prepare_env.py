#!/usr/bin/env python3
"""
Script para preparar el entorno de desarrollo y crear archivos de prueba.
"""
import os
import sys
import subprocess
from pathlib import Path

def create_directories_and_files():
    """Crea directorios y archivos de prueba manualmente."""
    print("📁 Creando directorios y archivos de prueba...")
    
    base_dir = Path(__file__).parent.parent
    files_dir = base_dir / "files"
    
    # Crear directorios
    for peer_num in range(1, 4):
        peer_dir = files_dir / f"peer{peer_num}"
        peer_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Creado directorio: {peer_dir}")
    
    # Archivos de prueba específicos
    test_files = {
        "peer1": [
            ("documento1.txt", "Este es un documento del peer 1"),
            ("imagen1.jpg", "fake_image_data_peer1"),
            ("video_especial.mp4", "fake_video_data_especial_peer1"),  # ÚNICO en peer1
            ("config.yaml", "configuracion: peer1"),
        ],
        "peer2": [
            ("documento2.txt", "Este es un documento del peer 2"),
            ("imagen2.png", "fake_image_data_peer2"),
            ("video_comun.mp4", "fake_video_data_comun_peer2"),
            ("readme.md", "# README del peer 2"),  # ÚNICO en peer2
        ],
        "peer3": [
            ("documento3.txt", "Este es un documento del peer 3"),
            ("imagen3.gif", "fake_image_data_peer3"),
            ("video_comun.mp4", "fake_video_data_comun_peer3"),  # Duplicado con peer2
            ("script.py", "print('Hola desde peer 3')"),  # ÚNICO en peer3
        ]
    }
    
    # Crear archivos
    for peer, files in test_files.items():
        peer_dir = files_dir / peer
        for filename, content in files:
            file_path = peer_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ Creado archivo: {file_path}")
    
    print("\n✅ Archivos de prueba creados exitosamente!")
    print("\n📋 Archivos para probar búsqueda distribuida:")
    print("  - 'video_especial.mp4' → SOLO en peer1")
    print("  - 'readme.md' → SOLO en peer2")
    print("  - 'script.py' → SOLO en peer3")
    print("  - 'video_comun.mp4' → En peer2 y peer3 (múltiples resultados)")

def install_dependencies():
    """Instala las dependencias del proyecto."""
    print("\n📦 Instalando dependencias...")
    
    base_dir = Path(__file__).parent.parent
    requirements_file = base_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ Archivo requirements.txt no encontrado")
        return False
    
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        print(f"Salida de error: {e.stderr}")
        return False

def show_next_steps():
    """Muestra los próximos pasos para el usuario."""
    print("\n" + "="*60)
    print("🎉 ENTORNO PREPARADO - FASE 2 LISTA PARA PRUEBAS")
    print("="*60)
    
    print("\n📝 PRÓXIMOS PASOS:")
    
    print("\n1️⃣  Para iniciar la red P2P completa:")
    print("   python scripts/start_nodes.py")
    
    print("\n2️⃣  Para hacer pruebas manuales (con nodos ya iniciados):")
    print("   python scripts/test_client.py full-test")
    
    print("\n3️⃣  Para comandos individuales:")
    print("   python scripts/test_client.py --node 127.0.0.1:50001 search video_especial.mp4")
    print("   python scripts/test_client.py --node 127.0.0.1:50003 search readme.md")
    
    print("\n4️⃣  Para iniciar nodos individualmente:")
    print("   python simple_main.py --config config/peer_01.yaml")
    print("   python simple_main.py --config config/peer_02.yaml")
    print("   python simple_main.py --config config/peer_03.yaml")
    
    print("\n🎯 OBJETIVO DE LA FASE 2:")
    print("   ✓ Búsqueda distribuida con flooding (TTL=3)")
    print("   ✓ QuerySet para evitar redundancia")
    print("   ✓ Propagación de mensajes entre nodos")
    print("   ✓ Prueba: Nodo 3 busca archivo que solo tiene Nodo 1")

def main():
    print("🚀 PREPARANDO ENTORNO PARA FASE 2 - PROYECTO P2P")
    print("="*60)
    
    # Paso 1: Crear archivos de prueba
    try:
        create_directories_and_files()
    except Exception as e:
        print(f"❌ Error creando archivos: {e}")
        return
    
    # Paso 2: Instalar dependencias
    try:
        if not install_dependencies():
            print("⚠️  Continuando sin instalar dependencias...")
    except Exception as e:
        print(f"⚠️  Error instalando dependencias: {e}")
    
    # Paso 3: Mostrar próximos pasos
    show_next_steps()

if __name__ == "__main__":
    main()
