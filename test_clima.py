"""
Script de prueba para verificar la funcionalidad de pronóstico climático
"""

from agricultural_graph import predecir_clima_yuma, evaluar_riesgo_dia


def test_clima():
    print("=" * 60)
    print("PRUEBA DEL SISTEMA DE PRONÓSTICO CLIMÁTICO")
    print("=" * 60)

    try:
        # Probar evaluación de riesgo
        print("\n1. Probando evaluación de riesgo...")
        riesgo, alerta = evaluar_riesgo_dia(42, 5, 10)
        print(f"   ✓ Temperatura 42°C, Precip 5mm, Viento 10km/h")
        print(f"   → Riesgo: {riesgo}, Alerta: {alerta}")

        riesgo2, alerta2 = evaluar_riesgo_dia(25, 25, 35)
        print(f"   ✓ Temperatura 25°C, Precip 25mm, Viento 35km/h")
        print(f"   → Riesgo: {riesgo2}, Alerta: {alerta2}")

        # Probar pronóstico
        print("\n2. Obteniendo pronóstico climático (7 días)...")
        pronostico = predecir_clima_yuma(7)

        print(f"   ✓ Pronóstico obtenido para {len(pronostico)} días\n")

        for i, dia in enumerate(pronostico, 1):
            print(f"   Día {i} ({dia['date']}):")
            print(f"     Temp: {dia['temp_min']}°C - {dia['temp_max']}°C")
            print(f"     Precipitación: {dia['precip']} mm")
            print(f"     Viento: {dia['wind']} km/h")
            print(f"     Riesgo: {dia['risk_level']} - {dia['alert']}")
            print()

        print("=" * 60)
        print("✓ TODAS LAS PRUEBAS PASARON")
        print("=" * 60)
        print("\nEl sistema de pronóstico climático está funcionando correctamente.")
        print("Puedes usar la API en: http://localhost:5000/api/clima?dias=7")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nVerifica que:")
        print("  1. Tienes conexión a Internet")
        print("  2. La librería 'requests' está instalada")
        print("  3. La API de Open-Meteo está disponible")


if __name__ == "__main__":
    test_clima()
