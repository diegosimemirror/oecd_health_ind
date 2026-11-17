# ============================================================
# PROCESO 10: Promedio OCDE por indicador y valor de Perú al lado
# Insumo:    4_salidas/datos_procesados/p07_observaciones.parquet
#            4_salidas/tablas/p07_frontera_indicadores.csv, p06_clasificacion_marco.csv
#            1_datos_crudos/catalogo/dataflows.xml (selección por defecto de la OCDE)
#            1_datos_crudos/disponibilidad/*.xml   (nombres de las unidades y categorías)
# Resultado: 4_salidas/tablas/p10_promedios.csv  (1 fila por indicador)
# Método:
#   Un indicador tiene muchas series (por sexo, edad, unidad...). Para promediar hace falta UNA serie
#   igual para todos los países. Se elige así:
#     1) se aplica la selección que la OCDE muestra por defecto en su Data Explorer;
#     2) en las demás desagregaciones se prefiere el total (_T) o "no aplica" (_Z);
#        si no hay total, la categoría con más países;
#     3) la unidad debe ser comparable entre países (tasas, %, por persona; no números absolutos
#        ni moneda nacional); entre las comparables, la que tiene más países.
#   Promedio OCDE = promedio simple del último valor de los miembros con dato actualizado.
#   Perú = su último valor en la misma serie (con su año). Si no tiene, la celda queda vacía.
# ============================================================

# --- Paquetes ---
import pandas as pd
import xml.etree.ElementTree as ET
import sys, glob
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
TABLAS = PROYECTO / "4_salidas" / "tablas"
NS = {"s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
      "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"}
LANG = "{http://www.w3.org/XML/1998/namespace}lang"
OCDE38 = set(("AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN "
              "KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA").split())
VENTANA = 2

# Unidades que NO se pueden promediar entre países: números absolutos y moneda nacional
NO_COMPARABLES = {"BD", "CS", "DEVC", "DSC", "DT", "EUR_PPP", "EXM", "FC", "HSPTL", "PRC", "PS", "PS_FTE",
                  "T_CO2E", "USD_EXC", "USD_PPP", "XDC", "XDC_PS", "D"}
# "D" (días) sí es comparable cuando mide estancia o espera (no días-cama totales)
DIAS_COMPARABLES = {"STAY", "WAIT_MEAN", "WAIT_MEDIAN"}
# Ajustes manuales (revisados uno por uno) cuando la regla automática no elige la serie de referencia
AJUSTES = {
    "DF_REMUN|AI": {"UNIT_MEASURE": "FCTR_WG_A_SAL_A"},   # remuneración en veces el salario promedio
    "DF_HOSP_DISCHARGE|DISCHARGE": {"DIAGNOSTIC_TYPE": "DICDA000"},  # todas las causas (no solo infecciosas)
    "DF_HOSP_AV_LENGTH|STAY": {"DIAGNOSTIC_TYPE": "DICDA000"},       # todas las causas
    "DF_GRAD|HSG": {"HEALTH_PROF": "PHYS"},               # graduados de medicina (no dentistas)
    "DF_C|CNCR": {"CANCER_SITE": "CICDTUME"},             # todos los cánceres C00-C97 (CICDCANC es pulmón)
}
SIN_PROMEDIO = {  # indicadores donde un promedio no tiene sentido
    "DF_HSCS2023|TODAS": "Respuestas cualitativas (cuestionario)",
    "DF_HSCS|TODAS": "Respuestas cualitativas (cuestionario)",
    "DF_MORTALITY|M": "Serie semanal en números absolutos",
    "DF_MORTALITY_COVID|MCVD19": "Serie semanal",
    "DF_MORTALITY_EXCESS|EM": "Serie semanal",
}

# --- Paso 10.1: selección por defecto de la OCDE (anotación DEFAULT de cada conjunto) ---
catalogo = ET.parse(PROYECTO / "1_datos_crudos" / "catalogo" / "dataflows.xml").getroot()
por_defecto = {}
for f in catalogo.iter("{%s}Dataflow" % NS["s"]):
    for a in f.iter("{%s}Annotation" % NS["c"]):
        if a.findtext("c:AnnotationType", namespaces=NS) == "DEFAULT":
            reglas = {}
            for par in (a.findtext("c:AnnotationTitle", namespaces=NS) or "").split(","):
                if "=" in par:
                    dim, valores = par.split("=", 1)
                    if dim not in ("TIME_PERIOD_START", "LASTNPERIODS", "MEASURE", "REF_AREA"):
                        reglas[dim] = valores.split("+")
            por_defecto[f.get("id").split("@")[1]] = reglas

