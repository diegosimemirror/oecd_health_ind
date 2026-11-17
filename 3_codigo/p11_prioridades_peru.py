# ============================================================
# PROCESO 11: Prioridades de medición para Perú
# Insumo:    4_salidas/tablas/p08_ranking_indicadores.csv (qué tanto reportan los miembros)
#            4_salidas/tablas/p10_promedios.csv           (si Perú mide la misma serie u otra variante)
# Resultado: 4_salidas/tablas/p11_prioridades_peru.csv    (1 fila por indicador elegible)
#            4_salidas/tablas/p11_resumen_prioridades.csv (prioridades por caja del marco)
# Lógica: lo urgente es lo que casi todos los miembros reportan al día y Perú no tiene.
#   1. Empezar a medir    -> ≥60 % de miembros al día y Perú sin dato
#   2. Actualizar         -> ≥60 % de miembros al día y Perú con dato antiguo
#   3. Alinear definición -> Perú tiene dato, pero en otra variante que la de referencia OCDE
#   4. Evaluar            -> 30-59 % de miembros al día y Perú sin dato o con dato antiguo
#   5. Baja prioridad     -> <30 % de miembros al día y Perú sin dato o con dato antiguo
#   Al día                -> Perú tiene la misma serie y está actualizado
# ============================================================

# --- Paquetes ---
import pandas as pd
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
TABLAS = PROYECTO / "4_salidas" / "tablas"

ranking = pd.read_csv(TABLAS / "p08_ranking_indicadores.csv")
promedios = pd.read_csv(TABLAS / "p10_promedios.csv")

# --- Paso 11.1: solo indicadores elegibles + información de la serie de Perú ---
# .merge(): como BUSCARV; trae de p10 si Perú tiene la serie de referencia u otra variante
#   Antes: 224 indicadores | Después: 202 elegibles con columnas de Perú
prioridades = ranking[ranking["elegible"]].merge(
    promedios[["id_indicador", "unidad", "promedio_ocde", "valor_peru", "anio_peru",
               "peru_otra_variante_valor", "peru_otra_variante_anio", "peru_otra_variante_diferencia"]],
    on="id_indicador", how="left")
otra_variante = prioridades["valor_peru"].isna() & prioridades["peru_otra_variante_valor"].notna()

# --- Paso 11.2: asignar la prioridad (las condiciones se evalúan en orden) ---
pct = prioridades["pct_actualizado"]
estado = prioridades["peru_estado"]
prioridades["prioridad"] = "5. Baja prioridad"
prioridades.loc[(pct >= 30) & (estado != "Actualizado"), "prioridad"] = "4. Evaluar"
prioridades.loc[(pct >= 60) & (estado == "Desactualizado"), "prioridad"] = "2. Actualizar"
prioridades.loc[(pct >= 60) & (estado == "Sin dato"), "prioridad"] = "1. Empezar a medir"
prioridades.loc[estado == "Actualizado", "prioridad"] = "Al día"
prioridades.loc[otra_variante, "prioridad"] = "3. Alinear definición"
prioridades = prioridades.sort_values(["prioridad", "pct_actualizado"], ascending=[True, False])

# --- Paso 11.3: resumen por caja (como una tabla dinámica: cajas en filas, prioridades en columnas) ---
resumen = pd.crosstab([prioridades["caja"], prioridades["subcaja"]], prioridades["prioridad"],
                      margins=True, margins_name="Total").reset_index()

# --- Paso 11.4: verificar ---
print(prioridades["prioridad"].value_counts().sort_index().to_string())
print("\nPrioridad 1 (empezar a medir):")
print(prioridades.loc[prioridades["prioridad"] == "1. Empezar a medir",
                      ["nombre_es", "subcaja", "pct_actualizado"]].to_string(index=False))
print("\n", resumen.to_string(index=False))

prioridades.to_csv(TABLAS / "p11_prioridades_peru.csv", index=False, encoding="utf-8-sig")
resumen.to_csv(TABLAS / "p11_resumen_prioridades.csv", index=False, encoding="utf-8-sig")
