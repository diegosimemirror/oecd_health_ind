# ============================================================
# EXPLORACIÓN 1: Catálogo de conjuntos de datos de Salud de la OCDE
#               y disponibilidad (qué indicadores, países y años tiene cada uno)
# Insumo:    API pública SDMX de la OCDE (https://sdmx.oecd.org/public/rest)
# Resultado: 1_datos_crudos/catalogo/*.xml          (catálogo completo y temas)
#            1_datos_crudos/disponibilidad/*.xml    (una "ficha de disponibilidad" por conjunto)
#            4_salidas/exploracion/conjuntos_salud.csv  (lista de conjuntos del tema Salud)
# Nota: este script solo DESCARGA y LISTA; no modifica ningún dato.
# ============================================================

# --- Paquetes ---
# requests: hace pedidos a páginas web/API (como abrir una URL, pero desde código)
import requests
# xml.etree.ElementTree: lee archivos XML (texto con etiquetas, formato en que responde la API)
import xml.etree.ElementTree as ET
# pandas: tablas (filas y columnas) como en Excel
import pandas as pd
# time: pausar entre pedidos para no saturar la API de la OCDE
import time, sys, re, html
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1])               # carpeta raíz del proyecto (se pasa al ejecutar)
CATALOGO = PROYECTO / "1_datos_crudos" / "catalogo"
DISPONIB = PROYECTO / "1_datos_crudos" / "disponibilidad"
SALIDA = PROYECTO / "4_salidas" / "exploracion"
API = "https://sdmx.oecd.org/public/rest"
NS = {"s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
      "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"}
LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def descargar(url, destino, intentos=4):
    """Descarga una URL a un archivo; si la API pide esperar (código 429), espera y reintenta."""
    for i in range(intentos):
        r = requests.get(url, timeout=180)
        if r.status_code == 200:
            destino.write_bytes(r.content)
            return True
        if r.status_code in (429, 503):
            time.sleep(30 * (i + 1))
            continue
        print("  aviso:", r.status_code, url)
        return False
    return False


def nombre_en(el):
    """Devuelve el nombre en inglés de un elemento SDMX."""
    for n in el.findall("c:Name", NS):
        if n.get(LANG) == "en":
            return n.text
    return ""


# --- Paso 1.1: descargar el catálogo de conjuntos y el esquema de temas ---
# Antes: nada en disco | Después: dos archivos XML con todos los conjuntos de la OCDE
if not (CATALOGO / "dataflows.xml").exists():
    descargar(f"{API}/dataflow/all/all/latest", CATALOGO / "dataflows.xml")
if not (CATALOGO / "temas_y_categorias.xml").exists():
    descargar(f"{API}/categoryscheme/OECD/OECDCS1/latest?references=categorisation",
              CATALOGO / "temas_y_categorias.xml")

# --- Paso 1.2: quedarse con los conjuntos clasificados en el tema "Health" (HEA) ---
# Antes: ~1 500 conjuntos de todos los temas | Después: solo los del tema Salud
temas = ET.parse(CATALOGO / "temas_y_categorias.xml").getroot()
conjunto_a_subtema = {}
for cz in temas.iter("{%s}Categorisation" % NS["s"]):
    origen, destino = cz.find("s:Source/Ref", NS), cz.find("s:Target/Ref", NS)
    if origen is None or destino is None or destino.get("maintainableParentID") != "OECDCS1":
        continue
    if destino.get("id").startswith("HEA"):
        clave = (origen.get("agencyID"), origen.get("id"))
        conjunto_a_subtema.setdefault(clave, set()).add(destino.get("id"))

catalogo = ET.parse(CATALOGO / "dataflows.xml").getroot()
filas = []
for f in catalogo.iter("{%s}Dataflow" % NS["s"]):
    clave = (f.get("agencyID"), f.get("id"))
    if clave not in conjunto_a_subtema:
        continue
    desc = [d.text or "" for d in f.findall("c:Description", NS) if d.get(LANG) == "en"]
    desc = html.unescape(desc[0]) if desc else ""
    enlaces = re.findall(r'href="([^"]+)"', desc)
    filas.append({
        "agencia": clave[0], "conjunto": clave[1], "version": f.get("version"),
        "nombre": nombre_en(f),
        "estructura": f.find("s:Structure/Ref", NS).get("id"),
        "subtemas_ocde": ";".join(sorted(conjunto_a_subtema[clave])),
        "enlaces_metodologia": " ".join(e for e in enlaces if not e.startswith("mailto")),
        "descripcion": re.sub(r"<[^>]+>", " ", desc).strip()[:500],
    })
conjuntos = pd.DataFrame(filas).drop_duplicates(["agencia", "conjunto"])
print("Conjuntos del tema Salud:", conjuntos.shape)

# --- Paso 1.3: pedir la disponibilidad de cada conjunto (sin bajar los datos) ---
# availableconstraint responde qué códigos existen realmente en cada dimensión
# (indicadores, países, unidades) más el rango de años y el n.º de observaciones.
# Antes: lista de conjuntos | Después: un XML de disponibilidad por conjunto
for i, c in enumerate(conjuntos.itertuples(), 1):
    archivo = DISPONIB / f"{c.conjunto.replace('@', '__')}.xml"
    if archivo.exists():
        continue
    url = (f"{API}/availableconstraint/{c.agencia},{c.conjunto},{c.version}/all/all/all"
           "?mode=exact&references=codelist")
    ok = descargar(url, archivo)
    print(f"{i:3d}/{len(conjuntos)} {'ok ' if ok else 'ERR'} {c.conjunto}")
    time.sleep(2)

conjuntos.to_csv(SALIDA / "conjuntos_salud.csv", index=False, encoding="utf-8-sig")
print("Guardado:", SALIDA / "conjuntos_salud.csv")
