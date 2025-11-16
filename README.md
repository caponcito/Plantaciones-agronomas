# Sistema Logístico Agrícola - Yuma County, Arizona

Sistema web interactivo para visualización y análisis de rutas logísticas agrícolas con integración de IA para predicción de producción.

## Características

- 🗺️ Mapa interactivo con Folium y Leaflet
- 📊 Visualización de parcelas, centros de acopio y planta extractora
- 🔗 Cálculo de rutas y distancias entre nodos
- 🤖 Predicción de producción usando Machine Learning (Random Forest)
- 💰 Análisis de costos, tiempos y accesibilidad
- 🌧️ Consideración de accesibilidad en temporada de lluvias

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Aplicación Web Interactiva

1. Ejecutar el servidor Flask:
```bash
python app.py
```

2. Abrir en el navegador:
```
http://localhost:5000
```

3. En el mapa interactivo puedes:
   - Hacer clic en dos nodos para ver la distancia entre ellos
   - Ver información detallada de rutas (distancia, tiempo, costo)
   - Obtener predicciones de producción usando IA
   - Explorar la red logística completa

### Uso desde Python

```python
from agricultural_graph import sistema_agricola

# Obtener información de una parcela
parcela = sistema_agricola.df_parcelas.iloc[0]

# Calcular ruta entre dos nodos
ruta = sistema_agricola.calcular_ruta_entre_nodos('PARCELA_001', 'ACOPIO_01')

# Predecir producción usando IA
produccion_predicha = sistema_agricola.predecir_produccion('PARCELA_001')
```

## Estructura del Proyecto

```
ruta_agronoma/
├── app.py                      # Aplicación Flask
├── agricultural_graph.py       # Lógica del grafo e IA
├── templates/
│   └── mapa.html              # Template HTML con mapa interactivo
├── requirements.txt           # Dependencias
├── proyecto_prog.ipynb         # Notebook de ejemplo
└── README.md                  # Este archivo
```

## Componentes del Sistema

### Nodos
- **25 Parcelas de cultivo**: Con información de cultivo, área, producción estimada
- **5 Centros de acopio**: Con capacidad de almacenamiento y camiones disponibles
- **1 Planta extractora**: Con capacidad de procesamiento

### Aristas (Rutas)
Cada ruta incluye:
- Distancia (km)
- Tiempo de viaje (minutos)
- Costo por tonelada ($)
- Tipo de camino (pavimentado, grava, tierra)
- Accesibilidad en temporada de lluvias (0-1)

### Modelo de IA
- **Algoritmo**: Random Forest Regressor
- **Características**: Área, cultivo, conectividad, condiciones ambientales
- **Objetivo**: Predecir producción de parcelas

## API Endpoints

- `GET /api/nodos` - Obtener todos los nodos
- `GET /api/aristas` - Obtener todas las aristas
- `POST /api/ruta` - Calcular ruta entre dos nodos
- `GET /api/prediccion/<nodo_id>` - Obtener predicción de producción

## Tecnologías

- **Backend**: Flask, NetworkX, scikit-learn
- **Frontend**: Leaflet.js, HTML5, CSS3, JavaScript
- **IA**: Random Forest Regressor
- **Visualización**: Folium, Leaflet

## Problemas que Resuelve

Este sistema aborda los siguientes desafíos en la logística agrícola:

- ✅ Optimización de rutas de recolección
- ✅ Predicción de producción para planificación
- ✅ Análisis de costos de transporte
- ✅ Consideración de condiciones climáticas
- ✅ Visualización de la red logística completa

## Licencia

Este proyecto es de uso educativo y de investigación.

