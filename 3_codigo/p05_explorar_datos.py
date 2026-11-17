# ============================================================
# PROCESO 5: Explorar los datos descargados (lista de 10 puntos)
# Insumo:    1_datos_crudos/datos/*.csv.gz  (79 conjuntos)
# Resultado: 4_salidas/tablas/p05_exploracion_conjuntos.csv  (1 fila por conjunto, todas las revisiones)
#            4_salidas/tablas/p05_marcas_obs_status.csv      (frecuencia de las marcas de calidad del dato)
#            4_salidas/tablas/p05_unidades.csv                (unidades de medida por indicador)
# Nota: este proceso SOLO mira; no elimina ni modifica ningún dato.
# ============================================================

# --- Paquetes ---
import pandas as pd   # leer los CSV comprimidos (pandas descomprime .gz automáticamente)
import numpy as np    # cálculos numéricos (contar ceros, negativos)
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
DATOS = PROYECTO / "1_datos_crudos" / "datos"
TABLAS = PROYECTO / "4_salidas" / "tablas"
OCDE38 = set(("AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN "
              "KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA").split())
# Columnas que NO son dimensiones (son el valor o atributos del valor)
NO_DIMENSION = {"DATAFLOW", "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "OBS_STATUS2", "OBS_STATUS3",
                "UNIT_MULT", "DECIMALS", "BASE_PER", "CONF_STATUS", "OBS_NOTE", "COMMENT_OBS"}

def leer_conjunto(archivo):
    """Lee un CSV comprimido. Todo como texto salvo OBS_VALUE, para no deformar códigos como '01'."""
    tabla = pd.read_csv(archivo, dtype=str, keep_default_na=False, na_values=[""])
    # pd.to_numeric(errors="coerce"): convierte a número; lo que no es número queda vacío (NaN)
    #   Antes: OBS_VALUE como texto | Después: OBS_VALUE como número
    tabla["OBS_VALUE_NUM"] = pd.to_numeric(tabla["OBS_VALUE"], errors="coerce")
    return tabla

filas, marcas, unidades = [], [], []
for archivo in sorted(DATOS.glob("*.csv.gz")):
    conjunto = archivo.name.replace(".csv.gz", "").replace("__", "@")
    tabla = leer_conjunto(archivo)
    dims = [c for c in tabla.columns if c not in NO_DIMENSION and c != "OBS_VALUE_NUM"]
    clave = dims + (["TIME_PERIOD"] if "TIME_PERIOD" in tabla.columns else [])
    v = tabla["OBS_VALUE_NUM"]
    periodos = tabla["TIME_PERIOD"].dropna() if "TIME_PERIOD" in tabla.columns else pd.Series(dtype=str)
    unidad_pct = tabla["UNIT_MEASURE"].str.startswith("PT", na=False) if "UNIT_MEASURE" in tabla else False
    filas.append({
        "conjunto": conjunto,
        # 1. Tamaño
        "filas": tabla.shape[0], "columnas": tabla.shape[1],
        # 3. Tipos: ¿hay valores no numéricos en OBS_VALUE?
        "valores_no_numericos": int(tabla["OBS_VALUE"].notna().sum() - v.notna().sum()),
        # 4. Qué es cada fila y duplicados (fila = combinación única de dimensiones + periodo)
        "dimensiones": len(dims),
        "duplicados_fila_completa": int(tabla.duplicated().sum()),
        "duplicados_por_clave": int(tabla.duplicated(subset=clave).sum()),
        # 5. Faltantes (y faltantes disfrazados)
        "valor_vacio": int(v.isna().sum()),
        "valor_cero": int((v == 0).sum()),
        "valor_negativo": int((v < 0).sum()),
        "valores_tipo_codigo_faltante": int(v.isin([-99, -999, 999, 9999]).sum()),
        # 6. Estadísticos básicos
        "minimo": v.min(), "mediana": v.median(), "maximo": v.max(),
        # 10. Imposibles: porcentajes por encima de 100
        "porcentaje_mayor_100": int((v[unidad_pct] > 100).sum()) if "UNIT_MEASURE" in tabla else 0,
        # 7-8. Frecuencias y valores únicos
        "paises_o_areas": tabla["REF_AREA"].nunique(),
        "miembros_ocde": len(OCDE38 & set(tabla["REF_AREA"])),
        "tiene_peru": "PER" in set(tabla["REF_AREA"]),
        "areas_no_pais": ", ".join(sorted(a for a in tabla["REF_AREA"].unique() if len(a) != 3)),
        "unidades": tabla["UNIT_MEASURE"].nunique() if "UNIT_MEASURE" in tabla else 0,
        # 9. Rango de fechas
        "periodo_min": periodos.min() if len(periodos) else "", "periodo_max": periodos.max() if len(periodos) else "",
        "frecuencia": ", ".join(sorted(tabla["FREQ"].unique())) if "FREQ" in tabla else "sin FREQ",
    })
    # Marcas de calidad del dato (OBS_STATUS): A normal, E estimado, B quiebre de serie, P provisional...
    if "OBS_STATUS" in tabla:
        for marca, n in tabla["OBS_STATUS"].fillna("(vacío)").value_counts().items():
            marcas.append({"conjunto": conjunto, "obs_status": marca, "n": n})
    if "UNIT_MEASURE" in tabla and "MEASURE" in tabla:
        u = tabla.groupby(["MEASURE", "UNIT_MEASURE"])["REF_AREA"].nunique().reset_index(name="paises")
        u.insert(0, "conjunto", conjunto)
        unidades.append(u)
    print(f"{conjunto:52s} {tabla.shape[0]:>9,} filas", flush=True)

exploracion = pd.DataFrame(filas)
exploracion.to_csv(TABLAS / "p05_exploracion_conjuntos.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(marcas).to_csv(TABLAS / "p05_marcas_obs_status.csv", index=False, encoding="utf-8-sig")
pd.concat(unidades).to_csv(TABLAS / "p05_unidades.csv", index=False, encoding="utf-8-sig")

# --- Resumen en pantalla ---
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 120)
print("\nTotal de filas:", f"{exploracion['filas'].sum():,}")
cols = ["filas", "valores_no_numericos", "duplicados_fila_completa", "duplicados_por_clave", "valor_vacio",
        "valor_cero", "valor_negativo", "valores_tipo_codigo_faltante", "porcentaje_mayor_100"]
print(exploracion[cols].sum().to_string())
print("\nConjuntos con algún problema:")
problema = exploracion[(exploracion[cols[1:]] > 0).any(axis=1)]
print(problema[["conjunto"] + cols + ["minimo", "maximo"]].to_string(index=False))
print("\nÁreas que no son países:", sorted(set(", ".join(exploracion["areas_no_pais"]).split(", ")) - {""}))
print("\nFrecuencias:", exploracion["frecuencia"].value_counts().to_dict())
print("\nMarcas OBS_STATUS (total):")
print(pd.DataFrame(marcas).groupby("obs_status")["n"].sum().sort_values(ascending=False).to_string())
