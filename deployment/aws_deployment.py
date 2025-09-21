#!/usr/bin/env python3
"""
Script de deployment en AWS para el sistema P2P - Fase 5.
Automatiza la creación de VMs y configuración de nodos en AWS EC2.
"""
import boto3
import time
import json
import base64
from pathlib import Path

class AWSP2PDeployer:
    """Deployer automático para nodos P2P en AWS EC2."""
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ec2_resource = boto3.resource('ec2', region_name=region)
        
        # Configuración de deployment
        self.deployment_config = {
            'instance_type': 't3.micro',  # Free tier eligible
            'ami_id': 'ami-0c55b159cbfafe1d0',  # Ubuntu 20.04 LTS (actualizar según región)
            'key_pair_name': 'p2p-project-key',
            'security_group_name': 'p2p-nodes-sg',
            'nodes': [
                {'name': 'p2p-node-1', 'rest_port': 50001, 'grpc_port': 51001},
                {'name': 'p2p-node-2', 'rest_port': 50002, 'grpc_port': 51002},
                {'name': 'p2p-node-3', 'rest_port': 50003, 'grpc_port': 51003}
            ]
        }
    
    def create_security_group(self):
        """Crear security group para nodos P2P."""
        try:
            print("🔒 Creando Security Group para nodos P2P...")
            
            # Crear security group
            response = self.ec2.create_security_group(
                GroupName=self.deployment_config['security_group_name'],
                Description='Security group for P2P nodes - REST and gRPC traffic'
            )
            
            security_group_id = response['GroupId']
            print(f"✅ Security Group creado: {security_group_id}")
            
            # Configurar reglas de entrada
            self.ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    # SSH
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    # REST APIs (50001-50003)
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 50001,
                        'ToPort': 50003,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    # gRPC (51001-51003)
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 51001,
                        'ToPort': 51003,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            
            print("✅ Reglas de Security Group configuradas")
            return security_group_id
            
        except Exception as e:
            print(f"❌ Error creando Security Group: {e}")
            return None
    
    def generate_user_data_script(self, node_config):
        """Generar script de inicialización para la instancia."""
        
        user_data = f"""#!/bin/bash
# Script de inicialización para nodo P2P - {node_config['name']}
        
# Actualizar sistema
apt-get update -y
apt-get install -y python3 python3-pip git

# Instalar dependencias Python
pip3 install fastapi uvicorn aiohttp pyyaml grpcio grpcio-tools psutil

# Crear usuario para P2P
useradd -m -s /bin/bash p2puser

# Crear directorios
mkdir -p /opt/p2p-project
mkdir -p /opt/p2p-project/files/peer{node_config['name'][-1]}
mkdir -p /opt/p2p-project/config
mkdir -p /opt/p2p-project/logs

# Crear archivos de ejemplo
cat > /opt/p2p-project/files/peer{node_config['name'][-1]}/sample_file_{node_config['name'][-1]}.txt << 'EOF'
Este es un archivo de ejemplo en {node_config['name']}
Creado automáticamente durante el deployment en AWS
Timestamp: $(date)
EOF

# Crear configuración del nodo
cat > /opt/p2p-project/config/peer_0{node_config['name'][-1]}.yaml << 'EOF'
peer_id: "peer_0{node_config['name'][-1]}"
ip: "0.0.0.0"  # Escuchar en todas las interfaces
rest_port: {node_config['rest_port']}
grpc_port: {node_config['grpc_port']}
files_directory: "/opt/p2p-project/files/peer{node_config['name'][-1]}"
EOF

# Configurar ownership
chown -R p2puser:p2puser /opt/p2p-project

# Crear servicio systemd
cat > /etc/systemd/system/p2p-node.service << 'EOF'
[Unit]
Description=P2P Node Service
After=network.target

[Service]
Type=simple
User=p2puser
WorkingDirectory=/opt/p2p-project
ExecStart=/usr/bin/python3 simple_main.py --config config/peer_0{node_config['name'][-1]}.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Log de finalización
echo "Inicialización de {node_config['name']} completada: $(date)" >> /opt/p2p-project/logs/init.log
"""
        
        return base64.b64encode(user_data.encode()).decode()
    
    def deploy_nodes(self):
        """Desplegar todos los nodos P2P en AWS."""
        print("🚀 INICIANDO DEPLOYMENT DE NODOS P2P EN AWS")
        print("="*60)
        
        # Crear security group
        security_group_id = self.create_security_group()
        if not security_group_id:
            print("❌ No se pudo crear Security Group")
            return
        
        deployed_instances = []
        
        for node_config in self.deployment_config['nodes']:
            print(f"\n🖥️  Desplegando {node_config['name']}...")
            
            try:
                # Generar user data
                user_data = self.generate_user_data_script(node_config)
                
                # Crear instancia EC2
                response = self.ec2.run_instances(
                    ImageId=self.deployment_config['ami_id'],
                    MinCount=1,
                    MaxCount=1,
                    InstanceType=self.deployment_config['instance_type'],
                    KeyName=self.deployment_config['key_pair_name'],
                    SecurityGroupIds=[security_group_id],
                    UserData=user_data,
                    TagSpecifications=[
                        {
                            'ResourceType': 'instance',
                            'Tags': [
                                {'Key': 'Name', 'Value': node_config['name']},
                                {'Key': 'Project', 'Value': 'P2P-Network'},
                                {'Key': 'RestPort', 'Value': str(node_config['rest_port'])},
                                {'Key': 'GrpcPort', 'Value': str(node_config['grpc_port'])}
                            ]
                        }
                    ]
                )
                
                instance_id = response['Instances'][0]['InstanceId']
                print(f"✅ Instancia creada: {instance_id}")
                
                deployed_instances.append({
                    'name': node_config['name'],
                    'instance_id': instance_id,
                    'rest_port': node_config['rest_port'],
                    'grpc_port': node_config['grpc_port']
                })
                
            except Exception as e:
                print(f"❌ Error desplegando {node_config['name']}: {e}")
        
        # Esperar a que las instancias estén running
        print(f"\n⏳ Esperando a que las instancias estén en estado 'running'...")
        self.wait_for_instances(deployed_instances)
        
        # Obtener IPs públicas
        instances_info = self.get_instances_info(deployed_instances)
        
        # Guardar información de deployment
        self.save_deployment_info(instances_info)
        
        print(f"\n🎉 DEPLOYMENT COMPLETADO")
        print("="*40)
        
        return instances_info
    
    def wait_for_instances(self, deployed_instances):
        """Esperar a que las instancias estén running."""
        instance_ids = [inst['instance_id'] for inst in deployed_instances]
        
        waiter = self.ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=instance_ids)
        
        print("✅ Todas las instancias están en estado 'running'")
    
    def get_instances_info(self, deployed_instances):
        """Obtener información detallada de las instancias."""
        print("\n📋 Obteniendo información de instancias...")
        
        instance_ids = [inst['instance_id'] for inst in deployed_instances]
        
        response = self.ec2.describe_instances(InstanceIds=instance_ids)
        
        instances_info = []
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                public_ip = instance.get('PublicIpAddress', 'N/A')
                private_ip = instance.get('PrivateIpAddress', 'N/A')
                
                # Encontrar configuración correspondiente
                node_config = next(
                    (inst for inst in deployed_instances if inst['instance_id'] == instance_id),
                    None
                )
                
                if node_config:
                    info = {
                        'name': node_config['name'],
                        'instance_id': instance_id,
                        'public_ip': public_ip,
                        'private_ip': private_ip,
                        'rest_port': node_config['rest_port'],
                        'grpc_port': node_config['grpc_port'],
                        'rest_endpoint': f"http://{public_ip}:{node_config['rest_port']}",
                        'grpc_endpoint': f"{public_ip}:{node_config['grpc_port']}"
                    }
                    
                    instances_info.append(info)
                    
                    print(f"🌐 {node_config['name']}:")
                    print(f"   Instance ID: {instance_id}")
                    print(f"   Public IP: {public_ip}")
                    print(f"   REST API: http://{public_ip}:{node_config['rest_port']}")
                    print(f"   gRPC: {public_ip}:{node_config['grpc_port']}")
        
        return instances_info
    
    def save_deployment_info(self, instances_info):
        """Guardar información del deployment."""
        deployment_info = {
            'timestamp': time.time(),
            'region': self.region,
            'security_group': self.deployment_config['security_group_name'],
            'instances': instances_info
        }
        
        # Crear directorio si no existe
        Path('deployment').mkdir(exist_ok=True)
        
        with open('deployment/aws_deployment_info.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        # Crear archivo de endpoints para testing
        endpoints = {
            'nodes': {
                info['name'].replace('-', '_'): {
                    'rest': info['rest_endpoint'],
                    'grpc': info['grpc_endpoint'],
                    'instance_id': info['instance_id']
                }
                for info in instances_info
            }
        }
        
        with open('deployment/aws_endpoints.json', 'w') as f:
            json.dump(endpoints, f, indent=2)
        
        print(f"\n📊 Información de deployment guardada:")
        print(f"   - deployment/aws_deployment_info.json")
        print(f"   - deployment/aws_endpoints.json")
    
    def generate_ssh_commands(self, instances_info):
        """Generar comandos SSH para conectarse a las instancias."""
        print(f"\n🔗 COMANDOS SSH PARA CONEXIÓN:")
        print("-" * 40)
        
        for info in instances_info:
            print(f"# Conectar a {info['name']}")
            print(f"ssh -i {self.deployment_config['key_pair_name']}.pem ubuntu@{info['public_ip']}")
            print()
    
    def cleanup_deployment(self):
        """Limpiar deployment (terminar instancias)."""
        print("🧹 LIMPIANDO DEPLOYMENT...")
        
        # Obtener instancias con tag Project=P2P-Network
        response = self.ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Project', 'Values': ['P2P-Network']},
                {'Name': 'instance-state-name', 'Values': ['running', 'pending']}
            ]
        )
        
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        if instance_ids:
            print(f"🗑️  Terminando {len(instance_ids)} instancias...")
            self.ec2.terminate_instances(InstanceIds=instance_ids)
            print("✅ Instancias terminadas")
        
        # Eliminar security group
        try:
            self.ec2.delete_security_group(GroupName=self.deployment_config['security_group_name'])
            print("✅ Security Group eliminado")
        except Exception as e:
            print(f"⚠️  No se pudo eliminar Security Group: {e}")

