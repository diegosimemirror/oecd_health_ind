# ============================================================
# PROCESO 13: Representación (página web + libro de Excel)
# Insumo:    4_salidas/tablas/p02 ... p12  (resultados de los procesos anteriores)
#            3_codigo/plantilla_pagina.html (diseño de la página, con un hueco para los datos)
# Resultado: 5_pagina/index.html            (página lista para GitHub Pages)
#            5_pagina/datos/*.csv, *.xlsx    (descargas que ofrece la página)
#            4_salidas/indicadores_ocde_salud.xlsx (libro de Excel con todas las tablas)
# La página no calcula nada nuevo: solo muestra las tablas ya calculadas.
# ============================================================

# --- Paquetes ---
import pandas as pd        # leer las tablas y escribir el Excel
import json, sys, shutil   # json: convertir las tablas al formato que lee la página (JavaScript)
from urllib.parse import quote
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
TABLAS = PROYECTO / "4_salidas" / "tablas"
PAGINA = PROYECTO / "5_pagina"
(PAGINA / "datos").mkdir(parents=True, exist_ok=True)
FECHA_DATOS = "16 y 17 de noviembre de 2026"

# --- Paso 13.1: unidades en español ---
UNIDADES = {
    "0_TO_1": "escala 0-1", "0_TO_100": "escala 0-100", "0_TO_48": "escala 0-48",
    "10P2ADM": "por 100 ingresos", "10P2DLV": "por 100 partos", "10P2HB_Y_GE65": "por 100 hab. de 65+",
    "10P2PAT": "por 100 pacientes", "10P3HB": "por 1 000 hab.", "10P3HB_Y_GE65": "por 1 000 hab. de 65+",
    "10P3PAT_Y_GE65": "por 1 000 pacientes de 65+", "10P5DSC": "por 100 000 egresos",
    "10P5HB": "por 100 000 hab.", "10P5PAT": "por 100 000 pacientes", "10P6HB": "por millón de hab.",
    "CG_SM_D": "cigarrillos por fumador al día", "CN_PS": "consultas por persona",
    "CS_10P5PS": "casos por 100 000 hab.", "D": "días", "DDD_10P3HB": "DDD por 1 000 hab. al día",
    "DSC_10P5PS": "egresos por 100 000 hab.", "DT_10P3BR": "muertes por 1 000 nacimientos",
    "DT_10P3BR_L": "muertes por 1 000 nacidos vivos", "DT_10P5BR_L": "muertes por 100 000 nacidos vivos",
    "DT_10P5HB": "muertes por 100 000 hab.", "D_PS": "días por persona", "EXM_10P3PS": "exámenes por 1 000 hab.",
    "FCTR_POP_MORT": "veces la mortalidad de la población", "FCTR_WG_A_SAL_A": "veces el salario promedio",
    "G_PS_D": "gramos por persona al día", "IJ_10P6HB": "lesionados por millón de hab.",
    "KCAL_PS_D": "kcal por persona al día", "KG_CO2E_PS": "kg de CO₂e por persona",
    "KG_PS_Y": "kg por persona al año", "L_PS": "litros por persona", "PO": "puntos",
    "PRC_10P5PS": "procedimientos por 100 000 hab.", "PT_B1GQ": "% del PIB", "PT_BD_AV": "% de camas disponibles",
    "PT_BD_FC_LT": "% de camas de largo plazo", "PT_BR_L": "% de nacidos vivos",
    "PT_CH_ELG_IM": "% de niños elegibles", "PT_DDD_PRSC": "% de DDD recetadas", "PT_DT": "% de muertes",
    "PT_EXP_FS": "% del gasto del esquema", "PT_EXP_HLTH": "% del gasto en salud", "PT_EXP_PRV": "% del gasto del proveedor",
    "PT_FC_LT": "% de establecimientos", "PT_PAT": "% de pacientes", "PT_PAT_DIAB": "% de pacientes con diabetes",
    "PT_PAT_MH": "% de pacientes de salud mental", "PT_PAT_WAIT_M_GT3": "% que espera más de 3 meses",
    "PT_POP": "% de la población", "PT_POP_AGE": "% de la población de esa edad",
    "PT_POP_COND": "% de personas con la condición", "PT_POP_SEX_AGE": "% de la población de ese sexo y edad",
    "PT_POP_Y_GE65": "% de la población de 65+", "PT_POP_Y_GE75": "% de la población de 75+",
    "PT_RCP_FC_LT": "% de receptores", "PT_RESP": "% de encuestados", "PT_SL_VOL_M": "% del volumen de ventas",
    "PT_WR_PRF_HLTH": "% de la profesión", "SCR_PROMIS": "puntaje PROMIS", "USD_PPP_PS": "USD PPA por persona",
    "WK_Y_PS": "semanas al año por persona", "Y": "años", "Y_10P5PS": "años por 100 000 hab.",
}

