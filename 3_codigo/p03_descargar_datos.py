# ============================================================
# PROCESO 3: Descargar los datos de cada conjunto seleccionado
# Insumo:    4_salidas/tablas/p02_conjuntos_seleccionados.csv (79 conjuntos)
#            1_datos_crudos/disponibilidad/*.xml (orden de las dimensiones)
# Resultado: 1_datos_crudos/datos/<conjunto>.csv.gz  (un archivo comprimido por conjunto)
#            4_salidas/tablas/p03_registro_descargas.csv (qué se bajó, filtro, tamaño)
# Nota: los datos se guardan TAL CUAL llegan de la OCDE (códigos, sin etiquetas);
#       los nombres de los códigos están en los XML de disponibilidad.
# ============================================================

# --- Paquetes ---
# requests: pedir datos a la API de la OCDE
# gzip: comprimir los archivos al guardarlos (como un .zip, pero de un solo archivo)
import requests, gzip, time, sys
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
DATOS = PROYECTO / "1_datos_crudos" / "datos"
DATOS.mkdir(parents=True, exist_ok=True)
TABLAS = PROYECTO / "4_salidas" / "tablas"
API = "https://sdmx.oecd.org/public/rest"
NS_C = "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common}"
OCDE38 = ("AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN "
          "KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA").split()

# --- Paso 3.1: filtros para los dos conjuntos gigantes ---
# Sin filtro pesarían unos 2 GB cada uno. Se baja solo la serie principal.
FILTROS = {
    # Gasto en salud: total de funciones y total de proveedores (todas las fuentes de financiamiento)
    "DSD_SHA@DF_SHA": {"MEASURE": ["EXP_HEALTH"], "FUNCTION": ["_T"], "PROVIDER": ["_T"]},
    # Exposición ambiental (estimación OCDE-IHME): 38 miembros + Perú, ambos sexos, todas las edades
    "DSD_EXP_MORSC@DF_EXP_MORSC": {"REF_AREA": OCDE38 + ["PER"], "AGE": ["_T"], "SEX": ["_T"]},
}

def orden_dimensiones(conjunto):
    """Devuelve las dimensiones del conjunto en el orden que exige la API (sin TIME_PERIOD)."""
    raiz = ET.parse(PROYECTO / "1_datos_crudos" / "disponibilidad" /
                    f"{conjunto.replace('@', '__')}.xml").getroot()
    return [kv.get("id") for kv in raiz.iter(NS_C + "KeyValue") if kv.get("id") != "TIME_PERIOD"]

def clave_filtro(conjunto):
    """Arma la 'clave' SDMX: valores separados por puntos, en el orden de las dimensiones.
    Vacío = todos los valores; '+' = varios valores. Ej.: '..EXP_HEALTH.....'"""
    filtro = FILTROS.get(conjunto)
    if not filtro:
        return "all"
    return ".".join("+".join(filtro.get(d, [])) for d in orden_dimensiones(conjunto))

def descargar(url, destino, intentos=4):
    """Baja la respuesta por partes y la guarda comprimida. Devuelve (código HTTP, bytes)."""
    for i in range(intentos):
        try:
            with requests.get(url, stream=True, timeout=900,
                              headers={"Accept": "application/vnd.sdmx.data+csv; charset=utf-8"}) as r:
                if r.status_code in (429, 503, 504):
                    time.sleep(60 * (i + 1)); continue
                if r.status_code != 200:
                    return r.status_code, 0
                with gzip.open(destino, "wb") as salida:
                    for parte in r.iter_content(chunk_size=1 << 20):
                        salida.write(parte)
                return 200, destino.stat().st_size
        except requests.RequestException as e:
            print("   reintento por error de red:", type(e).__name__)
            time.sleep(30 * (i + 1))
    return -1, 0

# --- Paso 3.2: descargar cada conjunto ---
# Antes: lista de 79 conjuntos | Después: 79 archivos .csv.gz en 1_datos_crudos/datos
conjuntos = pd.read_csv(TABLAS / "p02_conjuntos_seleccionados.csv")
registro = []
for i, c in enumerate(conjuntos.itertuples(), 1):
    archivo = DATOS / f"{c.conjunto.replace('@', '__')}.csv.gz"
    clave = clave_filtro(c.conjunto)
    url = f"{API}/data/{c.agencia},{c.conjunto},{c.version}/{clave}?dimensionAtObservation=AllDimensions"
    if archivo.exists() and archivo.stat().st_size > 0:
        estado, tamanio = 200, archivo.stat().st_size
    else:
        inicio = time.time()
        estado, tamanio = descargar(url, archivo)
        print(f"{i:2d}/{len(conjuntos)} {estado} {tamanio/1e6:7.1f} MB {time.time()-inicio:5.0f}s {c.conjunto}",
              flush=True)
        time.sleep(3)   # pausa de cortesía con la API
    registro.append({"conjunto": c.conjunto, "filtro_clave": clave, "url": url,
                     "estado_http": estado, "mb_comprimido": round(tamanio / 1e6, 2)})

# --- Paso 3.3: verificar ---
registro = pd.DataFrame(registro)
registro.to_csv(TABLAS / "p03_registro_descargas.csv", index=False, encoding="utf-8-sig")
print("Descargas correctas:", (registro["estado_http"] == 200).sum(), "de", len(registro))
print("Tamaño total comprimido (MB):", registro["mb_comprimido"].sum().round(1))