# --- Paso 10.2: nombres de códigos (para describir la serie elegida) ---
nombres = {}
for archivo in glob.glob(str(PROYECTO / "1_datos_crudos" / "disponibilidad" / "*.xml")):
    for lista in ET.parse(archivo).getroot().iter("{%s}Codelist" % NS["s"]):
        for codigo in lista.findall("s:Code", NS):
            nm = [n.text for n in codigo.findall("c:Name", NS) if n.get(LANG) == "en"]
            nombres[(lista.get("id"), codigo.get("id"))] = nm[0] if nm else codigo.get("id")
def nombre(dim, valor):
    for (lista, cod), nm in nombres.items():
        if cod == valor and dim.replace("_", "") in lista.replace("_", ""):
            return nm
    return valor

# --- Paso 10.3: leer las observaciones y separar la serie en columnas ---
obs = pd.read_parquet(PROYECTO / "4_salidas" / "datos_procesados" / "p07_observaciones.parquet")
obs = obs[obs["valor"].notna()]
frontera = pd.read_csv(TABLAS / "p07_frontera_indicadores.csv").set_index("id_indicador")["frontera"]
clasificacion = pd.read_csv(TABLAS / "p06_clasificacion_marco.csv")

def elegir_serie(datos, id_indicador):
    """Devuelve (datos de la serie elegida, unidad, descripción, nota)."""
    conjunto, medida = id_indicador.split("|")
    corte = frontera[id_indicador] - VENTANA
    # Separar "DIM=valor;DIM=valor" en columnas
    dims = pd.DataFrame([dict(p.split("=", 1) for p in s.split(";") if "=" in p) for s in datos["serie"]],
                        index=datos.index) if datos["serie"].str.len().max() else pd.DataFrame(index=datos.index)
    d = pd.concat([datos, dims], axis=1)
    nota = []

    def paises_recientes(sub):
        return sub.loc[(sub["anio"] >= corte) & sub["REF_AREA"].isin(OCDE38), "REF_AREA"].nunique()

    # 1) ajustes manuales
    for dim, valor in AJUSTES.get(id_indicador, {}).items():
        d = d[d[dim] == valor]; nota.append(f"ajuste manual {dim}={valor}")
    # 2) selección por defecto de la OCDE (solo si deja datos y no hay ajuste manual en esa dimensión)
    for dim, valores in por_defecto.get(conjunto, {}).items():
        if dim in d and dim != "UNIT_MEASURE" and dim not in AJUSTES.get(id_indicador, {}):
            sub = d[d[dim].isin(valores)]
            if paises_recientes(sub) > 0:
                d = sub
    # 3) unidad comparable
    comparable = ~d["UNIT_MEASURE"].isin(NO_COMPARABLES) | (
        (d["UNIT_MEASURE"] == "D") & (medida in DIAS_COMPARABLES))
    d = d[comparable]
    if d.empty or paises_recientes(d) == 0:
        return None, "", "", "Solo hay unidades no comparables (números absolutos o moneda nacional)"
    n_por_unidad = d.groupby("UNIT_MEASURE").apply(paises_recientes)
    candidatas = n_por_unidad[n_por_unidad >= 0.5 * n_por_unidad.max()]
    preferidas = [u for u in por_defecto.get(conjunto, {}).get("UNIT_MEASURE", []) if u in candidatas]
    unidad = (candidatas[preferidas].idxmax() if preferidas else candidatas.idxmax())
    d = d[d["UNIT_MEASURE"] == unidad]
    # 4) demás desagregaciones: total, "no aplica" o la categoría con más países
    elegidas = {}
    for dim in dims.columns:
        valores = d[dim].unique()
        if len(valores) <= 1:
            if len(valores) == 1 and valores[0] not in ("_T", "_Z"):
                elegidas[dim] = valores[0]
            continue
        if "_T" in valores:
            v = "_T"
        elif "_Z" in valores:
            v = "_Z"
        else:
            v = d.groupby(dim).apply(paises_recientes).idxmax()
        d = d[d[dim] == v]
        if v not in ("_T", "_Z"):
            elegidas[dim] = v
    # Descripción legible: solo las categorías con contenido (se omiten vacíos)
    #   si un código no tiene nombre, se muestra como DIMENSIÓN=código (p. ej. SURVEY_VERSION=2)
    descripcion = "; ".join((nombre(k, v) if nombre(k, v) != v else f"{k}={v}")
                            for k, v in elegidas.items() if v and v.strip())
    return d, unidad, descripcion, "; ".join(nota)