# --- Paso 13.2: explicaciones en español de las diferencias de definición de Perú ---
ALINEAR = {
    "DF_PHYS|HSE": "Perú reporta médicos profesionalmente activos; la OCDE compara médicos en ejercicio (los que atienden pacientes).",
    "DF_HEALTH_LVNG_BW|SP_OBS": "Perú reporta obesidad medida (ENDES); la mayoría de miembros reporta obesidad autorreportada. Solo es comparable con países que también miden.",
    "DF_HEALTH_LVNG_BW|SP_OVRGHT": "Perú reporta sobrepeso medido (ENDES); la mayoría de miembros lo reporta autorreportado.",
    "DF_HEALTH_LVNG_BW|SP_OVRGHT_OBS": "Perú reporta sobrepeso u obesidad medido (ENDES); la mayoría de miembros lo reporta autorreportado.",
    "DF_CONSULT|CONSULT": "Perú solo reporta consultas presenciales con dentistas; falta el total de consultas médicas (presenciales y a distancia).",
    "DF_SCREEN|SCREEN": "Perú reporta tamizaje de cuello uterino por encuesta (20 a 69 años); la referencia OCDE es la mamografía de programa (50 a 69 años).",
    "DF_BEDS_ICU|HBU_ICU_A": "Perú reporta la ocupación de las UCI, no el número de camas de UCI de adultos por habitante.",
    "DF_MED_TECH|MTU": "Perú cuenta equipos solo en hospitales del MINSA y gobiernos regionales; la referencia OCDE cuenta todos los proveedores.",
    "DF_GEN_MRKT|PH_MARKET": "Perú reporta el mercado de farmacias comunitarias; la referencia OCDE es el mercado total.",
    "DF_AGGR|STAY": "Perú reporta la estancia promedio en atención curativa (aguda); la referencia OCDE es la de todas las hospitalizaciones.",
    "DF_PSC|HOSP_SUP":"Perú aplicó la versión 2 de la encuesta de cultura de seguridad; el promedio OCDE de este ítem usa la versión 1.",
    "DF_PSC|LEARNING": "Perú aplicó la versión 2 de la encuesta de cultura de seguridad; el promedio OCDE de este ítem usa la versión 1.",
    "DF_PSC|SUPER_SUP": "Perú aplicó la versión 2 de la encuesta de cultura de seguridad; el promedio OCDE de este ítem usa la versión 1.",
}

# --- Paso 13.3: leer las tablas de los procesos anteriores ---
clasificacion = pd.read_csv(TABLAS / "p06_clasificacion_marco.csv")
ranking = pd.read_csv(TABLAS / "p08_ranking_indicadores.csv")
promedios = pd.read_csv(TABLAS / "p10_promedios.csv")
prioridades = pd.read_csv(TABLAS / "p11_prioridades_peru.csv")
comparabilidad = pd.read_csv(TABLAS / "p12_comparabilidad_peru.csv")
paises = pd.read_csv(TABLAS / "p09_ranking_paises.csv")
conjuntos = pd.read_csv(TABLAS / "p02_conjuntos_seleccionados.csv")
fichas = pd.read_csv(TABLAS / "p04_indice_fichas.csv")

# Enlace al conjunto en el OECD Data Explorer (la "herramienta real") y a su ficha principal
conjuntos["enlace_datos"] = ("https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]="
                             + conjuntos["conjunto"].map(quote) + "&df[ag]=" + conjuntos["agencia"])
conjuntos["conjunto_corto"] = conjuntos["conjunto"].str.split("@").str[1]
ficha = (fichas[fichas["tipo"] == "documento"].groupby("conjunto")["url"].first()
         .rename("enlace_ficha").reset_index())
conjuntos = conjuntos.merge(ficha, on="conjunto", how="left")

# --- Paso 13.4: una tabla por indicador con todo lo que muestra la página ---
#   .merge() sucesivos: como varios BUSCARV que pegan columnas de cada tabla
ind = (clasificacion[["id_indicador", "nombre_es", "nombre_en", "caja", "subcaja", "transversales",
                      "fuente_asignacion", "tipo_fuente", "detalle_fuente", "conjunto"]]
       .merge(ranking[["id_indicador", "elegible", "motivo_no_elegible", "frontera", "n_actualizado",
                       "pct_actualizado", "n_con_dato", "nivel_priorizacion", "peru_estado", "peru_ultimo_anio"]],
              on="id_indicador")
       .merge(promedios[["id_indicador", "unidad_codigo", "serie_elegida", "promedio_ocde", "n_paises_promedio",
                         "anios_promedio", "valor_peru", "anio_peru", "peru_otra_variante_valor",
                         "peru_otra_variante_anio", "peru_otra_variante_misma_unidad",
                         "peru_otra_variante_diferencia", "nota"]],
              on="id_indicador", how="left")
       .merge(prioridades[["id_indicador", "prioridad"]], on="id_indicador", how="left")
       .merge(comparabilidad[["id_indicador", "alertas", "fuente_peru_segun_ficha"]], on="id_indicador", how="left")
       .merge(conjuntos[["conjunto", "enlace_datos", "enlace_ficha"]], on="conjunto", how="left"))
