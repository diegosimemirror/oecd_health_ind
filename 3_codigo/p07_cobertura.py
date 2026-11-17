# ============================================================
# PROCESO 7: Cobertura país × indicador
# Insumo:    1_datos_crudos/datos/*.csv.gz              (79 conjuntos, tal como los entrega la OCDE)
#            4_salidas/tablas/p06_clasificacion_marco.csv (224 indicadores clasificados)
# Resultado: 4_salidas/datos_procesados/p07_observaciones.parquet  (observaciones válidas, 38 miembros + Perú)
#            4_salidas/tablas/p07_registro_filtros.csv     (cuántas filas se dejaron fuera y por qué)
#            4_salidas/tablas/p07_cobertura_pais_indicador.csv (224 indicadores × 39 países)
#            4_salidas/tablas/p07_frontera_indicadores.csv  (año más reciente de cada indicador)
# Definiciones acordadas:
#   - "frontera" de un indicador = el año más reciente que reporta algún miembro de la OCDE
#   - "actualizado" = el último año del país está a no más de 2 años de la frontera (opción A)
#   - "serie vigente" = la frontera es 2022 o posterior (si no, la serie está descontinuada o fue puntual)
# Los archivos crudos NO se modifican: los filtros solo afectan a la tabla de trabajo.
# ============================================================

# --- Paquetes ---
import pandas as pd   # tablas
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
DATOS = PROYECTO / "1_datos_crudos" / "datos"
TABLAS = PROYECTO / "4_salidas" / "tablas"
PROCESADOS = PROYECTO / "4_salidas" / "datos_procesados"
PROCESADOS.mkdir(exist_ok=True)
OCDE38 = ("AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN "
          "KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA").split()
PAISES = OCDE38 + ["PER"]
VENTANA = 2          # años de tolerancia respecto de la frontera
ANIO_VIGENCIA = 2022  # una serie es vigente si su frontera es este año o posterior
# Columnas que no son dimensiones de la serie
NO_SERIE = {"DATAFLOW", "REF_AREA", "MEASURE", "UNIT_MEASURE", "FREQ", "TIME_PERIOD", "OBS_VALUE",
            "OBS_STATUS", "OBS_STATUS2", "OBS_STATUS3", "UNIT_MULT", "DECIMALS", "STATISTICAL_OPERATION",
            "OBS_PART", "OBS_SECTION", "ROUND_HSCS", "BASE_PER", "CONF_STATUS", "OBS_NOTE"}

clasificacion = pd.read_csv(TABLAS / "p06_clasificacion_marco.csv")

# --- Paso 7.1: leer cada conjunto y quedarse con las observaciones válidas ---
partes, registro = [], []
for archivo in sorted(DATOS.glob("*.csv.gz")):
    conjunto = archivo.name.replace(".csv.gz", "").replace("__", "@")
    corto = conjunto.split("@")[1]
    tabla = pd.read_csv(archivo, dtype=str, keep_default_na=False, na_values=[""])
    filas_inicio = len(tabla)

    # 7.1.a Medida: la encuesta HSCS se trata como un solo indicador
    if "HSCS" in conjunto:
        tabla["MEASURE"] = "TODAS"
    tabla["id_indicador"] = corto + "|" + tabla["MEASURE"]

    # 7.1.b Filtro 1: medidas que no son indicadores de este conjunto (EM y MCVD19 en DF_MORTALITY)
    #   Antes: todas las medidas | Después: solo las 224 medidas acordadas
    fuera_medida = ~tabla["id_indicador"].isin(clasificacion["id_indicador"])
    # 7.1.c Filtro 2: filas sin valor (vienen vacías desde la OCDE; no contienen información)
    sin_valor = tabla["OBS_VALUE"].isna()
    # 7.1.d Filtro 3: límites de intervalos de confianza (no son el valor del indicador)
    es_intervalo = (tabla["STATISTICAL_OPERATION"].isin(["BOUNDLCI", "BOUNDUCI"])
                    if "STATISTICAL_OPERATION" in tabla else pd.Series(False, index=tabla.index))
    # 7.1.e Filtro 4: países fuera del análisis (socios distintos de Perú)
    otro_pais = ~tabla["REF_AREA"].isin(PAISES)

    registro.append({"conjunto": conjunto, "filas_descargadas": filas_inicio,
                     "fuera_medida": int(fuera_medida.sum()),
                     "sin_valor": int((sin_valor & ~fuera_medida).sum()),
                     "intervalo_confianza": int((es_intervalo & ~sin_valor & ~fuera_medida).sum()),
                     "otro_pais": int((otro_pais & ~es_intervalo & ~sin_valor & ~fuera_medida).sum())})
    tabla = tabla[~(fuera_medida | sin_valor | es_intervalo | otro_pais)].copy()
    registro[-1]["filas_validas"] = len(tabla)

    # 7.1.f Año de cada observación
    #   "2024" -> 2024 | "2024-W05" (semana) -> 2024 | "2023-01-01/P2Y" (PaRIS) -> 2023
    #   HSCS: la ronda está en ROUND_HSCS; la ronda 2023 no trae columna de año
    if "ROUND_HSCS" in tabla:
        tabla["anio"] = tabla["ROUND_HSCS"].astype(int)
    elif "TIME_PERIOD" in tabla:
        tabla["anio"] = tabla["TIME_PERIOD"].str[:4].astype(int)
    else:
        tabla["anio"] = 2023
    if "TIME_PERIOD" not in tabla:
        tabla["TIME_PERIOD"] = tabla["anio"].astype(str)

    # 7.1.g Descripción de la serie: el resto de dimensiones en un solo texto "DIM=valor;..."
    dims = [c for c in tabla.columns if c not in NO_SERIE | {"id_indicador", "anio"}]
    #   (se arma pegando columnas de texto, como CONCATENAR en Excel)
    tabla["serie"] = ""
    for i, d in enumerate(dims):
        tabla["serie"] = tabla["serie"] + (";" if i else "") + d + "=" + tabla[d].fillna("")

    # 7.1.h Valor numérico (multiplicado por su UNIT_MULT: 3 = miles, 6 = millones)
    valor = pd.to_numeric(tabla["OBS_VALUE"], errors="coerce")
    multiplo = pd.to_numeric(tabla.get("UNIT_MULT", pd.Series(0, index=tabla.index)), errors="coerce").fillna(0)
    tabla["valor"] = valor * (10.0 ** multiplo)

    for col in ["UNIT_MEASURE", "OBS_STATUS"]:
        if col not in tabla:
            tabla[col] = pd.NA
    partes.append(tabla[["id_indicador", "REF_AREA", "anio", "TIME_PERIOD", "UNIT_MEASURE", "serie",
                         "OBS_VALUE", "valor", "OBS_STATUS"]])
    print(f"{conjunto:52s} {filas_inicio:>9,} -> {len(tabla):>9,}", flush=True)

