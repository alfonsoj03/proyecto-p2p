#!/usr/bin/env python3
"""
Script para crear directorios y archivos de prueba para el sistema P2P.
"""
import os
import sys

def create_test_files():
    """Crea directorios y archivos de prueba para cada peer."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files_dir = os.path.join(base_dir, "files")
    
    # Crear directorios base
    for peer_num in range(1, 4):
        peer_dir = os.path.join(files_dir, f"peer{peer_num}")
        os.makedirs(peer_dir, exist_ok=True)
        print(f"Creado directorio: {peer_dir}")
    
    # Crear archivos de prueba específicos para cada peer
    test_files = {
        "peer1": [
            ("documento1.txt", "Este es un documento del peer 1"),
            ("imagen1.jpg", "fake_image_data_peer1"),
            ("video_especial.mp4", "fake_video_data_especial_peer1"),
            ("config.yaml", "configuracion: peer1"),
        ],
        "peer2": [
            ("documento2.txt", "Este es un documento del peer 2"),
            ("imagen2.png", "fake_image_data_peer2"),
            ("video_comun.mp4", "fake_video_data_comun_peer2"),
            ("readme.md", "# README del peer 2"),
        ],
        "peer3": [
            ("documento3.txt", "Este es un documento del peer 3"),
            ("imagen3.gif", "fake_image_data_peer3"),
            ("video_comun.mp4", "fake_video_data_comun_peer3"),  # Archivo duplicado
            ("script.py", "print('Hola desde peer 3')"),
        ]
    }
    
    # Crear archivos
    for peer, files in test_files.items():
        peer_dir = os.path.join(files_dir, peer)
        for filename, content in files:
            file_path = os.path.join(peer_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Creado archivo: {file_path}")
    
    print("\n¡Archivos de prueba creados exitosamente!")
    print("Archivos únicos para probar búsqueda:")
    print("- 'video_especial.mp4' solo en peer1")
    print("- 'readme.md' solo en peer2") 
    print("- 'script.py' solo en peer3")
    print("- 'video_comun.mp4' en peer2 y peer3 (para probar múltiples resultados)")

if __name__ == "__main__":
    create_test_files()
