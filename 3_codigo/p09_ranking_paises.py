# ============================================================
# PROCESO 9: Ranking de países (¿quién reporta más y quién menos?)
# Insumo:    4_salidas/tablas/p07_cobertura_pais_indicador.csv
#            4_salidas/tablas/p08_ranking_indicadores.csv (para saber qué indicadores son elegibles)
# Resultado: 4_salidas/tablas/p09_ranking_paises.csv        (1 fila por país; 38 miembros + Perú)
#            4_salidas/tablas/p09_paises_por_subcaja.csv     (país × subcaja: % actualizado)
# Se cuentan solo los indicadores elegibles (vigentes y que el país decide reportar).
# Perú se muestra como referencia: no entra en el puesto de los miembros.
# ============================================================

# --- Paquetes ---
import pandas as pd
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
TABLAS = PROYECTO / "4_salidas" / "tablas"
NOMBRES = {"AUS": "Australia", "AUT": "Austria", "BEL": "Bélgica", "CAN": "Canadá", "CHL": "Chile",
           "COL": "Colombia", "CRI": "Costa Rica", "CZE": "Chequia", "DNK": "Dinamarca", "EST": "Estonia",
           "FIN": "Finlandia", "FRA": "Francia", "DEU": "Alemania", "GRC": "Grecia", "HUN": "Hungría",
           "ISL": "Islandia", "IRL": "Irlanda", "ISR": "Israel", "ITA": "Italia", "JPN": "Japón",
           "KOR": "Corea", "LVA": "Letonia", "LTU": "Lituania", "LUX": "Luxemburgo", "MEX": "México",
           "NLD": "Países Bajos", "NZL": "Nueva Zelanda", "NOR": "Noruega", "POL": "Polonia",
           "PRT": "Portugal", "SVK": "Eslovaquia", "SVN": "Eslovenia", "ESP": "España", "SWE": "Suecia",
           "CHE": "Suiza", "TUR": "Turquía", "GBR": "Reino Unido", "USA": "Estados Unidos", "PER": "Perú"}

cobertura = pd.read_csv(TABLAS / "p07_cobertura_pais_indicador.csv")
ranking_ind = pd.read_csv(TABLAS / "p08_ranking_indicadores.csv")
elegibles = ranking_ind.loc[ranking_ind["elegible"], ["id_indicador", "caja", "subcaja"]]

# --- Paso 9.1: quedarse con los indicadores elegibles ---
#   Antes: 224 indicadores × 39 países | Después: solo los elegibles × 39 países
cob = cobertura.merge(elegibles, on="id_indicador")
total = elegibles.shape[0]

# --- Paso 9.2: contar por país ---
paises = (cob.groupby("REF_AREA")
          .agg(n_actualizado=("estado", lambda s: (s == "Actualizado").sum()),
               n_con_dato=("estado", lambda s: (s != "Sin dato").sum()))
          .reset_index())
paises["pct_actualizado"] = (paises["n_actualizado"] / total * 100).round(1)
paises["pct_con_dato"] = (paises["n_con_dato"] / total * 100).round(1)
paises["pais"] = paises["REF_AREA"].map(NOMBRES)
paises["es_ocde"] = paises["REF_AREA"] != "PER"
paises = paises.sort_values("n_actualizado", ascending=False).reset_index(drop=True)

# Puesto entre los 38 miembros (Perú no ocupa puesto)
# .rank(method="min"): empates comparten el mismo puesto, como JERARQUIA.EQV en Excel
paises["puesto_ocde"] = paises.loc[paises["es_ocde"], "n_actualizado"].rank(ascending=False, method="min")
# Dónde quedaría Perú si se lo comparara: cuántos miembros tienen más indicadores actualizados
n_peru = paises.loc[paises["REF_AREA"] == "PER", "n_actualizado"].iloc[0]
posicion_peru = int((paises.loc[paises["es_ocde"], "n_actualizado"] > n_peru).sum()) + 1
paises["indicadores_elegibles"] = total

# --- Paso 9.3: país × subcaja (para el mapa de calor de la página) ---
por_subcaja = (cob.groupby(["REF_AREA", "caja", "subcaja"])["estado"]
               .apply(lambda s: round((s == "Actualizado").mean() * 100, 1))
               .rename("pct_actualizado").reset_index())

# --- Paso 9.4: verificar ---
print("Indicadores elegibles:", total)
print(paises[["puesto_ocde", "pais", "n_actualizado", "pct_actualizado", "n_con_dato"]].to_string(index=False))
print(f"\nPerú: {n_peru} indicadores actualizados; quedaría en el puesto {posicion_peru} de 39")

paises.to_csv(TABLAS / "p09_ranking_paises.csv", index=False, encoding="utf-8-sig")
por_subcaja.to_csv(TABLAS / "p09_paises_por_subcaja.csv", index=False, encoding="utf-8-sig")
