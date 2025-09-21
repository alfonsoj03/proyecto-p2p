# FASE 2 - BÚSQUEDA DISTRIBUIDA COMPLETADA ✅

## 🎯 Objetivo de la Fase 2
Implementar la propagación de consultas entre nodos usando flooding con TTL=3 para lograr búsqueda distribuida en la red P2P.

## ✅ Funcionalidades Implementadas

### 1. Sistema de Búsqueda con Flooding
- **Algoritmo de flooding** con TTL (Time To Live) = 3
- **Propagación paralela** a múltiples nodos vecinos
- **Búsqueda local** en cada nodo visitado
- **Combinación de resultados** de todos los nodos

### 2. QuerySet para Evitar Redundancia
- **Almacenamiento de queryIDs** procesados (máximo 5)
- **Verificación de duplicados** antes de procesar consultas
- **Prevención de loops infinitos** en la red

### 3. Cliente HTTP Asíncrono
- **Comunicación HTTP** entre nodos con retry logic
- **Manejo de timeouts** y errores de conexión
- **Requests paralelos** para optimizar performance

### 4. APIs REST Extendidas
- `POST /directory/search` - Búsqueda con parámetros completos
- `GET /directory/search/simple/{filename}` - Búsqueda simplificada
- Logging detallado de todas las operaciones

## 🚀 Cómo Ejecutar las Pruebas

### Preparación del Entorno
```bash
# 1. Preparar archivos de prueba y dependencias
python scripts/prepare_env.py

# 2. Iniciar la red P2P completa (3 nodos + bootstrap)
python scripts/start_nodes.py
```

### Pruebas Automatizadas
```bash
# Ejecutar prueba completa de la Fase 2
python scripts/test_client.py full-test
```

### Pruebas Manuales
```bash
# Buscar archivo que SOLO está en peer1
python scripts/test_client.py --node 127.0.0.1:50003 search video_especial.mp4

# Buscar archivo que SOLO está en peer2  
python scripts/test_client.py --node 127.0.0.1:50001 search readme.md

# Buscar archivo que SOLO está en peer3
python scripts/test_client.py --node 127.0.0.1:50002 search script.py

# Buscar archivo duplicado (peer2 y peer3)
python scripts/test_client.py --node 127.0.0.1:50001 search video_comun.mp4
```

## 🔍 Pruebas de la Fase 2

### Escenario Principal: Nodo 3 → Nodo 1
**Objetivo**: Nodo 3 busca archivo que solo tiene Nodo 1

**Flujo de búsqueda**:
1. **Nodo 3** inicia búsqueda de `video_especial.mp4`
2. **Nodo 3** busca localmente (no encuentra)
3. **Nodo 3** propaga a vecinos: Nodo 2
4. **Nodo 2** recibe búsqueda, busca localmente (no encuentra)
5. **Nodo 2** propaga a vecinos: Nodo 1
6. **Nodo 1** recibe búsqueda, busca localmente ✅ **ENCUENTRA**
7. **Nodo 1** retorna resultado a Nodo 2
8. **Nodo 2** retorna resultado a Nodo 3
9. **Nodo 3** recibe resultado final

### Casos de Prueba Adicionales
- ✅ **Archivos únicos**: Búsqueda encuentra exactamente 1 resultado
- ✅ **Archivos duplicados**: Búsqueda encuentra múltiples resultados
- ✅ **Archivos inexistentes**: Búsqueda retorna 0 resultados
- ✅ **QuerySet**: Evita procesar la misma consulta múltiples veces
- ✅ **TTL**: Limita la propagación a máximo 3 saltos

## 📊 Arquitectura de la Búsqueda

```
Nodo 3 (Origen)     Nodo 2 (Intermedio)     Nodo 1 (Destino)
     │                        │                      │
     ├── Búsqueda local      ├── Búsqueda local     ├── Búsqueda local
     │   (no encuentra)      │   (no encuentra)     │   ✅ ENCUENTRA
     │                       │                      │
     ├── Propagar TTL=2 ──→  ├── Propagar TTL=1 ──→ ├── Retorna resultado
     │                       │                      │
     ←── Resultado final ←── ←── Resultado ←────────
```

## 🔧 Archivos Modificados/Creados

### Archivos de Servicio
- `services/directory_simple/service.py` - Lógica de flooding y querySet
- `services/directory_simple/api.py` - Endpoints de búsqueda
- `services/http_client.py` - Cliente HTTP asíncrono

### Scripts de Prueba
- `scripts/prepare_env.py` - Preparación del entorno
- `scripts/start_nodes.py` - Gestión de múltiples nodos
- `scripts/test_client.py` - Cliente de pruebas
- `scripts/setup_test_files.py` - Creación de archivos de prueba

### Configuración
- `config/peer_03.yaml` - Configuración del tercer nodo
- `requirements.txt` - Dependencia `aiohttp` agregada

## 🎯 Criterios de Éxito - CUMPLIDOS ✅

- ✅ **Flooding implementado** con TTL=3
- ✅ **QuerySet funcional** (máximo 5 queryIDs)
- ✅ **Propagación entre nodos** funcionando
- ✅ **Búsqueda distribuida exitosa**: Nodo 3 encuentra archivo de Nodo 1
- ✅ **Concurrencia asíncrona** con FastAPI y aiohttp
- ✅ **Manejo de errores** y timeouts
- ✅ **Logging detallado** de operaciones

## 📈 Próximos Pasos - FASE 3

1. **Implementar gRPC Transfer Service**
   - Download(FileRequest) → FileResponse
   - Upload(FileRequest) → Ack

2. **Integración con File Service**
   - Tras download, ejecutar indexar()
   - Actualizar índice local

3. **Pruebas de transferencia real**
   - Cliente A descarga archivo de Cliente B
   - Verificar que se indexe localmente

---

**🎉 FASE 2 COMPLETADA EXITOSAMENTE** 

La búsqueda distribuida está funcionando correctamente. El sistema puede propagar consultas a través de la red P2P y encontrar archivos en nodos remotos usando flooding con TTL.