def main():
    """Función principal de deployment."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AWS P2P Deployment Tool")
    parser.add_argument("action", choices=["deploy", "cleanup", "info"], help="Acción a realizar")
    parser.add_argument("--region", default="us-east-1", help="Región de AWS")
    
    args = parser.parse_args()
    
    deployer = AWSP2PDeployer(region=args.region)
    
    if args.action == "deploy":
        instances_info = deployer.deploy_nodes()
        if instances_info:
            deployer.generate_ssh_commands(instances_info)
            
            print(f"\n🎯 PRÓXIMOS PASOS:")
            print("1. Esperar 2-3 minutos para que se complete la inicialización")
            print("2. Conectarse vía SSH y subir el código del proyecto")
            print("3. Ejecutar: python3 simple_main.py --config config/peer_XX.yaml")
            print("4. Probar endpoints REST y gRPC")
            
    elif args.action == "cleanup":
        deployer.cleanup_deployment()
        
    elif args.action == "info":
        try:
            with open('deployment/aws_deployment_info.json', 'r') as f:
                info = json.load(f)
            
            print("📊 INFORMACIÓN DE DEPLOYMENT ACTUAL:")
            print(f"Región: {info['region']}")
            print(f"Instancias desplegadas: {len(info['instances'])}")
            
            for instance in info['instances']:
                print(f"\n🖥️  {instance['name']}:")
                print(f"   REST: {instance['rest_endpoint']}")
                print(f"   gRPC: {instance['grpc_endpoint']}")
                
        except FileNotFoundError:
            print("❌ No se encontró información de deployment")

if __name__ == "__main__":
    main()
