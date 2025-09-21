#!/usr/bin/env python3
"""
Script para generar código Python desde archivos .proto
"""
import subprocess
import sys
from pathlib import Path

def generate_grpc_code():
    """Genera código Python desde archivos .proto usando protoc."""
    
    base_dir = Path(__file__).parent.parent
    proto_dir = base_dir / "protos"
    output_dir = base_dir / "services" / "transfer_grpc"
    
    # Crear directorio de salida
    output_dir.mkdir(exist_ok=True)
    
    # Archivo .proto
    proto_file = proto_dir / "transfer.proto"
    
    if not proto_file.exists():
        print(f"❌ Archivo .proto no encontrado: {proto_file}")
        return False
    
    print(f"📄 Generando código desde: {proto_file}")
    print(f"📁 Directorio de salida: {output_dir}")
    
    try:
        # Comando para generar código Python
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            str(proto_file)
        ]
        
        print(f"🔨 Ejecutando: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Código gRPC generado exitosamente")
        
        # Verificar archivos generados
        generated_files = [
            output_dir / "transfer_pb2.py",
            output_dir / "transfer_pb2_grpc.py"
        ]
        
        for file_path in generated_files:
            if file_path.exists():
                print(f"✓ Generado: {file_path.name}")
            else:
                print(f"❌ No se generó: {file_path.name}")
        
        # Crear __init__.py
        init_file = output_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write('"""Transfer gRPC service module"""\n')
        print(f"✓ Creado: {init_file.name}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generando código gRPC:")
        print(f"   Código de salida: {e.returncode}")
        print(f"   Stdout: {e.stdout}")
        print(f"   Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    print("🚀 GENERANDO CÓDIGO gRPC PARA TRANSFER SERVICE")
    print("="*50)
    
    if generate_grpc_code():
        print("\n✅ Generación completada exitosamente")
        print("\nArchivos generados:")
        print("  - services/transfer_grpc/transfer_pb2.py")
        print("  - services/transfer_grpc/transfer_pb2_grpc.py")
        print("  - services/transfer_grpc/__init__.py")
    else:
        print("\n❌ Error en la generación")
        print("\nVerifica que tengas instalado grpcio-tools:")
        print("  pip install grpcio-tools")

if __name__ == "__main__":
    main()
