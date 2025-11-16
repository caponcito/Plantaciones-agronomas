"""
Sistema de grafo agrícola para Yuma County, Arizona
Incluye generación de datos, grafo y funciones de IA para predicciones
"""

import numpy as np
import pandas as pd
import networkx as nx
from math import radians, cos, sin, asin, sqrt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle
import os
import osmnx as ox
from shapely.geometry import Point

# Coordenadas aproximadas del condado de Yuma, Arizona
YUMA_CENTER_LAT = 32.6927
YUMA_CENTER_LON = -114.6277
YUMA_BOUNDS = {"min_lat": 32.3, "max_lat": 33.0, "min_lon": -115.0, "max_lon": -114.2}


def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia entre dos puntos geográficos usando la fórmula de Haversine."""
    R = 6371000  # Radio de la Tierra en metros
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


class AgriculturalGraphSystem:
    """Sistema completo de grafo agrícola con IA para predicciones"""

    def __init__(self, seed=42):
        self.seed = seed
        np.random.seed(seed)
        self.G_agricola = nx.DiGraph()
        self.G_osmnx = None  # Grafo vial real de OSMnx
        self.df_parcelas = None
        self.df_acopios = None
        self.df_planta = None
        self.df_nodos_completos = None
        self.df_aristas = None
        self.modelo_ia = None
        self.label_encoder = LabelEncoder()
        self.nodos_osmnx_mapeo = (
            {}
        )  # Mapeo de nodos agrícolas a nodos OSMnx más cercanos

    def generar_datos(self):
        """Genera todos los datos simulados del sistema agrícola"""
        # 1. Parcelas de cultivo (solo naranjas)
        num_parcelas = 25
        parcelas = []
        cultivo = "Naranjas"  # Solo naranjas

        for i in range(num_parcelas):
            lat = np.random.uniform(YUMA_BOUNDS["min_lat"], YUMA_BOUNDS["max_lat"])
            lon = np.random.uniform(YUMA_BOUNDS["min_lon"], YUMA_BOUNDS["max_lon"])
            area_hectareas = np.random.uniform(10, 200)
            produccion_estimada = np.random.uniform(50, 500)

            parcelas.append(
                {
                    "id": f"PARCELA_{i+1:03d}",
                    "tipo": "parcela_cultivo",
                    "latitud": lat,
                    "longitud": lon,
                    "cultivo": "Naranjas",  # Solo naranjas
                    "area_hectareas": area_hectareas,
                    "produccion_estimada_ton": produccion_estimada,
                    "capacidad_almacenamiento_ton": produccion_estimada * 0.3,
                    "tiene_cuarto_frio": np.random.choice([True, False], p=[0.3, 0.7]),
                }
            )

        self.df_parcelas = pd.DataFrame(parcelas)

        # 2. Centros de acopio
        num_centros_acopio = 5
        centros_acopio = []

        for i in range(num_centros_acopio):
            lat = np.random.uniform(YUMA_BOUNDS["min_lat"], YUMA_BOUNDS["max_lat"])
            lon = np.random.uniform(YUMA_BOUNDS["min_lon"], YUMA_BOUNDS["max_lon"])
            capacidad = np.random.uniform(500, 2000)

            centros_acopio.append(
                {
                    "id": f"ACOPIO_{i+1:02d}",
                    "tipo": "centro_acopio",
                    "latitud": lat,
                    "longitud": lon,
                    "capacidad_ton": capacidad,
                    "tiene_cadena_frio": np.random.choice([True, False], p=[0.8, 0.2]),
                    "num_camiones_disponibles": np.random.randint(2, 8),
                }
            )

        self.df_acopios = pd.DataFrame(centros_acopio)

        # 3. Planta extractora
        self.df_planta = pd.DataFrame(
            [
                {
                    "id": "PLANTA_EXTRACTORA_01",
                    "tipo": "planta_extractora",
                    "latitud": YUMA_CENTER_LAT + np.random.uniform(-0.1, 0.1),
                    "longitud": YUMA_CENTER_LON + np.random.uniform(-0.1, 0.1),
                    "capacidad_procesamiento_ton_dia": 5000,
                    "horario_operacion": "24/7",
                    "requiere_cadena_frio": True,
                }
            ]
        )

        # 4. Combinar nodos
        df_nodos = pd.concat(
            [
                self.df_parcelas[["id", "tipo", "latitud", "longitud"]],
                self.df_acopios[["id", "tipo", "latitud", "longitud"]],
                self.df_planta[["id", "tipo", "latitud", "longitud"]],
            ],
            ignore_index=True,
        )

        nodos_completos = []
        for idx, row in df_nodos.iterrows():
            nodo_data = row.to_dict()

            if row["tipo"] == "parcela_cultivo":
                parcela_info = self.df_parcelas[
                    self.df_parcelas["id"] == row["id"]
                ].iloc[0]
                nodo_data.update(
                    {
                        "cultivo": parcela_info["cultivo"],
                        "area_hectareas": parcela_info["area_hectareas"],
                        "produccion_estimada_ton": parcela_info[
                            "produccion_estimada_ton"
                        ],
                        "capacidad_almacenamiento_ton": parcela_info[
                            "capacidad_almacenamiento_ton"
                        ],
                        "tiene_cuarto_frio": parcela_info["tiene_cuarto_frio"],
                    }
                )
            elif row["tipo"] == "centro_acopio":
                acopio_info = self.df_acopios[self.df_acopios["id"] == row["id"]].iloc[
                    0
                ]
                nodo_data.update(
                    {
                        "capacidad_ton": acopio_info["capacidad_ton"],
                        "tiene_cadena_frio": acopio_info["tiene_cadena_frio"],
                        "num_camiones_disponibles": acopio_info[
                            "num_camiones_disponibles"
                        ],
                    }
                )
            elif row["tipo"] == "planta_extractora":
                planta_info = self.df_planta[self.df_planta["id"] == row["id"]].iloc[0]
                nodo_data.update(
                    {
                        "capacidad_procesamiento_ton_dia": planta_info[
                            "capacidad_procesamiento_ton_dia"
                        ],
                        "horario_operacion": planta_info["horario_operacion"],
                        "requiere_cadena_frio": planta_info["requiere_cadena_frio"],
                    }
                )

            nodos_completos.append(nodo_data)

        self.df_nodos_completos = pd.DataFrame(nodos_completos)

    def mapear_nodos_a_osmnx(self):
        """Mapea cada nodo agrícola a su nodo OSMnx más cercano"""
        self.nodos_osmnx_mapeo = {}

        if self.G_osmnx is None:
            return

        print("Mapeando nodos agrícolas a nodos OSMnx más cercanos...")

        for _, nodo in self.df_nodos_completos.iterrows():
            nodo_osmnx, distancia = self.encontrar_nodo_osmnx_mas_cercano(
                nodo["latitud"], nodo["longitud"]
            )
            if nodo_osmnx is not None:
                self.nodos_osmnx_mapeo[nodo["id"]] = {
                    "nodo_osmnx": nodo_osmnx,
                    "distancia_camino": distancia,
                    "latitud": nodo["latitud"],
                    "longitud": nodo["longitud"],
                }

        print(f"Mapeados {len(self.nodos_osmnx_mapeo)} nodos a OSMnx")

    def crear_grafo(self):
        """Crea el grafo con nodos y aristas usando rutas reales de OSMnx cuando sea posible"""
        # Agregar nodos
        for idx, row in self.df_nodos_completos.iterrows():
            node_attrs = row.to_dict()
            self.G_agricola.add_node(row["id"], **node_attrs)

        # Mapear nodos a OSMnx
        self.mapear_nodos_a_osmnx()

        # Generar aristas
        aristas = []

        # Parcelas -> Centros de acopio
        for _, parcela in self.df_parcelas.iterrows():
            distancias_acopios = []
            for _, acopio in self.df_acopios.iterrows():
                # Intentar usar ruta real de OSMnx
                ruta_osmnx = self.calcular_ruta_osmnx(
                    parcela["latitud"],
                    parcela["longitud"],
                    acopio["latitud"],
                    acopio["longitud"],
                )

                if ruta_osmnx:
                    distancia = ruta_osmnx["distancia_metros"]
                    usar_ruta_real = True
                else:
                    # Usar distancia Haversine como fallback
                    distancia = calcular_distancia_haversine(
                        parcela["latitud"],
                        parcela["longitud"],
                        acopio["latitud"],
                        acopio["longitud"],
                    )
                    usar_ruta_real = False

                distancias_acopios.append(
                    (acopio["id"], distancia, ruta_osmnx, usar_ruta_real)
                )

            distancias_acopios.sort(key=lambda x: x[1])
            num_conexiones = np.random.randint(2, min(4, len(distancias_acopios) + 1))

            for acopio_id, distancia, ruta_osmnx, usar_ruta_real in distancias_acopios[
                :num_conexiones
            ]:
                acopio = self.df_acopios[self.df_acopios["id"] == acopio_id].iloc[0]

                # Determinar tipo de camino y velocidad basado en ruta OSMnx o estimación
                if usar_ruta_real and ruta_osmnx:
                    # Usar información de OSMnx para determinar tipo de camino
                    # Obtener tipo de carretera de OSMnx
                    tipo_camino = "pavimentado"  # Por defecto, las carreteras de OSMnx suelen ser pavimentadas
                    velocidad_promedio = 50  # Velocidad promedio en carreteras

                    # Intentar obtener información de la carretera
                    if (
                        ruta_osmnx.get("nodos_osmnx")
                        and len(ruta_osmnx["nodos_osmnx"]) > 1
                    ):
                        try:
                            # Obtener información de la primera arista
                            nodo1 = ruta_osmnx["nodos_osmnx"][0]
                            nodo2 = ruta_osmnx["nodos_osmnx"][1]
                            edge_data = self.G_osmnx[nodo1][nodo2]

                            # Determinar tipo de camino basado en highway type
                            highway_type = edge_data.get("highway", "")
                            if isinstance(highway_type, list):
                                highway_type = highway_type[0] if highway_type else ""

                            if highway_type in [
                                "motorway",
                                "trunk",
                                "primary",
                                "secondary",
                            ]:
                                tipo_camino = "pavimentado"
                                velocidad_promedio = np.random.uniform(60, 80)
                            elif highway_type in [
                                "tertiary",
                                "unclassified",
                                "residential",
                            ]:
                                tipo_camino = "pavimentado"
                                velocidad_promedio = np.random.uniform(40, 60)
                            else:
                                tipo_camino = "grava"
                                velocidad_promedio = np.random.uniform(30, 50)
                        except:
                            pass

                    coordenadas_ruta = ruta_osmnx.get("coordenadas", [])
                else:
                    # Generar ruta ficticia desde nodo OSMnx más cercano
                    coordenadas_ruta = []

                    # Obtener nodos OSMnx más cercanos
                    mapeo_origen = self.nodos_osmnx_mapeo.get(parcela["id"])
                    mapeo_destino = self.nodos_osmnx_mapeo.get(acopio_id)

                    if mapeo_origen and mapeo_destino:
                        # Calcular ruta entre nodos OSMnx
                        ruta_osmnx_intermedia = self.calcular_ruta_osmnx(
                            mapeo_origen["latitud"],
                            mapeo_origen["longitud"],
                            mapeo_destino["latitud"],
                            mapeo_destino["longitud"],
                        )

                        if ruta_osmnx_intermedia:
                            # Construir ruta completa: parcela -> nodo OSMnx -> ... -> nodo OSMnx -> acopio
                            coordenadas_ruta = [
                                [parcela["latitud"], parcela["longitud"]]
                            ]
                            coordenadas_ruta.extend(
                                ruta_osmnx_intermedia.get("coordenadas", [])
                            )
                            coordenadas_ruta.append(
                                [acopio["latitud"], acopio["longitud"]]
                            )

                            # Actualizar distancia incluyendo acceso a carretera
                            distancia = (
                                (mapeo_origen["distancia_camino"] or 0)
                                + ruta_osmnx_intermedia["distancia_metros"]
                                + (mapeo_destino["distancia_camino"] or 0)
                            )
                            tipo_camino = "pavimentado"  # Rutas OSMnx son generalmente pavimentadas
                            velocidad_promedio = np.random.uniform(50, 70)
                        else:
                            # Fallback: línea recta
                            coordenadas_ruta = [
                                [parcela["latitud"], parcela["longitud"]],
                                [acopio["latitud"], acopio["longitud"]],
                            ]
                            # Determinar tipo basado en distancia
                            if distancia < 5000:
                                tipo_camino = np.random.choice(
                                    ["pavimentado", "grava"], p=[0.7, 0.3]
                                )
                                velocidad_promedio = np.random.uniform(40, 60)
                            elif distancia < 15000:
                                tipo_camino = np.random.choice(
                                    ["pavimentado", "grava", "tierra"],
                                    p=[0.5, 0.3, 0.2],
                                )
                                velocidad_promedio = np.random.uniform(35, 55)
                            else:
                                tipo_camino = np.random.choice(
                                    ["pavimentado", "grava", "tierra"],
                                    p=[0.4, 0.4, 0.2],
                                )
                                velocidad_promedio = np.random.uniform(30, 50)
                    else:
                        # Sin mapeo OSMnx, usar línea recta
                        coordenadas_ruta = [
                            [parcela["latitud"], parcela["longitud"]],
                            [acopio["latitud"], acopio["longitud"]],
                        ]
                        if distancia < 5000:
                            tipo_camino = np.random.choice(
                                ["pavimentado", "grava"], p=[0.7, 0.3]
                            )
                            velocidad_promedio = np.random.uniform(40, 60)
                        elif distancia < 15000:
                            tipo_camino = np.random.choice(
                                ["pavimentado", "grava", "tierra"], p=[0.5, 0.3, 0.2]
                            )
                            velocidad_promedio = np.random.uniform(35, 55)
                        else:
                            tipo_camino = np.random.choice(
                                ["pavimentado", "grava", "tierra"], p=[0.4, 0.4, 0.2]
                            )
                            velocidad_promedio = np.random.uniform(30, 50)

                tiempo_segundos = (distancia / 1000) / velocidad_promedio * 3600
                costo_combustible_por_km = 0.15
                costo_base = (distancia / 1000) * costo_combustible_por_km

                if tipo_camino == "tierra":
                    costo_base *= 1.3
                elif tipo_camino == "grava":
                    costo_base *= 1.1

                if tipo_camino == "pavimentado":
                    accesibilidad_lluvia = np.random.uniform(0.85, 1.0)
                elif tipo_camino == "grava":
                    accesibilidad_lluvia = np.random.uniform(0.5, 0.85)
                else:
                    accesibilidad_lluvia = np.random.uniform(0.2, 0.6)

                aristas.append(
                    {
                        "origen": parcela["id"],
                        "destino": acopio_id,
                        "distancia_metros": distancia,
                        "distancia_km": distancia / 1000,
                        "tiempo_segundos": tiempo_segundos,
                        "tiempo_minutos": tiempo_segundos / 60,
                        "costo_por_ton_dolares": costo_base,
                        "tipo_camino": tipo_camino,
                        "velocidad_promedio_kmh": velocidad_promedio,
                        "accesibilidad_lluvia": accesibilidad_lluvia,
                        "tipo_conexion": "parcela_acopio",
                        "usar_ruta_real": usar_ruta_real,
                        "coordenadas_ruta": (
                            coordenadas_ruta if coordenadas_ruta else None
                        ),
                    }
                )

        # Centros de acopio -> Planta extractora
        planta_id = self.df_planta.iloc[0]["id"]
        planta_lat = self.df_planta.iloc[0]["latitud"]
        planta_lon = self.df_planta.iloc[0]["longitud"]

        for _, acopio in self.df_acopios.iterrows():
            # Intentar usar ruta real de OSMnx
            ruta_osmnx = self.calcular_ruta_osmnx(
                acopio["latitud"], acopio["longitud"], planta_lat, planta_lon
            )

            if ruta_osmnx:
                distancia = ruta_osmnx["distancia_metros"]
                usar_ruta_real = True
                coordenadas_ruta = ruta_osmnx.get("coordenadas", [])
                tipo_camino = "pavimentado"
                velocidad_promedio = np.random.uniform(60, 80)  # Carreteras principales
            else:
                # Generar ruta ficticia desde nodo OSMnx más cercano
                mapeo_origen = self.nodos_osmnx_mapeo.get(acopio["id"])
                mapeo_destino = self.nodos_osmnx_mapeo.get(planta_id)

                if mapeo_origen and mapeo_destino:
                    ruta_osmnx_intermedia = self.calcular_ruta_osmnx(
                        mapeo_origen["latitud"],
                        mapeo_origen["longitud"],
                        mapeo_destino["latitud"],
                        mapeo_destino["longitud"],
                    )

                    if ruta_osmnx_intermedia:
                        coordenadas_ruta = [[acopio["latitud"], acopio["longitud"]]]
                        coordenadas_ruta.extend(
                            ruta_osmnx_intermedia.get("coordenadas", [])
                        )
                        coordenadas_ruta.append([planta_lat, planta_lon])
                        distancia = (
                            (mapeo_origen["distancia_camino"] or 0)
                            + ruta_osmnx_intermedia["distancia_metros"]
                            + (mapeo_destino["distancia_camino"] or 0)
                        )
                        usar_ruta_real = True
                        tipo_camino = "pavimentado"
                        velocidad_promedio = np.random.uniform(60, 80)
                    else:
                        distancia = calcular_distancia_haversine(
                            acopio["latitud"],
                            acopio["longitud"],
                            planta_lat,
                            planta_lon,
                        )
                        coordenadas_ruta = [
                            [acopio["latitud"], acopio["longitud"]],
                            [planta_lat, planta_lon],
                        ]
                        usar_ruta_real = False
                        tipo_camino = np.random.choice(
                            ["pavimentado", "grava"], p=[0.9, 0.1]
                        )
                        velocidad_promedio = np.random.uniform(50, 70)
                else:
                    distancia = calcular_distancia_haversine(
                        acopio["latitud"], acopio["longitud"], planta_lat, planta_lon
                    )
                    coordenadas_ruta = [
                        [acopio["latitud"], acopio["longitud"]],
                        [planta_lat, planta_lon],
                    ]
                    usar_ruta_real = False
                    tipo_camino = np.random.choice(
                        ["pavimentado", "grava"], p=[0.9, 0.1]
                    )
                    velocidad_promedio = np.random.uniform(50, 70)

            tiempo_segundos = (distancia / 1000) / velocidad_promedio * 3600
            costo_por_ton = (distancia / 1000) * 0.12
            accesibilidad_lluvia = np.random.uniform(0.9, 1.0)

            aristas.append(
                {
                    "origen": acopio["id"],
                    "destino": planta_id,
                    "distancia_metros": distancia,
                    "distancia_km": distancia / 1000,
                    "tiempo_segundos": tiempo_segundos,
                    "tiempo_minutos": tiempo_segundos / 60,
                    "costo_por_ton_dolares": costo_por_ton,
                    "tipo_camino": tipo_camino,
                    "velocidad_promedio_kmh": velocidad_promedio,
                    "accesibilidad_lluvia": accesibilidad_lluvia,
                    "tipo_conexion": "acopio_planta",
                    "usar_ruta_real": usar_ruta_real,
                    "coordenadas_ruta": coordenadas_ruta if coordenadas_ruta else None,
                }
            )

        # Parcelas grandes -> Planta extractora
        parcelas_grandes = self.df_parcelas[self.df_parcelas["area_hectareas"] > 100]
        num_directas = min(5, len(parcelas_grandes))

        for _, parcela in parcelas_grandes.sample(
            n=num_directas, random_state=self.seed
        ).iterrows():
            # Intentar usar ruta real de OSMnx
            ruta_osmnx = self.calcular_ruta_osmnx(
                parcela["latitud"], parcela["longitud"], planta_lat, planta_lon
            )

            if ruta_osmnx:
                distancia = ruta_osmnx["distancia_metros"]
                usar_ruta_real = True
                coordenadas_ruta = ruta_osmnx.get("coordenadas", [])
                tipo_camino = "pavimentado"
                velocidad_promedio = np.random.uniform(60, 80)
            else:
                # Generar ruta ficticia desde nodo OSMnx más cercano
                mapeo_origen = self.nodos_osmnx_mapeo.get(parcela["id"])
                mapeo_destino = self.nodos_osmnx_mapeo.get(planta_id)

                if mapeo_origen and mapeo_destino:
                    ruta_osmnx_intermedia = self.calcular_ruta_osmnx(
                        mapeo_origen["latitud"],
                        mapeo_origen["longitud"],
                        mapeo_destino["latitud"],
                        mapeo_destino["longitud"],
                    )

                    if ruta_osmnx_intermedia:
                        coordenadas_ruta = [[parcela["latitud"], parcela["longitud"]]]
                        coordenadas_ruta.extend(
                            ruta_osmnx_intermedia.get("coordenadas", [])
                        )
                        coordenadas_ruta.append([planta_lat, planta_lon])
                        distancia = (
                            (mapeo_origen["distancia_camino"] or 0)
                            + ruta_osmnx_intermedia["distancia_metros"]
                            + (mapeo_destino["distancia_camino"] or 0)
                        )
                        usar_ruta_real = True
                        tipo_camino = "pavimentado"
                        velocidad_promedio = np.random.uniform(60, 80)
                    else:
                        distancia = calcular_distancia_haversine(
                            parcela["latitud"],
                            parcela["longitud"],
                            planta_lat,
                            planta_lon,
                        )
                        coordenadas_ruta = [
                            [parcela["latitud"], parcela["longitud"]],
                            [planta_lat, planta_lon],
                        ]
                        usar_ruta_real = False
                        tipo_camino = "pavimentado"
                        velocidad_promedio = np.random.uniform(55, 70)
                else:
                    distancia = calcular_distancia_haversine(
                        parcela["latitud"], parcela["longitud"], planta_lat, planta_lon
                    )
                    coordenadas_ruta = [
                        [parcela["latitud"], parcela["longitud"]],
                        [planta_lat, planta_lon],
                    ]
                    usar_ruta_real = False
                    tipo_camino = "pavimentado"
                    velocidad_promedio = np.random.uniform(55, 70)

            tiempo_segundos = (distancia / 1000) / velocidad_promedio * 3600
            costo_por_ton = (distancia / 1000) * 0.12
            accesibilidad_lluvia = np.random.uniform(0.9, 1.0)

            aristas.append(
                {
                    "origen": parcela["id"],
                    "destino": planta_id,
                    "distancia_metros": distancia,
                    "distancia_km": distancia / 1000,
                    "tiempo_segundos": tiempo_segundos,
                    "tiempo_minutos": tiempo_segundos / 60,
                    "costo_por_ton_dolares": costo_por_ton,
                    "tipo_camino": tipo_camino,
                    "velocidad_promedio_kmh": velocidad_promedio,
                    "accesibilidad_lluvia": accesibilidad_lluvia,
                    "tipo_conexion": "parcela_planta_directa",
                    "usar_ruta_real": usar_ruta_real,
                    "coordenadas_ruta": coordenadas_ruta if coordenadas_ruta else None,
                }
            )

        self.df_aristas = pd.DataFrame(aristas)

        # Agregar aristas al grafo
        for _, edge in self.df_aristas.iterrows():
            edge_attrs = {
                "distancia_metros": edge["distancia_metros"],
                "distancia_km": edge["distancia_km"],
                "tiempo_segundos": edge["tiempo_segundos"],
                "tiempo_minutos": edge["tiempo_minutos"],
                "costo_por_ton_dolares": edge["costo_por_ton_dolares"],
                "tipo_camino": edge["tipo_camino"],
                "velocidad_promedio_kmh": edge["velocidad_promedio_kmh"],
                "accesibilidad_lluvia": edge["accesibilidad_lluvia"],
                "tipo_conexion": edge["tipo_conexion"],
            }

            # Agregar información de ruta OSMnx si está disponible
            if "usar_ruta_real" in edge:
                edge_attrs["usar_ruta_real"] = edge["usar_ruta_real"]
            if "coordenadas_ruta" in edge and edge["coordenadas_ruta"] is not None:
                edge_attrs["coordenadas_ruta"] = edge["coordenadas_ruta"]

            self.G_agricola.add_edge(edge["origen"], edge["destino"], **edge_attrs)

    def preparar_datos_ia(self):
        """Prepara dataset para entrenamiento del modelo de IA"""
        features = []

        for _, parcela in self.df_parcelas.iterrows():
            # Características de la parcela
            num_rutas = len(self.df_aristas[self.df_aristas["origen"] == parcela["id"]])
            dist_prom = (
                self.df_aristas[
                    (self.df_aristas["origen"] == parcela["id"])
                    & (self.df_aristas["tipo_conexion"] == "parcela_acopio")
                ]["distancia_km"].mean()
                if num_rutas > 0
                else 0
            )

            acc_prom = (
                self.df_aristas[self.df_aristas["origen"] == parcela["id"]][
                    "accesibilidad_lluvia"
                ].mean()
                if num_rutas > 0
                else 0
            )

            costo_prom = (
                self.df_aristas[self.df_aristas["origen"] == parcela["id"]][
                    "costo_por_ton_dolares"
                ].mean()
                if num_rutas > 0
                else 0
            )

            features.append(
                {
                    "cultivo": parcela["cultivo"],
                    "area_hectareas": parcela["area_hectareas"],
                    "tiene_cuarto_frio": 1 if parcela["tiene_cuarto_frio"] else 0,
                    "num_rutas_disponibles": num_rutas,
                    "distancia_promedio_acopios": dist_prom,
                    "accesibilidad_promedio_lluvia": acc_prom,
                    "costo_promedio_transporte": costo_prom,
                    "indice_vegetacion": np.random.uniform(0.3, 0.9),
                    "humedad_suelo": np.random.uniform(20, 60),
                    "temperatura_promedio": np.random.uniform(25, 35),
                    "produccion_ton": parcela["produccion_estimada_ton"],  # Target
                }
            )

        return pd.DataFrame(features)

    def entrenar_modelo_ia(self):
        """Entrena el modelo de IA para predecir producción"""
        df_features = self.preparar_datos_ia()

        # Codificar cultivo
        df_features["cultivo_encoded"] = self.label_encoder.fit_transform(
            df_features["cultivo"]
        )

        # Preparar features y target
        feature_cols = [
            "cultivo_encoded",
            "area_hectareas",
            "tiene_cuarto_frio",
            "num_rutas_disponibles",
            "distancia_promedio_acopios",
            "accesibilidad_promedio_lluvia",
            "costo_promedio_transporte",
            "indice_vegetacion",
            "humedad_suelo",
            "temperatura_promedio",
        ]

        X = df_features[feature_cols]
        y = df_features["produccion_ton"]

        # Entrenar modelo
        self.modelo_ia = RandomForestRegressor(
            n_estimators=100, random_state=self.seed, max_depth=10
        )
        self.modelo_ia.fit(X, y)

        return self.modelo_ia

    def predecir_produccion(self, parcela_id):
        """Predice la producción de una parcela usando el modelo de IA"""
        if self.modelo_ia is None:
            self.entrenar_modelo_ia()

        parcela = self.df_parcelas[self.df_parcelas["id"] == parcela_id]
        if parcela.empty:
            return None

        parcela = parcela.iloc[0]

        # Preparar features
        num_rutas = len(self.df_aristas[self.df_aristas["origen"] == parcela_id])
        dist_prom = (
            self.df_aristas[
                (self.df_aristas["origen"] == parcela_id)
                & (self.df_aristas["tipo_conexion"] == "parcela_acopio")
            ]["distancia_km"].mean()
            if num_rutas > 0
            else 0
        )

        acc_prom = (
            self.df_aristas[self.df_aristas["origen"] == parcela_id][
                "accesibilidad_lluvia"
            ].mean()
            if num_rutas > 0
            else 0
        )

        costo_prom = (
            self.df_aristas[self.df_aristas["origen"] == parcela_id][
                "costo_por_ton_dolares"
            ].mean()
            if num_rutas > 0
            else 0
        )

        # Codificar cultivo
        cultivo_encoded = self.label_encoder.transform([parcela["cultivo"]])[0]

        features = np.array(
            [
                [
                    cultivo_encoded,
                    parcela["area_hectareas"],
                    1 if parcela["tiene_cuarto_frio"] else 0,
                    num_rutas,
                    dist_prom,
                    acc_prom,
                    costo_prom,
                    np.random.uniform(0.3, 0.9),  # indice_vegetacion
                    np.random.uniform(20, 60),  # humedad_suelo
                    np.random.uniform(25, 35),  # temperatura_promedio
                ]
            ]
        )

        produccion_predicha = self.modelo_ia.predict(features)[0]
        return max(0, produccion_predicha)  # Asegurar valor positivo

    def calcular_ruta_entre_nodos(self, nodo1_id, nodo2_id):
        """Calcula la ruta entre dos nodos mezclando OSMnx y segmentos sintéticos."""
        try:
            if (
                nodo1_id not in self.G_agricola.nodes()
                or nodo2_id not in self.G_agricola.nodes()
            ):
                return None

            nodo1 = self.obtener_info_nodo(nodo1_id)
            nodo2 = self.obtener_info_nodo(nodo2_id)

            if not nodo1 or not nodo2:
                return None

            lat1, lon1 = nodo1.get("latitud"), nodo1.get("longitud")
            lat2, lon2 = nodo2.get("latitud"), nodo2.get("longitud")
            if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
                return None

            ruta_osmnx = self.calcular_ruta_osmnx(lat1, lon1, lat2, lon2)

            if ruta_osmnx:
                distancia_km = ruta_osmnx["distancia_km"]
                velocidad_base = (
                    60 if ruta_osmnx.get("tipo_camino") == "pavimentado" else 45
                )
                if ruta_osmnx.get("tiene_segmentos_sinteticos"):
                    velocidad_base *= 0.75  # más lento por caminos de acceso
                tiempo_minutos = (distancia_km / max(velocidad_base, 1)) * 60

                return {
                    "existe_ruta": True,
                    "distancia_km": distancia_km,
                    "tiempo_minutos": tiempo_minutos,
                    "costo_por_ton": distancia_km * 0.15,
                    "tipo_camino": ruta_osmnx.get("tipo_camino", "desconocido"),
                    "accesibilidad_lluvia": (
                        0.9 if ruta_osmnx.get("tipo_camino") == "pavimentado" else 0.5
                    ),
                    "ruta": [nodo1_id, nodo2_id],
                    "coordenadas_ruta": ruta_osmnx.get("coordenadas", []),
                    "usar_ruta_real": ruta_osmnx.get("usar_ruta_real", False),
                    "tiene_segmentos_sinteticos": ruta_osmnx.get(
                        "tiene_segmentos_sinteticos", False
                    ),
                    "segmentos": ruta_osmnx.get("segmentos", []),
                    "nodos_osmnx": ruta_osmnx.get("nodos_osmnx", []),
                }

            # Fallback: línea recta completamente sintética
            distancia_metros = calcular_distancia_haversine(lat1, lon1, lat2, lon2)
            distancia_km = distancia_metros / 1000
            tiempo_minutos = (distancia_km / 40) * 60  # 40 km/h estimado para tierra
            coordenadas_directas = [[lat1, lon1], [lat2, lon2]]

            return {
                "existe_ruta": True,
                "distancia_km": distancia_km,
                "tiempo_minutos": tiempo_minutos,
                "costo_por_ton": distancia_km * 0.15,
                "tipo_camino": "tierra",
                "accesibilidad_lluvia": 0.5,
                "ruta": [nodo1_id, nodo2_id],
                "coordenadas_ruta": coordenadas_directas,
                "usar_ruta_real": False,
                "tiene_segmentos_sinteticos": True,
                "segmentos": [
                    {
                        "tipo": "tierra",
                        "coordenadas": coordenadas_directas,
                        "es_segmento_sintetico": True,
                    }
                ],
                "nodos_osmnx": [],
            }

        except Exception as exc:
            print(f"Error calculando ruta entre {nodo1_id} y {nodo2_id}: {exc}")
            return None

    def obtener_info_nodo(self, nodo_id):
        """Obtiene información completa de un nodo"""
        if nodo_id not in self.G_agricola.nodes():
            return None

        nodo_data = self.G_agricola.nodes[nodo_id].copy()
        return nodo_data

    def calcular_rutas_optimas_por_produccion(
        self, parcela_id, criterio="costo", considerar_lluvia=False
    ):
        """
        Calcula las rutas óptimas desde una parcela considerando la producción predicha.

        Parámetros:
        -----------
        parcela_id : str
            ID de la parcela
        criterio : str
            'costo', 'tiempo', 'distancia', o 'accesibilidad'
        considerar_lluvia : bool
            Si True, ajusta los pesos según accesibilidad en lluvia
        """
        if parcela_id not in self.G_agricola.nodes():
            return None

        produccion_predicha = self.predecir_produccion(parcela_id)
        if produccion_predicha is None:
            produccion_predicha = self.df_parcelas[
                self.df_parcelas["id"] == parcela_id
            ].iloc[0]["produccion_estimada_ton"]

        rutas_disponibles = []

        # Obtener todas las aristas salientes de la parcela
        for destino in self.G_agricola.successors(parcela_id):
            edge_data = self.G_agricola[parcela_id][destino]

            # Calcular peso según criterio
            if criterio == "costo":
                peso = edge_data["costo_por_ton_dolares"] * produccion_predicha
            elif criterio == "tiempo":
                peso = edge_data["tiempo_minutos"]
            elif criterio == "distancia":
                peso = edge_data["distancia_km"]
            elif criterio == "accesibilidad":
                peso = 1 / edge_data["accesibilidad_lluvia"]  # Invertir para minimizar
            else:
                peso = edge_data["costo_por_ton_dolares"]

            # Ajustar por accesibilidad en lluvia si se solicita
            if considerar_lluvia:
                peso = peso / edge_data["accesibilidad_lluvia"]

            rutas_disponibles.append(
                {
                    "destino": destino,
                    "peso": peso,
                    "distancia_km": edge_data["distancia_km"],
                    "tiempo_minutos": edge_data["tiempo_minutos"],
                    "costo_total": edge_data["costo_por_ton_dolares"]
                    * produccion_predicha,
                    "accesibilidad_lluvia": edge_data["accesibilidad_lluvia"],
                    "tipo_camino": edge_data["tipo_camino"],
                    "produccion_predicha": produccion_predicha,
                }
            )

        # Ordenar por peso (menor es mejor)
        rutas_disponibles.sort(key=lambda x: x["peso"])

        return rutas_disponibles

    def priorizar_parcelas_por_rendimiento(self, top_n=10):
        """
        Prioriza parcelas con mayor rendimiento esperado basado en predicciones de IA.

        Parámetros:
        -----------
        top_n : int
            Número de parcelas a retornar
        """
        parcelas_priorizadas = []

        for _, parcela in self.df_parcelas.iterrows():
            produccion_original = parcela["produccion_estimada_ton"]
            produccion_predicha = self.predecir_produccion(parcela["id"])

            if produccion_predicha:
                parcelas_priorizadas.append(
                    {
                        "parcela_id": parcela["id"],
                        "produccion_original": produccion_original,
                        "produccion_predicha": produccion_predicha,
                        "rendimiento_esperado": produccion_predicha,
                        "area_hectareas": parcela["area_hectareas"],
                        "rendimiento_por_hectarea": produccion_predicha
                        / parcela["area_hectareas"],
                        "latitud": parcela["latitud"],
                        "longitud": parcela["longitud"],
                    }
                )

        # Ordenar por rendimiento esperado (mayor primero)
        parcelas_priorizadas.sort(key=lambda x: x["rendimiento_esperado"], reverse=True)

        return parcelas_priorizadas[:top_n]

    def obtener_predicciones_todas_parcelas(self):
        """Obtiene predicciones de producción para todas las parcelas"""
        predicciones = []

        for _, parcela in self.df_parcelas.iterrows():
            produccion_original = parcela["produccion_estimada_ton"]
            produccion_predicha = self.predecir_produccion(parcela["id"])

            predicciones.append(
                {
                    "parcela_id": parcela["id"],
                    "produccion_original": produccion_original,
                    "produccion_predicha": (
                        produccion_predicha
                        if produccion_predicha
                        else produccion_original
                    ),
                    "latitud": parcela["latitud"],
                    "longitud": parcela["longitud"],
                }
            )

        return predicciones

    def descargar_grafo_osmnx(self):
        """Descarga el grafo vial real de OSMnx para Yuma County"""
        try:
            lugar = "Yuma County, Arizona, USA"
            print("Descargando grafo vial de OSMnx para Yuma County...")
            self.G_osmnx = ox.graph_from_place(lugar, network_type="drive")
            print(
                f"Grafo OSMnx descargado: {self.G_osmnx.number_of_nodes()} nodos, {self.G_osmnx.number_of_edges()} aristas"
            )
            return True
        except Exception as e:
            print(f"Error descargando grafo OSMnx: {e}")
            print("Continuando sin grafo OSMnx (usando rutas ficticias)")
            self.G_osmnx = None
            return False

    def encontrar_nodo_osmnx_mas_cercano(self, lat, lon):
        """Encuentra el nodo más cercano en el grafo OSMnx a un punto dado"""
        if self.G_osmnx is None:
            return None, None

        try:
            # Encontrar el nodo más cercano usando OSMnx
            nodo_cercano = ox.distance.nearest_nodes(self.G_osmnx, lon, lat)

            # Calcular distancia usando Haversine
            nodo_data = self.G_osmnx.nodes[nodo_cercano]
            nodo_lat = nodo_data.get("y", lat)
            nodo_lon = nodo_data.get("x", lon)
            distancia = calcular_distancia_haversine(lat, lon, nodo_lat, nodo_lon)

            return nodo_cercano, distancia
        except Exception as e:
            print(f"Error encontrando nodo cercano: {e}")
            return None, None

    def _crear_segmento_sintetico(self, lat1, lon1, lat2, lon2, tipo="tierra"):
        """Genera un segmento sintético entre dos puntos con puntos intermedios"""
        distancia = calcular_distancia_haversine(lat1, lon1, lat2, lon2)

        # Añadir puntos intermedios para que el trazo no sea una simple línea recta
        num_puntos = max(2, int(distancia / 200))  # Un punto aproximadamente cada 200 m
        puntos = []

        for i in range(num_puntos + 1):
            t = i / num_puntos
            lat = lat1 + (lat2 - lat1) * t
            lon = lon1 + (lon2 - lon1) * t
            puntos.append([lat, lon])

        return {
            "coordenadas": puntos,
            "distancia_metros": distancia,
            "tipo_camino": tipo,
            "es_segmento_sintetico": True,
        }

    def _crear_ruta_sintetica(self, lat1, lon1, lat2, lon2):
        """Crea una ruta completamente sintética entre dos puntos"""
        segmento = self._crear_segmento_sintetico(lat1, lon1, lat2, lon2, tipo="tierra")

        return {
            "coordenadas": segmento["coordenadas"],
            "distancia_metros": segmento["distancia_metros"],
            "distancia_km": segmento["distancia_metros"] / 1000,
            "usar_ruta_real": False,
            "tipo_camino": "tierra",
            "tiene_segmentos_sinteticos": True,
            "segmentos": [
                {
                    "tipo": segmento["tipo_camino"],
                    "coordenadas": segmento["coordenadas"],
                    "es_segmento_sintetico": True,
                }
            ],
            "nodos_osmnx": [],
        }

    def calcular_ruta_osmnx(self, origen_lat, origen_lon, destino_lat, destino_lon):
        """
        Calcula la ruta real usando OSMnx entre dos puntos, incluyendo segmentos sintéticos
        cuando sea necesario.
        """
        if self.G_osmnx is None:
            return self._crear_ruta_sintetica(
                origen_lat, origen_lon, destino_lat, destino_lon
            )

        try:
            # Encontrar nodos OSMnx más cercanos
            nodo_origen, dist_origen = self.encontrar_nodo_osmnx_mas_cercano(
                origen_lat, origen_lon
            )
            nodo_destino, dist_destino = self.encontrar_nodo_osmnx_mas_cercano(
                destino_lat, destino_lon
            )

            if nodo_origen is None or nodo_destino is None:
                return self._crear_ruta_sintetica(
                    origen_lat, origen_lon, destino_lat, destino_lon
                )

            # Inicializar con las coordenadas vacías
            coordenadas_ruta = []
            distancia_total = 0
            usar_ruta_real = False
            tipo_camino = "tierra"  # Por defecto, asumimos camino de tierra
            tiene_segmentos_sinteticos = False
            segmentos = []

            def _extender_coordenadas(destino_lista, nuevas_coordenadas):
                if not nuevas_coordenadas:
                    return
                if not destino_lista:
                    destino_lista.extend(nuevas_coordenadas)
                else:
                    if destino_lista[-1] == nuevas_coordenadas[0]:
                        destino_lista.extend(nuevas_coordenadas[1:])
                    else:
                        destino_lista.extend(nuevas_coordenadas)

            # Agregar segmento sintético desde el origen hasta la carretera
            if (
                dist_origen and dist_origen > 10
            ):  # Solo si está lo suficientemente lejos
                segmento_origen = self._crear_segmento_sintetico(
                    origen_lat,
                    origen_lon,
                    self.G_osmnx.nodes[nodo_origen]["y"],
                    self.G_osmnx.nodes[nodo_origen]["x"],
                    tipo="tierra",
                )
                _extender_coordenadas(coordenadas_ruta, segmento_origen["coordenadas"])
                distancia_total += segmento_origen["distancia_metros"]
                tiene_segmentos_sinteticos = True
                segmentos.append(
                    {
                        "tipo": segmento_origen["tipo_camino"],
                        "coordenadas": segmento_origen["coordenadas"],
                        "es_segmento_sintetico": True,
                    }
                )

            # Calcular ruta en la red vial
            if (
                nodo_origen
                and nodo_destino
                and nx.has_path(self.G_osmnx, nodo_origen, nodo_destino)
            ):
                ruta_nodos = nx.shortest_path(
                    self.G_osmnx, nodo_origen, nodo_destino, weight="length"
                )

                # Obtener coordenadas de la ruta OSMnx
                coordenadas_osmnx = []
                for i in range(len(ruta_nodos) - 1):
                    nodo1 = ruta_nodos[i]
                    nodo2 = ruta_nodos[i + 1]

                    # Obtener coordenadas de los nodos
                    lat1, lon1 = (
                        self.G_osmnx.nodes[nodo1]["y"],
                        self.G_osmnx.nodes[nodo1]["x"],
                    )
                    lat2, lon2 = (
                        self.G_osmnx.nodes[nodo2]["y"],
                        self.G_osmnx.nodes[nodo2]["x"],
                    )

                    # Agregar coordenadas a la ruta
                    if not coordenadas_osmnx or coordenadas_osmnx[-1] != [lat1, lon1]:
                        coordenadas_osmnx.append([lat1, lon1])
                    coordenadas_osmnx.append([lat2, lon2])

                    # Sumar distancia
                    edge_data = self.G_osmnx.get_edge_data(nodo1, nodo2)
                    if edge_data:
                        key = list(edge_data.keys())[0]
                        distancia_total += edge_data[key].get("length", 0)
                        highway_type = edge_data[key].get("highway")
                        if isinstance(highway_type, list):
                            highway_type = highway_type[0]
                        if highway_type in [
                            "motorway",
                            "trunk",
                            "primary",
                            "secondary",
                            "residential",
                            "tertiary",
                        ]:
                            tipo_camino = "pavimentado"
                        elif highway_type in ["unclassified", "service"]:
                            tipo_camino = "grava"
                        else:
                            tipo_camino = "tierra"

                usar_ruta_real = True
                _extender_coordenadas(coordenadas_ruta, coordenadas_osmnx)
                segmentos.append(
                    {
                        "tipo": tipo_camino,
                        "coordenadas": coordenadas_osmnx,
                        "es_segmento_sintetico": False,
                    }
                )

            # Agregar segmento sintético desde la carretera hasta el destino
            if (
                dist_destino and dist_destino > 10
            ):  # Solo si está lo suficientemente lejos
                segmento_destino = self._crear_segmento_sintetico(
                    self.G_osmnx.nodes[nodo_destino]["y"],
                    self.G_osmnx.nodes[nodo_destino]["x"],
                    destino_lat,
                    destino_lon,
                    tipo="tierra",
                )
                _extender_coordenadas(coordenadas_ruta, segmento_destino["coordenadas"])
                distancia_total += segmento_destino["distancia_metros"]
                tiene_segmentos_sinteticos = True
                segmentos.append(
                    {
                        "tipo": segmento_destino["tipo_camino"],
                        "coordenadas": segmento_destino["coordenadas"],
                        "es_segmento_sintetico": True,
                    }
                )

            # Si no hay ruta OSMnx, crear una ruta completamente sintética
            if not usar_ruta_real:
                return self._crear_ruta_sintetica(
                    origen_lat, origen_lon, destino_lat, destino_lon
                )

            return {
                "coordenadas": coordenadas_ruta,
                "distancia_metros": distancia_total,
                "distancia_km": distancia_total / 1000,
                "usar_ruta_real": usar_ruta_real,
                "tipo_camino": tipo_camino,
                "tiene_segmentos_sinteticos": tiene_segmentos_sinteticos,
                "segmentos": segmentos,
                "nodos_osmnx": ruta_nodos,
            }

        except Exception as e:
            print(f"Error calculando ruta OSMnx: {e}")
            return self._crear_ruta_sintetica(
                origen_lat, origen_lon, destino_lat, destino_lon
            )

    def inicializar_sistema(self):
        """Inicializa todo el sistema"""
        self.descargar_grafo_osmnx()
        self.generar_datos()
        self.crear_grafo()
        self.entrenar_modelo_ia()
        print("Sistema agrícola inicializado correctamente")


# Instancia global del sistema
sistema_agricola = AgriculturalGraphSystem()
sistema_agricola.inicializar_sistema()