# pd.concat(): apila todas las tablas una debajo de otra (como copiar y pegar hojas en una sola)
observaciones = pd.concat(partes, ignore_index=True)
registro = pd.DataFrame(registro)
print("\nObservaciones válidas:", observaciones.shape)
print(registro.drop(columns="conjunto").sum().to_string())

# --- Paso 7.2: resumir por país e indicador ---
# .groupby().agg(): como una tabla dinámica; 1 fila por indicador × país
#   Antes: millones de observaciones | Después: a lo sumo 224 × 39 filas
resumen = (observaciones.groupby(["id_indicador", "REF_AREA"])
           .agg(primer_anio=("anio", "min"), ultimo_anio=("anio", "max"),
                n_anios=("anio", "nunique"), n_obs=("anio", "size"))
           .reset_index())

# --- Paso 7.3: frontera de cada indicador (año más reciente entre los miembros) ---
frontera = (resumen[resumen["REF_AREA"].isin(OCDE38)]
            .groupby("id_indicador")["ultimo_anio"].max().rename("frontera").reset_index())

# --- Paso 7.4: cuadrícula completa 224 indicadores × 39 países (incluye los "sin dato") ---
# pd.MultiIndex.from_product: todas las combinaciones posibles, como una tabla de doble entrada
cuadricula = pd.MultiIndex.from_product([clasificacion["id_indicador"], PAISES],
                                        names=["id_indicador", "REF_AREA"]).to_frame(index=False)
cobertura = (cuadricula.merge(resumen, how="left", on=["id_indicador", "REF_AREA"])
             .merge(frontera, how="left", on="id_indicador"))
cobertura["rezago"] = cobertura["frontera"] - cobertura["ultimo_anio"]
cobertura["estado"] = "Sin dato"
cobertura.loc[cobertura["ultimo_anio"].notna(), "estado"] = "Desactualizado"
cobertura.loc[cobertura["rezago"] <= VENTANA, "estado"] = "Actualizado"
cobertura["es_ocde"] = cobertura["REF_AREA"].isin(OCDE38)

frontera = frontera.merge(clasificacion[["id_indicador"]], how="right")
frontera["serie_vigente"] = frontera["frontera"] >= ANIO_VIGENCIA

# --- Paso 7.5: verificar ---
print("\nCobertura:", cobertura.shape)
print(cobertura.groupby("es_ocde")["estado"].value_counts().unstack().to_string())
print("Indicadores sin ningún dato de miembros:", frontera["frontera"].isna().sum())
print("Series no vigentes:", (~frontera["serie_vigente"]).sum())
print(frontera[~frontera["serie_vigente"]].to_string(index=False))

observaciones.to_parquet(PROCESADOS / "p07_observaciones.parquet", index=False)
registro.to_csv(TABLAS / "p07_registro_filtros.csv", index=False, encoding="utf-8-sig")
cobertura.to_csv(TABLAS / "p07_cobertura_pais_indicador.csv", index=False, encoding="utf-8-sig")
frontera.to_csv(TABLAS / "p07_frontera_indicadores.csv", index=False, encoding="utf-8-sig")
