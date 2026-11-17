# ============================================================
# EXPLORACIÓN 2: Resumir la disponibilidad de cada conjunto de Salud
# Insumo:    1_datos_crudos/disponibilidad/*.xml  +  conjuntos_salud.csv
# Resultado: 4_salidas/exploracion/resumen_conjuntos.csv   (1 fila por conjunto)
#            4_salidas/exploracion/indicadores_catalogo.csv (1 fila por conjunto × indicador)
# Nota: solo lee y resume; no modifica datos.
# ============================================================

# --- Paquetes ---
import xml.etree.ElementTree as ET   # leer los XML de disponibilidad
import pandas as pd                  # armar tablas resumen
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1])
DISPONIB = PROYECTO / "1_datos_crudos" / "disponibilidad"
SALIDA = PROYECTO / "4_salidas" / "exploracion"
NS = {"s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
      "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"}
LANG = "{http://www.w3.org/XML/1998/namespace}lang"

conjuntos = pd.read_csv(SALIDA / "conjuntos_salud.csv")
resumen, indicadores = [], []

for c in conjuntos.itertuples():
    raiz = ET.parse(DISPONIB / f"{c.conjunto.replace('@', '__')}.xml").getroot()
    # Diccionario código -> nombre en inglés, por lista de códigos (codelist)
    nombres = {}
    for cl in raiz.iter("{%s}Codelist" % NS["s"]):
        for code in cl.findall("s:Code", NS):
            nm = [n.text for n in code.findall("c:Name", NS) if n.get(LANG) == "en"]
            nombres[(cl.get("id"), code.get("id"))] = nm[0] if nm else ""
    # Restricción "real": qué códigos aparecen en cada dimensión
    cc = raiz.find(".//s:ContentConstraint", NS)
    obs = None
    for a in cc.iter("{%s}Annotation" % NS["c"]):
        if a.get("id") == "obs_count":
            obs = int(a.findtext("c:AnnotationTitle", namespaces=NS))
    dims, inicio, fin = {}, None, None
    for kv in cc.iter("{%s}KeyValue" % NS["c"]):
        if kv.get("id") == "TIME_PERIOD":
            inicio = kv.findtext(".//c:StartPeriod", namespaces=NS)
            fin = kv.findtext(".//c:EndPeriod", namespaces=NS)
        else:
            dims[kv.get("id")] = [v.text for v in kv.findall("c:Value", NS)]
    # El nombre de un indicador está en la codelist cuyo id contiene "MEASURE"
    def nombre_codigo(dim, cod):
        for (cl, k), v in nombres.items():
            if k == cod and dim.replace("_", "") in cl.replace("_", ""):
                return v
        for (cl, k), v in nombres.items():
            if k == cod:
                return v
        return ""
    medidas = dims.get("MEASURE", [])
    resumen.append({
        "conjunto": c.conjunto, "nombre": c.nombre, "estructura": c.estructura,
        "subtemas_ocde": c.subtemas_ocde, "observaciones": obs,
        "anio_inicio": (inicio or "")[:4], "anio_fin": (fin or "")[:4],
        "n_paises_o_areas": len(dims.get("REF_AREA", [])),
        "n_indicadores": len(medidas),
        "dimensiones": " | ".join(f"{k}({len(v)})" for k, v in dims.items()),
    })
    for m in medidas:
        indicadores.append({"conjunto": c.conjunto, "estructura": c.estructura,
                            "codigo_indicador": m, "indicador": nombre_codigo("MEASURE", m)})

resumen = pd.DataFrame(resumen).sort_values("observaciones", ascending=False)
indicadores = pd.DataFrame(indicadores)
resumen.to_csv(SALIDA / "resumen_conjuntos.csv", index=False, encoding="utf-8-sig")
indicadores.to_csv(SALIDA / "indicadores_catalogo.csv", index=False, encoding="utf-8-sig")

pd.set_option("display.width", 250, "display.max_rows", 200, "display.max_colwidth", 60)
print(resumen[["conjunto", "observaciones", "anio_inicio", "anio_fin",
               "n_paises_o_areas", "n_indicadores"]].to_string(index=False))
print("\nTotal observaciones:", resumen.observaciones.sum())
print("Filas conjunto×indicador:", len(indicadores))
print("Indicadores únicos por (estructura, código):",
      indicadores.drop_duplicates(["estructura", "codigo_indicador"]).shape[0])
