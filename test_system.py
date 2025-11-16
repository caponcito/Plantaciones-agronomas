"""
Script de prueba para verificar que el sistema funciona correctamente
"""

from agricultural_graph import sistema_agricola


def test_sistema():
    print("=" * 60)
    print("PRUEBA DEL SISTEMA AGRÍCOLA")
    print("=" * 60)

    # Verificar que el sistema se inicializó
    assert sistema_agricola.G_agricola is not None, "El grafo no se inicializó"
    assert len(sistema_agricola.df_parcelas) > 0, "No hay parcelas"
    assert len(sistema_agricola.df_acopios) > 0, "No hay centros de acopio"

    print("✓ Sistema inicializado correctamente")
    print(f"  - Nodos: {sistema_agricola.G_agricola.number_of_nodes()}")
    print(f"  - Aristas: {sistema_agricola.G_agricola.number_of_edges()}")

    # Probar cálculo de ruta
    nodo1 = sistema_agricola.df_parcelas.iloc[0]["id"]
    nodo2 = sistema_agricola.df_acopios.iloc[0]["id"]

    ruta = sistema_agricola.calcular_ruta_entre_nodos(nodo1, nodo2)
    assert ruta is not None, "No se pudo calcular la ruta"
    print(f"✓ Ruta calculada entre {nodo1} y {nodo2}")
    print(f"  - Distancia: {ruta['distancia_km']:.2f} km")

    # Probar predicción de IA
    produccion_predicha = sistema_agricola.predecir_produccion(nodo1)
    assert produccion_predicha is not None, "No se pudo predecir producción"
    assert produccion_predicha > 0, "La producción predicha debe ser positiva"
    print(f"✓ Predicción de producción para {nodo1}")
    print(f"  - Producción predicha: {produccion_predicha:.2f} ton")

    print("\n" + "=" * 60)
    print("✓ TODAS LAS PRUEBAS PASARON")
    print("=" * 60)
    print("\nEl sistema está listo para usar.")
    print("Ejecuta 'python app.py' para iniciar la aplicación web.")


if __name__ == "__main__":
    test_sistema()
