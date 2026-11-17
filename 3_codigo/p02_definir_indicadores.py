# ============================================================
# PROCESO 2: Definir qué cuenta como "indicador"
# Insumo:    4_salidas/exploracion/conjuntos_salud.csv   (90 conjuntos del tema Salud)
#            1_datos_crudos/disponibilidad/*.xml          (qué medidas tiene cada conjunto)
# Resultado: 4_salidas/tablas/p02_conjuntos_seleccionados.csv  (79 conjuntos a descargar)
#            4_salidas/tablas/p02_indicadores.csv               (224 indicadores)
# Regla:     indicador = conjunto de detalle × medida (MEASURE)
#            - se excluyen 7 "vistas resumen" (repiten medidas de otros conjuntos)
#            - se excluyen 4 conjuntos regionales (datos dentro de cada país)
#            - la encuesta HSCS cuenta como 1 indicador por conjunto (2 en total)
# ============================================================

# --- Paquetes ---
# pandas: tablas como en Excel; xml.etree: leer los XML de disponibilidad
import pandas as pd
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
# Carpeta del proyecto: la que contiene a 3_codigo (o la que se indique al ejecutar)
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
EXPLORA = PROYECTO / "4_salidas" / "exploracion"
TABLAS = PROYECTO / "4_salidas" / "tablas"
TABLAS.mkdir(parents=True, exist_ok=True)
NS = {"s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
      "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"}
LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# --- Paso 2.1: leer la lista de conjuntos del tema Salud ---
conjuntos_salud = pd.read_csv(EXPLORA / "conjuntos_salud.csv")
print("Conjuntos del tema Salud:", conjuntos_salud.shape)          # (90, 8)

# --- Paso 2.2: marcar los conjuntos que se excluyen y por qué ---
# Vistas resumen: muestran a la vez medidas que ya están en conjuntos de detalle
VISTAS_RESUMEN = {
    "DSD_HEALTH_STAT@DF_HEALTH_STATUS": "vista resumen de Estado de salud",
    "DSD_HEALTH_PROC@DF_KEY_INDIC": "vista resumen de Uso de servicios",
    "DSD_HEALTH_EMP_REAC@DF_REAC": "vista resumen de Recursos humanos",
    "DSD_HEALTH_REAC_HOSP@DF_HOSP_REAC": "vista resumen de Recursos de proveedores",
    "DSD_HCQO@DF_HCQO": "vista resumen de Calidad de la atención",
    "DSD_HEALTH_LVNG@DF_HEALTH_LVNG": "vista resumen de Factores de riesgo",
    "HEALTH_PHMC@DF_KEY_INDIC": "vista resumen de Mercado farmacéutico",
}
def motivo_exclusion(conjunto):
    if conjunto in VISTAS_RESUMEN:
        return VISTAS_RESUMEN[conjunto]
    if conjunto.startswith("DSD_REG_HEALTH@"):
        return "datos regionales (subnacionales)"
    return ""

# .assign(): agrega una columna nueva sin quitar ninguna
#   Antes: 90 filas sin motivo | Después: 90 filas con columna motivo_exclusion
conjuntos_salud = conjuntos_salud.assign(
    motivo_exclusion=conjuntos_salud["conjunto"].map(motivo_exclusion))
conjuntos_seleccionados = conjuntos_salud[conjuntos_salud["motivo_exclusion"] == ""].copy()
print("Excluidos:", (conjuntos_salud["motivo_exclusion"] != "").sum(),
      "| Seleccionados:", conjuntos_seleccionados.shape[0])           # 11 | 79

# --- Paso 2.3: listar las medidas (MEASURE) de cada conjunto seleccionado ---
def medidas_del_conjunto(conjunto):
    """Lee el XML de disponibilidad y devuelve [(código, nombre en inglés)]."""
    raiz = ET.parse(PROYECTO / "1_datos_crudos" / "disponibilidad" /
                    f"{conjunto.replace('@', '__')}.xml").getroot()
    nombres = {}
    for lista in raiz.iter("{%s}Codelist" % NS["s"]):
        if "MEASURE" not in lista.get("id"):
            continue
        for codigo in lista.findall("s:Code", NS):
            nm = [n.text for n in codigo.findall("c:Name", NS) if n.get(LANG) == "en"]
            nombres[codigo.get("id")] = nm[0] if nm else ""
    codigos = []
    for kv in raiz.iter("{%s}KeyValue" % NS["c"]):
        if kv.get("id") == "MEASURE":
            codigos = [v.text for v in kv.findall("c:Value", NS)]
    return [(c, nombres.get(c, "")) for c in codigos]

filas = []
for c in conjuntos_seleccionados.itertuples():
    if "HSCS" in c.conjunto:
        # La encuesta HSCS es un cuestionario de políticas: 1 indicador por ronda
        filas.append({"conjunto": c.conjunto, "codigo_medida": "TODAS",
                      "nombre_en": c.nombre})
        continue
    for codigo, nombre in medidas_del_conjunto(c.conjunto):
        # En la mortalidad semanal, EM y MCVD19 ya tienen su propio conjunto de detalle
        if c.conjunto == "DSD_HEALTH_MORTALITY@DF_MORTALITY" and codigo in ("EM", "MCVD19"):
            continue
        filas.append({"conjunto": c.conjunto, "codigo_medida": codigo, "nombre_en": nombre})

# pd.DataFrame(): convierte la lista de filas en tabla
#   Después: 1 fila por indicador (conjunto × medida)
indicadores = pd.DataFrame(filas)
indicadores = indicadores.merge(
    conjuntos_seleccionados[["conjunto", "nombre", "subtemas_ocde", "enlaces_metodologia"]]
    .rename(columns={"nombre": "conjunto_nombre_en"}), on="conjunto", how="left")
# id_indicador: identificador corto y único, p. ej. "DF_LE|LFEXP"
indicadores.insert(0, "id_indicador",
                   indicadores["conjunto"].str.split("@").str[1] + "|" + indicadores["codigo_medida"])

# --- Paso 2.4: verificar ---
print("Indicadores:", indicadores.shape)
print("¿id_indicador duplicados?:", indicadores["id_indicador"].duplicated().sum())
print(indicadores.head())

conjuntos_salud.to_csv(TABLAS / "p02_conjuntos_todos_con_motivo.csv", index=False, encoding="utf-8-sig")
conjuntos_seleccionados.to_csv(TABLAS / "p02_conjuntos_seleccionados.csv", index=False, encoding="utf-8-sig")
indicadores.to_csv(TABLAS / "p02_indicadores.csv", index=False, encoding="utf-8-sig")
