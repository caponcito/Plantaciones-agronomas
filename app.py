"""
Aplicación Flask para visualización interactiva del grafo agrícola
"""

from flask import Flask, render_template, jsonify, request
from agricultural_graph import (
    sistema_agricola,
    calcular_distancia_haversine,
    predecir_clima_yuma,
)
import json
import math

app = Flask(__name__)


def sanitize_for_json(value, default=0):
    """
    Convierte NaN, Infinity y otros valores no serializables a valores válidos para JSON.
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return default
    return value


@app.route("/")
def index():
    """Página principal con el mapa interactivo"""
    return render_template("mapa.html")


@app.route("/api/nodos")
def obtener_nodos():
    """API para obtener todos los nodos del grafo"""
    nodos = []
    for node_id, data in sistema_agricola.G_agricola.nodes(data=True):
        nodo_info = {
            "id": node_id,
            "tipo": data.get("tipo", ""),
            "latitud": data.get("latitud", 0),
            "longitud": data.get("longitud", 0),
            "info": {},
        }

        # Agregar información específica según el tipo
        if data.get("tipo") == "parcela_cultivo":
            nodo_info["info"] = {
                "cultivo": data.get("cultivo", ""),
                "area_hectareas": round(
                    sanitize_for_json(data.get("area_hectareas", 0)), 2
                ),
                "produccion_estimada_ton": round(
                    sanitize_for_json(data.get("produccion_estimada_ton", 0)), 2
                ),
                "tiene_cuarto_frio": data.get("tiene_cuarto_frio", False),
            }
        elif data.get("tipo") == "centro_acopio":
            nodo_info["info"] = {
                "capacidad_ton": round(
                    sanitize_for_json(data.get("capacidad_ton", 0)), 2
                ),
                "num_camiones_disponibles": int(
                    sanitize_for_json(data.get("num_camiones_disponibles", 0))
                ),
                "tiene_cadena_frio": data.get("tiene_cadena_frio", False),
            }
        elif data.get("tipo") == "planta_extractora":
            nodo_info["info"] = {
                "capacidad_procesamiento_ton_dia": int(
                    sanitize_for_json(data.get("capacidad_procesamiento_ton_dia", 0))
                ),
                "horario_operacion": data.get("horario_operacion", ""),
                "requiere_cadena_frio": data.get("requiere_cadena_frio", False),
            }

        nodos.append(nodo_info)

    return jsonify(nodos)


@app.route("/api/aristas")
def obtener_aristas():
    """API para obtener todas las aristas del grafo"""
    aristas = []
    for u, v, data in sistema_agricola.G_agricola.edges(data=True):
        origen = sistema_agricola.obtener_info_nodo(u)
        destino = sistema_agricola.obtener_info_nodo(v)

        if origen and destino:
            arista_info = {
                "origen": u,
                "destino": v,
                "origen_lat": sanitize_for_json(origen.get("latitud", 0)),
                "origen_lon": sanitize_for_json(origen.get("longitud", 0)),
                "destino_lat": sanitize_for_json(destino.get("latitud", 0)),
                "destino_lon": sanitize_for_json(destino.get("longitud", 0)),
                "distancia_km": round(
                    sanitize_for_json(data.get("distancia_km", 0)), 2
                ),
                "tiempo_minutos": round(
                    sanitize_for_json(data.get("tiempo_minutos", 0)), 2
                ),
                "costo_por_ton": round(
                    sanitize_for_json(data.get("costo_por_ton_dolares", 0)), 2
                ),
                "tipo_camino": data.get("tipo_camino", ""),
                "accesibilidad_lluvia": round(
                    sanitize_for_json(data.get("accesibilidad_lluvia", 0)), 2
                ),
            }

            # Agregar coordenadas de ruta OSMnx si están disponibles
            if "coordenadas_ruta" in data and data["coordenadas_ruta"] is not None:
                arista_info["coordenadas_ruta"] = data["coordenadas_ruta"]
                arista_info["usar_ruta_real"] = data.get("usar_ruta_real", False)

            aristas.append(arista_info)

    return jsonify(aristas)


@app.route("/api/ruta", methods=["POST"])
def calcular_ruta():
    """API para calcular ruta entre dos nodos"""
    data = request.json
    nodo1_id = data.get("nodo1")
    nodo2_id = data.get("nodo2")

    if not nodo1_id or not nodo2_id:
        return jsonify({"error": "Se requieren dos nodos"}), 400

    # Obtener información de los nodos
    nodo1_info = sistema_agricola.obtener_info_nodo(nodo1_id)
    nodo2_info = sistema_agricola.obtener_info_nodo(nodo2_id)

    if not nodo1_info or not nodo2_info:
        return jsonify({"error": "Uno o ambos nodos no existen"}), 404

    # Calcular distancia directa (línea recta)
    distancia_directa = (
        calcular_distancia_haversine(
            nodo1_info["latitud"],
            nodo1_info["longitud"],
            nodo2_info["latitud"],
            nodo2_info["longitud"],
        )
        / 1000
    )  # Convertir a km

    # Calcular ruta en el grafo
    ruta_grafo = sistema_agricola.calcular_ruta_entre_nodos(nodo1_id, nodo2_id)

    # Sanitizar ruta_grafo si existe
    if ruta_grafo:
        ruta_grafo_sanitizada = {}
        for key, value in ruta_grafo.items():
            if key == "ruta":
                ruta_grafo_sanitizada[key] = value
            elif isinstance(value, (int, float)):
                ruta_grafo_sanitizada[key] = sanitize_for_json(value)
            else:
                ruta_grafo_sanitizada[key] = value
        ruta_grafo = ruta_grafo_sanitizada

    # Sanitizar info de nodos
    def sanitize_nodo_info(info):
        """Sanitiza la información de un nodo recursivamente"""
        if not isinstance(info, dict):
            return info
        sanitized = {}
        for key, value in info.items():
            if isinstance(value, (int, float)):
                sanitized[key] = sanitize_for_json(value)
            elif isinstance(value, dict):
                sanitized[key] = sanitize_nodo_info(value)
            else:
                sanitized[key] = value
        return sanitized

    resultado = {
        "nodo1": {
            "id": nodo1_id,
            "tipo": nodo1_info.get("tipo", ""),
            "latitud": sanitize_for_json(nodo1_info.get("latitud", 0)),
            "longitud": sanitize_for_json(nodo1_info.get("longitud", 0)),
            "info": sanitize_nodo_info(nodo1_info),
        },
        "nodo2": {
            "id": nodo2_id,
            "tipo": nodo2_info.get("tipo", ""),
            "latitud": sanitize_for_json(nodo2_info.get("latitud", 0)),
            "longitud": sanitize_for_json(nodo2_info.get("longitud", 0)),
            "info": sanitize_nodo_info(nodo2_info),
        },
        "distancia_directa_km": round(sanitize_for_json(distancia_directa), 2),
        "ruta_grafo": ruta_grafo,
    }

    return jsonify(resultado)


@app.route("/api/prediccion/<nodo_id>")
def obtener_prediccion(nodo_id):
    """API para obtener predicción de producción de una parcela"""
    if nodo_id not in sistema_agricola.G_agricola.nodes():
        return jsonify({"error": "Nodo no encontrado"}), 404

    nodo_info = sistema_agricola.obtener_info_nodo(nodo_id)
    if nodo_info.get("tipo") != "parcela_cultivo":
        return jsonify({"error": "El nodo no es una parcela de cultivo"}), 400

    produccion_original = sanitize_for_json(nodo_info.get("produccion_estimada_ton", 0))
    produccion_predicha = sistema_agricola.predecir_produccion(nodo_id)
    produccion_predicha = (
        sanitize_for_json(produccion_predicha) if produccion_predicha else None
    )

    diferencia = None
    porcentaje_cambio = None

    if produccion_predicha is not None and produccion_original > 0:
        diferencia = round(
            sanitize_for_json(produccion_predicha - produccion_original), 2
        )
        porcentaje_cambio = round(
            sanitize_for_json(((produccion_predicha / produccion_original - 1) * 100)),
            2,
        )

    return jsonify(
        {
            "parcela_id": nodo_id,
            "produccion_original": round(produccion_original, 2),
            "produccion_predicha": (
                round(produccion_predicha, 2)
                if produccion_predicha is not None
                else None
            ),
            "diferencia": diferencia,
            "porcentaje_cambio": porcentaje_cambio,
        }
    )


@app.route("/api/rutas-optimas/<parcela_id>")
def obtener_rutas_optimas(parcela_id):
    """API para obtener rutas óptimas desde una parcela basadas en producción predicha"""
    criterio = request.args.get(
        "criterio", "costo"
    )  # costo, tiempo, distancia, accesibilidad
    considerar_lluvia = request.args.get("lluvia", "false").lower() == "true"

    if parcela_id not in sistema_agricola.G_agricola.nodes():
        return jsonify({"error": "Parcela no encontrada"}), 404

    nodo_info = sistema_agricola.obtener_info_nodo(parcela_id)
    if nodo_info.get("tipo") != "parcela_cultivo":
        return jsonify({"error": "El nodo no es una parcela de cultivo"}), 400

    rutas = sistema_agricola.calcular_rutas_optimas_por_produccion(
        parcela_id, criterio=criterio, considerar_lluvia=considerar_lluvia
    )

    if rutas is None:
        return jsonify({"error": "No se pudieron calcular rutas"}), 400

    # Agregar información del destino y sanitizar valores
    rutas_completas = []
    for ruta in rutas:
        destino_info = sistema_agricola.obtener_info_nodo(ruta["destino"])
        ruta_completa = {
            "destino": ruta["destino"],
            "peso": sanitize_for_json(ruta.get("peso", 0)),
            "distancia_km": round(sanitize_for_json(ruta.get("distancia_km", 0)), 2),
            "tiempo_minutos": round(
                sanitize_for_json(ruta.get("tiempo_minutos", 0)), 2
            ),
            "costo_total": round(sanitize_for_json(ruta.get("costo_total", 0)), 2),
            "accesibilidad_lluvia": round(
                sanitize_for_json(ruta.get("accesibilidad_lluvia", 0)), 2
            ),
            "tipo_camino": ruta.get("tipo_camino", ""),
            "produccion_predicha": round(
                sanitize_for_json(ruta.get("produccion_predicha", 0)), 2
            ),
            "destino_info": {
                "id": ruta["destino"],
                "tipo": destino_info.get("tipo", "") if destino_info else "",
                "latitud": (
                    sanitize_for_json(destino_info.get("latitud", 0))
                    if destino_info
                    else 0
                ),
                "longitud": (
                    sanitize_for_json(destino_info.get("longitud", 0))
                    if destino_info
                    else 0
                ),
            },
        }
        rutas_completas.append(ruta_completa)

    return jsonify(
        {
            "parcela_id": parcela_id,
            "criterio": criterio,
            "considerar_lluvia": considerar_lluvia,
            "rutas": rutas_completas,
        }
    )


@app.route("/api/parcelas-priorizadas")
def obtener_parcelas_priorizadas():
    """API para obtener parcelas priorizadas por rendimiento esperado"""
    top_n = int(request.args.get("top", 10))

    parcelas = sistema_agricola.priorizar_parcelas_por_rendimiento(top_n=top_n)

    # Sanitizar valores en las parcelas
    parcelas_sanitizadas = []
    for parcela in parcelas:
        parcela_sanitizada = {
            "parcela_id": parcela["parcela_id"],
            "produccion_original": round(
                sanitize_for_json(parcela.get("produccion_original", 0)), 2
            ),
            "produccion_predicha": round(
                sanitize_for_json(parcela.get("produccion_predicha", 0)), 2
            ),
            "rendimiento_esperado": round(
                sanitize_for_json(parcela.get("rendimiento_esperado", 0)), 2
            ),
            "area_hectareas": round(
                sanitize_for_json(parcela.get("area_hectareas", 0)), 2
            ),
            "rendimiento_por_hectarea": round(
                sanitize_for_json(parcela.get("rendimiento_por_hectarea", 0)), 2
            ),
            "latitud": sanitize_for_json(parcela.get("latitud", 0)),
            "longitud": sanitize_for_json(parcela.get("longitud", 0)),
        }
        parcelas_sanitizadas.append(parcela_sanitizada)

    return jsonify(
        {"total": len(parcelas_sanitizadas), "parcelas": parcelas_sanitizadas}
    )


@app.route("/api/predicciones-todas")
def obtener_predicciones_todas():
    """API para obtener predicciones de todas las parcelas (para colorear el mapa)"""
    predicciones = sistema_agricola.obtener_predicciones_todas_parcelas()

    # Sanitizar predicciones
    predicciones_sanitizadas = []
    for pred in predicciones:
        pred_sanitizada = {
            "parcela_id": pred["parcela_id"],
            "produccion_original": round(
                sanitize_for_json(pred.get("produccion_original", 0)), 2
            ),
            "produccion_predicha": round(
                sanitize_for_json(pred.get("produccion_predicha", 0)), 2
            ),
            "latitud": sanitize_for_json(pred.get("latitud", 0)),
            "longitud": sanitize_for_json(pred.get("longitud", 0)),
        }
        predicciones_sanitizadas.append(pred_sanitizada)

    # Calcular min y max para normalización
    if predicciones_sanitizadas:
        producciones = [p["produccion_predicha"] for p in predicciones_sanitizadas]
        min_prod = min(producciones)
        max_prod = max(producciones)
    else:
        min_prod = 0
        max_prod = 1

    return jsonify(
        {
            "predicciones": predicciones_sanitizadas,
            "min_produccion": sanitize_for_json(min_prod),
            "max_produccion": sanitize_for_json(max_prod),
        }
    )


@app.route("/api/clima")
def obtener_clima():
    """API para obtener pronóstico climático de Yuma County"""
    dias = request.args.get("dias", 7, type=int)

    if dias < 1 or dias > 7:
        return jsonify({"error": "El número de días debe estar entre 1 y 7"}), 400

    try:
        pronostico = predecir_clima_yuma(dias)
        return jsonify(
            {
                "ubicacion": "Yuma County, Arizona",
                "coordenadas": {"latitud": 32.6927, "longitud": -114.6277},
                "dias_pronostico": dias,
                "pronostico": pronostico,
            }
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return (
            jsonify({"error": f"Error al obtener pronóstico climático: {str(e)}"}),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
