# Documentación Completa - Sistema Logístico Agrícola

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Instalación y Configuración](#instalación-y-configuración)
5. [Componentes Principales](#componentes-principales)
6. [API REST](#api-rest)
7. [Modelo de Datos](#modelo-de-datos)
8. [Sistema de Inteligencia Artificial](#sistema-de-inteligencia-artificial)
9. [Integración con OSMnx](#integración-con-osmnx)
10. [Interfaz de Usuario](#interfaz-de-usuario)
11. [Ejemplos de Uso](#ejemplos-de-uso)
12. [Troubleshooting](#troubleshooting)

---

## 📖 Descripción General

El **Sistema Logístico Agrícola** es una aplicación web interactiva diseñada para visualizar, analizar y optimizar rutas logísticas en el sector agrícola del condado de Yuma, Arizona. El sistema integra:

- **Visualización geográfica** de parcelas, centros de acopio y plantas extractoras
- **Cálculo de rutas** considerando distancias reales y tipos de camino
- **Predicción de producción** mediante Machine Learning (Random Forest)
- **Optimización de rutas** basada en múltiples criterios (costo, tiempo, distancia, accesibilidad)
- **Análisis de accesibilidad** considerando condiciones climáticas (lluvia)

### Objetivos del Sistema

- Optimizar rutas de recolección agrícola
- Predecir producción para planificación logística
- Analizar costos de transporte
- Considerar condiciones climáticas en la planificación
- Visualizar la red logística completa

---

## 🏗️ Arquitectura del Sistema

El sistema sigue una arquitectura de tres capas:

```
┌─────────────────────────────────────────┐
│         Frontend (Leaflet.js)           │
│  - Visualización de mapas              │
│  - Interacción con usuario              │
│  - Llamadas AJAX a API                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Backend (Flask REST API)           │
│  - Endpoints REST                        │
│  - Serialización JSON                   │
│  - Manejo de errores                    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│   Lógica de Negocio (Python)            │
│  - Grafo NetworkX                       │
│  - Modelo de IA (scikit-learn)          │
│  - Integración OSMnx                     │
│  - Cálculo de rutas                      │
└─────────────────────────────────────────┘
```

### Flujo de Datos

1. **Inicialización**: El sistema genera datos simulados y crea el grafo
2. **Entrenamiento**: Se entrena el modelo de IA con datos de parcelas
3. **Servicio Web**: Flask expone endpoints REST
4. **Visualización**: El frontend consume la API y muestra datos en el mapa

---

## 📁 Estructura del Proyecto

```
ruta_agronoma/
├── app.py                      # Aplicación Flask principal
├── agricultural_graph.py       # Lógica del grafo e IA
├── test_system.py             # Script de pruebas
├── enviroment.yml             # Configuración Conda
├── iniciar_servidor.bat       # Script inicio Windows
├── iniciar_servidor.sh         # Script inicio Linux/Mac
├── proyecto_prog.ipynb         # Notebook de ejemplo
├── README.md                   # Documentación básica
├── DOCUMENTACION.md            # Esta documentación
│
├── templates/
│   └── mapa.html              # Interfaz web con mapa interactivo
│
├── cache/                      # Cache de datos OSMnx (JSON)
│   └── [archivos .json]
│
└── venv/                       # Entorno virtual Python
    └── [dependencias]
```

---

## 🔧 Instalación y Configuración

### Requisitos Previos

- Python 3.10 o superior
- pip o conda
- Conexión a Internet (para descargar datos de OSMnx)

### Instalación con Conda (Recomendado)

```bash
# Crear entorno conda
conda env create -f enviroment.yml

# Activar entorno
conda activate entorno_geo
```

### Instalación con pip

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install flask numpy pandas networkx scikit-learn folium osmnx geopandas shapely
```

### Verificar Instalación

```bash
# Ejecutar script de prueba
python test_system.py
```

Este script verifica que:
- El grafo se inicializa correctamente
- Se pueden calcular rutas
- El modelo de IA funciona

---

## 🧩 Componentes Principales

### 1. `agricultural_graph.py`

Módulo principal que contiene la clase `AgriculturalGraphSystem`:

#### Métodos Principales

- **`generar_datos()`**: Genera datos simulados de parcelas, acopios y planta
- **`crear_grafo()`**: Construye el grafo dirigido con nodos y aristas
- **`entrenar_modelo_ia()`**: Entrena el modelo Random Forest
- **`predecir_produccion(parcela_id)`**: Predice producción de una parcela
- **`calcular_ruta_entre_nodos(nodo1, nodo2)`**: Calcula ruta entre dos nodos
- **`calcular_rutas_optimas_por_produccion()`**: Encuentra rutas óptimas
- **`priorizar_parcelas_por_rendimiento()`**: Prioriza parcelas por rendimiento
- **`descargar_grafo_osmnx()`**: Descarga red vial real de OpenStreetMap

#### Atributos Principales

- `G_agricola`: Grafo NetworkX con nodos y aristas agrícolas
- `G_osmnx`: Grafo OSMnx con red vial real
- `df_parcelas`: DataFrame con información de parcelas
- `df_acopios`: DataFrame con información de centros de acopio
- `df_aristas`: DataFrame con información de rutas
- `modelo_ia`: Modelo Random Forest entrenado

### 2. `app.py`

Aplicación Flask que expone la API REST:

#### Funciones de Utilidad

- **`sanitize_for_json()`**: Convierte valores NaN/Infinity a valores JSON válidos

#### Endpoints (ver sección API REST)

### 3. `templates/mapa.html`

Interfaz web interactiva con:

- Mapa Leaflet.js
- Panel de control lateral
- Visualización de nodos y rutas
- Interacción con clics
- Leyenda de elementos

---

## 🌐 API REST

### Base URL

```
http://localhost:5000
```

### Endpoints

#### 1. `GET /`

**Descripción**: Página principal con el mapa interactivo

**Respuesta**: HTML del mapa

---

#### 2. `GET /api/nodos`

**Descripción**: Obtiene todos los nodos del grafo

**Respuesta**:
```json
[
  {
    "id": "PARCELA_001",
    "tipo": "parcela_cultivo",
    "latitud": 32.6927,
    "longitud": -114.6277,
    "info": {
      "cultivo": "Naranjas",
      "area_hectareas": 150.5,
      "produccion_estimada_ton": 350.2,
      "tiene_cuarto_frio": true
    }
  }
]
```

**Tipos de nodos**:
- `parcela_cultivo`: Parcelas de cultivo
- `centro_acopio`: Centros de acopio
- `planta_extractora`: Planta extractora

---

#### 3. `GET /api/aristas`

**Descripción**: Obtiene todas las aristas (rutas) del grafo

**Respuesta**:
```json
[
  {
    "origen": "PARCELA_001",
    "destino": "ACOPIO_01",
    "origen_lat": 32.6927,
    "origen_lon": -114.6277,
    "destino_lat": 32.7000,
    "destino_lon": -114.6200,
    "distancia_km": 15.5,
    "tiempo_minutos": 18.3,
    "costo_por_ton": 2.33,
    "tipo_camino": "pavimentado",
    "accesibilidad_lluvia": 0.95,
    "coordenadas_ruta": [[32.6927, -114.6277], ...],
    "usar_ruta_real": true
  }
]
```

**Tipos de camino**:
- `pavimentado`: Carreteras pavimentadas
- `grava`: Caminos de grava
- `tierra`: Caminos de tierra

---

#### 4. `POST /api/ruta`

**Descripción**: Calcula ruta entre dos nodos

**Body**:
```json
{
  "nodo1": "PARCELA_001",
  "nodo2": "ACOPIO_01"
}
```

**Respuesta**:
```json
{
  "nodo1": {
    "id": "PARCELA_001",
    "tipo": "parcela_cultivo",
    "latitud": 32.6927,
    "longitud": -114.6277,
    "info": {...}
  },
  "nodo2": {
    "id": "ACOPIO_01",
    "tipo": "centro_acopio",
    "latitud": 32.7000,
    "longitud": -114.6200,
    "info": {...}
  },
  "distancia_directa_km": 12.5,
  "ruta_grafo": {
    "existe_ruta": true,
    "distancia_km": 15.5,
    "tiempo_minutos": 18.3,
    "costo_por_ton": 2.33,
    "tipo_camino": "pavimentado",
    "accesibilidad_lluvia": 0.95,
    "ruta": ["PARCELA_001", "ACOPIO_01"],
    "coordenadas_ruta": [[32.6927, -114.6277], ...],
    "usar_ruta_real": true
  }
}
```

---

#### 5. `GET /api/prediccion/<nodo_id>`

**Descripción**: Obtiene predicción de producción de una parcela

**Parámetros**:
- `nodo_id`: ID de la parcela (ej: `PARCELA_001`)

**Respuesta**:
```json
{
  "parcela_id": "PARCELA_001",
  "produccion_original": 350.2,
  "produccion_predicha": 385.5,
  "diferencia": 35.3,
  "porcentaje_cambio": 10.08
}
```

**Errores**:
- `404`: Nodo no encontrado
- `400`: El nodo no es una parcela de cultivo

---

#### 6. `GET /api/rutas-optimas/<parcela_id>`

**Descripción**: Obtiene rutas óptimas desde una parcela

**Parámetros de Query**:
- `criterio`: `costo`, `tiempo`, `distancia`, o `accesibilidad` (default: `costo`)
- `lluvia`: `true` o `false` (default: `false`)

**Ejemplo**:
```
GET /api/rutas-optimas/PARCELA_001?criterio=costo&lluvia=false
```

**Respuesta**:
```json
{
  "parcela_id": "PARCELA_001",
  "criterio": "costo",
  "considerar_lluvia": false,
  "rutas": [
    {
      "destino": "ACOPIO_01",
      "peso": 582.75,
      "distancia_km": 15.5,
      "tiempo_minutos": 18.3,
      "costo_total": 582.75,
      "accesibilidad_lluvia": 0.95,
      "tipo_camino": "pavimentado",
      "produccion_predicha": 375.0,
      "destino_info": {...}
    }
  ]
}
```

---

#### 7. `GET /api/parcelas-priorizadas`

**Descripción**: Obtiene parcelas priorizadas por rendimiento

**Parámetros de Query**:
- `top`: Número de parcelas a retornar (default: `10`)

**Ejemplo**:
```
GET /api/parcelas-priorizadas?top=10
```

**Respuesta**:
```json
{
  "total": 10,
  "parcelas": [
    {
      "parcela_id": "PARCELA_015",
      "produccion_original": 450.0,
      "produccion_predicha": 485.2,
      "rendimiento_esperado": 485.2,
      "area_hectareas": 180.5,
      "rendimiento_por_hectarea": 2.69,
      "latitud": 32.7500,
      "longitud": -114.6000
    }
  ]
}
```

---

#### 8. `GET /api/predicciones-todas`

**Descripción**: Obtiene predicciones de todas las parcelas (para colorear mapa)

**Respuesta**:
```json
{
  "predicciones": [
    {
      "parcela_id": "PARCELA_001",
      "produccion_original": 350.2,
      "produccion_predicha": 385.5,
      "latitud": 32.6927,
      "longitud": -114.6277
    }
  ],
  "min_produccion": 250.0,
  "max_produccion": 500.0
}
```

---

## 📊 Modelo de Datos

### Nodos

#### Parcela de Cultivo
```python
{
    "id": "PARCELA_001",
    "tipo": "parcela_cultivo",
    "latitud": float,
    "longitud": float,
    "cultivo": "Naranjas",
    "area_hectareas": float,
    "produccion_estimada_ton": float,
    "capacidad_almacenamiento_ton": float,
    "tiene_cuarto_frio": bool
}
```

#### Centro de Acopio
```python
{
    "id": "ACOPIO_01",
    "tipo": "centro_acopio",
    "latitud": float,
    "longitud": float,
    "capacidad_ton": float,
    "tiene_cadena_frio": bool,
    "num_camiones_disponibles": int
}
```

#### Planta Extractora
```python
{
    "id": "PLANTA_EXTRACTORA_01",
    "tipo": "planta_extractora",
    "latitud": float,
    "longitud": float,
    "capacidad_procesamiento_ton_dia": int,
    "horario_operacion": "24/7",
    "requiere_cadena_frio": bool
}
```

### Aristas (Rutas)

```python
{
    "origen": "PARCELA_001",
    "destino": "ACOPIO_01",
    "distancia_metros": float,
    "distancia_km": float,
    "tiempo_segundos": float,
    "tiempo_minutos": float,
    "costo_por_ton_dolares": float,
    "tipo_camino": "pavimentado" | "grava" | "tierra",
    "velocidad_promedio_kmh": float,
    "accesibilidad_lluvia": float,  # 0.0 - 1.0
    "tipo_conexion": "parcela_acopio" | "acopio_planta" | "parcela_planta_directa",
    "usar_ruta_real": bool,
    "coordenadas_ruta": [[lat, lon], ...]
}
```

### Tipos de Conexión

- **`parcela_acopio`**: Parcela → Centro de acopio
- **`acopio_planta`**: Centro de acopio → Planta extractora
- **`parcela_planta_directa`**: Parcela grande → Planta extractora (directo)

---

## 🤖 Sistema de Inteligencia Artificial

### Modelo: Random Forest Regressor

**Algoritmo**: Random Forest (scikit-learn)

**Objetivo**: Predecir producción de parcelas agrícolas

### Características (Features)

1. `cultivo_encoded`: Tipo de cultivo (codificado)
2. `area_hectareas`: Área de la parcela en hectáreas
3. `tiene_cuarto_frio`: Presencia de cuarto frío (0/1)
4. `num_rutas_disponibles`: Número de rutas disponibles
5. `distancia_promedio_acopios`: Distancia promedio a acopios
6. `accesibilidad_promedio_lluvia`: Accesibilidad promedio en lluvia
7. `costo_promedio_transporte`: Costo promedio de transporte
8. `indice_vegetacion`: Índice de vegetación (0.3 - 0.9)
9. `humedad_suelo`: Humedad del suelo (20 - 60%)
10. `temperatura_promedio`: Temperatura promedio (25 - 35°C)

### Target

- `produccion_ton`: Producción estimada en toneladas

### Parámetros del Modelo

```python
RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    max_depth=10
)
```

### Uso

```python
# Predecir producción de una parcela
produccion = sistema_agricola.predecir_produccion("PARCELA_001")
```

---

## 🗺️ Integración con OSMnx

El sistema integra **OSMnx** para obtener rutas reales de la red vial de OpenStreetMap.

### Funcionalidades

1. **Descarga de grafo vial**: Descarga la red vial del condado de Yuma
2. **Mapeo de nodos**: Mapea nodos agrícolas a nodos OSMnx más cercanos
3. **Cálculo de rutas reales**: Calcula rutas siguiendo la red vial real
4. **Segmentos sintéticos**: Genera segmentos sintéticos para acceso a carreteras

### Proceso de Cálculo de Ruta

1. Encuentra nodos OSMnx más cercanos al origen y destino
2. Calcula ruta en la red OSMnx entre esos nodos
3. Agrega segmentos sintéticos desde origen/destino a la carretera
4. Combina segmentos en una ruta completa

### Fallback

Si OSMnx no está disponible o falla:
- Usa distancia Haversine (línea recta)
- Genera ruta sintética con puntos intermedios
- Estima tipo de camino basado en distancia

### Cache

Las rutas OSMnx se cachean en `cache/` para mejorar rendimiento.

---

## 🖥️ Interfaz de Usuario

### Componentes Principales

#### 1. Mapa Interactivo

- **Biblioteca**: Leaflet.js
- **Tiles**: OpenStreetMap
- **Interacción**: Clic en nodos para seleccionar

#### 2. Panel de Control

Ubicado en la esquina superior izquierda:

- **Instrucciones**: Guía de uso
- **Nodos Seleccionados**: Lista de nodos seleccionados
- **Información de Ruta**: Detalles de ruta calculada
- **Botones**:
  - Limpiar Selección
  - Ver Predicciones IA
  - Rutas Óptimas
  - Parcelas Priorizadas
  - Colorear por Producción

#### 3. Leyenda

Ubicada en la esquina inferior izquierda:

- Parcelas de Naranjas (🍊)
- Centros de Acopio (🏭)
- Planta Extractora (🏢)
- Tipos de camino (colores)
- Producción (gradiente amarillo-rojo)
- Rutas óptimas (línea roja gruesa)

### Funcionalidades Interactivas

1. **Selección de Nodos**: Clic en nodos para seleccionar (máximo 2)
2. **Cálculo de Ruta**: Automático al seleccionar 2 nodos
3. **Visualización de Rutas**: Líneas en el mapa con colores según tipo
4. **Popups**: Información al hacer clic en nodos/rutas
5. **Coloreado por Producción**: Visualiza producción predicha

### Estilos CSS

El CSS está embebido en `mapa.html` con:
- Diseño moderno y responsivo
- Efectos de hover y transiciones
- Panel de control con backdrop blur
- Leyenda flotante
- Diseño adaptativo para móviles

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Calcular Ruta entre Dos Nodos

```python
from agricultural_graph import sistema_agricola

# Calcular ruta
ruta = sistema_agricola.calcular_ruta_entre_nodos(
    "PARCELA_001",
    "ACOPIO_01"
)

print(f"Distancia: {ruta['distancia_km']} km")
print(f"Tiempo: {ruta['tiempo_minutos']} min")
print(f"Costo: ${ruta['costo_por_ton']}/ton")
```

### Ejemplo 2: Predecir Producción

```python
# Predecir producción
produccion = sistema_agricola.predecir_produccion("PARCELA_001")
print(f"Producción predicha: {produccion} ton")
```

### Ejemplo 3: Obtener Rutas Óptimas

```python
# Rutas óptimas por costo
rutas = sistema_agricola.calcular_rutas_optimas_por_produccion(
    "PARCELA_001",
    criterio="costo",
    considerar_lluvia=False
)

for i, ruta in enumerate(rutas[:3], 1):
    print(f"Ruta {i}: {ruta['destino']}")
    print(f"  Costo total: ${ruta['costo_total']}")
    print(f"  Distancia: {ruta['distancia_km']} km")
```

### Ejemplo 4: Priorizar Parcelas

```python
# Top 10 parcelas por rendimiento
parcelas = sistema_agricola.priorizar_parcelas_por_rendimiento(top_n=10)

for parcela in parcelas:
    print(f"{parcela['parcela_id']}: {parcela['rendimiento_por_hectarea']:.2f} ton/ha")
```

### Ejemplo 5: Uso de la API REST

```python
import requests

# Obtener todos los nodos
response = requests.get("http://localhost:5000/api/nodos")
nodos = response.json()

# Calcular ruta
ruta_data = {
    "nodo1": "PARCELA_001",
    "nodo2": "ACOPIO_01"
}
response = requests.post(
    "http://localhost:5000/api/ruta",
    json=ruta_data
)
ruta = response.json()
```

---

## 🔍 Troubleshooting

### Problemas Comunes

#### 1. Error al descargar grafo OSMnx

**Síntoma**: 
```
Error descargando grafo OSMnx: ...
```

**Solución**:
- Verificar conexión a Internet
- El sistema continuará con rutas sintéticas si falla
- Reintentar más tarde

#### 2. Valores NaN en respuestas JSON

**Síntoma**: Error al serializar JSON

**Solución**: Ya implementado en `sanitize_for_json()`

#### 3. Mapa no carga

**Síntoma**: Mapa en blanco

**Solución**:
- Verificar que Leaflet.js se carga correctamente
- Revisar consola del navegador
- Verificar que el servidor Flask está corriendo

#### 4. Modelo de IA no predice

**Síntoma**: `produccion_predicha` es `None`

**Solución**:
- Verificar que el modelo se entrenó correctamente
- Ejecutar `sistema_agricola.entrenar_modelo_ia()` manualmente

#### 5. Rutas no se muestran en el mapa

**Síntoma**: Nodos visibles pero no rutas

**Solución**:
- Verificar que hay aristas en el grafo
- Revisar que `coordenadas_ruta` no está vacío
- Verificar consola del navegador para errores JavaScript

### Logs y Debugging

```python
# Activar modo debug en Flask
app.run(debug=True)

# Verificar estado del sistema
print(f"Nodos: {sistema_agricola.G_agricola.number_of_nodes()}")
print(f"Aristas: {sistema_agricola.G_agricola.number_of_edges()}")
print(f"Modelo entrenado: {sistema_agricola.modelo_ia is not None}")
```

---

## 📚 Referencias y Tecnologías

### Bibliotecas Python

- **Flask 3.1.2**: Framework web
- **NetworkX 3.5**: Manipulación de grafos
- **scikit-learn 1.7.2**: Machine Learning
- **pandas 2.3.3**: Manipulación de datos
- **numpy 2.3.4**: Cálculos numéricos
- **osmnx 1.6.0**: Red vial OpenStreetMap
- **geopandas 0.13.0**: Datos geoespaciales
- **shapely 2.0.0**: Geometrías

### Bibliotecas JavaScript

- **Leaflet 1.9.4**: Mapas interactivos

### Fuentes de Datos

- **OpenStreetMap**: Red vial real
- **Datos simulados**: Parcelas, acopios, planta

---

## 🚀 Mejoras Futuras

- [ ] Integración con datos reales de producción
- [ ] Optimización de rutas con algoritmos avanzados (Dijkstra, A*)
- [ ] Predicción de demanda
- [ ] Análisis de costos más detallado
- [ ] Exportación de reportes (PDF, Excel)
- [ ] Autenticación de usuarios
- [ ] Base de datos persistente
- [ ] API de tiempo real
- [ ] Integración con sensores IoT
- [ ] Dashboard de métricas

---

## 📝 Notas Adicionales

### Coordenadas del Sistema

- **Centro**: Yuma County, Arizona (32.6927°N, -114.6277°W)
- **Bounds**: 
  - Lat: 32.3° - 33.0°
  - Lon: -115.0° - -114.2°

### Semilla Aleatoria

El sistema usa `seed=42` para reproducibilidad.

### Cache OSMnx

Los datos de OSMnx se cachean en `cache/` para evitar descargas repetidas.

---

## 📞 Soporte

Para problemas o preguntas:
1. Revisar esta documentación
2. Ejecutar `test_system.py` para diagnóstico
3. Revisar logs del servidor Flask
4. Verificar consola del navegador

---

**Versión**: 1.0  
**Última actualización**: 2025  
**Autor**: Sistema Logístico Agrícola - Yuma County
```

Esta documentación cubre:

1. Descripción general y objetivos
2. Arquitectura del sistema
3. Estructura del proyecto
4. Instalación paso a paso
5. Componentes principales con detalles
6. API REST con ejemplos
7. Modelo de datos completo
8. Sistema de IA explicado
9. Integración con OSMnx
10. Interfaz de usuario
11. Ejemplos de código
12. Troubleshooting

¿Quieres que agregue alguna sección o profundice en algún tema?