def variante_peru(datos, serie_elegida, unidad, medida):
    """Si Perú no tiene la serie elegida pero sí otra variante del indicador, devuelve la más parecida.
    Parecida = misma unidad si se puede, menos dimensiones distintas y año más reciente."""
    peru = datos[(datos["REF_AREA"] == "PER") & datos["valor"].notna()]
    peru = peru[~peru["UNIT_MEASURE"].isin(NO_COMPARABLES) |
                ((peru["UNIT_MEASURE"] == "D") & (medida in DIAS_COMPARABLES))]
    if peru.empty or serie_elegida is None or serie_elegida.empty:
        return None
    ref = dict(p.split("=", 1) for p in serie_elegida["serie"].iloc[0].split(";") if "=" in p)
    def diferencias(serie):
        actual = dict(p.split("=", 1) for p in serie.split(";") if "=" in p)
        return [k for k in ref if actual.get(k, "") != ref[k]]
    peru = peru.assign(n_dif=peru["serie"].map(lambda s: len(diferencias(s))),
                       otra_unidad=(peru["UNIT_MEASURE"] != unidad).astype(int))
    mejor = peru.sort_values(["otra_unidad", "n_dif", "anio"], ascending=[True, True, False]).iloc[0]
    actual = dict(p.split("=", 1) for p in mejor["serie"].split(";") if "=" in p)
    cambios = [f"{nombre(k, actual.get(k, ''))} (OCDE: {nombre(k, ref[k])})" for k in diferencias(mejor["serie"])]
    if mejor["UNIT_MEASURE"] != unidad:
        cambios.insert(0, f"unidad {nombre('UNIT_MEASURE', mejor['UNIT_MEASURE'])} "
                          f"(OCDE: {nombre('UNIT_MEASURE', unidad)})")
    return {"peru_otra_variante_valor": mejor["valor"], "peru_otra_variante_anio": int(mejor["anio"]),
            "peru_otra_variante_misma_unidad": mejor["UNIT_MEASURE"] == unidad,
            "peru_otra_variante_diferencia": "; ".join(cambios)}

# --- Paso 10.4: calcular promedio OCDE y valor de Perú para cada indicador ---
filas = []
for id_indicador, datos in obs.groupby("id_indicador"):
    fila = {"id_indicador": id_indicador}
    if id_indicador in SIN_PROMEDIO:
        fila["nota"] = SIN_PROMEDIO[id_indicador]; filas.append(fila); continue
    serie, unidad, descripcion, nota = elegir_serie(datos, id_indicador)
    fila.update({"unidad_codigo": unidad, "unidad": nombre("UNIT_MEASURE", unidad) if unidad else "",
                 "serie_elegida": descripcion, "nota": nota})
    if serie is not None:
        # Último valor de cada país en la serie elegida
        #   .sort_values + .groupby().tail(1): para cada país, la fila del año más reciente
        ultimo = serie.sort_values("anio").groupby("REF_AREA").tail(1).set_index("REF_AREA")
        corte = frontera[id_indicador] - VENTANA
        miembros = ultimo[ultimo.index.isin(OCDE38) & (ultimo["anio"] >= corte)]
        fila.update({"promedio_ocde": miembros["valor"].mean(), "mediana_ocde": miembros["valor"].median(),
                     "min_ocde": miembros["valor"].min(), "max_ocde": miembros["valor"].max(),
                     "n_paises_promedio": len(miembros),
                     "anios_promedio": f"{miembros['anio'].min()}-{miembros['anio'].max()}"})
        if "PER" in ultimo.index:
            fila.update({"valor_peru": ultimo.loc["PER", "valor"], "anio_peru": int(ultimo.loc["PER", "anio"])})
        else:
            # Perú no tiene la serie de referencia: ¿reporta otra variante del mismo indicador?
            fila.update(variante_peru(datos, serie, unidad, id_indicador.split("|")[1]) or {})
    filas.append(fila)

promedios = clasificacion[["id_indicador", "nombre_es", "caja", "subcaja"]].merge(
    pd.DataFrame(filas), on="id_indicador", how="left")

# --- Paso 10.5: verificar ---
print("Indicadores con promedio:", promedios["promedio_ocde"].notna().sum(), "de", len(promedios))
print("Con valor de Perú:", promedios["valor_peru"].notna().sum(),
      "| Perú reporta otra variante:", promedios["peru_otra_variante_valor"].notna().sum())
print(promedios.loc[promedios["peru_otra_variante_valor"].notna(),
                    ["id_indicador", "peru_otra_variante_valor", "peru_otra_variante_diferencia"]].to_string(index=False))
pd.set_option("display.width", 250, "display.max_rows", 300, "display.max_colwidth", 55)
print(promedios[["id_indicador", "unidad_codigo", "serie_elegida", "promedio_ocde", "n_paises_promedio",
                 "valor_peru", "anio_peru"]].to_string(index=False))
promedios.to_csv(TABLAS / "p10_promedios.csv", index=False, encoding="utf-8-sig")
