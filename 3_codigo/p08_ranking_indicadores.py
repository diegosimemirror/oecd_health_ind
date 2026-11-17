# ============================================================
# PROCESO 8: Ranking de indicadores (¿cuáles priorizan los miembros?)
# Insumo:    4_salidas/tablas/p07_cobertura_pais_indicador.csv
#            4_salidas/tablas/p07_frontera_indicadores.csv
#            4_salidas/tablas/p06_clasificacion_marco.csv
# Resultado: 4_salidas/tablas/p08_ranking_indicadores.csv  (1 fila por indicador)
#            4_salidas/tablas/p08_resumen_por_caja.csv     (promedio de cobertura por caja y subcaja)
# Idea: como reportar no es obligatorio, el % de miembros con dato actualizado es una señal
#       de cuánto priorizan los países ese indicador.
# Solo entran al ranking los indicadores "elegibles": serie vigente y que el país decide reportar
# (se excluyen las estimaciones hechas por la OCDE u otras instituciones).
# ============================================================

# --- Paquetes ---
import pandas as pd
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
TABLAS = PROYECTO / "4_salidas" / "tablas"

cobertura = pd.read_csv(TABLAS / "p07_cobertura_pais_indicador.csv")
frontera = pd.read_csv(TABLAS / "p07_frontera_indicadores.csv")
clasificacion = pd.read_csv(TABLAS / "p06_clasificacion_marco.csv")

# --- Paso 8.1: contar países miembros por estado, para cada indicador ---
miembros = cobertura[cobertura["es_ocde"]]
conteo = (miembros.groupby("id_indicador")
          .agg(n_actualizado=("estado", lambda s: (s == "Actualizado").sum()),
               n_con_dato=("estado", lambda s: (s != "Sin dato").sum()),
               rezago_mediano=("rezago", "median"))
          .reset_index())
conteo["pct_actualizado"] = (conteo["n_actualizado"] / 38 * 100).round(1)
conteo["pct_con_dato"] = (conteo["n_con_dato"] / 38 * 100).round(1)

# --- Paso 8.2: situación de Perú en cada indicador ---
peru = (cobertura[cobertura["REF_AREA"] == "PER"][["id_indicador", "estado", "ultimo_anio"]]
        .rename(columns={"estado": "peru_estado", "ultimo_anio": "peru_ultimo_anio"}))

# --- Paso 8.3: unir todo y marcar los indicadores elegibles ---
ranking = (clasificacion[["id_indicador", "nombre_es", "caja", "subcaja", "transversales", "tipo_fuente"]]
           .merge(frontera, on="id_indicador").merge(conteo, on="id_indicador").merge(peru, on="id_indicador"))
ESTIMACION = "Estimación o fuente internacional"
ranking["elegible"] = ranking["serie_vigente"] & (ranking["tipo_fuente"] != ESTIMACION)
ranking["motivo_no_elegible"] = ""
ranking.loc[~ranking["serie_vigente"], "motivo_no_elegible"] = "Serie descontinuada o puntual"
ranking.loc[ranking["tipo_fuente"] == ESTIMACION, "motivo_no_elegible"] = \
    "Estimación o fuente internacional (el país no decide reportarla)"

# --- Paso 8.4: nivel de priorización según % de miembros con dato actualizado ---
# pd.cut(): agrupa un número en tramos (como una tabla de rangos con BUSCARV aproximado)
ranking["nivel_priorizacion"] = pd.cut(
    ranking["pct_actualizado"], bins=[-1, 29.99, 59.99, 89.99, 100],
    labels=["Minoritario (<30 %)", "Parcial (30-59 %)", "Mayoritario (60-89 %)", "Casi universal (≥90 %)"]
).astype(str)
ranking.loc[~ranking["elegible"], "nivel_priorizacion"] = "No aplica"
ranking = ranking.sort_values(["elegible", "pct_actualizado"], ascending=[False, False])
ranking.insert(0, "puesto", range(1, len(ranking) + 1))
ranking.loc[~ranking["elegible"], "puesto"] = pd.NA

# --- Paso 8.5: resumen por caja y subcaja (solo elegibles) ---
elegibles = ranking[ranking["elegible"]]
resumen_caja = (elegibles.groupby(["caja", "subcaja"])
                .agg(indicadores=("id_indicador", "size"),
                     pct_actualizado_promedio=("pct_actualizado", "mean"),
                     casi_universales=("nivel_priorizacion", lambda s: (s == "Casi universal (≥90 %)").sum()),
                     minoritarios=("nivel_priorizacion", lambda s: (s == "Minoritario (<30 %)").sum()),
                     peru_actualizado=("peru_estado", lambda s: (s == "Actualizado").sum()))
                .round(1).reset_index())

# --- Paso 8.6: verificar ---
print("Indicadores elegibles:", ranking["elegible"].sum(), "de", len(ranking))
print(elegibles["nivel_priorizacion"].value_counts().to_string())
print("\nMás reportados:\n", elegibles.head(10)[["nombre_es", "pct_actualizado"]].to_string(index=False))
print("\nMenos reportados:\n", elegibles.tail(10)[["nombre_es", "pct_actualizado"]].to_string(index=False))
print("\n", resumen_caja.to_string(index=False))

ranking.to_csv(TABLAS / "p08_ranking_indicadores.csv", index=False, encoding="utf-8-sig")
resumen_caja.to_csv(TABLAS / "p08_resumen_por_caja.csv", index=False, encoding="utf-8-sig")