ind["unidad_es"] = ind["unidad_codigo"].map(UNIDADES)
ind["alinear_es"] = ind["id_indicador"].map(ALINEAR)
sin_traducir = set(ind["unidad_codigo"].dropna()) - set(UNIDADES)
print("Unidades sin traducción:", sin_traducir or "ninguna")
print("Indicadores en la página:", ind.shape)

# --- Paso 13.5: insertar los datos en la plantilla ---
def a_registros(tabla):
    """Tabla -> lista de diccionarios; los vacíos (NaN) pasan a null para JavaScript."""
    return json.loads(tabla.to_json(orient="records", force_ascii=False))

datos = {"indicadores": a_registros(ind),
         "paises": a_registros(paises[["REF_AREA", "pais", "es_ocde", "n_actualizado", "pct_actualizado",
                                       "n_con_dato", "puesto_ocde", "indicadores_elegibles"]]),
         "fecha_datos": FECHA_DATOS}
plantilla = (PROYECTO / "3_codigo" / "plantilla_pagina.html").read_text(encoding="utf-8")
# Se escapa "</" para que ningún texto de los datos pueda cerrar la etiqueta <script> por accidente
json_datos = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
html = plantilla.replace("/*__DATOS__*/null", json_datos)
(PAGINA / "index.html").write_text(html, encoding="utf-8")
print("Página:", PAGINA / "index.html", f"({len(html)/1024:.0f} KB)")
# El pipeline (diagrama tipo n8n de cómo se hizo el trabajo) es una página fija: solo se copia
shutil.copy(PROYECTO / "3_codigo" / "plantilla_pipeline.html", PAGINA / "pipeline.html")
print("Pipeline:", PAGINA / "pipeline.html")

# --- Paso 13.6: libro de Excel con todas las tablas (para quien prefiera trabajar en Excel) ---
LEEME = pd.DataFrame({"Hoja": [
    "Indicadores", "Paises", "Prioridades_Peru", "Comparabilidad_Peru", "Resumen_por_caja",
    "Cobertura_pais_indicador", "Registro_filtros", "Fichas"], "Contenido": [
    "224 indicadores: caja del marco, % de miembros al día, promedio OCDE, valor de Perú y prioridad",
    "38 miembros + Perú: indicadores elegibles con dato al día",
    "202 indicadores elegibles con la prioridad de medición para Perú",
    "Indicadores que Perú reporta: marcas de calidad (estimado, definición distinta) y fuente según la ficha",
    "Promedio de cobertura por caja y subcaja del marco",
    "224 indicadores × 39 países: último año, rezago y estado (Actualizado / Desactualizado / Sin dato)",
    "Filas descargadas y filas excluidas de cada conjunto, con el motivo",
    "Índice de fichas metodológicas descargadas"]})
hojas = {
    "Leeme": LEEME,
    "Indicadores": ind.drop(columns=["nota"]),
    "Paises": paises,
    "Prioridades_Peru": prioridades,
    "Comparabilidad_Peru": comparabilidad,
    "Resumen_por_caja": pd.read_csv(TABLAS / "p08_resumen_por_caja.csv"),
    "Cobertura_pais_indicador": pd.read_csv(TABLAS / "p07_cobertura_pais_indicador.csv"),
    "Registro_filtros": pd.read_csv(TABLAS / "p07_registro_filtros.csv"),
    "Fichas": fichas,
}
libro = PROYECTO / "4_salidas" / "indicadores_ocde_salud.xlsx"
with pd.ExcelWriter(libro, engine="openpyxl") as escritor:
    for nombre, tabla in hojas.items():
        tabla.to_excel(escritor, sheet_name=nombre, index=False)
        hoja = escritor.sheets[nombre]
        hoja.freeze_panes = "A2"                      # inmovilizar la fila de títulos, como en Excel
        for columna in hoja.columns:                  # ancho de columna según el contenido (máx. 60)
            largo = max(len(str(c.value)) if c.value is not None else 0 for c in columna[:200])
            hoja.column_dimensions[columna[0].column_letter].width = min(max(10, largo + 2), 60)
print("Excel:", libro)

# --- Paso 13.7: copiar las descargas junto a la página ---
shutil.copy(libro, PAGINA / "datos" / libro.name)
for nombre in ["p06_clasificacion_marco.csv", "p08_ranking_indicadores.csv", "p09_ranking_paises.csv",
               "p10_promedios.csv", "p11_prioridades_peru.csv", "p12_comparabilidad_peru.csv",
               "p07_cobertura_pais_indicador.csv"]:
    shutil.copy(TABLAS / nombre, PAGINA / "datos" / nombre)
print("Descargas copiadas a", PAGINA / "datos")
